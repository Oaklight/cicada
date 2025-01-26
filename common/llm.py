import argparse
import logging
import os
import sys
from abc import ABC

import httpx
import openai
import tenacity

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common.basics import PromptBuilder
from common.utils import colorstring, cprint, load_config, setup_logging

logger = logging.getLogger(__name__)


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

        # Check if 'stream' is provided in model_kwargs, otherwise default to False
        self.stream = self.model_kwargs.get("stream", False)
        self.model_kwargs.pop("stream", None)

        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base_url, organization=self.org_id
        )

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3)
        | tenacity.stop_after_delay(30),  # Stop after 3 attempts or 30 seconds
        wait=tenacity.wait_random_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type(
            (openai.APIError, httpx.ReadTimeout, httpx.ConnectTimeout)
        ),  # Retry on API errors or network timeouts
        before_sleep=tenacity.before_sleep_log(
            logger, logging.WARNING
        ),  # Log before retrying
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
                    cprint(chunk_text, "white", end="", flush=True)
                    complete_response += chunk_text
                print()  # Add a newline after the response
                return complete_response.strip()
            else:
                return response.choices[0].text.strip()
        elif self.model_name in ["deepseek-r1", "deepseek-reasoner"]:
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
                    reasoning_content = getattr(
                        chunk.choices[0].delta, "reasoning_content", None
                    )
                    if chunk_content:
                        cprint(chunk_content, "white", end="", flush=True)
                        complete_response += chunk_content
                    if reasoning_content:
                        cprint(reasoning_content, "cyan", end="", flush=True)
                        complete_response += reasoning_content
                print()  # Add a newline after the response
                return complete_response.strip()
            else:
                response_content = response.choices[0].message.content
                reasoning_content = getattr(
                    response.choices[0].message, "reasoning_content", None
                )
                if reasoning_content:
                    return f"[Reasoning]: {reasoning_content}\n\n[Response]: {response_content}".strip()
                else:
                    return response_content.strip()
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
                        cprint(chunk_content, "white", end="", flush=True)
                        complete_response += chunk_content
                print()  # Add a newline after the response
                return complete_response.strip()
            else:
                return response.choices[0].message.content.strip()

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3)
        | tenacity.stop_after_delay(30),  # Stop after 3 attempts or 30 seconds
        wait=tenacity.wait_random_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type(
            (openai.APIError, httpx.ReadTimeout, httpx.ConnectTimeout)
        ),  # Retry on API errors or network timeouts
        before_sleep=tenacity.before_sleep_log(
            logger, logging.WARNING
        ),  # Log before retrying
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
                    cprint(chunk_content, "white", end="", flush=True)
                    complete_response += chunk_content
            print()  # Add a newline after the response
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
    setup_logging()

    llm_config = load_config(args.config, "llm")

    llm = LanguageModel(
        llm_config["api_key"],
        llm_config.get("api_base_url"),
        llm_config.get("model_name", "gpt-4o-mini"),
        llm_config.get("org_id"),
        **llm_config.get("model_kwargs", {}),
    )

    response = llm.query("How are you doing today?")
    if not llm.stream:
        logger.info(colorstring(response, "white"))
