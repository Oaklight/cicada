import argparse
import base64
import io
import json
import os
import sys
from typing import List, Union

import openai
from PIL import Image
from tqdm import tqdm

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from desc_utils import load_config, load_prompts
from llm import LLM


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

    def generate_descriptions(self, objects: List[dict], save=True):
        """
        Generate descriptions for the given objects and their images.

        :param objects: List of objects with their metadata.
        :return: List of generated descriptions of the images.
        """
        description_collection = []
        for obj in tqdm(objects, desc="Describing objects", unit="object", leave=True):
            object_id = obj["object_id"]
            object_description = obj.get("object_description", "")

            # load images in batch
            image_paths = [
                os.path.join(obj["base_path"], img["image_path"])
                for img in obj["images"]
            ]
            pre_descriptions = [img.get("pre_description", "") for img in obj["images"]]
            # Open the images from the local file paths
            images = [Image.open(image_path) for image_path in image_paths]
            image_data = [self._prepare_image(each_image) for each_image in images]

            description = self._try_describe(
                object_id,
                image_paths,
                pre_descriptions,
                image_data,
            )
            if save:
                save_descriptions(obj["base_path"], description)
            description_collection.append(description)
        return description_collection

    def _try_describe(
        self,
        object_id,
        image_path,
        pre_description,
        image_data,
    ):
        descriptions = {
            "object_id": object_id,
            "image_path": image_path,
            "pre_description": pre_description,
        }
        try:
            # Prepare the images for the API
            prompt = self._prepare_prompt(image_data, pre_description)

            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=prompt,
                **self.model_kwargs,
            )

            # Extract the generated descriptions
            description = response.choices[0].message.content
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
        return descriptions

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
        pre_description: Union[str, List[str]],
    ):
        """
        Prepare the prompt for the API based on the model.

        :param image_data: Base64 encoded string of the image.
        :param pre_description: Optional pre-description text for the image.
        :return: Prepared prompt for the API.
        """
        if not isinstance(image_data, list):
            image_data = [image_data]
        if not isinstance(pre_description, list):
            pre_description = [pre_description]

        len_image_data = len(image_data)
        len_pre_description = len(pre_description)
        if len_image_data != len_pre_description:
            # single pre description mode
            content = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{each_image_data}"},
                }
                for each_image_data in image_data
            ]
            if len(each_pre_description):
                content.append({"type": "text", "text": pre_description})
            content.append({"type": "text", "text": self.user_prompt_template})
        else:
            # multiple pre description mode
            content = []
            for each_image_data, each_pre_description in zip(
                image_data, pre_description
            ):
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{each_image_data}"
                        },
                    }
                )
                if len(each_pre_description):
                    content.append({"type": "text", "text": each_pre_description})
            content.append({"type": "text", "text": self.user_prompt_template})

        return [
            {"role": "system", "content": self.system_prompt_template},
            {
                "role": "user",
                "content": content,
            },
        ]


def load_image_metadata(task_path: str) -> List[dict]:
    if os.path.isdir(task_path):
        directory = task_path
        image_metadata = {
            "object_id": os.path.basename(directory),
            "object_description": "",
            "base_path": directory,
            "images": [],
        }
        for file in os.listdir(directory):
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                pre_description = (
                    file.split(".")[0].replace("-", " ").replace("_", " ").strip()
                )
                image_metadata["images"].append(
                    {"image_path": file, "pre_description": pre_description}
                )
        return [image_metadata]
    else:
        return load_config(task_path)


def save_descriptions(
    base_dirs: Union[str, List[str]], descriptions: Union[dict, List[dict]]
):

    if not isinstance(base_dirs, list):
        base_dirs = [base_dirs]
    if not isinstance(descriptions, list):
        descriptions = [descriptions]

    assert len(base_dirs) == len(
        descriptions
    ), "Number of base paths and descriptions do not match"

    for directory, desc in zip(base_dirs, descriptions):
        metadata = {}
        metadata_path = os.path.join(directory, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as file:
                metadata = json.load(file)

        # extend metadata.json with the new descriptions
        metadata.update(desc)

        with open(metadata_path, "w") as file:
            json.dump(metadata, file, indent=4)


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
    image_metadata = load_image_metadata(args.task)

    describe_vlm_config = config["describe-vlm"]
    assist_llm_config = config["assist-llm"]

    vlm = VisionLanguageModel(
        describe_vlm_config["api_key"],
        describe_vlm_config.get("api_base_url"),
        describe_vlm_config.get("model_name", "gpt-4o"),
        describe_vlm_config.get("org_id"),
        load_prompts(args.prompts, "vlm"),
        **describe_vlm_config.get("model_kwargs", {}),
    )
    descriptions = vlm.generate_descriptions(image_metadata, args.save)

    # llm = LLM(
    #     assist_llm_config["api_key"],
    #     assist_llm_config.get("api_base_url"),
    #     assist_llm_config.get("model_name", "gpt-4"),
    #     assist_llm_config.get("org_id"),
    #     load_prompts(args.prompts, "llm"),
    #     **assist_llm_config.get("model_kwargs", {}),
    # )

    # # extract more percise object descriptions
    # for desc in descriptions:
    #     if "generated_description" in desc:
    #         desc["object_description"] = llm.extract_object_description(
    #             desc["generated_description"]
    #         )

    for desc in descriptions:
        print(f"Object ID: {desc['object_id']}")
        print(f"Image Path: {desc['image_path']}")
        print(f"Pre-Description: {desc['pre_description']}")
        if "generated_description" in desc:
            print(f"Generated Description:\n{desc['generated_description']}")
        else:
            print(f"Error: {desc['error']}")
        print("-" * 40)


# Example usage
if __name__ == "__main__":
    main()
