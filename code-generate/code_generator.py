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
from utils import extract_section_markdown


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
        self.system_prompt_code_generation = prompt_templates.get(
            "system_prompt_code_generation", ""
        )
        self.system_prompt_code_planning = prompt_templates.get(
            "system_prompt_code_planning", ""
        )

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

    def generate_code(self, description: str, plan: dict = None):
        if plan:
            prompt = (
                f"Generate a build123d script to create a 3D model based on the following description and plan:\n"
                f"Description:\n{description}\n\n"
                f"Plan:\n{plan}\n\n"
                "The code should be enclosed within triple backticks:\n```python\n...```"
            )
        else:
            prompt = (
                f"Generate a build123d script to create a 3D model based on the following description:\n{description}\n\n"
                "The code should be enclosed within triple backticks:\n```python\n...```"
            )

        try:
            generated_code = self.query(prompt, self.system_prompt_code_generation)
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
            fixed_code = self.query(prompt, self.system_prompt_code_generation)
            return self._extract_code_from_response(fixed_code)
        except Exception as e:
            logging.error(f"API call failed: {e}")
            return None

    def plan_code(self, description):
        """
        Plans out the building blocks using build123d API.
        """
        prompt = f"Based on the following description, create a detailed plan in markdown format:\n{description}\n\n"

        try:
            plan_response = self.query(prompt, self.system_prompt_code_planning)
            plan = extract_section_markdown(plan_response, " Plan")
            elements = extract_section_markdown(plan_response, " Elements").split("\n")
            elements = [elem.strip() for elem in elements if elem.strip()]
            return {"plan": plan, "elements": elements}
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
    prompt_templates = load_prompts(args.prompts, "code-llm")
    code_generator = CodeGenerator(
        code_llm_config["api_key"],
        code_llm_config.get("api_base_url"),
        code_llm_config.get("model_name", "gpt-4o-mini"),
        code_llm_config.get("org_id"),
        prompt_templates,
        **code_llm_config.get("model_kwargs", {}),
    )

    # Step 1: Plan the code
    description = "Create a cylindrical container with a height of 50 units and a radius of 20 units, with a smaller cylindrical hole of radius 5 units drilled through its center along the height."
    plan = code_generator.plan_code(description)

    if plan:
        print("Code Plan:")
        print(plan["plan"])
        print("\nAPI Elements Involved:")
        print(plan["elements"])
    else:
        print("Failed to generate code plan.")
        sys.exit(1)

    # Step 2: Generate code based on the plan
    generated_code = code_generator.generate_code(description, plan=plan["plan"])

    if generated_code:
        print("\nGenerated Code:")
        print(generated_code)
        code_generator.save_code_to_file(generated_code, filename="generated_code.py")
    else:
        print("Failed to generate code.")
        sys.exit(1)

    # Step 3: Simulate feedback for fixing the code
    feedbacks = [
        "The cube side length should be 20 units instead of 10 units.",
        "Ensure the cube is centered at the origin.",
    ]

    # Step 4: Fix the code based on feedback
    fixed_code = code_generator.fix_code(generated_code, description, feedbacks)

    if fixed_code:
        print("\nFixed Code:")
        print(fixed_code)
        code_generator.save_code_to_file(fixed_code, filename="fixed_code.py")
    else:
        print("Failed to fix the code.")
