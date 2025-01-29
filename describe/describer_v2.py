import argparse
import logging
import os
import signal
import sys
from typing import Any, Dict, Tuple

import questionary
from questionary import Style

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common import vlm
from common.basics import DesignGoal, PromptBuilder
from common.utils import (
    colorstring,
    cprint,
    load_config,
    load_prompts,
    parse_json_response,
    setup_logging,
)

logger = logging.getLogger(__name__)

MAX_IMAGES_PER_QUERY = 4  # to prevent input exceed max input token

# Define a custom style for questionary prompts
custom_style = Style(
    [
        ("question", "fg:#ff0000 bold"),  # Red and bold for questions
        ("answer", "fg:#00ff00 underline"),  # Green and underlined for answers
    ]
)


class Describer(vlm.VisionLanguageModel):
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_templates,
        **model_kwargs,
    ):
        super().__init__(
            api_key,
            api_base_url,
            model_name,
            org_id,
            **model_kwargs,
        )
        self.reverse_engineer_prompt = prompt_templates.get("reverse_engineer", {})
        self.featurize_design_prompt = prompt_templates.get("featurize_design", {})

    def featurize_design_goal_with_confidence(
        self, design_goal: DesignGoal, user_feedback: str = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Generate a refined design based on the user's goal.
        Returns a tuple of (parsed JSON result, raw response).
        """
        text_goal = design_goal.text
        ref_images = design_goal.images
        logging.debug(
            f"Featurizing design goal: {text_goal}, with images: {ref_images}"
        )

        pb = PromptBuilder()
        pb.add_system_prompt(self.featurize_design_prompt["system_prompt_template"])

        pb.add_user_prompt(f"The current design goal: '{text_goal}'.")

        if ref_images:
            pb.add_text("The following reference images are provided:")
            pb.add_images(ref_images)

        if user_feedback:
            pb.add_text(
                "The user has provided the following feedback, please revise the current design against the feedback:"
            )
            pb.add_text(user_feedback)

        pb.add_user_prompt(self.featurize_design_prompt["user_prompt_template"])

        # Query the VLM with images and prompt
        response = self.query_with_promptbuilder(pb)

        # Parse the JSON response
        json_result = parse_json_response(response)

        return json_result, response

    def decompose_design(self, design_goal: DesignGoal) -> Tuple[Dict[str, Any], str]:
        """
        Decompose the design into its constituent parts, specifying building methods and geometric details.
        Returns a tuple of (parsed JSON result, raw response).
        """
        text_goal = design_goal.text
        ref_images = design_goal.images
        logging.debug(
            f"Decomposing design goal: {text_goal}, with images: {ref_images}"
        )

        # Dynamically construct the text_goal_section based on whether text_goal is provided
        if text_goal:
            text_goal_section = (
                f"The user has provided the following design goal: '{text_goal}'. "
                "Use this as the primary input for reverse engineering the design. "
                "The provided images are for reference only.\n\n"
            )
        else:
            text_goal_section = (
                "The user has provided the following images. "
                "Use these as the primary input for reverse engineering the design.\n\n"
            )

        # Replace the {text_goal_section} placeholder in the user prompt template
        user_prompt = self.reverse_engineer_prompt["user_prompt_template"].format(
            text_goal_section=text_goal_section
        )

        # Prepare the prompt for decomposing the design
        pb = PromptBuilder()
        pb.add_system_prompt(self.reverse_engineer_prompt["system_prompt_template"])
        pb.add_user_prompt(user_prompt)

        if ref_images:
            pb.add_text("The following is a set of reference images:")
            pb.add_images(ref_images)

        # Query the VLM with images and prompt
        response = self.query_with_promptbuilder(pb)

        # Parse the JSON response
        json_result = parse_json_response(response)

        return json_result, response

    def _analyze_text_goal_against_images(
        self, text_goal: str, ref_images: list
    ) -> bool:
        """
        Analyze the text goal against reference images and ask for confirmation if there's a conflict.
        Returns True if the user confirms to proceed, False otherwise.
        """
        logging.debug(f"Analyzing text goal against reference images: {text_goal}")

        # Prepare a prompt to analyze the text goal against images
        analysis_prompt = (
            "The user has provided the following text goal:\n"
            f"{text_goal}\n\n"
            "The following reference images are also provided:\n"
            f"{ref_images}\n\n"
            "Your task is to analyze whether the text goal aligns with the reference images. "
            "If there is a conflict, highlight it and ask for user confirmation.\n\n"
            "Return the analysis in JSON format."
        )

        pb = PromptBuilder()
        pb.add_system_prompt(self.featurize_design_prompt["system_prompt_template"])
        pb.add_user_prompt(analysis_prompt)

        # Query the VLM with the analysis prompt
        response = self.query_with_promptbuilder(pb)
        analysis_result = parse_json_response(response)

        # If there's a conflict, ask for user confirmation
        if analysis_result.get("conflict_detected", False):
            print(
                colorstring(
                    "\nConflict detected between text goal and reference images.",
                    "bright_red",
                )
            )
            confirmation = questionary.confirm(
                "The system detected a conflict between your text goal and reference images. Do you want to proceed with the current text goal?",
                style=custom_style,
            ).ask()

            if not confirmation:
                print(
                    colorstring(
                        "Please revise your text goal or reference images and try again.",
                        "bright_yellow",
                    )
                )
                return False

        return True

    def design_feedback_loop(
        self,
        design: DesignGoal,
        iteration: int = 1,
        max_iterations: int = 5,
        feedback: str = None,
    ) -> DesignGoal:
        """
        Execute the complete design feedback cycle using recursion.
        """

        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\nProcess interrupted by user. Exiting...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Base case: Maximum iterations reached
        if iteration > max_iterations:
            logger.warning(f"Maximum iterations ({max_iterations}) reached")
            # decompose the design and return the result
            updated_design = self._update_design_with_decomposition(design)

            return updated_design

        logger.info(f"Starting iteration {iteration}/{max_iterations}")
        try:
            logging.debug(f"Current Design: {design.text}")

            # At the start of the first iteration, check for conflicts between text goal and reference images
            if iteration == 1 and design.images:
                if not self._analyze_text_goal_against_images(
                    design.text, design.images
                ):
                    sys.exit(0)

            # Generate VLM response and parse the JSON result
            updated_design_result, response = (
                self.featurize_design_goal_with_confidence(design, feedback)
            )
            updated_design_text = updated_design_result.get(
                "current_design", design.text
            )
            updated_design = DesignGoal(updated_design_text, design.images)

            # Display the proposed design to the user
            print(f"\n{'='*40}\nIteration {iteration}/{max_iterations}")
            print(f"Proposed Design:\n{updated_design_text}")

            # Always require confirmation after the first iteration
            if iteration == 1:
                print(
                    colorstring(
                        "\nThe system requires your feedback or confirmation after the first iteration.",
                        "bright_yellow",
                    )
                )
            elif updated_design_result.get("needs_human_validation", True):
                print(
                    colorstring(
                        "\nThe system requires your feedback or confirmation.",
                        "bright_yellow",
                    )
                )
            else:
                print(
                    colorstring(
                        "\nThe system is confident in this solution.", "bright_blue"
                    )
                )

            # Always allow the user to provide feedback            # Define static choices once
            choices = [
                {"name": "Provide Feedback", "value": "feedback"},
                {"name": "Confirm", "value": "confirm"},
                {"name": "Exit", "value": "exit"},
            ]
            # Multi-choice prompt with dynamic choices
            action = questionary.select(
                "What would you like to do?",
                choices=choices,
                style=custom_style,
            ).ask()

            if action == "exit":
                logger.info("Exiting feedback loop by user request")
                return updated_design

            elif action == "confirm":
                # Confirm the design
                logger.info("Design confirmed. Decomposing the final design...")
                updated_design = self._update_design_with_decomposition(updated_design)

                return updated_design

            elif action == "feedback":
                # Allow the user to provide custom feedback
                feedback = questionary.text(
                    "Please provide your feedback:",
                    validate=lambda text: len(text.strip()) > 0
                    or "Feedback cannot be empty.",
                    style=custom_style,
                ).ask()

                # Recursively call the function with the updated design, incremented iteration, and feedback
                return self.design_feedback_loop(
                    updated_design, iteration + 1, max_iterations, feedback
                )

        except Exception as e:
            logger.error(f"Iteration {iteration} failed: {e}")
            raise e

    def _update_design_with_decomposition(self, updated_design) -> DesignGoal:
        decomposition_result, _ = self.decompose_design(updated_design)
        logger.info(f"Decomposition Result:\n{decomposition_result}")
        print(f"\n{'='*40}\nDecomposition Result:\n{decomposition_result}")

        # Store the decomposition result in design_goal.extra
        if not hasattr(updated_design, "extra"):
            updated_design.extra = {}
        updated_design.extra["decomposition"] = decomposition_result
        return updated_design


def _main():
    parser = argparse.ArgumentParser(description="Vision Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "text_goal",
        type=str,
        help="The text goal for the design",
    )
    parser.add_argument(
        "-img",
        "--ref_images",
        type=str,
        default=None,
        help="Paths to reference images for the design",
    )
    args = parser.parse_args()

    describe_vlm_config = load_config(args.config, "describe-vlm")

    vlm = Describer(
        describe_vlm_config["api_key"],
        describe_vlm_config.get("api_base_url"),
        describe_vlm_config.get("model_name", "gpt-4o"),
        describe_vlm_config.get("org_id"),
        load_prompts(args.prompts, "describe-vlm"),
        **describe_vlm_config.get("model_kwargs", {}),
    )

    design_goal = DesignGoal(args.text_goal, args.ref_images)
    print(design_goal)

    # Run the feedback loop process
    try:
        final_design = vlm.design_feedback_loop(design_goal)
        logger.info("Design process completed successfully")
        logger.info(colorstring(f"Final Design:\n{final_design}", "white"))

    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Design process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_logging()

    _main()
