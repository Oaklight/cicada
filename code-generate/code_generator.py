import argparse
import logging
import os

logging.basicConfig(level=logging.INFO)

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, parent_dir])
from common import llm
from common.utils import load_config, load_prompts


class CodeGenerator(llm.LanguageModel):
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_templates,
        **model_kwargs,
    ):
        super().__init__(
            api_key,
            api_base_url,
            model_name,
            org_id,
            **model_kwargs,
        )
        self.user_prompt_templates = prompt_templates.get("user_prompt_template", {})
        self.system_prompt_template = prompt_templates.get("system_prompt_template", "")

    def _extract_code_from_response(self, response):
        """
        Extracts the code block from the response of the LLM.
        """
        if "```python" in response:
            code_start = response.find("```python") + len("```python")
            code_end = response.find("```", code_start)
            return response[code_start:code_end].strip()
        else:
            return response.strip()

    def generate_code(self, description):
        prompt = (
            f"Generate a build123d script to create a 3D model based on the following description:\n{description}\n\n"
            "The code should be enclosed within triple backticks:\n```python\n...```"
        )

        try:
            generated_code = self.query(prompt, self.system_prompt_template)
            return self._extract_code_from_response(generated_code)
        except Exception as e:
            logging.error(f"API call failed: {e}")
            return None

    def save_code_to_file(self, code, filename="generated_code.py"):
        with open(filename, "w") as f:
            f.write(code)
        logging.info(f"Code saved to {filename}")

    def fix_code(self, code, description, feedbacks):
        if isinstance(feedbacks, list):
            feedbacks = "\n".join(feedbacks)

        prompt = (
            f"The following code has errors:\n```python\n{code}\n```\n"
            f"The original description was:\n{description}\n\n"
            f"Error feedbacks are:\n{feedbacks}\n\n"
            "Please fix the code and ensure it meets the original description. "
            "The corrected code should be enclosed within triple backticks:\n```python\n...```"
        )

        try:
            fixed_code = self.query(prompt, self.system_prompt_template)
            return self._extract_code_from_response(fixed_code)
        except Exception as e:
            logging.error(f"API call failed: {e}")
            return None


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

    # Step 1: Generate code
    description = "Create a simple cube with side length of 10 units."
    generated_code = code_generator.generate_code(description)

    if generated_code:
        print("Generated Code:")
        print(generated_code)
        code_generator.save_code_to_file(generated_code, filename="generated_code.py")
    else:
        print("Failed to generate code.")
        sys.exit(1)

    # Step 2: Simulate feedback for fixing the code
    feedbacks = [
        "The cube side length should be 20 units instead of 10 units.",
        "Ensure the cube is centered at the origin.",
    ]

    # Step 3: Fix the code based on feedback
    fixed_code = code_generator.fix_code(generated_code, description, feedbacks)

    if fixed_code:
        print("\nFixed Code:")
        print(fixed_code)
        code_generator.save_code_to_file(fixed_code, filename="fixed_code.py")
    else:
        print("Failed to fix the code.")
