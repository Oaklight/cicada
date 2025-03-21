import copy
import json
import logging
from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import openai
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from cicada.core.basics import PromptBuilder
from cicada.core.tools import ToolRegistry
from cicada.core.utils import cprint, recover_stream_tool_calls

# 同时抑制两个层级的日志源
logging.getLogger("httpx").setLevel(logging.WARNING)  # 屏蔽INFO级
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class MultiModalModel(ABC):
    """Language model base class with tool use support.

    Attributes:
        api_key (str): API key for authentication
        api_base_url (str): Base URL for API endpoint
        model_name (str): Name of the language model
        org_id (Optional[str]): Organization ID
        model_kwargs (Dict[str, Any]): Additional model parameters
        stream (bool): Whether to use streaming mode
        client (openai.OpenAI): OpenAI client instance
    """

    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        model_name: str,
        org_id: Optional[str] = None,
        **model_kwargs: Dict[str, Any],
    ) -> None:
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

    def query(
        self,
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        prompt_builder: Optional[PromptBuilder] = None,
        messages: Optional[List[ChatCompletionMessage]] = None,
        tools: Optional[ToolRegistry] = None,
    ) -> Dict[str, Any]:
        """Query the language model with support for tool use.

        Args:
            prompt (Optional[str]): User input prompt
            system_prompt (Optional[str]): System prompt
            stream (bool): Whether to use streaming mode
            prompt_builder (Optional[PromptBuilder]): PromptBuilder instance
            messages (Optional[List[ChatCompletionMessage]]): List of messages
            tools (Optional[ToolRegistry]): Tool registry instance

        Returns:
            Dict[str, Any]: Dictionary containing:
                - content: Main response content
                - reasoning_content: Reasoning steps (if available)
                - tool_responses: Tool execution results (if tools used)
                - formatted_response: Formatted final response
                - tool_chain: Chain of tool calls and responses (if tools used)

        Raises:
            ValueError: If no response is received from the model
        """
        # 构造消息
        messages = self._build_messages(prompt, system_prompt, prompt_builder, messages)

        # 调用API
        response = self._call_model_api(messages, stream, tools)

        # 处理响应
        if stream:
            return self._process_stream_response(messages, response, tools)
        else:
            return self._process_non_stream_response(messages, response, tools)

    def _build_messages(
        self,
        prompt: Optional[str],
        system_prompt: Optional[str],
        prompt_builder: Optional[PromptBuilder],
        messages: Optional[List[ChatCompletionMessage]],
    ) -> List[Dict[str, str]]:
        """Construct messages for the API call.

        Args:
            prompt (Optional[str]): User input prompt
            system_prompt (Optional[str]): System prompt
            prompt_builder (Optional[PromptBuilder]): PromptBuilder instance
            messages (Optional[List[ChatCompletionMessage]]): List of messages

        Returns:
            List[Dict[str, str]]: List of message dictionaries

        Raises:
            ValueError: If more than one message form is provided.
        """
        # 检查是否同时提供了多种消息形式
        provided_forms = [
            messages is not None,
            prompt_builder is not None,
            prompt is not None or system_prompt is not None,
        ]
        if sum(provided_forms) > 1:
            raise ValueError(
                "Only one of 'messages', 'prompt_builder', or 'prompt/system_prompt' can be provided."
            )

        if messages:
            # 优先使用直接传递的消息列表
            return messages
        if prompt_builder:
            # 次优先使用PromptBuilder
            return prompt_builder.messages
        else:
            # 回退到传统方式
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if prompt:
                messages.append({"role": "user", "content": prompt})
            return messages

    def _call_model_api(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        tools: Optional[ToolRegistry] = None,
    ) -> Any:
        """Call the model API with optional tool support.

        Args:
            messages (List[Dict[str, str]]): List of messages
            stream (bool): Whether to use streaming mode
            tools (Optional[ToolRegistry]): Tool registry instance

        Returns:
            Any: Raw response from the API
        """
        kwargs = self.model_kwargs.copy()
        if tools:
            kwargs["tools"] = tools.get_tools_json()
            kwargs["tool_choice"] = "auto"

        return self.client.chat.completions.create(
            model=self.model_name, messages=messages, stream=stream, **kwargs
        )

    def _process_non_stream_response(
        self,
        messages: List[Dict[str, str]],
        response: Any,
        tools: Optional[ToolRegistry] = None,
    ) -> Dict[str, Any]:
        """Process non-streaming response with tool support.

        Args:
            messages (List[Dict[str, str]]): List of messages
            response (Any): Raw API response
            tools (Optional[ToolRegistry]): Tool registry instance

        Returns:
            Dict[str, Any]: Processed response dictionary
        """
        if not response.choices:
            raise ValueError("No response from the model")
        # cprint(messages, "magenta")
        message = response.choices[0].message
        # cprint(response, "cyan")
        # 初始化结果
        result = {"content": message.content}
        if hasattr(message, "reasoning_content"):
            reasoning_content = getattr(message, "reasoning_content", "")
            if reasoning_content:
                result["reasoning_content"] = reasoning_content

        # 处理工具调用
        if tools and hasattr(message, "tool_calls") and message.tool_calls:

            result = self.get_response_with_tools(
                messages, message.tool_calls, tools, result, stream=False
            )
            # cprint(result, "yellow", flush=True)

        # 格式化响应
        result["formatted_response"] = self._format_response(result)
        return result

    @dataclass
    class StreamState:
        content: str = ""
        reasoning_content: str = ""
        stream_tool_calls: Dict[int, Dict[str, Any]] = field(default_factory=dict)
        tool_responses: List[Dict[str, Any]] = field(default_factory=list)

    def _process_content_chunk(self, delta: Any, state: StreamState) -> None:
        """Process content chunk and update state.

        Args:
            delta: Delta object from API response
            state: StreamState instance to update
        """
        if delta.content:
            state.content += delta.content
            cprint(delta.content, "white", end="", flush=True)

    def _process_reasoning_chunk(self, delta: Any, state: StreamState) -> None:
        """Process reasoning content chunk and update state.

        Args:
            delta: Delta object from API response
            state: StreamState instance to update
        """
        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
            state.reasoning_content += delta.reasoning_content
            cprint(delta.reasoning_content, "cyan", end="", flush=True)

    def _process_tool_call_chunk(
        self, delta: Any, state: StreamState, tools: Optional[ToolRegistry] = None
    ) -> None:
        """Process tool call chunk and update state.

        Args:
            delta: Delta object from API response
            state: StreamState instance to update
            tools: Optional tool registry instance
        """
        if not tools or not hasattr(delta, "tool_calls") or not delta.tool_calls:
            return

        for tool_call in delta.tool_calls:
            index = tool_call.index
            if index not in state.stream_tool_calls:
                state.stream_tool_calls[index] = {
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                }
            if tool_call.id:
                state.stream_tool_calls[index]["id"] += tool_call.id
            if tool_call.function.name:
                state.stream_tool_calls[index]["function"][
                    "name"
                ] += tool_call.function.name
            if tool_call.function.arguments:
                state.stream_tool_calls[index]["function"][
                    "arguments"
                ] += tool_call.function.arguments

    def _process_stream_chunk(
        self, chunk: Any, state: StreamState, tools: Optional[ToolRegistry] = None
    ) -> None:
        """Process a single streaming chunk and update state.

        Args:
            chunk: Raw API response chunk
            state: StreamState instance to update
            tools: Optional tool registry instance
        """
        if not chunk.choices:
            return

        delta = chunk.choices[0].delta
        self._process_content_chunk(delta, state)
        self._process_reasoning_chunk(delta, state)
        self._process_tool_call_chunk(delta, state, tools)

    def _process_stream_response(
        self,
        messages: List[Dict[str, str]],
        response: Any,
        tools: Optional[ToolRegistry] = None,
    ) -> Dict[str, Any]:
        """Process streaming response with tool support.

        Args:
            messages (List[Dict[str, str]]): List of messages
            response (Any): Raw API response
            tools (Optional[ToolRegistry]): Tool registry instance

        Returns:
            Dict[str, Any]: Processed response dictionary
        """
        state = self.StreamState()

        # 处理所有chunks
        for chunk in response:
            self._process_stream_chunk(chunk, state, tools)

        if state.content or state.reasoning_content:
            print()  # 流式结束后换行

        # 处理工具调用
        if state.stream_tool_calls:
            result = {"content": state.content}
            if state.reasoning_content:
                result["reasoning_content"] = state.reasoning_content

            if not state.stream_tool_calls:
                return result

            tool_calls = recover_stream_tool_calls(state.stream_tool_calls)
            result = self.get_response_with_tools(
                messages, tool_calls, tools, result, stream=True
            )
        else:
            result = {"content": state.content}
            if state.reasoning_content:
                result["reasoning_content"] = state.reasoning_content

        # 格式化响应
        result["formatted_response"] = self._format_response(result)
        return result

    def get_response_with_tools(
        self, messages, tool_calls, tools, result, stream=False
    ):
        # 使用 ToolRegistry 执行工具调用
        tool_responses = tools.execute_tool_calls(tool_calls)
        result["tool_responses"] = tool_responses

        # 使用 ToolRegistry 构造工具调用结果消息
        messages.extend(
            tools.recover_tool_call_assistant_message(tool_calls, tool_responses)
        )

        result_copy = copy.deepcopy(result)
        # 调用模型生成最终响应
        result = self.query(messages=messages, stream=stream, tools=tools)

        # 将当前结果加入工具调用链
        if "tool_chain" in result:
            result["tool_chain"].insert(0, result_copy)
        else:
            result["tool_chain"] = [result_copy]
        return result

    def _format_response(self, result: Dict[str, Any]) -> str:
        """Format the complete response.

        Args:
            result (Dict[str, Any]): Response dictionary

        Returns:
            str: Formatted response string
        """
        response_parts = []

        if "reasoning_content" in result and result["reasoning_content"]:
            response_parts.append(f"[Reasoning]: {result['reasoning_content']}")

        if result["content"]:
            response_parts.append(f"[Response]: {result['content']}")

        return "\n\n".join(response_parts)

    def _generate_with_tool_response(
        self,
        messages: List[Dict[str, str]],
        tool_calls: List[Any],
        tool_responses: Dict[str, str],
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Generate final response with tool results.

        Args:
            messages (List[Dict[str, str]]): List of messages
            tool_calls (List[Any]): List of tool calls
            tool_responses (Dict[str, str]): Tool execution results
            stream (bool): Whether to use streaming mode

        Returns:
            Dict[str, Any]: Final response dictionary
        """
        # 构造包含工具结果的上下文

        messages.extend(
            self._recover_tool_call_assistant_message(tool_calls, tool_responses)
        )
        print(messages)

        # 调用模型生成最终响应
        final_response = self.query(messages=messages, stream=stream)
        print(final_response)

        return final_response


# 使用示例
if __name__ == "__main__":
    import argparse

    from cicada.core.utils import load_config, setup_logging

    parser = argparse.ArgumentParser(description="Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()
    setup_logging()

    llm_config = load_config(args.config, "llm")

    llm = MultiModalModel(
        llm_config["api_key"],
        llm_config.get("api_base_url"),
        llm_config.get("model_name", "gpt-4o-mini"),
        llm_config.get("org_id"),
        **llm_config.get("model_kwargs", {}),
    )

    from cicada.core.basics import PromptBuilder

    # # 流式模式
    # print("Streaming response:")
    # stream_response = llm.query("告诉我一个极短的笑话", stream=True)
    # print("Complete stream response:", stream_response)
    # pb = PromptBuilder()
    # pb.add_system_message("You are a helpful assistant")
    # pb.add_user_message("Explain quantum computing")
    # result = llm.query(prompt_builder=pb, stream=True)
    # print("PromptBuilder response:", result["formatted_response"])
    # 创建工具注册表
    from cicada.core.tools import ToolRegistry

    tool_registry = ToolRegistry()

    # 注册工具
    @tool_registry.register
    def get_weather(location: str) -> str:
        """Get weather information for a location.

        Args:
            location (str): Location to get weather for

        Returns:
            str: Weather information string
        """
        return f"Weather in {location}: Sunny, 25°C"

    @tool_registry.register
    def c_to_f(celsius: float) -> str:
        """Convert Celsius to Fahrenheit.

        Args:
            celsius (float): Temperature in Celsius

        Returns:
            str: Formatted conversion result
        """
        fahrenheit = (celsius * 1.8) + 32
        return f"{celsius} celsius degree == {fahrenheit} fahrenheit degree"

    # 使用工具调用
    response = llm.query(
        "What's the weather like in Shanghai, in fahrenheit?",
        tools=tool_registry,
        stream=True,
    )
    print(response["content"])

    cprint(response)
