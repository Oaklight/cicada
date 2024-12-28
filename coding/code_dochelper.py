import inspect
import importlib


def get_function_info(function_name, module_name, with_docstring=False):
    """
    Retrieve the signature and optionally the docstring of a function.

    Parameters:
    function_name (str): The name of the function.
    module_name (str): The name of the module where the function is located.
    with_docstring (bool): If True, include the docstring in the output.

    Returns:
    dict: A dictionary containing the function name, signature, and docstring (optional).
    """
    try:
        module = importlib.import_module(module_name)
        func = getattr(module, function_name)
        signature = str(inspect.signature(func))
        data = {"name": function_name, "signature": f"{function_name}{signature}"}
        if with_docstring:
            data["docstring"] = inspect.getdoc(func) or "No docstring available."
        return data
    except Exception as e:
        return {"error": f"Error getting function info: {e}"}


def get_class_info(class_name, module_name, with_docstring=False):
    """
    Retrieve the signature, methods, variables, and optionally the docstring of a class.

    Parameters:
    class_name (str): The name of the class.
    module_name (str): The name of the module where the class is located.
    with_docstring (bool): If True, include the docstring in the output.

    Returns:
    dict: A dictionary containing the class name, signature, methods, variables, and docstring (optional).
    """
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        if "__init__" in cls.__dict__:
            init_func = cls.__init__
            signature = str(inspect.signature(init_func))
            if signature.startswith("(self, "):
                signature = signature.replace("(self, ", "(")
        else:
            signature = "()"
        data = {
            "name": class_name,
            "signature": f"{class_name}{signature}",
            "methods": [],
            "variables": [],
        }
        if with_docstring:
            data["docstring"] = inspect.getdoc(cls) or "No docstring available."
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
                class_info = get_class_info(name, member.__module__, with_docstring)
                if "error" not in class_info:
                    data["classes"].append(class_info)
        # Get functions defined in the module or its submodules
        for name, member in inspect.getmembers(module, inspect.isfunction):
            if member.__module__.startswith(module_name):
                func_info = get_function_info(name, member.__module__, with_docstring)
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


def dict_to_markdown(data, show_docstring=True):
    """
    Convert a dictionary containing module, class, or function information into a Markdown-formatted string.

    Parameters:
    data (dict): A dictionary containing module, class, or function information.
    show_docstring (bool): If True, include docstrings in the output.

    Returns:
    str: A Markdown-formatted string.
    """
    if "error" in data:
        return f"# Error\n{data['error']}"
    if "name" in data:
        if "classes" in data or "functions" in data or "variables" in data:
            # Module info
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
            # Class info
            markdown_output = f"# Class: {data['name']}\n\n"
            markdown_output += f"- **Signature**: `{data['signature']}`\n"
            if show_docstring and "docstring" in data:
                markdown_output += (
                    f"- **Docstring**:\n```markdown\n{data['docstring']}\n```\n\n"
                )
            markdown_output += "## Methods\n"
            for method in data["methods"]:
                if isinstance(method, dict) and "name" in method:
                    markdown_output += f"### {method['name']}\n"
                    markdown_output += f"- **Signature**: `{method['signature']}`\n"
                    if show_docstring and "docstring" in method:
                        markdown_output += f"- **Docstring**:\n```markdown\n{method['docstring']}\n```\n\n"
                else:
                    continue  # Skip methods without 'name'
            markdown_output += "## Variables\n"
            for var in data["variables"]:
                markdown_output += f"- {var}\n"
            return markdown_output
        else:
            # Function info
            markdown_output = f"# Function: {data['name']}\n\n"
            markdown_output += f"- **Signature**: `{data['signature']}`\n"
            if show_docstring and "docstring" in data:
                markdown_output += (
                    f"- **Docstring**:\n```markdown\n{data['docstring']}\n```\n"
                )
            return markdown_output
    return "# Unknown\nInvalid data format."


# Example usage
if __name__ == "__main__":
    # # Example: Get info about the 'Box' class from the 'build123d' library
    # class_info = get_class_info("Box", "build123d", with_docstring=True)
    # print(dict_to_markdown(class_info, show_docstring=False))

    # # Example: Get info about the 'BuildPart' function from the 'build123d' library
    # func_info = get_function_info("BuildPart", "build123d", with_docstring=True)
    # print(dict_to_markdown(func_info, show_docstring=True))

    # Example: Get info about the 'build123d' module
    module_info = get_module_info("build123d.Box", with_docstring=True)
    print(dict_to_markdown(module_info, show_docstring=False))
