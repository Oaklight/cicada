import json
import os
import sys
from typing import Any, Dict, List, Optional

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common.utils import get_image_paths, image_to_base64


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

    def add_system_prompt(self, content):
        """Add a system prompt to the messages.

        Args:
            content (str): The content of the system prompt.
        """
        self.messages.append({"role": "system", "content": content})

    def add_user_prompt(self, content):
        """Add a user prompt with text content to the messages.

        Args:
            content (str): The text content of the user prompt.
        """
        self.add_text(content)

    def add_images(self, image_data: list[str] | str):
        """Add images to the messages.

        Accepts a list of image paths or a single image path. Each image is converted
        to a base64-encoded string and added as a user message with image content.

        Args:
            image_data (list[str] | str): A list of image paths or a single image path.
        """
        image_files = get_image_paths(image_data)
        for image_file in image_files:
            b64_image = image_to_base64(image_file)
            self._add_image_message(b64_image)

    def _add_image_message(self, b64_image):
        """Add a user message with an image to the messages.

        Args:
            b64_image (str): A base64-encoded string representing the image.
        """
        self.messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                    }
                ],
            }
        )

    def add_text(self, content):
        """Add a user message with text content to the messages.

        Args:
            content (str): The text content of the user message.
        """
        self.messages.append({"role": "user", "content": content})


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
        data = json.loads(json_str)
        return cls.from_dict(data)
