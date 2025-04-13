import logging
import os
from abc import ABC
from typing import Dict, List

from cicada.core.utils import colorstring

from .types import SupportStr
from .utils import make_http_request

logger = logging.getLogger(__name__)

# 同时抑制两个层级的日志源
logging.getLogger("httpx").setLevel(logging.WARNING)  # 屏蔽INFO级
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class Reranker(ABC):

    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        model_name: str,
        **model_kwargs,
    ):
        """
        Initialize the Rerank class.

        Args:
            api_key (str): API key for authentication.
            api_base_url (str, optional): Base URL for the rerank API.
            model_name (str, optional): Name of the rerank model.
            **model_kwargs: Additional model-specific parameters.
        """
        self.api_key = api_key
        self.api_base_url = api_base_url.rstrip("/")
        self.model_name = model_name
        self.model_kwargs = model_kwargs

        # Remove /v1 suffix if present
        if self.api_base_url.endswith("/v1"):
            self.api_base_url = self.api_base_url[:-3]

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

        response = make_http_request(
            base_url=self.api_base_url,
            endpoint="/v1/rerank",
            api_key=self.api_key,
            payload=payload,
        )

        return response["results"]


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
