import logging
from abc import ABC
from typing import List, Optional

from .types import SupportStr
from .utils import make_http_request

logger = logging.getLogger(__name__)

# 同时抑制两个层级的日志源
logging.getLogger("httpx").setLevel(logging.WARNING)  # 屏蔽INFO级
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class Embeddings(ABC):

    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        model_name: str,
        org_id: Optional[str] = None,
        **model_kwargs,
    ):
        """
        Initialize the Embed class with API configurations.

        Args:
            api_key (str): The API key for the API.
            api_base_url (str): The base URL for the API.
            model_name (str): The name of the embedding model.
            org_id (str): The organization ID if applicable.
            **model_kwargs: Additional keyword arguments for the model.
        """
        self.api_key = api_key
        self.api_base_url = api_base_url.rstrip("/")
        self.model_name = model_name
        self.org_id = org_id
        self.model_kwargs = model_kwargs

        # Remove /v1 suffix if present
        if self.api_base_url.endswith("/v1"):
            self.api_base_url = self.api_base_url[:-3]

    def embed(self, texts: List[SupportStr]) -> List[List[float]]:
        """
        Generate embeddings for texts using unified HTTP request helper.

        Args:
            texts (List[SupportStr]): A list of SupportStr objects to generate embeddings for.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """
        normalized_texts = [str(text) for text in texts]
        payload = {
            "input": normalized_texts,
            "model": self.model_name,
            **self.model_kwargs,
        }

        response = make_http_request(
            base_url=self.api_base_url,
            endpoint="/v1/embeddings",
            api_key=self.api_key,
            payload=payload,
        )

        return [embedding["embedding"] for embedding in response["data"]]

    def embed_query(self, text: SupportStr) -> List[float]:
        """
        Generate embedding for a single query text using HTTP API.

        Args:
            text (SupportStr): Query text to generate embedding for.

        Returns:
            List[float]: Embedding vector for the query text.
        """
        return self.embed([text])[0]

    def embed_documents(self, texts: List[SupportStr]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents using HTTP API.

        Args:
            texts (List[SupportStr]): A list of SupportStr objects to generate embeddings for.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """
        return self.embed(texts)


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

    embed = Embeddings(
        embed_config["api_key"],
        embed_config.get("api_base_url"),
        embed_config.get("model_name", "text-embedding-3-small"),
        embed_config.get("org_id"),
        **embed_config.get("model_kwargs", {}),
    )

    class SimpleSupportStr:
        def __init__(self, content: str):
            self.content = content

        def __str__(self):
            return self.content

    texts = [
        SimpleSupportStr("This is a test document."),
        SimpleSupportStr("Another test document."),
    ]
    embeddings = embed.embed(texts)
    logger.info(colorstring(f"Generated embeddings: {embeddings}", "white"))

    query = SimpleSupportStr("Test query")
    query_embedding = embed.embed_query(query)
    logger.info(colorstring(f"Generated query embedding: {query_embedding}", "white"))
