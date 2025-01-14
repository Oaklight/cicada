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
        # ... (rest of the __init__ method remains the same)
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.org_id = org_id
        self.model_kwargs = model_kwargs

        # Check if 'stream' is provided in model_kwargs, otherwise default to False
        self.stream = self.model_kwargs.get("stream", False)
        self.model_kwargs.pop("stream", None)

        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base_url, organization=self.org_id
        )

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_random_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type(openai.APIError),
        reraise=True,
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
        stream = self.stream  # Use stream from configuration

        if self.model_name == "gpto1preview":
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            response = self.client.completions.create(
                model=self.model_name,
                prompt=full_prompt,
                stream=stream,
                **self.model_kwargs,
            )
            if stream:
                complete_response = ""
                for chunk in response:
                    chunk_text = chunk.choices[0].text
                    print(colorstring(chunk_text, "white"), end="", flush=True)
                    complete_response += chunk_text
                print()  # Add a newline after the response
                return complete_response.strip()
            else:
                return response.choices[0].text.strip()
        else:
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
                stream=stream,
                **self.model_kwargs,
            )

            if stream:
                complete_response = ""
                for chunk in response:
                    chunk_content = chunk.choices[0].delta.content
                    if chunk_content:
                        print(colorstring(chunk_content, "white"), end="", flush=True)
                        complete_response += chunk_content
                print()  # Add a newline after the response
                return complete_response.strip()
            else:
                return response.choices[0].message.content.strip()

    # (The rest of the original code remains unchanged)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_random_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type(openai.APIError),
        reraise=True,
    )
    def query_with_promptbuilder(self, pb: PromptBuilder) -> str:
        """
        Query the LanguageModel using a PromptBuilder object.

        Args:
            pb: The PromptBuilder object containing the prompt.

        Returns:
            str: Generated response from the model.
        """
        messages = pb.messages

        if self.model_name in ["argo:gpt-o1-preview", "gpto1preview"]:
            raise NotImplementedError("gpto1preview does not support PromptBuilder")

        # Use stream from configuration
        stream = self.stream

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=stream,
            **self.model_kwargs,
        )

        if stream:
            complete_response = ""
            for chunk in response:
                chunk_content = chunk.choices[0].delta.content
                if chunk_content:
                    print(colorstring(chunk_content, "white"), end="", flush=True)
                    complete_response += chunk_content
            return complete_response.strip()
        else:
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

    llm_config = config["llm"]

    llm = LanguageModel(
        llm_config["api_key"],
        llm_config.get("api_base_url"),
        llm_config.get("model_name", "gpt-4o-mini"),
        llm_config.get("org_id"),
        **llm_config.get("model_kwargs", {}),
    )

    response = llm.query("How are you doing today?")
    if not llm.stream:
        logging.info(colorstring(response, "white"))
