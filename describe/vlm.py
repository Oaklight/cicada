import argparse
import base64
import io
import logging
import os
import sys
from typing import List, Union

import openai
from PIL import Image
from tqdm import tqdm

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, parent_dir])

from desc_utils import load_object_metadata, save_descriptions

from utils import colorstring, load_config, load_prompts

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class VisionLanguageModel:
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_templates,
        **model_kwargs,
    ):
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.org_id = org_id

        self.model_kwargs = model_kwargs

        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base_url, organization=self.org_id
        )

        self.user_prompt_template = prompt_templates.get("user_prompt_template", "")
        self.system_prompt_template = prompt_templates.get("system_prompt_template", "")

    def query(self, prompt, system_prompt=None):
        messages = [
            {"role": "user", "content": prompt},
        ]

        if system_prompt:
            messages = [
                {"role": "system", "content": system_prompt},
            ] + messages

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **self.model_kwargs,
        )

        return response.choices[0].message.content.strip()

    def query_with_image(
        self,
        prompt: str,
        image: Union[bytes, List[bytes]],
        system_prompt: str = None,
    ):
        """
        Query the VisionLanguageModel with an additional image.

        :param prompt: User prompt text.
        :param image: PIL Image object or image path.
        :param system_prompt: Optional system prompt text.
        :return: Generated response from the model.
        """

        # Prepare the prompt for the API using _prepare_prompt
        full_prompt = self._prepare_prompt(image, prompt)

        if system_prompt:
            full_prompt = [
                {"role": "system", "content": system_prompt},
            ] + full_prompt

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=full_prompt,
            **self.model_kwargs,
        )
        logging.debug(
            colorstring(f"Response: {response.choices[0].message.content}", "yellow")
        )
        return response.choices[0].message.content.strip()

    def generate_descriptions(self, objects: List[dict], save=True):
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

            # Open the images from the local file paths
            images = [Image.open(image_path) for image_path in image_paths]
            image_data = [self._prepare_image(each_image) for each_image in images]

            # Generate description for each image
            descriptions = {
                "object_id": object_id,
                "image_path": image_paths,
                "pre_description": pre_descriptions,
            }
            try:
                description = self.query_with_image(pre_descriptions, image_data)
                descriptions.update(
                    {
                        "generated_description": description,
                        "error": None,
                    }
                )

            except Exception as e:
                descriptions.update(
                    {
                        "generated_description": None,
                        "error": str(e),
                    }
                )

            if save:
                save_descriptions(obj["base_path"], description)
                logging.info(
                    colorstring(f"Saved description for object id: {object_id}", "cyan")
                )

            description_collection.append(description)
            logging.info(
                colorstring(f"Generated description for object id: {object_id}", "cyan")
            )

        return description_collection

    def _prepare_image(self, image):
        """
        Convert the image to a base64 encoded string.

        :param image: PIL Image object.
        :return: Base64 encoded string of the image.
        """
        # Convert the images to RGB mode if they are in RGBA mode
        if image.mode == "RGBA":
            image = image.convert("RGB")

        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def _prepare_prompt(
        self,
        image_data: Union[bytes, List[bytes]],
        text_data: Union[str, List[str]],
    ):
        """
        Prepare the prompt for the API based on the model.

        :param image_data: Base64 encoded string of the image.
        :param text_data: Optional pre-description text for the image.
        :return: Prepared prompt for the API.
        """
        if not isinstance(image_data, list):
            image_data = [image_data]
        if not isinstance(text_data, list):
            text_data = [text_data]

        len_image_data = len(image_data)
        len_text_data = len(text_data)
        if len_image_data != len_text_data:
            # single pre description mode
            content = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{each_image_data}"},
                }
                for each_image_data in image_data
            ]
            if len(each_text_data):
                content.append({"type": "text", "text": text_data})
            content.append({"type": "text", "text": self.user_prompt_template})
        else:
            # multiple pre description mode
            content = []
            for each_image_data, each_text_data in zip(image_data, text_data):
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{each_image_data}"
                        },
                    }
                )
                if len(each_text_data):
                    content.append({"type": "text", "text": each_text_data})
            content.append({"type": "text", "text": self.user_prompt_template})

        return [
            {
                "role": "user",
                "content": content,
            },
        ]


def main():
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

    vlm = VisionLanguageModel(
        describe_vlm_config["api_key"],
        describe_vlm_config.get("api_base_url"),
        describe_vlm_config.get("model_name", "gpt-4o"),
        describe_vlm_config.get("org_id"),
        load_prompts(args.prompts, "vlm"),
        **describe_vlm_config.get("model_kwargs", {}),
    )
    descriptions = vlm.generate_descriptions(image_metadata, args.save)

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
    main()
