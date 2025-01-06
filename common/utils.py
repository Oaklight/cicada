import base64
import io
import os
from typing import Iterable, List, Optional

import yaml
from PIL import Image


# a class called DesignGoal, with text and images field
class DesignGoal:
    def __init__(self, text: str, images: Optional[list[str]] = None):
        self.text = text
        self.images = images

    def __str__(self):
        return f"DesignGoal(text='{self.text}', images={self.images})"


class PromptBuilder:
    def __init__(self):
        self.messages = []

    def add_system_prompt(self, content):
        self.messages.append({"role": "system", "content": content})

    def add_user_prompt(self, content):
        self.add_text(content)

    def add_images(self, image_data: list[str] | str):
        """
        Add images to the messages. Accepts a list of image paths or a single image path.

        :param image_data: List of image paths or a single image path.
        """
        image_files = get_image_paths(image_data)
        for image_file in image_files:
            b64_image = image_to_base64(image_file)
            self._add_image_message(b64_image)

    def _add_image_message(self, b64_image):
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
        self.messages.append({"role": "user", "content": content})


def load_config(config_path: str) -> dict:
    """
    Load a YAML configuration file and return its contents as a dictionary.

    :param config_path: Path to the YAML configuration file.
    :return: Dictionary containing the configuration data.
    """
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def load_prompts(prompts_path: str, which_model: str = "vlm") -> dict:
    """
    Load prompts from a YAML file and return prompts for a specific model.

    :param prompts_path: Path to the YAML file containing prompts.
    :param which_model: Key specifying which model's prompts to load. Default is "vlm".
    :return: Dictionary containing prompts for the specified model.
    """
    prompts_all = load_config(prompts_path)
    return prompts_all[which_model]


def colorstring(message: str, color: Optional[str] = "green") -> str:
    """
    Returns a colored string using ANSI escape codes.

    :param message: The message to be colored.
    :param color: The color to apply. Supported colors: 'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'.
    :return: A string with the specified color.
    """
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "bright_red": "\033[91m",
        "green": "\033[92m",
        "bright_green": "\033[32m",
        "yellow": "\033[33m",
        "bright_yellow": "\033[93m",
        "blue": "\033[34m",
        "bright_blue": "\033[94m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
    }

    # Default to white if the color is not found
    color_code = colors.get(color.lower(), "\033[37m")

    return f"{color_code}{message}\033[0m"


def get_image_paths(path: str | List[str]) -> List[str]:
    """
    Get image file paths from a specified folder, a single image file, or a list of image paths.

    Parameters:
    path (Union[str, List[str]]): The path to the folder, the single image file, or a list of image paths.

    Returns:
    List[str]: A list of image file paths.

    Raises:
    ValueError: If any path does not exist or is not a valid image file or folder of images.
    """
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

    def _get_single_image_path(p: str) -> List[str]:
        if not os.path.exists(p):
            raise ValueError(f"The path '{p}' does not exist.")

        if os.path.isfile(p):
            if os.path.splitext(p)[1].lower() in valid_extensions:
                return [p]
            raise ValueError(f"The file '{p}' is not a recognized image file.")

        if os.path.isdir(p):
            return [
                os.path.join(p, f)
                for f in os.listdir(p)
                if os.path.splitext(f)[1].lower() in valid_extensions
            ]

        raise ValueError(f"The path '{p}' is neither a file nor a directory of image.")

    if isinstance(path, str):
        return _get_single_image_path(path)
    elif isinstance(path, list):
        image_paths = []
        for p in path:
            image_paths.extend(_get_single_image_path(p))
        return image_paths
    else:
        raise ValueError("The input must be a string or a list of strings.")


def image_to_base64(image: Image.Image | str) -> str:
    """
    Convert the image to a base64 encoded string.

    :param image: PIL Image object or the path to the image file.
    :return: Base64 encoded string of the image.
    """
    if isinstance(image, str):
        # If the image is a string, assume it's a path and open it
        image = Image.open(image)

    # Convert the image to RGB mode if it's in RGBA mode
    if image.mode == "RGBA":
        image = image.convert("RGB")

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def find_files_with_extensions(
    directory_path: str,
    extensions: str | Iterable[str],
    return_all: bool = False,
) -> str | List[str] | None:
    """
    Find files with the specified extensions in the given directory.
    If `return_all` is False (default), returns the first matching file based on priority.
    If `return_all` is True, returns a list of all matching files, sorted by priority.

    Args:
        directory_path (str): Path to the directory to search.
        extensions (Union[str, List[str]]): A single extension or a list of extensions.
        return_all (bool): If True, return all matching files; otherwise, return the first match.

    Returns:
        Union[str, List[str], None]: A single file path, a list of file paths, or None if no files are found.
    """
    # Ensure extensions is a list for consistent handling
    if isinstance(extensions, str):
        extensions = [extensions]

    # List to store all matching files
    all_matching_files = []

    try:
        # Walk through the directory
        for root, _, files in os.walk(directory_path):
            for file in files:
                # Check if the file ends with any of the specified extensions
                for ext in extensions:
                    if file.endswith(f".{ext}"):
                        full_path = os.path.join(root, file)
                        if not return_all:
                            # Return the first matching file based on priority
                            return full_path
                        else:
                            # Add to the list of matching files
                            all_matching_files.append((ext, full_path))
    except FileNotFoundError:
        print(f"Error: The directory '{directory_path}' does not exist.")
        return None if not return_all else []
    except PermissionError:
        print(f"Error: Permission denied to access the directory '{directory_path}'.")
        return None if not return_all else []

    if return_all:
        # Sort the matching files by extension priority
        all_matching_files.sort(key=lambda x: extensions.index(x[0]))
        # Return only the file paths (without the extension used for sorting)
        return [file_path for _, file_path in all_matching_files]
    else:
        # Return None if no matching file is found
        return None


if __name__ == "__main__":
    print(colorstring("This is a red message", "red"))
    print(colorstring("This is a green message", "green"))
    print(colorstring("This is a blue message", "blue"))
    print(colorstring("This is a yellow message", "yellow"))
    print(colorstring("This is a magenta message", "magenta"))
    print(colorstring("This is a cyan message", "cyan"))
    print(colorstring("This is a black message", "black"))
    print(colorstring("This is a white message", "white"))

    import logging

    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Example usage:
    logging.info(colorstring("This is a red message", "red"))
    logging.info(colorstring("This is a green message", "green"))
    logging.info(colorstring("This is a blue message", "blue"))
    logging.info(colorstring("This is a yellow message", "yellow"))
    logging.info(colorstring("This is a magenta message", "magenta"))
    logging.info(colorstring("This is a cyan message", "cyan"))
    logging.info(colorstring("This is a black message", "black"))
    logging.info(colorstring("This is a white message", "white"))
