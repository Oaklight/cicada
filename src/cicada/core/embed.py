import logging
from abc import ABC
from typing import List

import openai

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

    import argparse

    from cicada.core.utils import colorstring, load_config, setup_logging

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
