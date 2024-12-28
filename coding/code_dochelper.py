import inspect
import importlib


def get_function_info(function_name, module_name):
    """
    Retrieve the docstring and function signature of a given function or class from an installed library.

    Parameters:
    function_name (str): The name of the function or class.
    module_name (str): The name of the module where the function or class is located.

    Returns:
    str: A formatted string containing the function/class name, signature, and docstring.
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

        # Format the output string
        output = (
            f"Function/Class: {function_name}\n"
            f"Signature: {function_name}{signature}\n"
            f"Docstring:\n{docstring}\n"
        )

        return output

    except ImportError:
        return f"Error: Module '{module_name}' not found."
    except AttributeError:
        return f"Error: Function/Class '{function_name}' not found in module '{module_name}'."
    except Exception as e:
        return f"Error: An unexpected error occurred: {str(e)}"


# Example usage
if __name__ == "__main__":
    # Example: Get info about the 'Box' class from the 'build123d' library
    info = get_function_info("Box", "build123d")
    print(info)
