import base64
import io

import yaml
from PIL import Image


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
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
    }

    # Default to white if the color is not found
    color_code = colors.get(color.lower(), "\033[37m")

    return f"{color_code}{message}\033[0m"


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
