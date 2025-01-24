import argparse
import importlib
import inspect
import logging
import os
import pickle
import re
import sys
from functools import lru_cache

from thefuzz import process

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common.utils import colorstring, setup_logging  # For fuzzy matching

logger = logging.getLogger(__name__)


class CodeDocHelper:
    def __init__(self, fuzzy_threshold=80, cache_file="code_doc_cache.pkl"):
        """
        Initialize the CodeDocHelper with a cache and fuzzy matching threshold.

        Parameters:
        fuzzy_threshold (int): The minimum similarity score (0-100) for fuzzy matching.
        cache_file (str): The file to store the cache for persistence.
        """
        self.query_cache = {}
        self.fuzzy_threshold = fuzzy_threshold
        self.cache_file = cache_file
        # Load cache from file if it exists
        self._load_cache()

    def __del__(self):
        """
        Save the cache to a file when the CodeDocHelper instance is destroyed.
        """
        self._save_cache()

    def _load_cache(self):
        """
        Load the cache from a file if it exists.
        """
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "rb") as f:
                self.query_cache = pickle.load(f)

    def _save_cache(self):
        """
        Save the cache to a file.
        """
        with open(self.cache_file, "wb") as f:
            pickle.dump(self.query_cache, f)

    def _fuzzy_match_cache(self, query):
        """
        Perform fuzzy matching on the cache keys to find the closest match.

        Parameters:
        query (str): The query to match against cache keys.

        Returns:
        tuple: The closest matching cache key and its score, or (None, 0) if no match is found.
        """
        if not self.query_cache:
            return None, 0

        # Extract all cache keys
        cache_keys = list(self.query_cache.keys())
        # Perform fuzzy matching
        match, score = process.extractOne(query, cache_keys)
        return match, score

    def pre_fill_cache(self, markdown_file):
        """
        Pre-fill the cache with objects/functions extracted from a markdown file.

        Parameters:
        markdown_file (str): The path to the markdown file.

        Returns:
        dict: A dictionary containing the parts of the cache that were changed during the pre-fill process.
        """

        def extract_objects_from_markdown(markdown_content):
            """
            Extract objects/functions from the markdown content.

            Parameters:
            markdown_content (str): The content of the markdown file.

            Returns:
            list: A list of objects/functions extracted from the markdown.
            """
            # Regular expressions to match stateful contexts, objects, operations, selectors, etc.
            stateful_context_pattern = re.compile(r"\* \*\*(\w+)\*\* \(`([\w\.]+)`\)")
            object_pattern = re.compile(r"\* \*\*(\w+)\*\* \(`([\w\.]+)`\)")
            operation_pattern = re.compile(r"\* \*\*(\w+)\*\* \(`([\w\.]+)`\)")
            selector_pattern = re.compile(r"\* \*\*(\w+)\*\* \(`([\w\.]+)`\)")
            enum_pattern = re.compile(r"\| \*\*(\w+)\*\*")

            # Extract stateful contexts
            stateful_contexts = stateful_context_pattern.findall(markdown_content)

            # Extract objects
            objects = object_pattern.findall(markdown_content)

            # Extract operations
            operations = operation_pattern.findall(markdown_content)

            # Extract selectors
            selectors = selector_pattern.findall(markdown_content)

            # Extract enums
            enums = enum_pattern.findall(markdown_content)

            # Combine all extracted objects/functions
            objects_functions = (
                [f"{context[1]}" for context in stateful_contexts]
                + [f"{obj[1]}" for obj in objects]
                + [f"{op[1]}" for op in operations]
                + [f"{sel[1]}" for sel in selectors]
                + [f"{enum}" for enum in enums]
            )

            return objects_functions

        # Read the markdown file
        with open(markdown_file, "r", encoding="utf-8") as file:
            markdown_content = file.read()

        # Extract objects/functions from the markdown content
        objects_functions = extract_objects_from_markdown(markdown_content)

        # Track changes to the cache
        changed_cache = {}

        # Fill the cache with the extracted objects/functions
        for obj in objects_functions:
            # Query the object/function and cache the result
            result = self.get_info(f"build123d.{obj}", with_docstring=True)
            if "error" not in result:
                changed_cache[obj] = result

        return changed_cache

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
                data = {"name": function_path, "signature": f"{parts[-1]}{signature}"}
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
        dict: A dictionary containing the class name, signature, methods, variables, and docstring (optional).
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

            # Handle built-in methods (e.g., __init__)
            if "__init__" in cls.__dict__:
                init_func = cls.__init__
                signature = str(inspect.signature(init_func))
                if signature.startswith("(self, "):
                    signature = signature.replace("(self, ", "(")
            else:
                signature = "()"

            data = {
                "name": class_path,
                "signature": f"{parts[-1]}{signature}",
                "methods": [],
                "variables": [],
            }
            if with_docstring:
                data["docstring"] = inspect.getdoc(cls) or "No docstring available."

            # Collect methods
            for name, member in inspect.getmembers(cls):
                if inspect.isfunction(member) or inspect.ismethod(member):
                    if not name.startswith("_"):
                        if inspect.isbuiltin(member):
                            continue  # Skip built-in methods
                        method = getattr(cls, name)
                        sig = str(inspect.signature(method))
                        if sig.startswith("(self, "):
                            sig = sig.replace("(self, ", "(")
                        method_info = {"name": name, "signature": f"{name}{sig}"}
                        if with_docstring:
                            method_info["docstring"] = (
                                inspect.getdoc(method) or "No docstring available."
                            )
                        data["methods"].append(method_info)

            # Collect variables
            for name, member in inspect.getmembers(cls):
                if not inspect.isfunction(member) and not name.startswith("_"):
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

            # Collect classes
            for name, member in inspect.getmembers(module, inspect.isclass):
                if member.__module__.startswith(module_name):
                    class_info = self.get_class_info(
                        f"{module_name}.{name}", with_docstring
                    )
                    if "error" not in class_info:
                        data["classes"].append(class_info)

            # Collect functions (including built-in functions)
            for name, member in inspect.getmembers(module):
                if (
                    inspect.isfunction(member)
                    or inspect.isbuiltin(member)
                    or inspect.ismethod(member)
                ):
                    if member.__module__.startswith(module_name):
                        func_info = self.get_function_info(
                            f"{module_name}.{name}", with_docstring
                        )
                        if "error" not in func_info:
                            data["functions"].append(func_info)

            # Collect variables
            for name, member in inspect.getmembers(module):
                if (
                    not inspect.isclass(member)
                    and not inspect.isfunction(member)
                    and not inspect.isbuiltin(member)
                    and not inspect.ismethod(member)
                    and not name.startswith("_")
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

    def get_info(self, path, with_docstring=True, disable_cache=False):
        """
        Retrieve information about a module, class, function, or variable.
        """
        if not disable_cache:
            cache_key = (path, with_docstring)
            if cache_key in self.query_cache:
                logger.debug(f"Cache hit for key: {cache_key}")
                return self.query_cache[cache_key]

            # Fuzzy match for similar queries
            match, score = self._fuzzy_match_cache(path)
            if score >= self.fuzzy_threshold:
                logger.debug(f"Fuzzy match found: {match} with score {score}")
                return self.query_cache[match]

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

            if not disable_cache:
                self.query_cache[cache_key] = result
                self._save_cache()  # Save cache after updating

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


def _main():
    """
    Command Line Interface for querying module, class, function, or method information.
    """
    parser = argparse.ArgumentParser(
        description="Query module, class, function, or method information."
    )
    # Exclusive group for path or fill_cache
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "path",
        type=str,
        nargs="?",  # Makes the path argument optional (consumes one argument if provided)
        help="The full import path or keyword to query (e.g., 'Box' or 'build123d.Box').",
    )
    group.add_argument(
        "-cfm",
        "--cache_from_cheatsheet",
        type=str,
        help="Pre-fill the cache using a markdown file.",
    )
    # --docstring only applies to the path branch
    parser.add_argument(
        "--docstring",
        action="store_true",
        help="Include the docstring in the output (only applies to path queries).",
    )
    parser.add_argument(
        "--disable_cache",
        action="store_true",
        help="Disable the cache for this query.",
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
        log_file="code_dochelper.log",
    )

    # Initialize the CodeDocHelper
    helper = CodeDocHelper()

    if args.cache_from_cheatsheet:
        # Pre-fill the cache and print the changed parts
        changed_cache = helper.pre_fill_cache(args.cache_from_cheatsheet)
        print("Cache pre-filled with the following items:")
        for key, value in changed_cache.items():
            print(f"{key}: {value}")
    else:
        # Get the information based on the provided path
        info = helper.get_info(
            args.path, with_docstring=args.docstring, disable_cache=args.disable_cache
        )
        if args.no_output:
            return
        # Convert the information to Markdown and print it
        print(helper.dict_to_markdown(info, show_docstring=args.docstring))


if __name__ == "__main__":
    _main()
