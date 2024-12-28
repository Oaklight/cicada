import inspect
import importlib


def get_function_info(function_name, module_name):
    """
    Retrieve the docstring and function signature of a given function or class from an installed library.

    Parameters:
    function_name (str): The name of the function or class.
    module_name (str): The name of the module where the function or class is located.

    Returns:
    dict: A dictionary containing the function/class name, signature, and docstring.
    """
    try:
        # Dynamically import the module
        module = importlib.import_module(module_name)

        # Get the function or class from the module
        func_or_class = getattr(module, function_name)

        # Get the docstring
        docstring = inspect.getdoc(func_or_class) or "No docstring available."

        # Get the signature
        if inspect.isclass(func_or_class):
            # Handle class constructor
            signature = inspect.signature(func_or_class.__init__)
            # Remove 'self' from the signature for better readability
            signature = str(signature).replace("(self, ", "(").replace("(self)", "()")
        else:
            signature = inspect.signature(func_or_class)

        # Clean up the signature
        signature = str(signature).replace("'", "")  # Remove quotes around type hints

        return {
            "name": function_name,
            "signature": f"{function_name}{signature}",
            "docstring": docstring,
        }

    except ImportError:
        return {"error": f"Module '{module_name}' not found."}
    except AttributeError:
        return {
            "error": f"Function/Class '{function_name}' not found in module '{module_name}'."
        }
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


def get_module_members(module_name, include_details=False):
    """
    Retrieve all public classes, methods, and variables available in a module or submodule.

    Parameters:
    module_name (str): The name of the module or submodule (e.g., "time.time" or "segment").
    include_details (bool): If True, include detailed information (signature and docstring) for each function or class.

    Returns:
    dict: A dictionary containing public classes, methods, and variables.
    """
    try:
        # Dynamically import the module or submodule
        module = importlib.import_module(module_name)

        # Get all members of the module
        members = inspect.getmembers(module)

        # Filter and categorize members
        classes = [
            name
            for name, member in members
            if inspect.isclass(member) and not name.startswith("_")
        ]
        methods = [
            name
            for name, member in members
            if (inspect.isfunction(member) or inspect.ismethod(member))
            and not name.startswith("_")
        ]
        variables = [
            name
            for name, member in members
            if not inspect.isclass(member)
            and not inspect.isfunction(member)
            and not name.startswith("_")
        ]

        # Include detailed information if requested
        if include_details:
            detailed_classes = []
            for cls in classes:
                class_info = get_function_info(cls, module_name)
                detailed_classes.append(class_info)

            detailed_methods = []
            for method in methods:
                method_info = get_function_info(method, module_name)
                detailed_methods.append(method_info)

            return {
                "module": module_name,
                "classes": detailed_classes,
                "methods": detailed_methods,
                "variables": variables,
            }
        else:
            return {
                "module": module_name,
                "classes": classes,
                "methods": methods,
                "variables": variables,
            }

    except ImportError:
        return {"error": f"Module '{module_name}' not found."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


def dict_to_markdown(data, show_docstring=True):
    """
    Convert a dictionary containing function or module information into a Markdown-formatted string.

    Parameters:
    data (dict): A dictionary containing function or module information.
    show_docstring (bool): If True, include docstrings in the output. Defaults to True.

    Returns:
    str: A Markdown-formatted string.
    """
    if "error" in data:
        return f"# Error\n{data['error']}"

    if "name" in data:  # Function/Class info
        markdown_output = (
            f"# [Function/Class] {data['name']}\n\n"
            f"- **Signature**: `{data['signature']}`\n"
        )
        if show_docstring:
            markdown_output += (
                f"- **Docstring**:\n```markdown\n{data['docstring']}\n```\n"
            )
    else:  # Module info
        markdown_output = f"# Module: {data['module']}\n\n"

        if data["classes"]:
            markdown_output += "## Classes\n"
            for cls in data["classes"]:
                if isinstance(cls, dict):  # Detailed class info
                    markdown_output += (
                        f"### [Class] {cls['name']}\n"
                        f"- **Signature**: `{cls['signature']}`\n"
                    )
                    if show_docstring:
                        markdown_output += (
                            f"- **Docstring**:\n```markdown\n{cls['docstring']}\n```\n"
                        )
                else:  # Simple class name
                    markdown_output += f"- {cls}\n"
            markdown_output += "\n---\n\n"

        if data["methods"]:
            markdown_output += "## Methods\n"
            for method in data["methods"]:
                if isinstance(method, dict):  # Detailed method info
                    markdown_output += (
                        f"### [Method] {method['name']}\n"
                        f"- **Signature**: `{method['signature']}`\n"
                    )
                    if show_docstring:
                        markdown_output += f"- **Docstring**:\n```markdown\n{method['docstring']}\n```\n"
                else:  # Simple method name
                    markdown_output += f"- {method}\n"
            markdown_output += "\n---\n\n"

        if data["variables"]:
            markdown_output += "## Variables\n"
            for var in data["variables"]:
                markdown_output += f"- [Variable] {var}\n"
            markdown_output += "\n---\n\n"

        if not data["classes"] and not data["methods"] and not data["variables"]:
            markdown_output += "No public members found.\n"

    return markdown_output


# Example usage
if __name__ == "__main__":
    # Example: Get info about the 'Box' class from the 'build123d' library
    function_info = get_function_info("BuildPart", "build123d")
    print(dict_to_markdown(function_info))

    # Example: Get members of the 'time' module without details
    module_info = get_module_members("build123d.objects_curve")
    print(dict_to_markdown(module_info))

    # Example: Get members of the 'time' module with details
    module_info_detailed = get_module_members(
        "build123d.objects_curve", include_details=True
    )
    print(dict_to_markdown(module_info_detailed, show_docstring=True))
