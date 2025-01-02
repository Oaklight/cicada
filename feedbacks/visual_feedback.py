import argparse
import logging
import os
import sys
from typing import List

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common import vlm
from common.utils import colorstring, image_to_base64, load_config, load_prompts
from describe.utils import (
    get_images_from_folder,
    load_object_metadata,
    save_descriptions,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class VisualFeedback(vlm.VisionLanguageModel):
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
        reference_images: List[bytes],
        rendered_images: List[bytes],
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

        # Attach reference and rendered images
        images = reference_images + rendered_images

        # Query the VLM with images and prompt
        response = self.query_with_image(
            prompt,
            images,
            system_prompt=self.visual_feedback_prompts["system_prompt_template"],
        )

        # Extract and return the feedback paragraph
        feedback = response.strip()
        return feedback


def _main():
    parser = argparse.ArgumentParser(description="Visual Feedback Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "--design_goal", required=True, help="Text description of the design goal"
    )
    parser.add_argument(
        "--reference_images", help="Path to the folder containing reference images"
    )
    parser.add_argument(
        "--rendered_images",
        required=True,
        help="Path to the folder containing rendered object images",
    )
    args = parser.parse_args()

    config = load_config(args.config).get("visual_feedback")
    print(config)
    prompt_templates = load_prompts(args.prompts, "visual_feedback")
    print(prompt_templates)
    # Initialize the VisualFeedback
    visual_feedback = VisualFeedback(
        config["api_key"],
        config.get("api_base_url"),
        config.get("model_name", "gpt-4"),
        config.get("org_id"),
        prompt_templates,
        **config.get("model_kwargs", {}),
    )

    # Convert images to base64
    reference_images = (
        [image_to_base64(img) for img in get_images_from_folder(args.reference_images)]
        if args.reference_images
        else []
    )
    rendered_images = [
        image_to_base64(img) for img in get_images_from_folder(args.rendered_images)
    ]

    # Generate feedback
    feedback = visual_feedback.generate_feedback_paragraph(
        args.design_goal, reference_images, rendered_images
    )

    # Print the feedback
    print(feedback)


if __name__ == "__main__":
    _main()
