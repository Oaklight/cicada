import argparse
import logging
import os
import sys
from typing import Tuple, Dict, Any

from tqdm import tqdm

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common import vlm
from common.utils import (
    DesignGoal,
    PromptBuilder,
    colorstring,
    load_config,
    load_prompts,
)
from describe.utils import load_object_metadata, save_descriptions


# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_IMAGES_PER_QUERY = 4  # to prevent input exceed max input token


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

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from VLM, handling potential errors"""
        import json

        try:
            # Extract JSON content from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]

            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response: {str(e)}")
            logging.debug(f"Original response: {response}")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error parsing response: {str(e)}")
            return {}

    def featurize_design_goal_with_confidence(
        self, design_goal: DesignGoal, user_feedback: str = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Generate a refined design based on the user's goal and optional feedback.
        Returns a tuple of (parsed JSON result, raw response).
        """
        text_goal = design_goal.text
        ref_images = design_goal.images
        logging.debug(
            f"Featurizing design goal: {text_goal}, with images: {ref_images}"
        )

        # Prepare the prompt for featurizing the design goal
        prompt = self.featurize_design_prompt["user_prompt_template"].format(
            text_goal=text_goal,
            user_feedback=f"User Feedback: {user_feedback}" if user_feedback else "",
        )

        pb = PromptBuilder()
        pb.add_system_prompt(self.featurize_design_prompt["system_prompt_template"])
        pb.add_user_prompt(prompt)

        if ref_images:
            pb.add_text("The following is a set of reference images:")
            pb.add_images(ref_images)

        # Query the VLM with images and prompt
        response = self.query_with_promptbuilder(pb)

        # Parse the JSON response
        result = self._parse_json_response(response)

        return result, response

    def handle_user_feedback(
        self, user_response: str, current_design: DesignGoal
    ) -> Tuple[str, str, DesignGoal]:
        """
        Handle user feedback by generating a new design or confirming the current one.
        Returns a tuple of (status, message, updated_design).
        """
        if user_response.lower() == "confirm":
            return ("confirmed", "Design confirmed", current_design)

        # Generate a new design based on the user's feedback
        updated_design_result, _ = self.featurize_design_goal_with_confidence(
            current_design, user_response
        )

        # Ensure the updated design is properly created
        updated_design = DesignGoal(
            updated_design_result.get("current_design", ""), current_design.images
        )

        # Determine the status based on whether human validation is needed
        if updated_design_result.get("needs_human_validation", True):
            return ("needs_update", "Design updated based on feedback", updated_design)
        else:
            return ("confirmed", "Design updated and validated", updated_design)

    def design_feedback_loop(
        self, initial_design: DesignGoal, max_iterations: int = 5
    ) -> DesignGoal:
        """Execute the complete design feedback cycle"""
        current_design = initial_design
        iteration = 1

        while iteration <= max_iterations:
            logging.info(f"Starting iteration {iteration}/{max_iterations}")
            try:
                logging.debug(f"Current Design: {current_design.text}")
                # Generate VLM response and parse the JSON result
                result, response = self.featurize_design_goal_with_confidence(
                    current_design
                )
                logging.debug(f"Iteration {iteration} Response:\n{response}")

                # Display the proposed design to the user
                print(f"\n{'='*40}\nIteration {iteration}/{max_iterations}")
                print(f"Proposed Design:\n{result.get('current_design', '')}")

                if result.get("needs_human_validation", True):
                    print("\nThe system requires your feedback or confirmation.")
                    user_input = input(
                        "Type 'confirm' to accept or provide feedback (or 'exit' to quit): "
                    ).strip()

                    if user_input.lower() == "exit":
                        logging.info("Exiting feedback loop by user request")
                        return current_design
                else:
                    print("\nThe system is confident in this solution.")
                    user_input = input(
                        "Type 'confirm' to accept or provide feedback (or 'exit' to quit): "
                    ).strip()

                    if user_input.lower() == "exit":
                        logging.info("Exiting feedback loop by user request")
                        return current_design

                # Process feedback
                status, message, updated_design = self.handle_user_feedback(
                    user_input, current_design
                )
                print(f"\nSystem: {message}")

                if status == "confirmed":
                    return updated_design

                # Ensure current_design is updated for the next iteration
                current_design = updated_design
                logging.debug(
                    f"Updated Design for Next Iteration:\n{current_design.text}"
                )
                iteration += 1

            except Exception as e:
                logging.error(f"Iteration {iteration} failed: {e}")
                raise

        logging.warning(f"Maximum iterations ({max_iterations}) reached")
        return current_design


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
        "-ref",
        "--ref_images",
        type=str,
        default=None,
        nargs="*",
        help="Paths to reference images for the design",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    describe_vlm_config = config["describe-vlm"]

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
        logging.info("Design process completed successfully")
        logging.info(colorstring(f"Final Design:\n{final_design}", "white"))

    except KeyboardInterrupt:
        logging.warning("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Design process failed: {e}")
        sys.exit(1)
    # response = vlm.featurize_design_goal_with_confidence(design_goal)
    # logging.info(f"Response: {response}")


# Example usage
if __name__ == "__main__":
    _main()
