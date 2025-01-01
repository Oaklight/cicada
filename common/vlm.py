import argparse
import logging
import os
import sys
from abc import ABC
from typing import List

import openai
import tenacity

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common import llm
from common.utils import colorstring, image_to_base64, load_config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class VisionLanguageModel(llm.LanguageModel, ABC):
    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        model_name: str,
        org_id: str,
        **model_kwargs,
    ):
        """
        Initialize the VisionLanguageModel.

        :param api_key: The API key for the OpenAI service.
        :param api_base_url: The base URL for the OpenAI API.
        :param model_name: The name of the model to use.
        :param org_id: The organization ID for the OpenAI service.
        :param model_kwargs: Additional keyword arguments for the model.
        """
        super().__init__(
            api_key,
            api_base_url,
            model_name,
            org_id,
            **model_kwargs,
        )

    def _prepare_prompt(
        self,
        image_data: bytes | List[bytes],
        text_data: str | List[str],
    ) -> List[dict]:
        """
        Prepare the prompt for the API based on the provided image and text data.

        :param image_data: A single base64-encoded image or a list of such images.
        :param text_data: A single text description or a list of text descriptions.
        :return: A list containing a single "user" role prompt with the prepared content.
        """
        if not isinstance(image_data, list):
            image_data = [image_data]
        if not isinstance(text_data, list):
            text_data = [text_data]

        if len(image_data) != len(text_data):
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

        return [
            {
                "role": "user",
                "content": content,
            },
        ]

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),  # Stop after 3 attempts
        wait=tenacity.wait_random_exponential(
            multiplier=1, min=2, max=10
        ),  # Exponential backoff with randomness
        retry=tenacity.retry_if_exception_type(
            openai.APIError
        ),  # Retry only on specific exceptions related to OpenAI API
        reraise=True,  # Reraise the last exception if all retries fail
    )
    def query_with_image(
        self,
        prompt: str,
        image: bytes | List[bytes],
        system_prompt: str = None,
    ) -> str:
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


# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vision Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    describe_vlm_config = config["describe-vlm"]
    image_path = "../data/cute-cat-with-glass.jpg"
    image_data = image_to_base64(image_path)

    vlm = VisionLanguageModel(
        describe_vlm_config["api_key"],
        describe_vlm_config.get("api_base_url"),
        describe_vlm_config.get("model_name", "gpt-4o"),
        describe_vlm_config.get("org_id"),
        **describe_vlm_config.get("model_kwargs", {}),
    )
    response = vlm.query_with_image(
        "Describe this image.", image_data, "you are great visual describer."
    )
    logging.info(colorstring(response, "white"))
    response = vlm.query("who made you?")
    logging.info(colorstring(response, "white"))
