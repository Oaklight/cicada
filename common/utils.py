import base64
import io
import json
import logging
import logging.config
import os
from typing import Any, Dict, Iterable, List, Optional

import yaml
from blessed import Terminal
from PIL import Image

logger = logging.getLogger(__name__)

# Initialize the terminal object
_term = Terminal()


def load_config(config_path: str, config_name: Optional[str] = None) -> dict:
    """Load a YAML configuration file or a specific configuration from a folder or file.

    Args:
        config_path (str): Path to the YAML configuration file or folder containing configuration files.
        config_name (Optional[str]): Name of the target configuration file (if config_path is a folder)
                                    or the key within the YAML file (if config_path is a file).
                                    If omitted and config_path is a file, the entire file is loaded.

    Returns:
        dict: Dictionary containing the configuration data.

    Raises:
        FileNotFoundError: If the specified `config_path` does not exist.
        yaml.YAMLError: If the YAML file is malformed or cannot be parsed.
        ValueError: If the `config_name` is not found in the configuration.
    """
    if os.path.isdir(config_path):
        # If config_path is a folder, config_name must be provided
        if config_name is None:
            raise ValueError(
                "config_name must be provided when config_path is a folder."
            )

        # Construct the full path to the config file
        config_file_path = os.path.join(config_path, f"{config_name}.yaml")
        if not os.path.exists(config_file_path):
            raise FileNotFoundError(
                f"Configuration file '{config_file_path}' not found in folder '{config_path}'."
            )

        with open(config_file_path, "r") as file:
            return yaml.safe_load(file)

    elif os.path.isfile(config_path):
        # If config_path is a file, load the YAML
        with open(config_path, "r") as file:
            config_data = yaml.safe_load(file)

        # If config_name is provided, extract the specific config
        if config_name is not None:
            if config_name not in config_data:
                raise ValueError(
                    f"Configuration key '{config_name}' not found in file '{config_path}'."
                )
            return config_data[config_name]

        # If config_name is omitted, return the entire config
        return config_data

    else:
        raise FileNotFoundError(f"Path '{config_path}' does not exist.")


def load_prompts(prompts_path: str, which_model: str) -> dict:
    """Load prompts from a YAML file and return prompts for a specific model.

    Args:
        prompts_path (str): Path to the YAML file containing prompts.
        which_model (str): Key specifying which model's prompts to load.

    Returns:
        dict: Dictionary containing prompts for the specified model.

    Raises:
        KeyError: If the specified `which_model` key is not found in the YAML file.
    """
    prompt_templates = load_config(prompts_path, which_model)
    return prompt_templates


def colorstring(message: str, color: Optional[str] = "green") -> str:
    """
    Returns a colored string using blessed terminal capabilities.

    :param message: The message to be colored.
    :param color: The color to apply. Supported colors: 'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'.
    :return: A string with the specified color.
    """
    color_mapping = {
        "black": _term.black,
        "red": _term.red,
        "bright_red": _term.bright_red,
        "green": _term.green,
        "bright_green": _term.bright_green,
        "yellow": _term.yellow,
        "bright_yellow": _term.bright_yellow,
        "blue": _term.blue,
        "bright_blue": _term.bright_blue,
        "magenta": _term.magenta,
        "cyan": _term.cyan,
        "white": _term.white,
    }

    # Default to white if the color is not found
    color_func = color_mapping.get(color.lower(), _term.white)

    return color_func(message)


def cprint(message: str, color: Optional[str] = "green", **kwargs) -> None:
    """
    Prints a colored string using blessed terminal capabilities.

    :param message: The message to be colored.
    :param color: The color to apply. Supported colors: 'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'.
    :param kwargs: Additional keyword arguments to pass to the `print` function (e.g., `end`, `sep`, `file`, `flush`).
    """
    print(colorstring(message, color), **kwargs)


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


def image_to_base64(
    image: Image.Image | str,
    quality: int = 85,
    max_resolution: tuple = (448, 448),
    img_format: str = "WEBP",
) -> str:
    """
    Convert the image to a base64 encoded string.

    :param image: PIL Image object or the path to the image file.
    :param quality: Compression quality (0-100) for WebP format. Higher values mean better quality but larger size.
    :param max_resolution: Optional maximum resolution (width, height) to fit the image within while preserving aspect ratio.
    :param img_format: Image format to use for encoding. Default is "WEBP".
    :return: Base64 encoded string of the image.
    """
    if isinstance(image, str):
        # If the image is a string, assume it's a path and open it
        image = Image.open(image)

    # Convert the image to RGB mode if it's in RGBA mode
    if image.mode == "RGBA":
        image = image.convert("RGB")

    # Resize the image while preserving aspect ratio
    if max_resolution:
        original_width, original_height = image.size
        max_width, max_height = max_resolution

        # Calculate the new dimensions while preserving aspect ratio
        ratio = min(max_width / original_width, max_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)

        # Resize the image
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Remove metadata (EXIF, etc.)
    if "exif" in image.info:
        del image.info["exif"]

    # Save the image to a BytesIO buffer as WebP with specified quality
    buffered = io.BytesIO()
    image.save(buffered, format=img_format, quality=quality)

    # Return the Base64 encoded string
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


def extract_section_markdown(text: str, heading: str) -> str:
    """
    Extracts content from a markdown text under the specified heading.
    """
    lines = text.split("\n")
    content = []
    capture = False
    for line in lines:
        line = line.strip()
        if line.startswith(f"#{heading}"):
            capture = True
            continue
        if line.startswith("#"):
            capture = False
            continue
        if capture:
            content.append(line)
    return "\n".join(content).strip()


def parse_json_response(response: str) -> Dict[str, Any]:
    """Parse JSON response from VLM, handling potential errors"""
    import json

    try:
        # Extract JSON content from response
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        json_str = response[json_start:json_end]

        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        logger.debug(f"Original response: {response}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error parsing response: {str(e)}")
        return {}


def parse_design_goal(design_goal_input: str) -> str:
    """
    Parse the design goal input, which can be either a JSON file or plain text.
    If it's a JSON file, extract the 'text' field.

    Args:
        design_goal_input (str): Path to a JSON file or plain text.

    Returns:
        str: The design goal text.
    """
    if os.path.isfile(design_goal_input):
        with open(design_goal_input, "r") as f:
            try:
                data = json.load(f)
                return data.get("text", "")
            except json.JSONDecodeError:
                logger.error("The provided file is not a valid JSON.")
                raise json.JSONDecodeError("The provided file is not a valid JSON.")
    return design_goal_input


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_log: bool = True,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> None:
    """
    Configure logging for the entire application.

    Args:
        log_level (str): The logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        log_file (Optional[str]): Path to the log file. If None, logging to file is disabled.
        console_log (bool): Whether to enable logging to the console.
        log_format (str): Format string for the log messages.
    """
    # Define the logging configuration dictionary
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": log_format,
            },
        },
        "handlers": {},
        "loggers": {
            "": {  # Root logger
                "level": log_level.upper(),
                "handlers": [],
                "propagate": True,
            },
        },
    }

    # Add console handler if enabled
    if console_log:
        logging_config["handlers"]["console"] = {
            "level": log_level.upper(),
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
        logging_config["loggers"][""]["handlers"].append("console")

    # Add file handler if log_file is provided
    if log_file:
        logging_config["handlers"]["file"] = {
            "level": log_level.upper(),
            "class": "logging.FileHandler",
            "filename": log_file,
            "formatter": "standard",
        }
        logging_config["loggers"][""]["handlers"].append("file")

    # Apply the logging configuration
    logging.config.dictConfig(logging_config)
    logging.info("Logging configuration is set up.")


if __name__ == "__main__":
    cprint("This is a red message", "red")
    cprint("This is a green message", "green")
    cprint("This is a blue message", "blue")
    cprint("This is a yellow message", "yellow")
    cprint("This is a magenta message", "magenta")
    cprint("This is a cyan message", "cyan")
    cprint("This is a black message", "black")
    cprint("This is a white message", "white")

    # Configure logging
    setup_logging()

    # Example usage:
    logger.info(colorstring("This is a red message", "red"))
    logger.info(colorstring("This is a green message", "green"))
    logger.info(colorstring("This is a blue message", "blue"))
    logger.info(colorstring("This is a yellow message", "yellow"))
    logger.info(colorstring("This is a magenta message", "magenta"))
    logger.info(colorstring("This is a cyan message", "cyan"))
    logger.info(colorstring("This is a black message", "black"))
    logger.info(colorstring("This is a white message", "white"))
