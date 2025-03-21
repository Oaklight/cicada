import argparse
import logging
from typing import Any, Dict, List

from cicada.core import model
from cicada.core.basics import PromptBuilder


logger = logging.getLogger(__name__)


class VisualFeedback(model.MultiModalModel):
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
        self.visual_feedback_prompts = prompt_templates

    def generate_feedback_paragraph(
        self,
        design_goal: str,
        reference_images: List[str] | None,
        rendered_images: List[str],
    ) -> str:
        """
        Generate a feedback paragraph comparing the rendered object with the design goal and reference images.
        Focus on geometry, shape, and physical feasibility.

        :param design_goal: Text description of the design specifications.
        :param reference_images: List of byte data for reference images.
        :param rendered_images: List of byte data for rendered object images.
        :return: A paragraph of feedback highlighting hits and misses.
        """
        # Use the user prompt template and format it with the design goal
        prompt = self.visual_feedback_prompts["user_prompt_template"].format(
            text=design_goal
        )

        pb = PromptBuilder()
        pb.add_system_message(self.visual_feedback_prompts["system_prompt_template"])
        pb.add_user_message(prompt)
        if reference_images:
            pb.add_text("The following is a set of reference images:")
            pb.add_images(reference_images)
        pb.add_text("The following is a set of rendered object images:")
        pb.add_images(rendered_images)

        # Query the VLM with images and prompt
        response = self.query(prompt_builder=pb, stream=self.stream)["content"]

        # Extract and return the feedback paragraph
        feedback = response.strip()
        return feedback


def parse_args() -> Dict[str, Any]:
    """
    Parse command line arguments.

    Returns:
        Dict[str, Any]: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Visual Feedback Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts", help="Path to the prompts YAML file or folder"
    )
    parser.add_argument(
        "--design_goal",
        required=True,
        help="Text description of the design goal or path to a JSON file containing the design goal",
    )
    parser.add_argument(
        "--reference_images", help="Path to the folder containing reference images"
    )
    parser.add_argument(
        "--rendered_images",
        required=True,
        help="Path to the folder containing rendered object images",
    )
    return parser.parse_args()


if __name__ == "__main__":
    from cicada.core.utils import (
        cprint,
        load_config,
        load_prompts,
        parse_design_goal,
        setup_logging,
    )

    args = parse_args()

    config = load_config(args.config, "visual_feedback")
    prompt_templates = load_prompts(args.prompts, "visual_feedback")

    # Initialize the VisualFeedback
    visual_feedback = VisualFeedback(
        config["api_key"],
        config.get("api_base_url"),
        config.get("model_name", "gpt-4"),
        config.get("org_id"),
        prompt_templates,
        **config.get("model_kwargs", {}),
    )

    # Parse the design goal
    design_goal = parse_design_goal(args.design_goal)

    # Generate feedback
    feedback = visual_feedback.generate_feedback_paragraph(
        design_goal, args.reference_images, args.rendered_images
    )

    # Print the feedback
    cprint(feedback, "cyan")
