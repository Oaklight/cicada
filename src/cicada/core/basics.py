import json
import os
from typing import Any, Dict, List, Optional

from cicada.core.utils import get_image_paths, image_to_base64, is_base64_encoded


def _create_text_content(text: str) -> dict:
    """Create text content message"""
    return {"type": "text", "text": text}


def _create_image_content(image_data: str) -> dict:
    """Create image content message from base64 encoded image string"""
    assert is_base64_encoded(image_data), "image_data must be base64 encoded"

    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
    }


class PromptBuilder:
    """A utility class for constructing prompts with text and images.

    This class is designed to build a list of messages that can be used as input for
    models that accept multi-modal prompts (e.g., text and images). Messages can include
    system prompts, user prompts with text, and user prompts with images.

    Attributes:
        messages (list): A list of messages, where each message is a dictionary
            containing a role ("system" or "user") and content (text or image data).
    """

    def __init__(self):
        """Initialize the PromptBuilder with an empty list of messages."""
        self.messages = []
        self.tools = None  # Add an attribute to hold tools

    def add_system_message(self, content):
        """Add a system prompt to the messages.

        Args:
            content (str): The content of the system prompt.
        """
        self.messages.append({"role": "system", "content": content})

    def add_user_message(self, content):
        """Add a user prompt with text content to the messages.

        Args:
            content (str): The text content of the user prompt.
        """
        self.add_text(content)

    def add_images(
        self, image_data: list[str] | str, msg_index: Optional[int] = None
    ) -> int:
        """Add images to the messages. If msg_index is provided, the images will be appended to the existing message at that index to form a multi-content message.

        Accepts a list of image paths or a single image path. Each image is converted
        to a base64-encoded string and added as a user message with image content.

        Args:
            image_data (list[str] | str): A list of image paths or a single image path.
            msg_index (Optional[int]): The index of the message in the messages list. Useful when appending to an existing message.

        Returns:
            msg_index (int): The index of the message in the messages list, or -1 if no valid images were found.
        """

        image_files = get_image_paths(image_data)
        if not image_files:
            return -1  # No valid images found

        # Convert images to base64 and create image content
        new_content = [
            _create_image_content(image_to_base64(image_file))
            for image_file in image_files
        ]

        if msg_index is None:
            self.messages.append({"role": "user", "content": new_content})
            return len(self.messages) - 1

        existing_content = self.messages[msg_index]["content"]

        if isinstance(existing_content, str):
            # Convert single text content to a multi-content message
            self.messages[msg_index]["content"] = [
                _create_text_content(existing_content),
                *new_content,
            ]
        elif isinstance(existing_content, list):
            # Append to existing multi-content message
            self.messages[msg_index]["content"].extend(new_content)

        return msg_index

    def add_text(self, content: str, msg_index: Optional[int] = None) -> int:
        """Add a user message with text content to the messages. If msg_index is provided, the text will be appended to the existing message at that index to form a multi-content message.

        Args:
            content (str): The text content of the user message.
            msg_index (Optional[int]): The index of the message in the messages list. Useful when appending to an existing message.

        Return:
            msg_index (int): The index of the message in the messages list.
        """

        if msg_index is None:
            self.messages.append({"role": "user", "content": content})
            return len(self.messages) - 1

        existing_content = self.messages[msg_index]["content"]
        new_content = _create_text_content(content)

        if isinstance(existing_content, str):
            # Convert single text content to a multi-content message
            self.messages[msg_index]["content"] = [
                _create_text_content(existing_content),
                new_content,
            ]
        elif isinstance(existing_content, list):
            # Append to existing multi-content message
            self.messages[msg_index]["content"].append(new_content)

        return msg_index


class DesignGoal:
    """Represents a design goal, which can be defined by either text, images, or both.

    A design goal encapsulates the user's input, which can be in the form of a textual
    description, one or more images, or a combination of both. Images can be provided
    as paths to individual image files or as a path to a folder containing multiple images.

    Args:
        text (Optional[str]): A textual description of the design goal. Defaults to None.
        images (Optional[list[str]]): A list of image file paths or a single folder path
            containing images. Defaults to None.
        extra (Optional[Dict[str, Any]]): Additional information related to the design goal,
            such as original user input or decomposed part list, etc. Defaults to an empty dictionary.

    Raises:
        ValueError: If neither `text` nor `images` is provided.

    Attributes:
        text (Optional[str]): The textual description of the design goal.
        images (Optional[list[str]]): A list of image file paths or a single folder path.
        extra (Dict[str, Any]): Additional information related to the design goal, such as
            original user input or decomposed part list, etc.
    """

    def __init__(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        # Validate that at least one of text or images is provided
        if text is None and images is None:
            raise ValueError("Either 'text' or 'images' must be provided.")

        self.text = text
        self.images = images
        # extra information, such as original user input, decomposed part list etc.
        self.extra = extra if extra else {}

    def __str__(self):
        return (
            f"DesignGoal(text='{self.text}', images={self.images}, extra={self.extra})"
        )

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DesignGoal object to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the DesignGoal object.
        """
        return {
            "text": self.text,
            "images": self.images,
            "extra": self.extra,
        }

    def to_json(self) -> str:
        """Convert the DesignGoal object to a JSON string.

        Returns:
            str: A JSON string representation of the DesignGoal object.
        """
        return json.dumps(self.to_dict(), indent=4)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DesignGoal":
        """Create a DesignGoal object from a dictionary.

        Args:
            data (Dict[str, Any]): A dictionary containing the design goal data.

        Returns:
            DesignGoal: A DesignGoal object.
        """
        return cls(
            text=data.get("text"),
            images=data.get("images"),
            extra=data.get("extra"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "DesignGoal":
        """Create a DesignGoal object from a JSON string.

        Args:
            json_str (str): A JSON string containing the design goal data.

        Returns:
            DesignGoal: A DesignGoal object.
        """
        if os.path.isfile(json_str):
            with open(json_str, "r") as f:
                data = json.load(f)
        else:
            data = json.loads(json_str)
        return cls.from_dict(data)
