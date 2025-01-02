import argparse
import logging
import os
import sys
from abc import ABC
from typing import List, Union

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
        images_with_text: List[Union[str, bytes]] | None = None,
        prompt: str | None = None,
        images: bytes | List[bytes] | None = None,
        max_items_per_message: int = 4,  # Adjust as needed
    ) -> List[dict]:
        """
        Prepare the prompt for the API by splitting the content into multiple messages if needed.

        :param images_with_text: A list of mixed text (str) and image (bytes) data.
        :param prompt: Optional user prompt text.
        :param images: Optional image data (single or list of bytes).
        :param max_items_per_message: Maximum items per message.
        :return: A list of messages with prepared content.
        """
        content = []
        messages = []

        if prompt:
            messages.append({"role": "user", "content": prompt})

        # either images or images_with_text
        # Handle images
        if images:
            if not isinstance(images, list):
                images = [images]
            content = []
            for image_data in images:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                    }
                )
                if len(content) >= max_items_per_message:
                    messages.append({"role": "user", "content": content})
                    content = []
            if content:  # Add remaining items
                messages.append({"role": "user", "content": content})

        # Handle images_with_text
        elif images_with_text:
            content = []
            for item in images_with_text:
                if isinstance(item, str):
                    content.append({"type": "text", "text": item})
                elif isinstance(item, bytes):
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{item}"},
                        }
                    )
                else:
                    raise ValueError(
                        f"Unsupported type in images_with_text: {type(item)}"
                    )
                if len(content) >= max_items_per_message:
                    messages.append({"role": "user", "content": content})
                    content = []
            if content:  # Add remaining items
                messages.append({"role": "user", "content": content})

        return messages

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
        prompt: str | None = None,
        images: bytes | List[bytes] | None = None,
        images_with_text: List[Union[str, bytes]] | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """
        Query the VisionLanguageModel with mixed text and image data.

        :param prompt: Optional user prompt text.
        :param images: Optional image data (single or list of bytes).
        :param images_with_text: Optional list of mixed text (str) and image (bytes) data.
        :param system_prompt: Optional system prompt text.
        :return: Generated response from the model.
        """
        full_prompt = self._prepare_prompt(
            images_with_text=images_with_text, prompt=prompt, images=images
        )
        logging.info(colorstring(len(full_prompt), "white"))
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
        "Describe this image.",
        image_data,
        system_prompt="you are great visual describer.",
    )
    logging.info(colorstring(response, "white"))
    response = vlm.query("who made you?")
    logging.info(colorstring(response, "white"))
