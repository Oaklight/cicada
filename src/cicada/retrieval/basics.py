from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Document:
    """A simple class to hold text and metadata."""

    def __init__(self, page_content: str, metadata: Optional[Dict] = None):
        """
        Initialize a Document instance.
        Args:
            page_content (str): The text content of the document.
            metadata (Optional[Dict]): A dictionary of metadata associated with the document. Defaults to None.
        """
        self.page_content = page_content
        self.metadata = metadata or {}

    def __str__(self):
        """
        Return a string representation of the Document instance.
        Returns:
            str: A string representation of the Document.
        """
        metadata_str = ", ".join(f"{k}: {v}" for k, v in self.metadata.items())
        return (
            f"Document(page_content='{self.page_content}', metadata={{{metadata_str}}})"
        )

    def pretty_print(self, indent: int = 0):
        """
        Return a formatted string representation of the Document instance with optional indentation.
        Args:
            indent (int): The number of spaces to indent the output. Defaults to 0.
        Returns:
            str: A formatted string representation of the Document.
        """
        indent_str = " " * indent
        metadata_str = (
            ",\n"
            + indent_str
            + "    ".join(f"{k}: {v}" for k, v in self.metadata.items())
        )
        return f"{indent_str}Document(\n{indent_str}    page_content='{self.page_content}',\n{indent_str}    metadata={{{metadata_str}\n{indent_str}}})"

    def __repr__(self):
        """
        Return a detailed string representation of the Document instance.

        Returns:
            str: A detailed string representation of the Document.
        """
        return self.__str__()


from typing import List, Union, Dict, Optional


class Embeddings:
    """Base class for embedding models."""

    def embed_query(self, text: str) -> List[float]:
        """
        Generate an embedding for a single query text.

        Args:
            text (str): The text to embed.

        Returns:
            List[float]: The embedding vector.
        """
        raise NotImplementedError

    def embed_documents(
        self, texts: Union[List[str], str, Document, List[Document]]
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts, a single text, a Document, or a list of Documents.

        Args:
            texts: Can be a list of strings, a single string, a Document, or a list of Documents.

        Returns:
            List[List[float]]: A list of embeddings, where each embedding is a list of floats.
        """
        raise NotImplementedError


class VectorStore:
    """Base class for vector stores."""

    def add_texts(
        self, texts: List[str], metadatas: Optional[List[Dict]] = None
    ) -> List[str]:
        """
        Add texts to the vector store with optional metadata.

        Args:
            texts (List[str]): A list of texts to add.
            metadatas (Optional[List[Dict]]): A list of metadata dictionaries corresponding to the texts. Defaults to None.

        Returns:
            List[str]: A list of IDs or keys associated with the added texts.
        """
        raise NotImplementedError

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        Perform a similarity search for the given query string.

        Args:
            query (str): The query string to search for.
            k (int): The number of results to return. Defaults to 4.

        Returns:
            List[Document]: A list of Document instances that are most similar to the query.
        """
        raise NotImplementedError

    def similarity_search_by_vector(
        self, embedding: List[float], k: int = 4
    ) -> List[Document]:
        """
        Perform a similarity search using a precomputed embedding vector.

        Args:
            embedding (List[float]): The embedding vector to search with.
            k (int): The number of results to return. Defaults to 4.

        Returns:
            List[Document]: A list of Document instances that are most similar to the embedding.
        """
        raise NotImplementedError
