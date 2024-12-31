import argparse
import logging
import os
import sys
from abc import ABC
from typing import List

import openai
import tenacity

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, parent_dir])

from common.utils import colorstring, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Embed(ABC):
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
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
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
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

    config = load_config(args.config)

    embed_config = config["embed"]

    embed = Embed(
        embed_config["api_key"],
        embed_config.get("api_base_url"),
        embed_config.get("model_name", "text-embedding-3-small"),
        embed_config.get("org_id"),
        **embed_config.get("model_kwargs", {}),
    )

    texts = ["This is a test document.", "Another test document."]
    embeddings = embed.embed(texts)
    logging.info(colorstring(f"Generated embeddings: {embeddings}", "white"))
