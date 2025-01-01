import argparse
import logging
import os
import sys
from typing import List

from tqdm import tqdm
import yaml

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common import vlm
from common.utils import colorstring, image_to_base64, load_config, load_prompts
from describe.utils import load_object_metadata, save_descriptions

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class VisualQualityVLM(vlm.VisionLanguageModel):
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
        self.user_prompt_template = prompt_templates.get("user_prompt_template", "")
        self.system_prompt_template = prompt_templates.get("system_prompt_template", "")

    def generate_visual_questions_from_description(
        self, text_data: str, image_data: bytes | List[bytes] = None
    ) -> dict:
        """
        Generate visual quality control questions from the given text and optional image data.

        :param text_data: The text description of the design goal.
        :param image_data: Byte data or list of byte data representing image(s) (optional).
        :return: Dictionary with categories as keys and lists of questions as values.
        """
        # Use the user prompt template and format it with the text data
        prompt = self.user_prompt_template.format(text=text_data)

        # If image data is provided, append a note about the attached image
        if image_data:
            prompt += "\nReference Image: [attached]"

        # Query the VLM with the appropriate method
        if image_data:
            if isinstance(image_data, bytes):
                image_data = [image_data]
            response = self.query_with_image(
                prompt, image_data, system_prompt=self.system_prompt_template
            )
        else:
            response = self.query(prompt, system_prompt=self.system_prompt_template)

        logging.info(response)
        # Parse the response to extract questions by category
        # Assuming the model responds with categories and questions in a structured format
        # This is a simplified example; actual parsing may require more complex logic
        response_lines = response.split("\n")
        questions = {}
        current_category = None
        for line in response_lines:
            if line.strip().endswith(":"):
                current_category = line.strip()[:-1]
                questions[current_category] = []
            elif line.strip().startswith("- "):
                if current_category:
                    questions[current_category].append(line.strip()[2:])
        return questions


def _main():
    parser = argparse.ArgumentParser(description="Vision Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "--task",
        default="tasks.yaml",
        help="Path to the task YAML file or directory containing images from a single object",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save generated descriptions to metadata.yaml",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    image_metadata = load_object_metadata(args.task)

    describe_vlm_config = config["visualquality-vlm"]

    # Initialize the VisualQualityVLM
    vlm = VisualQualityVLM(
        describe_vlm_config["api_key"],
        describe_vlm_config.get("api_base_url"),
        describe_vlm_config.get("model_name", "gpt-4o"),
        describe_vlm_config.get("org_id"),
        load_prompts(args.prompts, "visualquality-vlm"),
        **describe_vlm_config.get("model_kwargs", {}),
    )

    # Example usage of generate_visual_questions_from_description
    for obj_meta in image_metadata:
        text_data = obj_meta.get("object_description", "")
        image_path = (
            os.path.join(obj_meta["base_path"], obj_meta["images"][0]["image_path"])
            if obj_meta.get("images")
            else None
        )
        image_data = image_to_base64(image_path) if image_path else None
        metadata_json_path = os.path.join(obj_meta["base_path"], "metadata.json")
        if os.path.exists(metadata_json_path):
            with open(metadata_json_path, "r") as f:
                metadata_json = yaml.safe_load(f)
            text_data = metadata_json.get("object_description", text_data)

        logging.info(f"object_description:\n{text_data}")
        questions = vlm.generate_visual_questions_from_description(
            text_data, image_data
        )

        logging.info(f"Generated Questions for {obj_meta.get('object_id', 'Unknown')}:")
        logging.info(questions)
        logging.info("-" * 40)


if __name__ == "__main__":
    _main()
