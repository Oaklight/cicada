import argparse
import openai
import os
import logging

logging.basicConfig(level=logging.INFO)

import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, parent_dir])
from utils import load_config, load_prompts


class CodeGenerator:
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_templates,
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
        self.user_prompt_templates = prompt_templates.get("user_prompt_template", {})
        self.system_prompt_template = prompt_templates.get("system_prompt_template", "")

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

    def generate_code(self, description):
        prompt = (
            f"Generate a build123d script to create a 3D model based on the following description:\n{description}\n\n"
            "The code should be enclosed within triple backticks:\n```python\n...```"
        )

        try:
            generated_code = self.query(prompt, self.system_prompt_template)

            if "```python" in generated_code:
                code_start = generated_code.find("```python") + len("```python")
                code_end = generated_code.find("```", code_start)
                generated_code = generated_code[code_start:code_end].strip()
            else:
                generated_code = generated_code.strip()

            return generated_code
        except Exception as e:
            logging.error(f"API call failed: {e}")
            return None

    def save_code_to_file(self, code, filename="generated_code.py"):
        with open(filename, "w") as f:
            f.write(code)
        logging.info(f"Code saved to {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assistive Large Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    code_llm_config = config["code-llm"]
    code_generator = CodeGenerator(
        code_llm_config["api_key"],
        code_llm_config.get("api_base_url"),
        code_llm_config.get("model_name", "gpt-4o-mini"),
        code_llm_config.get("org_id"),
        load_prompts(args.prompts, "code-llm"),
        **code_llm_config.get("model_kwargs", {}),
    )

    description = "Create a simple cube with side length of 10 units."
    generated_code = code_generator.generate_code(description)

    if generated_code:
        print("Generated Code:")
        print(generated_code)
        code_generator.save_code_to_file(generated_code)
    else:
        print("Failed to generate code.")
