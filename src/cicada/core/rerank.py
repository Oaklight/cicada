import logging
import os
from abc import ABC
from typing import Dict, List

import httpx

from cicada.core.utils import colorstring

from .types import SupportStr

logger = logging.getLogger(__name__)


class Reranker(ABC):
    def __init__(
        self,
        api_key: str,
        api_base_url: str = "https://api.siliconflow.cn/v1",
        model_name: str = "BAAI/bge-reranker-v2-m3",
        **model_kwargs,
    ):
        """
        Initialize the Rerank class.

        Args:
            api_key (str): API key for authentication.
            api_base_url (str, optional): Base URL for the rerank API. Defaults to "https://api.siliconflow.cn/v1".
            model_name (str, optional): Name of the rerank model. Defaults to "BAAI/bge-reranker-v2-m3".
            **model_kwargs: Additional model-specific parameters.
        """
        self.api_key = api_key
        self.api_base_url = os.path.join(api_base_url, "rerank")
        self.model_name = model_name
        self.model_kwargs = model_kwargs

    def rerank(
        self,
        query: SupportStr,
        documents: List[SupportStr],
        top_n: int = 4,
        return_documents: bool = False,
    ) -> List[Dict]:
        """
        Rerank a list of documents based on a query.

        Args:
            query (str): The query to rerank documents against.
            documents (List[str]): List of documents to rerank.
            top_n (int, optional): Number of top documents to return. Defaults to 4.
            return_documents (bool, optional): Whether to return the full documents or just scores. Defaults to False.

        Returns:
            List[Dict]: List of reranked documents or scores.
        """

        query = str(query)
        documents = [str(doc) for doc in documents]

        payload = {
            "model": self.model_name,
            "query": query,
            "documents": documents,
            "top_n": top_n,
            "return_documents": return_documents,
            **self.model_kwargs,
        }

        response = self._make_request(payload)
        return response["results"]

    def _make_request(self, payload: Dict) -> Dict:
        """
        Helper function to handle HTTP requests and error handling.

        Args:
            payload (Dict): The JSON payload for the request.

        Returns:
            Dict: The JSON response from the server.

        Raises:
            RuntimeError: If the request fails or the server returns an error.
        """
        # logger.debug(colorstring(f"Payload: {payload}", "blue"))
        # logger.debug(colorstring(f"Headers: {headers}", "blue"))

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(self.api_base_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                colorstring(
                    f"HTTP error during request: {e.response.status_code} {e.response.text}",
                    "red",
                )
            )
            raise RuntimeError(
                f"Request failed with status {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            logger.error(
                colorstring(
                    f"Request error: {e}. Payload: {payload}, Headers: {headers}",
                    "red",
                )
            )
            raise RuntimeError(
                "Failed to complete the request due to a network error."
            ) from e


if __name__ == "__main__":
    import argparse

    from cicada.core.utils import colorstring, load_config, setup_logging

    parser = argparse.ArgumentParser(description="Reranking Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()

    setup_logging()

    rerank_config = load_config(args.config, "rerank")

    rerank = Reranker(
        api_key=rerank_config["api_key"],
        api_base_url=rerank_config.get(
            "api_base_url", "https://api.siliconflow.cn/v1/"
        ),
        model_name=rerank_config.get("model_name", "BAAI/bge-reranker-v2-m3"),
        **rerank_config.get("model_kwargs", {}),
    )

    query = "Apple"
    documents = ["苹果", "香蕉", "水果", "蔬菜"]
    reranked_results = rerank.rerank(query, documents, top_n=4, return_documents=False)
    logger.info(colorstring(f"Reranked results: {reranked_results}", "white"))
