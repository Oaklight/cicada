import argparse
import importlib
import inspect
from functools import lru_cache


def get_function_info(function_path, with_docstring=False):
    """
    Retrieve the signature and optionally the docstring of a function or class method.

    Parameters:
    function_path (str): The full import path to the function (e.g., "build123d.Box.bounding_box").
    with_docstring (bool): If True, include the docstring in the output.

    Returns:
    dict: A dictionary containing the function name, signature, and docstring (optional).
    """
    try:
        parts = function_path.split(".")
        module_name = parts[0]
        module = importlib.import_module(module_name)
        # Traverse the path to get the function
        obj = module
        for part in parts[1:]:
            obj = getattr(obj, part)
        # Get the signature
        signature = str(inspect.signature(obj))
        # Handle class methods
        if inspect.ismethod(obj):
            if signature.startswith("(self, "):
                signature = signature.replace("(self, ", "(")
        data = {"name": function_path, "signature": f"{parts[-1]}{signature}"}
        if with_docstring:
            data["docstring"] = inspect.getdoc(obj) or "No docstring available."
        return data
    except Exception as e:
        return {"error": f"Error getting function info: {e}"}


@lru_cache(maxsize=128)
def get_class_info(class_path, with_docstring=False):
    """
    Retrieve the signature, methods, variables, and optionally the docstring of a class.

    Parameters:
    class_path (str): The full import path to the class (e.g., "build123d.Box").
    with_docstring (bool): If True, include the docstring in the output.

    Returns:
    dict: A dictionary containing the class name, signature, methods, variables, and docstring (optional).
    """
    try:
        parts = class_path.split(".")
        module_name = parts[0]
        module = importlib.import_module(module_name)
        # Traverse the path to get the class
        cls = module
        for part in parts[1:]:
            cls = getattr(cls, part)
        # Get the class signature
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
        # Get public methods
        for name, member in inspect.getmembers(cls, inspect.isfunction):
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
        # Get member variables
        for name, member in inspect.getmembers(cls):
            if not inspect.isfunction(member) and not name.startswith("_"):
                data["variables"].append(name)
        return data
    except Exception as e:
        return {"error": f"Error getting class info: {e}"}


def get_module_info(module_name, with_docstring=False):
    """
    Retrieve the classes, functions, variables, and optionally the docstring of a module.

    Parameters:
    module_name (str): The name of the module.
    with_docstring (bool): If True, include the docstring in the output.

    Returns:
    dict: A dictionary containing the module name, classes, functions, variables, and docstring (optional).
    """
    try:
        module = importlib.import_module(module_name)
        data = {"name": module_name, "classes": [], "functions": [], "variables": []}
        if with_docstring:
            data["docstring"] = inspect.getdoc(module) or "No docstring available."
        # Get classes defined in the module or its submodules
        for name, member in inspect.getmembers(module, inspect.isclass):
            if member.__module__.startswith(module_name):
                class_info = get_class_info(f"{module_name}.{name}", with_docstring)
                if "error" not in class_info:
                    data["classes"].append(class_info)
        # Get functions defined in the module or its submodules
        for name, member in inspect.getmembers(module, inspect.isfunction):
            if member.__module__.startswith(module_name):
                func_info = get_function_info(f"{module_name}.{name}", with_docstring)
                if "error" not in func_info:
                    data["functions"].append(func_info)
        # Get variables defined in the module
        for name, member in inspect.getmembers(module):
            if (
                not inspect.isclass(member)
                and not inspect.isfunction(member)
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


def get_info(path, with_docstring=True):
    """
    Retrieve information about a module, class, function, or variable.

    Parameters:
    path (str): The full import path to the module, class, function, or variable.
    with_docstring (bool): If True, include the docstring in the output.

    Returns:
    dict: A dictionary containing the information about the module, class, function, or variable.
    """
    try:
        parts = path.split(".")
        module_name = parts[0]
        module = importlib.import_module(module_name)
        # Traverse the path to get the member
        obj = module
        for part in parts[1:]:
            obj = getattr(obj, part)
        # Determine the type of the member
        if inspect.isfunction(obj):
            return get_function_info(path, with_docstring=with_docstring)
        elif inspect.isclass(obj):
            return get_class_info(path, with_docstring=with_docstring)
        elif inspect.ismodule(obj):
            return get_module_info(path, with_docstring=with_docstring)
        else:
            # Handle variables or other types
            return {
                "name": path,
                "type": type(obj).__name__,
                "value": str(obj),
            }
    except ImportError:
        return {"error": f"Module '{module_name}' not found."}
    except AttributeError:
        return {"error": f"Member '{parts[-1]}' not found in module '{module_name}'."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


def dict_to_markdown(data, show_docstring=True):
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
                    markdown_output += (
                        f"- **Docstring**:\n```markdown\n{cls['docstring']}\n```\n\n"
                    )
        if data["functions"]:
            markdown_output += "## Functions\n"
            for func in data["functions"]:
                markdown_output += f"### {func['name']}\n"
                markdown_output += f"- **Signature**: `{func['signature']}`\n"
                if show_docstring and "docstring" in func:
                    markdown_output += (
                        f"- **Docstring**:\n```markdown\n{func['docstring']}\n```\n\n"
                    )
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


def main():
    """
    Command Line Interface for querying module, class, function, or method information.
    """
    parser = argparse.ArgumentParser(
        description="Query module, class, function, or method information."
    )
    parser.add_argument(
        "path",
        type=str,
        help="The full import path or keyword to query (e.g., 'Box' or 'build123d.Box').",
    )
    parser.add_argument(
        "--docstring",
        action="store_true",
        help="Include the docstring in the output.",
    )
    args = parser.parse_args()

    # Get the information based on the provided path
    info = get_info(args.path, with_docstring=args.docstring)
    # Convert the information to Markdown and print it
    print(dict_to_markdown(info, show_docstring=args.docstring))


if __name__ == "__main__":
    main()
