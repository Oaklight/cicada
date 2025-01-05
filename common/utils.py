import base64
import io
import os
from typing import List

import yaml
from PIL import Image


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


def colorstring(message: str, color: str) -> str:
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


def get_image_paths(path: str) -> List[str]:
    """
    Get image file paths from a specified folder or a single image file.

    Parameters:
    path (str): The path to the folder or the single image file.

    Returns:
    List[str]: A list of image file paths.

    Raises:
    ValueError: If the path does not exist or is not a valid image file or folder of images.
    """
    if not os.path.exists(path):
        raise ValueError(f"The path '{path}' does not exist.")

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

    if os.path.isfile(path):
        if os.path.splitext(path)[1].lower() in valid_extensions:
            return [path]
        raise ValueError(f"The file '{path}' is not a recognized image file.")

    if os.path.isdir(path):
        return [
            os.path.join(path, f)
            for f in os.listdir(path)
            if os.path.splitext(f)[1].lower() in valid_extensions
        ]

    raise ValueError(f"The path '{path}' is neither a file nor a directory of image.")


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
