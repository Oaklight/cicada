import inspect
import importlib


def export_module_docs(module_name, output_file):
    # Dynamically import the module
    module = importlib.import_module(module_name)

    # Collect public functions and methods
    public_methods = {
        name: obj
        for name, obj in inspect.getmembers(module)
        if inspect.isfunction(obj)
        or inspect.isbuiltin(obj)
        and not name.startswith("_")
    }

    # Prepare the output
    with open(output_file, "w") as f:
        for name, func in public_methods.items():
            signature = inspect.signature(func)
            docstring = inspect.getdoc(func) or "No docstring available."
            f.write(f"Function: {name}\n")
            f.write(f"Signature: {name}{signature}\n")
            f.write(f"Docstring:\n{docstring}\n")
            f.write("\n" + "=" * 80 + "\n\n")


# Example usage
module_name = "build123d"  # Replace with your module name
output_file = "module_docs.txt"
export_module_docs(module_name, output_file)
