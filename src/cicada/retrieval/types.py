import logging
from typing import Dict, Optional

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
