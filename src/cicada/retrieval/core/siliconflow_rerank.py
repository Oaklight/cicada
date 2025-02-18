from typing import Dict, List, Union

from cicada.common.rerank import Rerank
from cicada.common.utils import setup_logging
from cicada.retrieval.core.basics import Document


class SiliconFlowRerank(Rerank):
    """Rerank class for SiliconFlow BGE-Reranker API."""

    def __init__(
        self,
        api_key: str,
        api_base_url: str = "https://api.siliconflow.cn/v1",
        model_name: str = "BAAI/bge-reranker-v2-m3",
        **model_kwargs
    ):
        """
        Initialize the SiliconFlow BGE-Reranker model.

        Args:
            api_key (str): The API key for SiliconFlow.
            api_base_url (str, optional): The base URL for the API. Defaults to "https://api.siliconflow.cn/v1".
            model_name (str, optional): The name of the model to use. Defaults to "BAAI/bge-reranker-v2-m3".
            **model_kwargs: Additional keyword arguments for the model.
        """
        super().__init__(
            api_key=api_key,
            api_base_url=api_base_url,
            model_name=model_name,
            **model_kwargs
        )

    def rerank(
        self,
        query: str,
        texts: Union[List[str], str, Document, List[Document]],
        top_n: int = 4,
        return_documents: bool = False,
    ) -> List[Dict]:
        """
        Rerank a list of texts or documents based on a query.

        Args:
            query (str): The query to rerank texts or documents against.
            texts (Union[List[str], str, Document, List[Document]]): The input texts or documents to rerank.
            top_n (int, optional): Number of top documents to return. Defaults to 4.
            return_documents (bool, optional): Whether to return the full documents or just scores. Defaults to False.

        Returns:
            List[Dict]: List of reranked documents or scores.

        Raises:
            ValueError: If the input list contains mixed types of strings and Documents.
            TypeError: If the input is not a string, Document, list of strings, or list of Documents.
        """
        # Normalize input to a list of strings
        if isinstance(texts, str):
            texts = [texts]
        elif isinstance(texts, Document):
            texts = [texts.page_content]
        elif isinstance(texts, list):
            if all(isinstance(text, str) for text in texts):
                pass  # Already a list of strings
            elif all(isinstance(text, Document) for text in texts):
                texts = [text.page_content for text in texts]
            else:
                raise ValueError(
                    "Input list must contain only strings or only Document instances."
                )
        else:
            raise TypeError(
                "Input must be a string, Document, list of strings, or list of Documents."
            )

        # Call the parent class's rerank method with the normalized list of texts
        return super().rerank(query, texts, top_n, return_documents)


if __name__ == "__main__":
    setup_logging(log_level="DEBUG")
    # Initialize the SiliconFlow BGE-Reranker model
    rerank_model = SiliconFlowRerank(
        api_key="sk-EFhZxTqkXfedmKP_p9uUwDWJqIMvY0LGSClJ56RpZM7yO4Byvwb7vuRHpXc",
        # api_base_url="http://localhost:33000/v1",
        api_base_url="http://localhost:9998/v1",
        model_name="jina-reranker-v2",
    )

    # Rerank a list of documents based on a query
    query = "Apple的同义词"
    documents = ["苹果", "banana", "水果", "vegi", "manzana"]
    reranked_results = rerank_model.rerank(
        query, documents, top_n=4, return_documents=True
    )
    print(reranked_results)
