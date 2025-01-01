import argparse
import logging
import os
import sys
from abc import ABC
from typing import List, Dict
import requests
import tenacity

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common.utils import colorstring, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Rerank(ABC):
    def __init__(
        self,
        api_key: str,
        api_base_url: str = "https://api.siliconflow.cn/v1/rerank",
        model_name: str = "BAAI/bge-reranker-v2-m3",
        **model_kwargs,
    ):
        """
        Initialize the Rerank class.

        :param api_key: API key for authentication.
        :param api_base_url: Base URL for the rerank API.
        :param model_name: Name of the rerank model.
        :param model_kwargs: Additional model-specific parameters.
        """
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.model_kwargs = model_kwargs

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),  # Stop after 3 attempts
        wait=tenacity.wait_random_exponential(
            multiplier=1, min=2, max=10
        ),  # Exponential backoff with randomness
        retry=tenacity.retry_if_exception_type(
            requests.exceptions.RequestException
        ),  # Retry on request exceptions
        reraise=True,  # Reraise the last exception if all retries fail
    )
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 4,
        return_documents: bool = False,
    ) -> List[Dict]:
        """
        Rerank a list of documents based on a query.

        :param query: The query to rerank documents against.
        :param documents: List of documents to rerank.
        :param top_n: Number of top documents to return.
        :param return_documents: Whether to return the full documents or just scores.
        :return: List of reranked documents or scores.
        """
        payload = {
            "model": self.model_name,
            "query": query,
            "documents": documents,
            "top_n": top_n,
            "return_documents": return_documents,
            **self.model_kwargs,  # Include additional model-specific parameters
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(self.api_base_url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(colorstring(f"Failed to rerank documents: {e}", "red"))
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reranking Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    rerank_config = config["rerank"]

    rerank = Rerank(
        api_key=rerank_config["api_key"],
        api_base_url=os.path.join(
            rerank_config.get("api_base_url", "https://api.siliconflow.cn/v1/"),
            "rerank",
        ),
        model_name=rerank_config.get("model_name", "BAAI/bge-reranker-v2-m3"),
        **rerank_config.get("model_kwargs", {}),
    )

    query = "Apple"
    documents = ["苹果", "香蕉", "水果", "蔬菜"]
    reranked_results = rerank.rerank(query, documents, top_n=4, return_documents=False)
    logging.info(colorstring(f"Reranked results: {reranked_results}", "white"))
