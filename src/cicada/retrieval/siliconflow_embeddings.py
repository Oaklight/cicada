from typing import List, Union

from cicada.core.embed import Embed
from cicada.retrieval.basics import Document, Embeddings


class SiliconFlowEmbeddings(Embeddings):
    """Embedding class for SiliconFlow BGE-M3 API."""

    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        model_name: str,
        org_id: str = None,
        **model_kwargs,
    ):
        """
        Initialize the SiliconFlow BGE-M3 embedding model.

        Args:
            api_key (str): The API key for SiliconFlow.
            api_base_url (str): The base URL for the API.
            model_name (str): The name of the model to use.
            org_id (str, optional): The organization ID. Defaults to None.
            **model_kwargs: Additional keyword arguments for the model.
        """
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.org_id = org_id
        self.model_kwargs = model_kwargs

        # Initialize the Embed class from embed.py
        self.embed_client = Embed(
            api_key=self.api_key,
            api_base_url=self.api_base_url,
            model_name=self.model_name,
            org_id=self.org_id,
            **self.model_kwargs,
        )

    def embed_query(self, text: str) -> List[float]:
        """
        Generate an embedding for a single query text.

        Args:
            text (str): The query text to embed.

        Returns:
            List[float]: The embedding of the query text.
        """
        return self.embed_documents(text)[0]

    def embed_documents(
        self, texts: Union[List[str], str, Document, List[Document]]
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts or documents.

        Args:
            texts (Union[List[str], str, Document, List[Document]]): The input texts or documents to embed.

        Returns:
            List[List[float]]: A list of embeddings for the input texts or documents.

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

        # Generate embeddings using the Embed client
        return self.embed_client.embed(texts)


if __name__ == "__main__":
    import argparse

    from cicada.core.utils import load_config

    parser = argparse.ArgumentParser(description="Feedback Judge")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()

    embed_config = load_config(args.config, "embed")

    embedding_model = SiliconFlowEmbeddings(
        embed_config["api_key"],
        embed_config.get("api_base_url"),
        embed_config.get("model_name", "text-embedding-3-small"),
        embed_config.get("org_id"),
        **embed_config.get("model_kwargs", {}),
    )

    # Generate embeddings for a list of texts
    texts = ["This is a test document.", "Another test document."]
    embeddings = embedding_model.embed_documents(texts)
    print(embeddings)

    # Generate an embedding for a single query
    query_embedding = embedding_model.embed_query("This is a query.")
    print(query_embedding)
