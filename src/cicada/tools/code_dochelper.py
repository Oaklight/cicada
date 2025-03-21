import importlib
import inspect
import logging
from functools import lru_cache

from cicada.core.utils import colorstring

logger = logging.getLogger(__name__)


class CodeDocHelper:
    def __init__(self):
        """
        Initialize the CodeDocHelper
        """
        pass

    def get_function_info(self, function_path, with_docstring=False):
        """
        Retrieve the signature and optionally the docstring of a function or class method.

        Parameters:
        function_path (str): The full import path to the function (e.g., "build123d.Box.bounding_box").
        with_docstring (bool): If True, include the docstring in the output.

        Returns:
        dict: A dictionary containing the function name, signature, and docstring (optional).
        """
        logger.debug(
            colorstring(
                f"Getting function info for {function_path}", color="bright_blue"
            )
        )

        try:
            parts = function_path.split(".")
            module_name = parts[0]
            module = importlib.import_module(module_name)

            # Traverse the path to get the function or method
            obj = module
            for part in parts[1:]:
                obj = getattr(obj, part)

            # Check if the object is a function or method
            if inspect.isroutine(obj):
                signature = str(inspect.signature(obj))
                if inspect.ismethod(obj) and signature.startswith("(self, "):
                    signature = f"({signature[7:]}"  # Remove "(self, "

                # # `parts[-1]` version: clearer to read, but may be ambiguous for llm
                # data = {"name": parts[-1], "signature": f"{parts[-1]}{signature}"}

                # `function_path` version: more verbose, but provide which module it comes from
                data = {
                    "name": function_path,
                    "signature": f"{function_path}{signature}",
                }
                if with_docstring:
                    data["docstring"] = inspect.getdoc(obj) or "No docstring available."
                return data

            return {"error": f"Object '{function_path}' is not a function or method."}
        except Exception as e:
            return {"error": f"Error getting function info: {e}"}

    @lru_cache(maxsize=128)
    def get_class_info(self, class_path, with_docstring=False):
        """
        Retrieve the signature, methods, variables, and optionally the docstring of a class.

        Parameters:
        class_path (str): The full import path to the class (e.g., "build123d.Box").
        with_docstring (bool): If True, include the docstring in the output.

        Returns:
        dict: A dictionary containing the class name, signature, flattened methods, variables, and docstring (optional).
        """
        logger.debug(colorstring(f"Getting class info for {class_path}", "cyan"))

        try:
            parts = class_path.split(".")
            module_name = parts[0]
            module = importlib.import_module(module_name)

            # Traverse the path to get the class
            cls = module
            for part in parts[1:]:
                cls = getattr(cls, part)

            # Handle __init__ method
            init_func = cls.__init__ if "__init__" in cls.__dict__ else None
            signature = str(inspect.signature(init_func)) if init_func else "()"
            if signature.startswith("(self, "):
                signature = signature.replace("(self, ", "(")

            data = {
                "name": class_path,
                "signature": f"{class_path}{signature}",
                "methods": [],  # Flattened methods (as standalone functions)
                "variables": [],
            }
            if with_docstring:
                data["docstring"] = inspect.getdoc(cls) or "No docstring available."

            # Collect methods and flatten them using get_function_info
            for name, member in inspect.getmembers(cls):
                if inspect.isroutine(member) and not name.startswith("_"):
                    method_path = f"{class_path}.{name}"
                    method_info = self.get_function_info(method_path, with_docstring)
                    if "error" not in method_info:
                        data["methods"].append(method_info)

            # Collect variables
            for name, member in inspect.getmembers(cls):
                if not inspect.isroutine(member) and not name.startswith("_"):
                    data["variables"].append(name)

            return data
        except Exception as e:
            return {"error": f"Error getting class info: {e}"}

    def get_module_info(self, module_name, with_docstring=False):
        """
        Retrieve the classes, functions, variables, and optionally the docstring of a module.

        Parameters:
        module_name (str): The name of the module.
        with_docstring (bool): If True, include the docstring in the output.

        Returns:
        dict: A dictionary containing the module name, classes, functions, variables, and docstring (optional).
        """
        logger.debug(colorstring(f"Getting module info for {module_name}", "yellow"))

        try:
            module = importlib.import_module(module_name)
            data = {
                "name": module_name,
                "classes": [],
                "functions": [],
                "variables": [],
            }
            if with_docstring:
                data["docstring"] = inspect.getdoc(module) or "No docstring available."

            # Helper function to check if member belongs to the module
            def belongs_to_module(member):
                return hasattr(member, "__module__") and member.__module__.startswith(
                    module_name
                )

            # Collect classes
            for name, member in inspect.getmembers(module, inspect.isclass):
                if belongs_to_module(member):
                    class_info = self.get_class_info(
                        f"{module_name}.{name}", with_docstring
                    )
                    if "error" not in class_info:
                        data["classes"].append(class_info)

            # Collect functions (including built-in functions)
            for name, member in inspect.getmembers(
                module, lambda m: inspect.isroutine(m)
            ):
                if belongs_to_module(member):
                    func_info = self.get_function_info(
                        f"{module_name}.{name}", with_docstring
                    )
                    if "error" not in func_info:
                        data["functions"].append(func_info)

            # Collect variables
            for name, member in inspect.getmembers(module):
                if (
                    not inspect.isclass(member)
                    and not inspect.isroutine(member)
                    and not name.startswith("_")
                    and belongs_to_module(member)
                ):
                    variable_info = {
                        "name": name,
                        "value": str(member),
                        "type": type(member).__name__,
                    }
                    data["variables"].append(variable_info)

            return data
        except ImportError:
            return {"error": f"Module '{module_name}' not found."}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}

    def get_info(self, path, with_docstring=True):
        """
        Retrieve information about a module, class, function, or variable.
        """

        try:
            parts = path.split(".")
            module_name = parts[0]
            logger.debug(f"Importing module: {module_name}")
            module = importlib.import_module(module_name)
            logger.debug(f"Successfully imported module: {module_name}")

            # Traverse the path to get the member
            obj = module
            for part in parts[1:]:
                logger.debug(f"Traversing path: {part}")
                obj = getattr(obj, part)
                logger.debug(f"Retrieved object: {obj}")

            logger.debug(f"Inspecting object: {obj}")
            # Determine the type of the member
            if (
                inspect.isfunction(obj)
                or inspect.isbuiltin(obj)
                or inspect.ismethod(obj)
            ):
                logger.debug(colorstring(f"Detected function: {path}", "magenta"))
                result = self.get_function_info(path, with_docstring=with_docstring)
            elif inspect.isclass(obj):
                logger.debug(colorstring(f"Detected class: {path}", "cyan"))
                result = self.get_class_info(path, with_docstring=with_docstring)
            elif inspect.ismodule(obj):
                logger.debug(colorstring(f"Detected module: {path}", "yellow"))
                result = self.get_module_info(path, with_docstring=with_docstring)
            else:
                logger.debug(f"Detected variable: {path}")
                # Handle variables or other types
                result = {
                    "name": path,
                    "type": type(obj).__name__,
                    "value": str(obj),
                }

            # Save debug info
            logger.debug(f"Saving debug info to debug_info.json")
            if logging.root.level == logging.DEBUG:
                import json

                with open("debug_info.json", "w") as f:
                    json.dump(result, f, indent=4)

            return result
        except ImportError as e:
            logger.error(f"ImportError: {e}")
            return {"error": f"Module '{module_name}' not found."}
        except AttributeError as e:
            logger.error(f"AttributeError: {e}")
            return {
                "error": f"Member '{parts[-1]}' not found in module '{module_name}'."
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": f"An unexpected error occurred: {str(e)}"}

    def dict_to_markdown(self, data, show_docstring=True):
        """
        Convert a dictionary containing module, class, function, or variable information into a Markdown-formatted string.

        Parameters:
        data (dict): A dictionary containing module, class, function, or variable information.
        show_docstring (bool): If True, include docstrings in the output.

        Returns:
        str: A Markdown-formatted string.
        """
        if "error" in data:
            return f"# Error\n{data['error']}"
        if "classes" in data and "functions" in data:
            # It's module info
            markdown_output = f"# Module: {data['name']}\n\n"
            if show_docstring and "docstring" in data:
                markdown_output += (
                    f"- **Docstring**:\n```markdown\n{data['docstring']}\n```\n\n"
                )
            if data["classes"]:
                markdown_output += "## Classes\n"
                for cls in data["classes"]:
                    markdown_output += f"### {cls['name']}\n"
                    markdown_output += f"- **Signature**: `{cls['signature']}`\n"
                    if show_docstring and "docstring" in cls:
                        markdown_output += f"- **Docstring**:\n```markdown\n{cls['docstring']}\n```\n\n"
            if data["functions"]:
                markdown_output += "## Functions\n"
                for func in data["functions"]:
                    markdown_output += f"### {func['name']}\n"
                    markdown_output += f"- **Signature**: `{func['signature']}`\n"
                    if show_docstring and "docstring" in func:
                        markdown_output += f"- **Docstring**:\n```markdown\n{func['docstring']}\n```\n\n"
            if data["variables"]:
                markdown_output += "## Variables\n"
                for var in data["variables"]:
                    markdown_output += (
                        f"- **{var['name']}** (`{var['type']}`): {var['value']}\n"
                    )
            return markdown_output
        elif "methods" in data:
            # It's class info
            markdown_output = f"# Class: {data['name']}\n\n"
            markdown_output += f"- **Signature**: `{data['signature']}`\n"
            if show_docstring and "docstring" in data:
                markdown_output += (
                    f"- **Docstring**:\n```markdown\n{data['docstring']}\n```\n\n"
                )
            markdown_output += "## Methods\n"
            for method in data["methods"]:
                markdown_output += f"### {method['name']}\n"
                markdown_output += f"- **Signature**: `{method['signature']}`\n"
                if show_docstring and "docstring" in method:
                    markdown_output += (
                        f"- **Docstring**:\n```markdown\n{method['docstring']}\n```\n\n"
                    )
            markdown_output += "## Variables\n"
            for var in data["variables"]:
                markdown_output += f"- {var}\n"
            return markdown_output
        elif "signature" in data:
            # It's function info
            markdown_output = f"# Function: {data['name']}\n\n"
            markdown_output += f"- **Signature**: `{data['signature']}`\n"
            if show_docstring and "docstring" in data:
                markdown_output += (
                    f"- **Docstring**:\n```markdown\n{data['docstring']}\n```\n"
                )
            return markdown_output
        elif "type" in data:
            # It's a variable
            markdown_output = f"# Variable: {data['name']}\n\n"
            markdown_output += f"- **Type**: `{data['type']}`\n"
            markdown_output += f"- **Value**: `{data['value']}`\n"
            return markdown_output
        else:
            return "# Unknown\nInvalid data format."


def doc_helper(import_path, with_docstring: bool = False):
    """
    Query module, class, function, or method information and return it in Markdown format.
    """
    _helper = CodeDocHelper()
    info = _helper.get_info(import_path, with_docstring=with_docstring)
    markdown_formatted_str = _helper.dict_to_markdown(
        info, show_docstring=with_docstring
    )
    return markdown_formatted_str


if __name__ == "__main__":

    import argparse

    from cicada.core.utils import colorstring, setup_logging  # For fuzzy matching

    parser = argparse.ArgumentParser(
        description="Query module, class, function, or method information."
    )
    parser.add_argument(
        "path",
        type=str,
        default="math.sqrt",
        nargs="?",  # Makes the path argument optional (consumes one argument if provided)
        help="The full import path or keyword to query (e.g., 'Box' or 'build123d.Box').",
    )
    parser.add_argument(
        "--docstring",
        action="store_true",
        help="Include the docstring in the output (only applies to path queries).",
    )
    parser.add_argument(
        "--no_output",
        action="store_true",
        help="Disable output to the console.",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    setup_logging(
        log_level="DEBUG" if args.debug else "INFO",
        log_file="/tmp/cicada/code_dochelper.log",
    )

    # Initialize the CodeDocHelper
    helper = CodeDocHelper()

    # Get the information based on the provided path
    info = helper.get_info(args.path, with_docstring=args.docstring)

    # Convert the information to Markdown and print it
    markdown_formatted_str = helper.dict_to_markdown(
        info, show_docstring=args.docstring
    )
    print(markdown_formatted_str)
    # Save debug info

    logger.debug(f"Saving debug info to debug_info.json")
    if logging.root.level == logging.DEBUG:
        # Save the output to a file
        with open("debug_info.md", "w") as f:
            f.write(markdown_formatted_str)
