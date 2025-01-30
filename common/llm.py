import argparse
import logging
import os
import sys
from abc import ABC

import httpx
import openai
import tenacity

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common.basics import PromptBuilder
from common.tools import ToolRegistry
from common.utils import colorstring, cprint, load_config, setup_logging

logger = logging.getLogger(__name__)


class LanguageModel(ABC):
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        **model_kwargs,
    ):
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.org_id = org_id
        self.model_kwargs = model_kwargs

        # Check if 'stream' is provided in model_kwargs, otherwise default to False
        self.stream = self.model_kwargs.get("stream", False)
        self.model_kwargs.pop("stream", None)

        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base_url, organization=self.org_id
        )

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3) | tenacity.stop_after_delay(30),
        wait=tenacity.wait_random_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type(
            (openai.APIError, httpx.ReadTimeout, httpx.ConnectTimeout)
        ),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def query(self, prompt, system_prompt=None, tools: ToolRegistry = None):
        """
        Query the language model with a prompt, optionally a system prompt, and tools for function calling.

        Args:
            prompt (str): The user prompt to send to the model.
            system_prompt (str, optional): The system prompt to guide the model's behavior.
            tools (ToolRegistry, optional): A registry of tools for function calling.

        Returns:
            str: The model's response, including any function call results.
        """
        stream = self.stream  # Use stream from configuration

        # Prepare messages
        messages = [{"role": "user", "content": prompt}]
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        # Handle different models
        if self.model_name == "gpto1preview":
            # gpto1preview does not support function calling
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self.client.completions.create(
                model=self.model_name,
                prompt=full_prompt,
                stream=stream,
                **self.model_kwargs,
            )
            return self._handle_response(response, stream, is_gpto1preview=True)
        else:
            # Add tools to the request if provided and model supports it
            kwargs = self.model_kwargs.copy()
            if tools:
                if len(tools) > 0:
                    kwargs["tools"] = tools.get_tools_json()
                    kwargs["tool_choice"] = (
                        "auto"  # Automatically choose the tool to call
                    )

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=stream,
                **kwargs,
            )
            return self._handle_response(
                response,
                stream,
                is_deepseek=self.model_name in ["deepseek-r1", "deepseek-reasoner"],
                tools=tools,
                messages=messages,  # Pass the initial messages
            )

    def _handle_response(
        self,
        response,
        stream,
        is_gpto1preview=False,
        is_deepseek=False,
        tools: ToolRegistry = None,
        messages=None,  # Add messages parameter
    ):
        """
        Handle the response from the model, including function calling and streaming.

        Args:
            response: The response object from the model.
            stream (bool): Whether the response is streamed.
            is_gpto1preview (bool): Whether the model is gpto1preview.
            is_deepseek (bool): Whether the model is a Deepseek model.
            tools (ToolRegistry, optional): A registry of tools for function calling.
            messages (list, optional): The message history.

        Returns:
            str: The complete response from the model, including any function call results.
        """
        if stream:
            complete_response = ""
            tool_calls = {}  # To store tool call chunks
            for chunk in response:
                if is_gpto1preview:
                    chunk_text = chunk.choices[0].text
                    cprint(chunk_text, "white", end="", flush=True)
                    complete_response += chunk_text
                else:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        cprint(delta.content, "white", end="", flush=True)
                        complete_response += delta.content
                    if is_deepseek:
                        reasoning_content = getattr(delta, "reasoning_content", None)
                        if reasoning_content:
                            cprint(reasoning_content, "cyan", end="", flush=True)
                            complete_response += reasoning_content
                    if tools and delta.tool_calls:
                        # Handle tool calls in streaming mode
                        for tool_call in delta.tool_calls:
                            index = tool_call.index
                            if index not in tool_calls:
                                tool_calls[index] = {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }
                            if tool_call.id:
                                tool_calls[index]["id"] += tool_call.id
                            if tool_call.function.name:
                                tool_calls[index]["function"][
                                    "name"
                                ] += tool_call.function.name
                            if tool_call.function.arguments:
                                tool_calls[index]["function"][
                                    "arguments"
                                ] += tool_call.function.arguments

            print()  # Add a newline after the response

            # Execute tool calls if any
            if tool_calls:
                cprint("Executing tool calls...", "yellow")
                tool_responses = []
                for index, tool_call in tool_calls.items():
                    function_name = tool_call["function"]["name"]
                    function_args = tool_call["function"]["arguments"]
                    cprint(
                        f"Executing {function_name} with args {function_args}...",
                        "yellow",
                    )
                    function_response = self._execute_function_call(
                        function_name, function_args, tools
                    )
                    tool_responses.append(function_response)

                # Append function call results to the message history
                if messages is not None:
                    # Add the assistant's message with tool_calls
                    assistant_message = {
                        "role": "assistant",
                        "content": complete_response,
                        "tool_calls": [
                            {
                                "id": tool_call["id"],
                                "type": "function",
                                "function": {
                                    "name": tool_call["function"]["name"],
                                    "arguments": tool_call["function"]["arguments"],
                                },
                            }
                            for tool_call in tool_calls.values()
                        ],
                    }
                    messages.append(assistant_message)

                    # Add the tool responses
                    for index, tool_call in tool_calls.items():
                        messages.append(
                            {
                                "role": "tool",
                                "content": tool_responses[index],
                                "tool_call_id": tool_call["id"],
                            }
                        )

                    # Make a second request with the updated message history
                    second_response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        stream=stream,
                        **self.model_kwargs,
                    )

                    # Stream the second response
                    second_complete_response = ""
                    for chunk in second_response:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            cprint(delta.content, "white", end="", flush=True)
                            second_complete_response += delta.content
                    print()  # Add a newline after the response

                    return second_complete_response.strip()

            return complete_response.strip()
        else:
            if is_gpto1preview:
                return response.choices[0].text.strip()
            else:
                message = response.choices[0].message
                response_content = (
                    message.content or ""
                )  # Initialize as empty string if None

                # Handle function calling (only for models that support it)
                if tools and hasattr(message, "tool_calls") and message.tool_calls:
                    tool_calls = message.tool_calls
                    tool_responses = []
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = tool_call.function.arguments
                        cprint(
                            f"Executing {function_name} with args {function_args}...",
                            "yellow",
                        )
                        function_response = self._execute_function_call(
                            function_name, function_args, tools
                        )
                        tool_responses.append(function_response)

                    # Append function call results to the response
                    if tool_responses:
                        response_content += (
                            "\n\n[Function Call Results]:\n" + "\n".join(tool_responses)
                        )

                    # Add the function call results back to the message history
                    if messages is not None:
                        messages.append(message)
                        for tool_call, tool_response in zip(tool_calls, tool_responses):
                            messages.append(
                                {
                                    "role": "tool",
                                    "content": tool_response,
                                    "tool_call_id": tool_call.id,
                                }
                            )

                        # Make a second call to the model with the updated message history
                        second_response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=messages,
                            stream=stream,
                            **self.model_kwargs,
                        )
                        return self._handle_response(
                            second_response,
                            stream,
                            is_deepseek=is_deepseek,
                            tools=tools,
                            messages=messages,
                        )

                if is_deepseek:
                    reasoning_content = getattr(message, "reasoning_content", None)
                    if reasoning_content:
                        return f"[Reasoning]: {reasoning_content}\n\n[Response]: {response_content}".strip()
                return response_content.strip()

    def _execute_function_call(self, function_name, function_args, tools: ToolRegistry):
        """
        Execute a function call based on the provided function name and arguments.

        Args:
            function_name (str): The name of the function to call.
            function_args (str): The arguments for the function (as a JSON string).
            tools (ToolRegistry): A registry of tools for function calling.

        Returns:
            str: The result of the function call.
        """
        if not tools:
            return f"Error: No tools provided to execute function '{function_name}'."

        # Retrieve the callable function from the ToolRegistry
        function_to_call = tools[function_name]  # or tools.get_callable(function_name)
        if not function_to_call:
            return f"Error: Function '{function_name}' not found in the ToolRegistry."

        try:
            # Parse the arguments
            import json

            args_dict = json.loads(function_args)
            # Execute the function
            result = function_to_call(**args_dict)
            return f"{function_name}({function_args}) -> {result}"
        except Exception as e:
            return f"Error executing function '{function_name}': {str(e)}"

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3) | tenacity.stop_after_delay(30),
        wait=tenacity.wait_random_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type(
            (openai.APIError, httpx.ReadTimeout, httpx.ConnectTimeout)
        ),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def query_with_promptbuilder(self, pb: PromptBuilder) -> str:
        """
        Query the LanguageModel using a PromptBuilder object.

        Args:
            pb: The PromptBuilder object containing the prompt and tools.

        Returns:
            str: Generated response from the model.
        """
        if self.model_name in ["argo:gpt-o1-preview", "gpto1preview"]:
            raise NotImplementedError("gpto1preview does not support PromptBuilder")

        # Extract the user prompt, system prompt, and tools from the PromptBuilder
        user_prompt = ""
        system_prompt = None
        tools: ToolRegistry = pb.get_tools()

        for message in pb.messages:
            if message["role"] == "user":
                user_prompt = message["content"]
            elif message["role"] == "system":
                system_prompt = message["content"]

        # Call the query method with extracted prompts and tools
        return self.query(prompt=user_prompt, system_prompt=system_prompt, tools=tools)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()
    setup_logging()

    llm_config = load_config(args.config, "llm")

    llm = LanguageModel(
        llm_config["api_key"],
        llm_config.get("api_base_url"),
        llm_config.get("model_name", "gpt-4o-mini"),
        llm_config.get("org_id"),
        **llm_config.get("model_kwargs", {}),
    )

    # Register tools
    from common.tools import tool_registry

    # # Query the model
    # response = llm.query("What's the weather in San Francisco?", tools=tool_registry)

    # if not llm.stream:
    #     print(response)
    print("=" * 80)

    # ======== doc helper test ========
    import os
    import sys

    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _parent_dir = os.path.dirname(_current_dir)
    sys.path.extend([_current_dir, _parent_dir])
    from coding.code_dochelper import doc_helper

    tool_registry.register(doc_helper)
    response = llm.query(
        """Got the following error feedbacks:              

        Traceback (most recent call last):\n  File "/tmp/tmpgw4eo_ew/script.py", line 7, in <module>\n    tabletop_sketch = Circle(radius=50)\n                      ^^^^^^^^^^^^^^^^^\n  File "/home/pding/mambaforge/envs/codecad/lib/python3.11/site-packages/build123d/objects_sketch.py", line 121, in __init__\n    validate_inputs(context, self)\n  File "/home/pding/mambaforge/envs/codecad/lib/python3.11/site-packages/build123d/build_common.py", line 793, in validate_inputs\n    context.validate_inputs(validating_class, objects)\n  File "/home/pding/mambaforge/envs/codecad/lib/python3.11/site-packages/build123d/build_common.py", line 731, in validate_inputs\n    raise RuntimeError(\nRuntimeError: BuildPart doesn\'t have a Circle object or operation (Circle applies to [\'BuildSketch\']) 

        Which documentation or sections should I look up to address these issues?  Remember always include top level import path `build123d`, such as `build123d.Box` for `Box` class. 
        """,
        tools=tool_registry,
    )
    # if not llm.stream:
    print(response)
