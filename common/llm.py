import argparse
import logging
import os
import sys
from abc import ABC

import openai

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, parent_dir])

from common.utils import colorstring, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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

        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base_url, organization=self.org_id
        )

    def query(self, prompt, system_prompt=None):
        messages = [
            {"role": "user", "content": prompt},
        ]

        if system_prompt:
            messages = [
                {"role": "system", "content": system_prompt},
            ] + messages

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **self.model_kwargs,
        )

        return response.choices[0].message.content.strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    assist_llm_config = config["assist-llm"]

    llm = LanguageModel(
        assist_llm_config["api_key"],
        assist_llm_config.get("api_base_url"),
        assist_llm_config.get("model_name", "gpt-4o-mini"),
        assist_llm_config.get("org_id"),
        **assist_llm_config.get("model_kwargs", {}),
    )

    response = llm.query("How are you doing today?")
    logging.info(colorstring(response, "white"))
