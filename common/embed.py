import argparse
import logging
import os
import sys
from abc import ABC
from typing import List

import httpx
import openai
import tenacity

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common.utils import colorstring, cprint, load_config, setup_logging

logger = logging.getLogger(__name__)


class Embed(ABC):
    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        model_name: str,
        org_id: str,
        **model_kwargs,
    ):
        """
        Initialize the Embed class with OpenAI API configurations.

        Args:
            api_key (str): The API key for OpenAI.
            api_base_url (str): The base URL for the OpenAI API.
            model_name (str): The name of the embedding model.
            org_id (str): The organization ID for OpenAI.
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
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using the OpenAI API.

        Args:
            texts (List[str]): A list of text strings to generate embeddings for.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """
        response = self.client.embeddings.create(
            input=texts,
            model=self.model_name,
            **self.model_kwargs,
        )
        return [embedding.embedding for embedding in response.data]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embedding Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()

    setup_logging()

    embed_config = load_config(args.config, "embed")

    embed = Embed(
        embed_config["api_key"],
        embed_config.get("api_base_url"),
        embed_config.get("model_name", "text-embedding-3-small"),
        embed_config.get("org_id"),
        **embed_config.get("model_kwargs", {}),
    )

    texts = ["This is a test document.", "Another test document."]
    embeddings = embed.embed(texts)
    logger.info(colorstring(f"Generated embeddings: {embeddings}", "white"))
