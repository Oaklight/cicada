# common/tools.py
import inspect
import json
from typing import Any, Callable, Dict, List

from pydantic import BaseModel


class Tool(BaseModel):
    """
    Represents a tool (function) that can be called by the language model.
    """

    name: str
    description: str
    parameters: Dict[str, Any]
    callable: Callable


class ToolRegistry:
    """
    A registry for managing tools (functions) and their metadata.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, func: Callable, description: str = None):
        """
        Register a function as a tool.

        Args:
            func (Callable): The function to register.
            description (str, optional): A description of the function. If not provided,
                                        the function's docstring will be used.
        """
        # Generate the function's JSON schema based on its signature
        parameters = self._generate_parameters_schema(func)
        name = func.__name__
        description = description or func.__doc__ or "No description provided."

        # Create a Tool instance
        tool = Tool(
            name=name,
            description=description,
            parameters=parameters,
            callable=func,
        )

        # Add the tool to the registry
        self._tools[name] = tool

    def _generate_parameters_schema(self, func: Callable) -> Dict[str, Any]:
        """
        Generate a JSON schema for the function's parameters.

        Args:
            func (Callable): The function to generate the schema for.

        Returns:
            Dict[str, Any]: The JSON schema for the function's parameters.
        """
        signature = inspect.signature(func)
        parameters = {}

        for name, param in signature.parameters.items():
            if name == "self":
                continue  # Skip 'self' for methods
            param_type = (
                str(param.annotation)
                if param.annotation != inspect.Parameter.empty
                else "str"
            )
            parameters[name] = {
                "type": param_type,
                "description": f"The {name} parameter.",
            }

        return {
            "type": "object",
            "properties": parameters,
            "required": [
                name
                for name, param in signature.parameters.items()
                if param.default == inspect.Parameter.empty
            ],
        }

    def get_tools_json(self) -> List[Dict[str, Any]]:
        """
        Get the JSON representation of all registered tools.

        Returns:
            List[Dict[str, Any]]: A list of tools in JSON format.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    def get_callable(self, function_name: str) -> Callable:
        """
        Get a callable function by its name.

        Args:
            function_name (str): The name of the function.

        Returns:
            Callable: The function to call, or None if not found.
        """
        tool = self._tools.get(function_name)
        return tool.callable if tool else None

    def __repr__(self):
        """
        Return the JSON representation of the registry for debugging purposes.
        """
        return json.dumps(self.get_tools_json(), indent=2)

    def __str__(self):
        """
        Return the JSON representation of the registry as a string.
        """
        return json.dumps(self.get_tools_json(), indent=2)

    def __getitem__(self, key: str) -> Callable:
        """
        Enable key-value access to retrieve callables.

        Args:
            key (str): The name of the function.

        Returns:
            Callable: The function to call, or None if not found.
        """
        return self.get_callable(key)


# Create a global instance of the ToolRegistry
tool_registry = ToolRegistry()

# Example usage
if __name__ == "__main__":
    # Register a function
    def get_weather(location: str) -> str:
        """Get the current weather for a given location."""
        return f"Weather in {location}: Sunny, 25°C"

    tool_registry.register(get_weather)

    # Register another function
    def get_news(topic: str) -> str:
        """Get the latest news on a given topic."""
        return f"Latest news about {topic}."

    tool_registry.register(get_news)

    # Get the JSON representation of all tools
    tools_json = tool_registry.get_tools_json()
    print(tool_registry)

    # Get a callable function by name
    # weather_function = tool_registry.get_callable("get_weather")
    # if weather_function:
    #     print(weather_function("San Francisco"))
    print(tool_registry["get_weather"]("San Francisco"))

    import os, sys

    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _parent_dir = os.path.dirname(_current_dir)
    sys.path.extend([_current_dir, _parent_dir])
    from coding.code_dochelper import CodeDocHelper

    def doc_helper(import_path, with_docstring: bool = False):
        helper = CodeDocHelper()
        info = helper.get_info(import_path, with_docstring=with_docstring)
        markdown_formatted_str = helper.dict_to_markdown(
            info, show_docstring=with_docstring
        )
        return markdown_formatted_str

    tool_registry.register(doc_helper)

    # Get the JSON representation of all tools again
    tools_json = tool_registry.get_tools_json()
    print(json.dumps(tools_json, indent=2))

    print(tool_registry["doc_helper"]("build123d.Box", with_docstring=True))
