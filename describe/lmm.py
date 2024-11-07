import openai
from PIL import Image
import io
import base64
import yaml


class VisionLanguageModel:
    def __init__(
        self,
        api_key,
        api_base_url=None,
        model_name="gpt-4-vision-preview",
        org_id=None,
        prompt_template=None,
        system_prompt_template=None,
    ):
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.org_id = org_id
        self.prompt_template = prompt_template
        self.system_prompt_template = system_prompt_template
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
        for obj in objects:
            object_id = obj["object_id"]
            object_description = obj.get("object_description", "")
            for img in obj["images"]:
                image_path = img["image_path"]
                pre_description = img.get("pre_description", "")
                try:
                    # Open the image from the local file path
                    image = Image.open(image_path)

                    # Convert the image to RGB mode if it is in RGBA mode
                    if image.mode == "RGBA":
                        image = image.convert("RGB")

                    # Prepare the image for the API
                    image_data = self._prepare_image(image)

                    # Prepare the prompt for the API
                    prompt = self._prepare_prompt(image_data, pre_description)

                    # Call the OpenAI API
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=prompt,
                        max_tokens=300,
                    )

                    # Extract the generated description
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
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def _prepare_prompt(self, image_data, pre_description):
        """
        Prepare the prompt for the API based on the model.

        :param image_data: Base64 encoded string of the image.
        :param pre_description: Optional pre-description text for the image.
        :return: Prepared prompt for the API.
        """
        prompt_text = self.prompt_template.format(pre_description=pre_description)
        return [
            {"role": "system", "content": self.system_prompt_template},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                    },
                ],
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
    prompt_template = config.get("prompt_template")
    system_prompt_template = config.get("system_prompt_template")

    model = VisionLanguageModel(
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_template,
        system_prompt_template,
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
