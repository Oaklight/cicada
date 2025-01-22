import argparse
import logging
import os
from typing import List, Literal

logging.basicConfig(level=logging.INFO)

import os
import sys

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common import llm
from common.utils import extract_section_markdown, load_config, load_prompts


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

    def generate_code(self, description: str, plan: dict = None) -> str:
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

    def fix_code(self, code: str, description: str, feedbacks: List[str] | None) -> str:
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

    def plan_code(
        self,
        description,
        feedbacks: str = None,
        previous_plan: dict = None,
    ) -> dict | None:
        """
        Plans out the building blocks using build123d API.
        """
        if not feedbacks:
            prompt = f"Based on the following description, create a detailed plan in markdown format:\n{description}\n\n"
        else:  # a prompt to refine/revise/redo previous plan
            prompt = (
                f"Based on the following description and previous plan, create a revised plan in markdown format:\n"
                f"Description:\n{description}\n\n"
                f"Previous Plan:\n{previous_plan}\n\n"
                f"Feedbacks:\n{feedbacks}\n\n"
            )

        try:
            plan_response = self.query(prompt, self.system_prompt_code_planning)
            plan = extract_section_markdown(plan_response, " Plan")
            elements = extract_section_markdown(plan_response, " Elements").split("\n")
            elements = [elem.strip() for elem in elements if elem.strip()]
            return {"plan": plan, "elements": elements}
        except Exception as e:
            logging.error(f"API call failed: {e}")
        return None

    def patch_code_to_export(
        self, code, format: Literal["stl", "step"] = "stl", target_output_dir=None
    ) -> tuple[str, str]:
        """
        Extends the provided code with export functionality, exporting the result to the specified format.

        Args:
            code (str): Code to be extended with export functionality.
            format (Literal["stl", "step"], optional): Desired export format. Defaults to "stl".
            target_output_dir (str, optional): Directory to save the exported 3D file. Defaults to None, which will use the code execution directory.

        Returns:
            patched_code: Extended code with export functionality.
            target_output_dir: Directory where the exported 3D file will be saved.
        """

        target_output_dir = target_output_dir or f"."

        # Define the filename based on format
        filename = f"exported_model.{format}"
        file_path = os.path.join(target_output_dir, filename)

        # Code to append - will depend on the build123d API or relevant method used to export
        export_code = f"""
# Export the result to {format} format
from build123d import export_{format}
export_{format}(to_export=result, file_path="{file_path}")
"""

        # Update the code by appending the export functionality
        patched_code = f"{code}\n{export_code}"

        return patched_code, target_output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assistive Large Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "--output_dir",
        default="./code_examples",
        help="Directory to save the generated code",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    code_llm_config = load_config(args.config, "code-llm")

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
        code_generator.save_code_to_file(
            generated_code, filename=os.path.join(args.output_dir, "generated_code.py")
        )
    else:
        print("Failed to generate code.")
        sys.exit(1)

    # Step 3: Simulate feedback for fixing the code (Optional)
    feedbacks = [
        "The cube side length should be 20 units instead of 10 units.",
        "Ensure the cube is centered at the origin.",
    ]

    # Step 4: Fix the code based on feedback (Optional)
    fixed_code = code_generator.fix_code(generated_code, description, feedbacks)

    if fixed_code:
        print("\nFixed Code:")
        print(fixed_code)
        code_generator.save_code_to_file(
            fixed_code, filename=os.path.join(args.output_dir, "fixed_code.py")
        )
    else:
        print("Failed to fix the code.")

    # Step 5: Patch code to export with export functionality
    if fixed_code:
        patched_code, file_path = code_generator.patch_code_to_export(
            fixed_code, format="stl"
        )
        print("\nPatched Code with Export Functionality:")
        print(patched_code)
        code_generator.save_code_to_file(
            patched_code, filename=os.path.join(args.output_dir, "patched_code.py")
        )
        print(f"Export path: {file_path}")
    else:
        print("No valid code to patch and export.")
