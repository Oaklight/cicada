import yaml


def load_config(config_path: str) -> dict:
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def load_prompts(prompts_path: str, which_model: str = "vlm") -> dict:
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
