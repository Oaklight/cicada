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
from common.utils import colorstring, image_to_base64, load_config, load_prompts
from describe.utils import load_object_metadata, save_descriptions

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_IMAGES_PER_QUERY = 4  # to prevent input exceed max input token


class DescriberVLM(vlm.VisionLanguageModel):
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

    def generate_descriptions_metadata(self, objects: List[dict], save=True):
        """
        Generate descriptions for the given objects and their images.

        :param objects: List of objects with their metadata.
        :return: List of generated descriptions of the images.
        """
        description_collection = []
        for obj in tqdm(objects, desc="Describing objects", unit="object", leave=True):
            logging.debug(colorstring(f"Processing object: {obj['object_id']}", "cyan"))
            object_id = obj["object_id"]
            object_description = obj.get("object_description", "")

            # Load images in batch
            image_paths = [
                os.path.join(obj["base_path"], img["image_path"])
                for img in obj["images"]
            ]
            pre_descriptions = [img.get("pre_description", "") for img in obj["images"]]

            # open and convert image to base64
            image_data = [image_to_base64(image_path) for image_path in image_paths]

            # Generate description for each image
            metadata_dict = {
                "object_id": object_id,
                "image_path": image_paths,
                "pre_description": pre_descriptions,
                "generated_description": None,
                "error": None,
            }
            try:
                # Flatten the sampled pairs into a list
                # images_with_pre_descriptions = [
                #     item for pair in zip(pre_descriptions, image_data) for item in pair
                # ]
                # sample uniformly half of the zip
                packed_images = list(
                    zip(pre_descriptions, image_data)
                )  # Pack images and pre-descriptions together
                images_with_pre_descriptions = random.sample(
                    packed_images, min(MAX_IMAGES_PER_QUERY, len(packed_images))
                )
                images_with_pre_descriptions = [
                    item for pair in images_with_pre_descriptions for item in pair
                ]  # Flatten the sampled pairs into a list
                description = self.query_with_image(
                    prompt=self.reverse_engineer_prompt["user_prompt_template"],
                    images_with_text=images_with_pre_descriptions,
                    system_prompt=self.reverse_engineer_prompt[
                        "system_prompt_template"
                    ],
                )

                metadata_dict.update({"generated_description": description})

            except Exception as e:
                metadata_dict.update({"error": str(e)})

            if save:
                save_descriptions(obj["base_path"], metadata_dict)
                logging.info(
                    colorstring(f"Saved description for object id: {object_id}", "cyan")
                )

            description_collection.append(metadata_dict)
            logging.info(
                colorstring(f"Generated description for object id: {object_id}", "cyan")
            )

        return description_collection


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

    describe_vlm_config = config["describe-vlm"]

    vlm = DescriberVLM(
        describe_vlm_config["api_key"],
        describe_vlm_config.get("api_base_url"),
        describe_vlm_config.get("model_name", "gpt-4o"),
        describe_vlm_config.get("org_id"),
        load_prompts(args.prompts, "describe-vlm"),
        **describe_vlm_config.get("model_kwargs", {}),
    )
    descriptions = vlm.generate_descriptions_metadata(image_metadata, args.save)

    for desc in descriptions:
        logging.debug(f"Object ID: {desc['object_id']}")
        logging.debug(f"Image Path: {desc['image_path']}")
        logging.debug(f"Pre-Description: {desc['pre_description']}")
        if "generated_description" in desc:
            logging.debug(f"Generated Description:\n{desc['generated_description']}")
        else:
            logging.debug(f"Error: {desc['error']}")
        logging.debug("-" * 40)


# Example usage
if __name__ == "__main__":
    _main()
