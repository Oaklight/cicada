import copy
import json
import logging
from abc import ABC
from typing import Dict, List, Optional

import httpx
import openai
import tenacity

from cicada.common.basics import PromptBuilder
from cicada.common.tools import ToolRegistry
from cicada.common.utils import cprint, recover_stream_tool_calls

logger = logging.getLogger(__name__)


class LanguageModel(ABC):
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id=None,
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

    def query(
        self,
        prompt=None,
        system_prompt=None,
        stream=False,
        prompt_builder=None,
        messages=None,
        tools=None,
    ):
        """
        支持Tool Use的查询方法
        Args:
            prompt (str, optional): 用户输入
            system_prompt (str, optional): 系统提示
            stream (bool): 是否启用流式模式
            prompt_builder (PromptBuilder, optional): PromptBuilder实例
            messages (List[Dict], optional): 直接传递消息列表
            tools (ToolRegistry, optional): 工具注册表
        Returns:
            dict: 包含完整响应、reasoning_content和工具调用结果
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

    def _build_messages(self, prompt, system_prompt, prompt_builder, messages):
        """支持PromptBuilder的消息构造"""
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

    def _call_model_api(self, messages, stream, tools=None):
        """调用模型API，支持工具调用"""
        kwargs = self.model_kwargs.copy()
        if tools:
            kwargs["tools"] = tools.get_tools_json()
            kwargs["tool_choice"] = "auto"

        return self.client.chat.completions.create(
            model=self.model_name, messages=messages, stream=stream, **kwargs
        )

    def _process_non_stream_response(self, messages, response, tools=None):
        """处理非流式响应，支持工具调用"""
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

            tool_responses = self._execute_tool_calls(message.tool_calls, tools)

            # 将工具结果传回LLM
            # cprint(messages, "magenta")
            messages.extend(
                self._recover_tool_call_assistant_message(
                    message.tool_calls, tool_responses
                )
            )

            # 调用模型生成最终响应
            result = self.query(messages=messages, stream=False, tools=tools)

            # move existing result into tool_chain_results
            result["tool_responses"] = tool_responses
            result_copy = copy.deepcopy(result)
            result["tool_chain"] = result_copy

        result["formatted_response"] = self._format_response(result)
        return result

    def _process_stream_response(self, messages, response, tools=None):
        """处理流式响应，支持工具调用"""
        complete_response = ""
        reasoning_content = ""
        tool_calls = {}
        tool_responses = []

        for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta

                # 收集常规内容
                if delta.content:
                    complete_response += delta.content
                    cprint(delta.content, "white", end="", flush=True)

                # 收集reasoning_content
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    reasoning_content += delta.reasoning_content
                    cprint(delta.reasoning_content, "cyan", end="", flush=True)

                # 收集工具调用
                if tools and hasattr(delta, "tool_calls") and delta.tool_calls:
                    # cprint(delta.tool_calls, "bright_yellow")
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

        result = {"content": complete_response}
        if reasoning_content:
            result["reasoning_content"] = reasoning_content

        print()  # 流式结束后换行

        # 执行工具调用
        if tool_calls:
            tool_calls = recover_stream_tool_calls(tool_calls)

            tool_responses = self._execute_tool_calls(tool_calls, tools)

            # 将工具结果传回LLM
            messages.extend(
                self._recover_tool_call_assistant_message(tool_calls, tool_responses)
            )

            # 调用模型生成最终响应
            result = self.query(messages=messages, stream=True, tools=tools)

            # move existing result into tool_chain_results
            result["tool_responses"] = tool_responses
            result_copy = copy.deepcopy(result)
            result["tool_chain"] = result_copy

        # 格式化响应
        result["formatted_response"] = self._format_response(result)
        return result

    def _execute_tool_calls(
        self, tool_calls: List, tools: ToolRegistry
    ) -> Dict[str, str]:
        """执行工具调用"""
        tool_responses = {}
        # cprint(tool_calls, "bright_red")
        # cprint(type(tool_calls))
        for tool_call in tool_calls:

            tool_result = None
            try:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_call_id = tool_call.id
                # cprint(type(tool_call_id), "bright_blue")

                # 从注册表中获取工具
                tool = tools.get_callable(function_name)
                if tool:
                    function_response = tool(**function_args)
                    tool_result = f"{function_name} -> {function_response}"
                else:
                    tool_result = f"Error: Tool '{function_name}' not found"
            except Exception as e:
                tool_result = f"Error executing {function_name}: {str(e)}"

            tool_responses[tool_call_id] = tool_result

        return tool_responses

    def _recover_tool_call_assistant_message(self, tool_calls, tool_responses):
        messages = []
        for tool_call in tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    ],
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "content": tool_responses[tool_call.id],
                    "tool_call_id": tool_call.id,
                }
            )
        return messages

    def _format_response(self, result):
        """格式化完整响应"""
        response_parts = []

        if result["reasoning_content"]:
            response_parts.append(f"[Reasoning]: {result['reasoning_content']}")

        if result["content"]:
            response_parts.append(f"[Response]: {result['content']}")

        if result["tool_responses"]:
            response_parts.append(
                "[Tool Results]:\n" + "\n".join(result["tool_responses"])
            )

        return "\n\n".join(response_parts)


# 使用示例
if __name__ == "__main__":
    import argparse

    from cicada.common.utils import load_config, setup_logging

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

    from cicada.common.basics import PromptBuilder

    # 流式模式
    print("Streaming response:")
    stream_response = llm.query("告诉我一个极短的笑话", stream=True)
    print("Complete stream response:", stream_response)

    # pb = PromptBuilder()
    # pb.add_system_prompt("You are a helpful assistant")
    # pb.add_user_prompt("Explain quantum computing")

    # result = llm.query(prompt_builder=pb, stream=True)
    # print("PromptBuilder response:", result["formatted_response"])

    # 创建工具注册表
    from cicada.common.tools import ToolRegistry

    tool_registry = ToolRegistry()

    # 注册工具
    @tool_registry.register
    def get_weather(location: str):
        return f"Weather in {location}: Sunny, 25°C"

    @tool_registry.register
    def c_to_f(celsius: float) -> float:
        fahrenheit = (celsius * 1.8) + 32
        return f"{celsius} celsius degree == {fahrenheit} fahrenheit degree"

    # 使用工具调用
    response = llm.query(
        "What's the weather like in Shanghai, in fahrenheit?",
        tools=tool_registry,
        # stream=True,
    )
    print(response["content"])
