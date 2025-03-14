import json
import logging
from abc import ABC
from typing import Dict, List, Optional

import httpx
import openai
import tenacity

from cicada.common.basics import PromptBuilder
from cicada.common.tools import ToolRegistry
from cicada.common.utils import cprint

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

    def query(self, prompt=None, system_prompt=None, stream=False, prompt_builder=None):
        """
        支持PromptBuilder和reasoning_content的查询方法
        Args:
            prompt (str, optional): 用户输入
            system_prompt (str, optional): 系统提示
            stream (bool): 是否启用流式模式
            prompt_builder (PromptBuilder, optional): PromptBuilder实例
        Returns:
            dict: 包含完整响应和reasoning_content的结果
        """
        # 构造消息
        messages = self._build_messages(prompt, system_prompt, prompt_builder)

        # 调用API
        response = self._call_model_api(messages, stream)

        # 处理响应
        if stream:
            return self._process_stream_response(response)
        else:
            return self._process_non_stream_response(response)

    def _build_messages(self, prompt, system_prompt, prompt_builder):
        """支持PromptBuilder的消息构造"""
        if prompt_builder:
            # 优先使用PromptBuilder
            return prompt_builder.messages
        else:
            # 回退到传统方式
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if prompt:
                messages.append({"role": "user", "content": prompt})
            return messages

    def _call_model_api(self, messages, stream):
        """调用模型API，支持流式模式"""
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=stream,  # 动态设置流式模式
            **self.model_kwargs,
        )

    def _process_non_stream_response(self, response):
        """处理非流式响应，支持reasoning_content"""
        if not response.choices:
            raise ValueError("No response from the model")

        choice = response.choices[0]
        message = choice.message

        # 构造返回结果
        result = {
            "content": message.content,
            "reasoning_content": getattr(message, "reasoning_content", None),
        }

        # 如果存在reasoning_content，附加到响应中
        if result["reasoning_content"]:
            result["formatted_response"] = (
                f"[Reasoning]: {result['reasoning_content']}\n\n"
                f"[Response]: {result['content']}"
            )
        else:
            result["formatted_response"] = result["content"]

        return result

    def _process_stream_response(self, response):
        """处理流式响应，支持reasoning_content"""
        complete_response = ""
        reasoning_content = ""

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

        print()  # 流式结束后换行

        # 构造返回结果
        result = {"content": complete_response, "reasoning_content": reasoning_content}

        # 格式化响应
        if reasoning_content:
            result["formatted_response"] = (
                f"[Reasoning]: {reasoning_content}\n\n"
                f"[Response]: {complete_response}"
            )
        else:
            result["formatted_response"] = complete_response

        return result


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

    pb = PromptBuilder()
    pb.add_system_prompt("You are a helpful assistant")
    pb.add_user_prompt("Explain quantum computing")

    result = llm.query(prompt_builder=pb, stream=True)
    print("PromptBuilder response:", result["formatted_response"])
