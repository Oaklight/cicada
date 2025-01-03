import argparse
import json
import logging
import os
import sys
from abc import ABC

import openai
import tenacity

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common.utils import PromptBuilder, colorstring, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class LanguageModel(ABC):
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        **model_kwargs,
    ):
        """
        Initialize the LanguageModel instance.

        Args:
            api_key (str): The API key for the language model.
            api_base_url (str): The base URL for the API.
            model_name (str): The name of the model to use.
            org_id (str): The organization ID for the API.
            **model_kwargs: Additional keyword arguments for the model.
        """
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.org_id = org_id
        self.model_kwargs = model_kwargs

        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base_url, organization=self.org_id
        )

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),  # Stop after 5 attempts
        wait=tenacity.wait_random_exponential(
            multiplier=1, min=2, max=10
        ),  # Exponential backoff with randomness
        retry=tenacity.retry_if_exception_type(
            openai.APIError
        ),  # Retry only on specific exceptions related to OpenAI API
        reraise=True,  # Reraise the last exception if all retries fail
    )
    def query(self, prompt, system_prompt=None):
        """
        Query the language model with a prompt and optionally a system prompt.

        Args:
            prompt (str): The user prompt to send to the model.
            system_prompt (str, optional): The system prompt to guide the model's behavior.

        Returns:
            str: The model's response.
        """
        if self.model_name == "gpto1preview":
            # Use the prompt interface for gpto1preview, incorporating the system_prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"  # Combine system_prompt and user prompt
            response = self.client.completions.create(
                model=self.model_name,
                prompt=full_prompt,  # Use the combined prompt
                **self.model_kwargs,
            )
            # Adjust the return format for legacy completion endpoint
            return response.choices[0].text.strip()
        else:
            # Use the messages interface for other models
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

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),  # Stop after 5 attempts
        wait=tenacity.wait_random_exponential(
            multiplier=1, min=2, max=10
        ),  # Exponential backoff with randomness
        retry=tenacity.retry_if_exception_type(
            openai.APIError
        ),  # Retry only on specific exceptions related to OpenAI API
        reraise=True,  # Reraise the last exception if all retries fail
    )
    def query_with_promptbuilder(self, pb: PromptBuilder) -> str:
        """
        Query the LanguageModel using a PromptBuilder object.
        :param pb: The PromptBuilder object containing the prompt.
        :return: Generated response from the model.
        """
        messages = pb.messages
        # logging.info(colorstring(json.dumps(messages, indent=4), "white"))

        if self.model_name == "gpto1preview":
            raise NotImplementedError("gpto1preview does not support PromptBuilder")
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **self.model_kwargs,
            )

        return response.choices[0].message.content.strip()


if __name__ == "__main__":
    """
    Main entry point for the script.

    Parses command-line arguments, loads configuration, and queries the language model.
    """
    parser = argparse.ArgumentParser(description="Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    assist_llm_config = config["assist-llm"]

    llm = LanguageModel(
        assist_llm_config["api_key"],
        assist_llm_config.get("api_base_url"),
        assist_llm_config.get("model_name", "gpt-4o-mini"),
        assist_llm_config.get("org_id"),
        **assist_llm_config.get("model_kwargs", {}),
    )

    response = llm.query("How are you doing today?")
    logging.info(colorstring(response, "white"))
