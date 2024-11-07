import base64
import io
from typing import List, Union

import openai
import yaml
from PIL import Image
from tqdm import tqdm


class VisionLanguageModel:
    def __init__(
        self,
        api_key,
        api_base_url=None,
        model_name="gpt-4-vision-preview",
        org_id=None,
        prompt_template=None,
        system_prompt_template=None,
        batch_mode=False,
        **model_kwargs,
    ):
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.org_id = org_id
        self.prompt_template = prompt_template
        self.system_prompt_template = system_prompt_template
        self.batch_mode = batch_mode
        self.model_kwargs = model_kwargs
        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base_url, organization=self.org_id
        )

    def generate_descriptions(self, objects):
        """
        Generate descriptions for the given objects and their images.

        :param objects: List of objects with their metadata.
        :return: List of generated descriptions of the images.
        """
        descriptions = []
        for obj in tqdm(objects, desc="Describing objects", unit="object", leave=True):
            object_id = obj["object_id"]
            object_description = obj.get("object_description", "")

            # load images in batch
            image_paths = [img["image_path"] for img in obj["images"]]
            pre_descriptions = [img.get("pre_description", "") for img in obj["images"]]
            # Open the images from the local file paths
            images = [Image.open(image_path) for image_path in image_paths]
            image_data = [self._prepare_image(each_image) for each_image in images]

            pbar = tqdm(
                total=len(images), desc="Processing images...", unit="image", leave=True
            )
            if self.batch_mode:
                print("Batch mode is enabled")
                descriptions.extend(
                    self._try_describe(
                        object_id,
                        object_description,
                        image_paths,
                        pre_descriptions,
                        image_data,
                    )
                )
                pbar.update(len(images))
            else:
                print("In regular mode")
                for each_image_data, each_image_path, each_pre_description in zip(
                    image_data, image_paths, pre_descriptions
                ):
                    descriptions.extend(
                        self._try_describe(
                            object_id,
                            object_description,
                            each_image_path,
                            each_pre_description,
                            each_image_data,
                        )
                    )
                    pbar.update(1)

        return descriptions

    def _try_describe(
        self,
        object_id,
        object_description,
        image_path,
        pre_description,
        image_data,
    ):
        descriptions = []
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
            descriptions.append(
                {
                    "object_id": object_id,
                    "object_description": object_description,
                    "image_path": image_path,
                    "pre_description": pre_description,
                    "generated_description": description,
                }
            )
        except Exception as e:
            descriptions.append(
                {
                    "object_id": object_id,
                    "object_description": object_description,
                    "image_path": image_path,
                    "pre_description": pre_description,
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
        image.save(buffered, format="JPEG")
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
                    "image_url": {"url": f"data:image/jpeg;base64,{each_image_data}"},
                }
                for each_image_data in image_data
            ]
            if len(each_pre_description):
                content.append({"type": "text", "text": pre_description})
            content.append({"type": "text", "text": self.prompt_template})
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
                            "url": f"data:image/jpeg;base64,{each_image_data}"
                        },
                    }
                )
                if len(each_pre_description):
                    content.append({"type": "text", "text": each_pre_description})
            content.append({"type": "text", "text": self.prompt_template})

        return [
            {"role": "system", "content": self.system_prompt_template},
            {
                "role": "user",
                "content": content,
            },
        ]


# Example usage
if __name__ == "__main__":
    # Load configuration from config.yaml
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    # Load image metadata from images.yaml
    with open("images.yaml", "r") as file:
        image_metadata = yaml.safe_load(file)

    api_key = config["api_key"]
    api_base_url = config.get("api_base_url")
    model_name = config.get("model_name", "gpt-4-vision-preview")
    org_id = config.get("org_id")
    prompt_template = config.get("prompt", {}).get("prompt_template")
    system_prompt_template = config.get("prompt", {}).get("system_prompt_template")
    batch_mode = config.get("batch_mode", False)
    model_kwargs = config.get("model_kwargs", {})

    model = VisionLanguageModel(
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_template,
        system_prompt_template,
        batch_mode=batch_mode,
        **model_kwargs,
    )
    descriptions = model.generate_descriptions(image_metadata["objects"])

    for desc in descriptions:
        print(f"Object ID: {desc['object_id']}")
        print(f"Object Description: {desc['object_description']}")
        print(f"Image Path: {desc['image_path']}")
        print(f"Pre-Description: {desc['pre_description']}")
        if "generated_description" in desc:
            print(f"Generated Description:\n{desc['generated_description']}")
        else:
            print(f"Error: {desc['error']}")
        print("-" * 40)
