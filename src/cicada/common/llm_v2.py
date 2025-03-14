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

    def query(self, prompt, system_prompt=None, stream=False):
        """
        支持流式和非流式的查询方法
        Args:
            prompt (str): 用户输入
            system_prompt (str, optional): 系统提示
            stream (bool): 是否启用流式模式
        Returns:
            str: 模型生成的完整响应
        """
        # 构造消息
        messages = self._build_messages(prompt, system_prompt)

        # 调用API
        response = self._call_model_api(messages, stream)

        # 处理响应
        if stream:
            return self._process_stream_response(response)
        else:
            return self._process_non_stream_response(response)

    def _build_messages(self, prompt, system_prompt):
        """构造消息列表"""
        messages = [{"role": "user", "content": prompt}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
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
        """处理非流式响应"""
        if not response.choices:
            raise ValueError("No response from the model")

        # 获取第一条选择的响应内容
        choice = response.choices[0]
        message = choice.message

        # 返回模型生成的内容
        return message.content

    def _process_stream_response(self, response):
        """处理流式响应"""
        complete_response = ""

        for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    # 收集流式内容
                    complete_response += delta.content
                    # 实时输出（可选）
                    print(delta.content, end="", flush=True)

        print()  # 流式结束后换行
        return complete_response


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

    response = llm.query("Hello, how are you?")
    print(response)

    # 流式模式
    print("Streaming response:")
    stream_response = llm.query("Tell me a story", stream=True)
    print("Complete stream response:", stream_response)
