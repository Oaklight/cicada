import base64
import io
import json
import logging
import logging.config
import os
import re
from typing import Any, Dict, Iterable, List, Optional

import yaml
from blessed import Terminal
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
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


def colorstring(
    message: Any,  # Accept any type of input
    color: Optional[str] = "green",
    bold: bool = False,
) -> str:
    """
    Returns a colored string using either ANSI escape codes or blessed terminal capabilities.

    :param message: The message to be colored. Can be of any type (e.g., str, int, float, bool).
    :param color: The color to apply. Supported colors: 'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
                 and their bright variants: 'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue',
                 'bright_magenta', 'bright_cyan', 'bright_white'.
    :param bold: If True, applies bold styling to the text (only applicable when use_ansi=True).
    :return: A string with the specified color and styling.
    """
    color_mapping = {
        "black": _term.black,
        "blue": _term.blue,
        "cyan": _term.cyan,
        "green": _term.green,
        "magenta": _term.magenta,
        "red": _term.red,
        "white": _term.white,
        "yellow": _term.yellow,
        "bright_black": _term.bright_black,
        "bright_blue": _term.bright_blue,
        "bright_cyan": _term.bright_cyan,
        "bright_green": _term.bright_green,
        "bright_magenta": _term.bright_magenta,
        "bright_red": _term.bright_red,
        "bright_white": _term.bright_white,
        "bright_yellow": _term.bright_yellow,
    }

    # Convert the message to a string
    message_str = str(message)

    color_func = color_mapping.get(color.lower(), _term.white)
    styled_message = color_func(message_str)
    if bold:
        styled_message = _term.bold(styled_message)
    return styled_message


def cprint(message: Any, color: Optional[str] = "green", **kwargs) -> None:
    """
    Prints a colored string using blessed terminal capabilities.

    :param message: The message to be colored. Can be of any type (e.g., str, int, float, bool).
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


def is_base64_encoded(s: str) -> bool:
    """
    Check if a string is Base64 encoded.
    :param s: The string to check.
    :return: True if the string is Base64 encoded, False otherwise.
    """
    # Base64 encoded string length should be a multiple of 4, and only contain Base64 character set
    if len(s) % 4 != 0 or not re.match(r"^[A-Za-z0-9+/]*={0,2}$", s):
        return False

    try:
        # Try to decode the string
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False


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

    def _validate_directory_path(path: str):
        """Validate directory path exists and is accessible"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path '{path}' does not exist.")
        if not os.path.isdir(path):
            raise ValueError(f"Path '{path}' is not a directory.")

    def _find_matching_files(directory_path: str, extensions: List[str]) -> List[str]:
        """Find all files matching extensions in directory"""
        matching_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(f".{ext}") for ext in extensions):
                    matching_files.append(os.path.join(root, file))
        return matching_files

    def _sort_files_by_priority(files: List[str], extensions: List[str]) -> List[str]:
        """Sort files by extension priority"""
        return sorted(files, key=lambda f: extensions.index(os.path.splitext(f)[1][1:]))

    try:
        extensions = [extensions] if isinstance(extensions, str) else extensions
        _validate_directory_path(directory_path)

        matching_files = _find_matching_files(directory_path, extensions)

        if not matching_files:
            return None if not return_all else []

        if return_all:
            return _sort_files_by_priority(matching_files, extensions)

        return matching_files[0]

    except (FileNotFoundError, PermissionError) as e:
        logger.error(str(e))
        return None if not return_all else []


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
    try:
        # Normalize bracket usage for JSON parsing
        response = response.replace("{{", "{").replace("}}", "}")

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


class ANSIStrippingFormatter(logging.Formatter):
    """
    A logging formatter that removes ANSI escape codes from log messages.

    This formatter is particularly useful when logging to files, where ANSI escape codes
    (used for terminal coloring) are not needed and can clutter the log output.
    """

    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    def format(self, record):
        """
        Format the log record, removing any ANSI escape codes from the message.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message with ANSI escape codes removed.
        """
        message = super().format(record)
        return self.ansi_escape.sub("", message)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> None:
    """
    Configure the logging system.

    This function sets up logging with the following behavior:
    - Console logs retain ANSI escape codes for colored output.
    - File logs (if specified) have ANSI escape codes removed for cleaner output.
    - Mutes httpx INFO logs while keeping the global log_level at INFO.

    Args:
        log_level (str): The logging level (e.g., "INFO", "DEBUG"). Defaults to "INFO".
        log_file (Optional[str]): Path to the log file. If None, no file logging is performed.
        log_format (str): The format string for log messages. Defaults to "%(asctime)s - %(name)s - %(levelname)s - %(message)s".

    Returns:
        None
    """
    # Define formatters
    formatters = {
        "console": {
            "format": log_format,
        },
        "file": {
            "()": ANSIStrippingFormatter,  # Remove ANSI escape codes for file logs
            "format": log_format,
        },
    }

    # define handlers (default enable console)
    handlers = {
        "console": {
            "level": log_level.upper(),
            "class": "logging.StreamHandler",
            "formatter": "console",
            "stream": "ext://sys.stdout",
        }
    }

    # only add file handler when log_file is provided
    if log_file:
        handlers["file"] = {
            "level": log_level.upper(),
            "class": "logging.FileHandler",
            "filename": log_file,
            "formatter": "file",
            "mode": "w",
        }

    # configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": {
            "": {
                "level": log_level.upper(),
                "handlers": list(handlers.keys()),
                "propagate": True,  # Logs propagate to root logger
            },
            # Add a custom logger for httpx to mute INFO logs
            "httpx": {
                "level": "WARNING",  # Set httpx logger to WARNING to mute INFO logs
                "handlers": list(handlers.keys()),
                "propagate": False,  # Prevent httpx logs from propagating to root logger
            },
        },
    }

    logging.config.dictConfig(logging_config)
    logging.info("Logging configuration is set up.")


def recover_stream_tool_calls(
    stream_tool_calls: Dict,
) -> List[ChatCompletionMessageToolCall]:
    tool_calls = []
    for index, tool_call_str in stream_tool_calls.items():
        tool_call_instance = ChatCompletionMessageToolCall(
            id=tool_call_str["id"],
            type="function",
            function=Function(
                name=tool_call_str["function"]["name"],
                arguments=tool_call_str["function"]["arguments"],
            ),
            index=index,
        )
        tool_calls.append(tool_call_instance)
    return tool_calls


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
