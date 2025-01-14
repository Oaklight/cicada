import argparse
import logging
import os
import random
import sys
from typing import List

from tqdm import tqdm

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common import vlm
from common.utils import (
    DesignGoal,
    PromptBuilder,
    colorstring,
    image_to_base64,
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

    def featurize_design_goal(self, design_goal: DesignGoal) -> str:
        text_goal = design_goal.text
        ref_images = design_goal.images

        # Prepare the prompt for featurizing the design goal
        prompt = self.featurize_design_prompt["user_prompt_template"].format(
            text_goal=text_goal
        )

        pb = PromptBuilder()
        pb.add_system_prompt(self.featurize_design_prompt["system_prompt_template"])
        pb.add_user_prompt(prompt)
        if ref_images:
            pb.add_text("The following is a set of reference images:")
            pb.add_images(ref_images)

        # Query the VLM with images and prompt
        response = self.query_with_promptbuilder(pb)

        return response

    def handle_user_feedback(self, user_response):
        """
        Processes user feedback to either confirm a proposed design or clarify an unclear point.
        """
        if "confirm" in user_response.lower():
            return "Design confirmed. Proceeding to implementation."
        elif "clarify" in user_response.lower():
            clarification_prompt = "Please provide more details about the following aspect: [specific unclear point]."
            return self.query(clarification_prompt)
        else:
            return (
                "Invalid response. Please confirm the design or request clarification."
            )


def _main():
    parser = argparse.ArgumentParser(description="Vision Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save generated descriptions to metadata.yaml",
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

    text_goal = "I need a table"
    ref_images = None
    design_goal = DesignGoal(text_goal, ref_images)

    response = vlm.featurize_design_goal(design_goal)


# Example usage
if __name__ == "__main__":
    _main()
