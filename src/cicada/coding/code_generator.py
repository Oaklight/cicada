import logging
import os
from typing import List, Literal

logging.basicConfig(level=logging.INFO)

import os
import sys

from cicada.core import model
from cicada.core.basics import DesignGoal
from cicada.core.tools import tool_registry
from cicada.core.utils import colorstring, cprint, extract_section_markdown

from cicada.tools.code_dochelper import doc_helper

logger = logging.getLogger(__name__)


class CodeGenerator(model.MultiModalModel):
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

    def generate_or_fix_code(
        self,
        design_goal: DesignGoal,
        plan: dict = None,
        existing_code: str = None,
        feedbacks: List[str] = None,
    ) -> str:
        """
        Generate new code or fix existing code based on the provided design goal, plan, and feedback.

        Args:
            design_goal (DesignGoal): The design goal containing text and decomposition details.
            plan (dict, optional): A dictionary containing the coding plan, typically including a 'plan' key.
            existing_code (str, optional): The existing code that needs to be fixed or improved.
            feedbacks (List[str], optional): A list of feedback messages or errors from previous iterations.

        Returns:
            str: The generated or fixed code as a string. Returns None if no code could be generated or fixed.
        """
        if existing_code:
            # Fix existing code
            cprint("Fixing existing code...", "cyan")
            generated_code = self.fix_code(existing_code, design_goal, feedbacks)
            logger.info(colorstring(f"Fixed code:\n{generated_code}", "white"))
        else:
            # Generate new code
            cprint("Generating new code...", "cyan")
            generated_code = self.generate_code(design_goal, plan=plan)
            logger.info(colorstring(f"Generated code:\n{generated_code}", "white"))

        return generated_code

    def generate_code(self, design_goal: DesignGoal, plan: dict = None) -> str:
        """
        Generates a build123d script based on the design goal and plan, focusing purely on geometric information.
        """
        description = design_goal.text
        decomposition = design_goal.extra.get("decomposition", {})

        if plan:
            prompt = (
                f"Generate a build123d script based on the following description and plan:\n"
                f"Description:\n{description}\n\n"
                f"Decomposition Details:\n"
                f"- Parts: {decomposition.get('parts', [])}\n"
                f"- Assembly Steps: {decomposition.get('assembly_plan', [])}\n"
                f"- Uncertainties: {decomposition.get('uncertainty_reasons', [])}\n\n"
                f"Plan:\n{plan}\n\n"
                "The code should be enclosed within triple backticks:\n```python\n...```"
            )
        else:
            prompt = (
                f"Generate a build123d script based on the following description:\n{description}\n\n"
                f"Decomposition Details:\n"
                f"- Parts: {decomposition.get('parts', [])}\n"
                f"- Assembly Steps: {decomposition.get('assembly_plan', [])}\n"
                f"- Uncertainties: {decomposition.get('uncertainty_reasons', [])}\n\n"
                "The code should be enclosed within triple backticks:\n```python\n...```"
            )

        try:
            generated_code = self.query(
                prompt=prompt,
                system_prompt=self.system_prompt_code_generation,
                stream=self.stream,
            )["content"]
            return self._extract_code_from_response(generated_code)
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return None

    def save_code_to_file(self, code, filename="generated_code.py"):
        with open(filename, "w") as f:
            f.write(code)
        logger.info(f"Code saved to {filename}")

    def fix_code(
        self, code: str, design_goal: DesignGoal, feedbacks: List[str] | None
    ) -> str:
        """
        Fixes the code using error feedback, leveraging dochelper to query documentation insights if necessary.
        """
        description = design_goal.text
        decomposition = design_goal.extra.get("decomposition", {})

        if isinstance(feedbacks, list):
            feedbacks = "\n".join(feedbacks)

        # First, query dochelper for insights into the error
        doc_query_prompt = (
            f"Got the following error feedbacks:\n{feedbacks}\n"
            "Which documentation or sections should I look up to address these issues? "
            "Remember to include the top-level import path `build123d`, such as `build123d.Box` for the `Box` class."
        )

        try:
            cprint("Querying dochelper for documentation insights...", "cyan")
            # Ensure the dochelper tool is registered
            tool_registry.register(doc_helper)

            # Query the LLM with dochelper tool for documentation insights
            doc_response = self.query(
                prompt=doc_query_prompt,
                tools=tool_registry,
                stream=self.stream,
            )["content"]

            # Extract helpful documentation info from the response
            documentation_insights = doc_response.strip()

        except Exception as e:
            logger.error(f"Dochelper API call failed: {e}")
            documentation_insights = "No additional documentation insights were found."

        # Now fix the code using the documentation insights
        fix_prompt = (
            f"The following code has errors:\n```python\n{code}\n```\n"
            f"The original description was:\n{description}\n\n"
            f"Decomposition Details:\n"
            f"- Parts: {decomposition.get('parts', [])}\n"
            f"- Assembly Steps: {decomposition.get('assembly_plan', [])}\n"
            f"- Uncertainties: {decomposition.get('uncertainty_reasons', [])}\n\n"
            f"Error feedbacks are:\n{feedbacks}\n\n"
            f"Based on the following documentation insights:\n{documentation_insights}\n\n"
            "Please fix the code and ensure it meets the original description. "
            "The corrected code should be enclosed within triple backticks:\n```python\n...```"
        )

        try:
            # Attempt to fix the code with enriched prompt
            fixed_code = self.query(
                prompt=fix_prompt,
                system_prompt=self.system_prompt_code_generation,
                tools=tool_registry,
                stream=self.stream,
            )["content"]

            return self._extract_code_from_response(fixed_code)

        except Exception as e:
            logger.error(f"Code fixing API call failed: {e}")
            return None

    def plan_code(
        self,
        design_goal: DesignGoal,  # Receives the full design_goal structure
        feedbacks: str = None,
        previous_plan: dict = None,
    ) -> dict | None:
        """
        Plans out the building blocks using build123d API, focusing purely on geometric information.
        """
        # Parse structured data
        description = design_goal.text
        decomposition = design_goal.extra.get("decomposition", {})

        # Construct the prompt
        prompt = (
            f"Generate a detailed geometric plan based on the following input:\n"
            f"Text Description:\n{description}\n\n"
            f"Decomposition Details:\n"
            f"- Parts: {decomposition.get('parts', [])}\n"
            f"- Assembly Steps: {decomposition.get('assembly_plan', [])}\n"
            f"- Uncertainties: {decomposition.get('uncertainty_reasons', [])}\n\n"
        )

        # If there are feedbacks or a previous plan, add them to the prompt
        if feedbacks or previous_plan:
            prompt += (
                f"Feedbacks:\n{feedbacks}\n\n" f"Previous Plan:\n{previous_plan}\n\n"
            )

        try:
            # Call the LLM to generate the plan
            plan_response = self.query(
                prompt=prompt,
                system_prompt=self.system_prompt_code_planning,
                stream=self.stream,
            )["content"]

            # Extract the plan section
            plan = extract_section_markdown(plan_response, " Plan")

            # Extract the API elements section
            elements = extract_section_markdown(plan_response, " Elements").split("\n")
            elements = [elem.strip() for elem in elements if elem.strip()]

            # Extract the considerations section
            considerations = extract_section_markdown(
                plan_response, " Considerations"
            ).split("\n")
            considerations = [cons.strip() for cons in considerations if cons.strip()]

            return {
                "plan": plan,
                "elements": elements,
                "considerations": considerations,  # New considerations section
            }
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return None

        except Exception as e:
            logger.error(f"API call failed: {e}")
            return None

    def patch_code_to_export(
        self, code, format: Literal["stl", "step"] = "stl", target_output_dir=None
    ) -> tuple[str, str]:
        """
        This method appends code to center the 3D model at the origin and export it in the desired format (STL or STEP).
        The exported file is saved in the specified directory or the current working directory if none is provided.

        Args:
            code (str): The original code to be extended with export functionality.
            format (Literal["stl", "step"], optional): The desired export format. Defaults to "stl".
            target_output_dir (str, optional): The directory where the exported 3D file will be saved.
            If None, the file will be saved in the current working directory.

        Returns:
            tuple[str, str]: A tuple containing:
                - patched_code: The extended code with the added export functionality.
                - target_output_dir: The directory where the exported 3D file will be saved.
        """

        # use absolute path except for current directory
        target_output_dir = target_output_dir or "."
        if target_output_dir != ".":
            target_output_dir = os.path.abspath(target_output_dir)

        # Define the filename based on format
        filename = f"exported_model.{format}"
        file_path = os.path.join(target_output_dir, filename)

        # Add centering logic and export code
        export_code = f"""
# =========== end of the original code ===========
# Center the model at the origin
bbox = result.bounding_box()
current_center = (bbox.min + bbox.max) / 2
result = result.translate(-current_center)

# Export the result to {format} format
from build123d import export_{format}
export_{format}(to_export=result, file_path="{file_path}")
"""

        # Update the code by appending the export functionality
        patched_code = f"{code}\n{export_code}"

        return patched_code, target_output_dir


def test_code_generator(code_generator, design_goal, output_dir):
    """
    Performs end-to-end testing of the CodeGenerator class functionalities.
    """
    # Test 1: Generate code from a description
    plan = code_generator.plan_code(design_goal)

    if plan:
        print("Code Plan:")
        print(plan["plan"])
        print("\nAPI Elements Involved:")
        print(plan["elements"])
    else:
        print("Failed to generate code plan.")
        sys.exit(1)

    generated_code = code_generator.generate_code(design_goal, plan=plan["plan"])

    if generated_code:
        print("\nGenerated Code:")
        print(generated_code)
        code_generator.save_code_to_file(
            generated_code, filename=os.path.join(output_dir, "generated_code.py")
        )
    else:
        print("Failed to generate code.")
        sys.exit(1)

    # Test 2: Fix code based on feedback
    feedbacks = [
        "The hole should be centered along the height of the container.",
        "Ensure the hole has a radius of 5 units.",
    ]

    # Fix the code based on feedback
    fixed_code = code_generator.fix_code(generated_code, design_goal, feedbacks)

    if fixed_code:
        print("\nFixed Code:")
        print(fixed_code)
        code_generator.save_code_to_file(
            fixed_code, filename=os.path.join(output_dir, "fixed_code.py")
        )
    else:
        print("Failed to fix the code.")

    # Test 3: Test generate_or_fix_code for generating new code
    print("\nTesting generate_or_fix_code for generating new code:")
    new_code = code_generator.generate_or_fix_code(
        design_goal,
        plan=plan["plan"],
    )

    if new_code:
        print("\nGenerated Code (via generate_or_fix_code):")
        print(new_code)
        code_generator.save_code_to_file(
            new_code, filename=os.path.join(output_dir, "new_code.py")
        )
    else:
        print("Failed to generate code via generate_or_fix_code.")

    # Test 4: Test generate_or_fix_code for fixing existing code
    print("\nTesting generate_or_fix_code for fixing existing code:")
    fixed_code_via_generate_or_fix = code_generator.generate_or_fix_code(
        design_goal,
        existing_code=generated_code,
        feedbacks=feedbacks,
    )

    if fixed_code_via_generate_or_fix:
        print("\nFixed Code (via generate_or_fix_code):")
        print(fixed_code_via_generate_or_fix)
        code_generator.save_code_to_file(
            fixed_code_via_generate_or_fix,
            filename=os.path.join(output_dir, "fixed_code_via_generate_or_fix.py"),
        )
    else:
        print("Failed to fix code via generate_or_fix_code.")

    # Step 5: Patch code to export with export functionality
    if fixed_code_via_generate_or_fix:
        patched_code, file_path = code_generator.patch_code_to_export(
            fixed_code_via_generate_or_fix, format="stl"
        )
        print("\nPatched Code with Export Functionality:")
        print(patched_code)
        code_generator.save_code_to_file(
            patched_code, filename=os.path.join(output_dir, "patched_code.py")
        )
        print(f"Export path: {file_path}")
    else:
        print("No valid code to patch and export.")


if __name__ == "__main__":
    import argparse

    from cicada.core.utils import load_config, load_prompts, setup_logging

    parser = argparse.ArgumentParser(description="Assistive Large Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "--output_dir",
        default="/tmp/cicada/code_examples",
        help="Directory to save the generated code",
    )
    args = parser.parse_args()

    setup_logging()

    os.makedirs(args.output_dir, exist_ok=True)

    # Load configuration and prompts
    code_llm_config = load_config(args.config, "code-llm")
    prompt_templates = load_prompts(args.prompts, "code-llm")

    # Initialize CodeGenerator
    code_generator = CodeGenerator(
        code_llm_config["api_key"],
        code_llm_config.get("api_base_url"),
        code_llm_config.get("model_name", "gpt-4"),
        code_llm_config.get("org_id"),
        prompt_templates,
        **code_llm_config.get("model_kwargs", {}),
    )

    # Define design goal for testing
    description = "Create a cylindrical container with a height of 50 units and a radius of 20 units, with a smaller cylindrical hole of radius 5 units drilled through its center along the height."
    design_goal = DesignGoal(description)

    # Run the tests
    test_code_generator(code_generator, design_goal, args.output_dir)
