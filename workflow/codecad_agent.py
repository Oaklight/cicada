import argparse
import logging
import os
import sys
import uuid
from typing import List, Literal, Optional

from pydantic import BaseModel

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])


from coding.code_cache import CodeCache
from coding.code_executor import CodeExecutor
from coding.code_generator import CodeGenerator
from common.utils import (
    colorstring,
    find_files_with_extensions,
    load_config,
    load_prompts,
)
from geometry_pipeline.snapshots import generate_snapshots

logging.basicConfig(level=logging.INFO)


# a class called DesignGoal, with text and images field
class DesignGoal:
    def __init__(self, text: str, images: Optional[list[str]] = None):
        self.text = text
        self.images = images

    def __str__(self):
        return f"DesignGoal(text='{self.text}', images={self.images})"


class CodeExecutionLoop:
    def __init__(
        self,
        code_generator: CodeGenerator,
        code_executor: CodeExecutor,
        code_cache: CodeCache,
        max_iterations=5,
        max_correction_iterations=3,
        code_master: CodeGenerator = None,
    ):
        self.code_generator = code_generator
        self.code_executor = code_executor
        self.code_cache = code_cache
        self.max_iterations = max_iterations
        self.max_correction_iterations = max_correction_iterations
        self.code_master = code_master

    def run(self, design_goal: DesignGoal, output_path: str):
        # generate_executable_code
        generated_code = self._generate_executable_code(design_goal)
        logging.info(colorstring(f"Generated code:\n{generated_code}", "green"))

        # render_from_code
        is_success, messages, render_path = self._render_from_code(
            generated_code, output_path
        )

        # get_visual_feedback
        self._get_visual_feedback(design_goal, render_path)

        pass

    def _get_visual_feedback(
        self, design_goal: DesignGoal, render_path: str, snapshot_directions
    ) -> str:
        """
        find out rendered object inside render_path, then take snapshots according to snapshot_directions, then compare with design_goal and generate feedbacks
        """
        # Literal["stl", "step"] = "stl", find rendered object inside render_path

        pass

    def _render_from_code(
        self,
        code: str,
        output_path: str = "./results",
        format: Literal["stl", "step"] = "stl",
    ) -> tuple[bool, str, str]:
        """
        Patches the provided code with an export function, executes the code, and saves the output.

        This method takes the generated code, patches it to include an export function based on the specified format,
        and then executes the patched code to generate the output files. The output files are saved in a uniquely named
        directory within the specified output path. Both the original and patched versions of the code are saved for
        reference. The method returns the execution status, any messages from the execution process, and the path to
        the output directory.

        Args:
            code (str): The code to be executed.
            output_path (str): The path to save the output files. Defaults to "./results".
            format (Literal["stl", "step"]): The format of the output files. Defaults to "stl".

        Returns:
            tuple[bool, str, str]: A tuple containing:
                - A boolean indicating whether the code execution was successful.
                - A message or error from the execution process.
                - The path to the directory where the output files are saved.
        """
        random_name = f"render_{str(uuid.uuid4())[:8]}"
        absolute_output_path = os.path.abspath(output_path)
        render_path = os.path.join(absolute_output_path, random_name)
        os.makedirs(render_path, exist_ok=True)

        # patch the code with export function
        code_with_export, _ = self.code_generator.patch_code_to_export(
            code=code, format=format, target_output_dir=render_path
        )

        # save both code versions
        self.code_generator.save_code_to_file(
            code, os.path.join(render_path, "code.py")
        )
        self.code_generator.save_code_to_file(
            code_with_export, os.path.join(render_path, "code_with_export.py")
        )

        # execute the code
        is_valid, messages = self.code_executor.execute_and_save(
            code_with_export, render_path
        )

        if not is_valid:
            logging.error(
                colorstring(f"Code is not valid during export: {messages}", "red")
            )
        else:
            logging.info(
                colorstring(f"Code is valid during export: {messages}", "blue")
            )

        return is_valid, messages, render_path

    def _generate_executable_code(self, design_goal: DesignGoal) -> str | None:
        """
        Generates executable code based on the provided design goal.

        This method first generates a coding plan using the design goal's text. It then iteratively
        generates or fixes code, validates it, and attempts to execute it. If the code is not valid
        or fails to execute, feedback is collected and used to improve the code in subsequent iterations.
        The process continues until valid and executable code is generated or the maximum number of
        iterations is reached.
        Args:
            design_goal (DesignGoal): The design goal containing the text description and optional images.

        Returns:
            str | None: The generated executable code as a string if successful, otherwise None.
        """
        # generate plan (using text only)
        coding_plan = self._generate_and_save_plan(design_goal)

        generated_code = None
        feedbacks = None
        use_master = False
        # iterate to generate executable code
        for i in range(self.max_iterations):
            logging.info(f"Iteration {i + 1}/{self.max_iterations}")
            if i >= 2 / 3 * self.max_iterations:
                use_master = True

            # generate code
            generated_code = self._generate_or_fix_code(
                design_goal.text,
                coding_plan,
                existing_code=generated_code,
                feedbacks=feedbacks,
                use_master=use_master,
            )

            # validate
            is_valid, errors = self.code_executor.validate_code(generated_code)
            if not is_valid:
                feedbacks = errors
                logging.warning(colorstring(f"Code is not valid:\n{errors}", "yellow"))
                continue

            # execute
            is_runnable, results = self.code_executor.execute_code(
                generated_code, test_run=True
            )

            if not is_runnable:
                feedbacks = results
                logging.warning(
                    colorstring(f"Code is not runnable:\n{results}", "yellow")
                )
                continue

            return generated_code

    def _generate_and_save_plan(self, design_goal: DesignGoal) -> dict:
        if self.code_master:
            coding_plan = self.code_master.plan_code(design_goal.text)
        else:
            coding_plan = self.code_generator.plan_code(design_goal.text)
        logging.info(colorstring(f"Coding plan:\n{coding_plan}", "white"))
        return coding_plan

    def _generate_or_fix_code(
        self,
        description: str,
        plan: dict = None,
        existing_code: str = None,
        feedbacks: List[str] = None,
        use_master: bool = False,
    ) -> str:
        """
        Generate new code or fix existing code based on the provided description, plan, and feedback.

        Args:
            description (str): A textual description of the design goal or the problem to solve.
            plan (dict, optional): A dictionary containing the coding plan, typically including a 'plan' key.
            existing_code (str, optional): The existing code that needs to be fixed or improved.
            feedbacks (List[str], optional): A list of feedback messages or errors from previous iterations.
            use_master (bool, optional): If True, the master code generator will be used for code generation or fixing.

        Returns:
            str: The generated or fixed code as a string. Returns None if no code could be generated or fixed.
        """
        generated_code = None

        generator = self.code_generator
        if use_master and self.code_master:
            generator = self.code_master

        if existing_code:
            generated_code = generator.fix_code(existing_code, description, feedbacks)
            logging.info(colorstring(f"Fixed code:\n{generated_code}", "white"))
        else:
            generated_code = generator.generate_code(description, plan["plan"])
            logging.info(colorstring(f"Generated code:\n{generated_code}", "white"))
        return generated_code

    def _insert_iteration(self, session_id, generated_code):
        iteration_id = self.code_cache.insert_iteration(session_id, generated_code)
        logging.info(colorstring(f"Inserted iteration with id: {iteration_id}", "blue"))
        return iteration_id

        for correction_iteration in range(self.max_correction_iterations):
            # Validate the code
            is_valid, error_message = self.code_executor.validate_code(generated_code)
            if is_valid:
                # Execute the code if it's valid
                is_execution_valid, execution_result = self.code_executor.execute_code(
                    generated_code, timeout=10
                )
                if is_execution_valid:
                    return True, execution_result
                else:
                    # Handle execution errors
                    logging.warning(
                        colorstring(
                            f"Execution error:\n{execution_result['error']}", "yellow"
                        )
                    )
                    self.code_cache.insert_error(
                        iteration_id, "runtime", execution_result["error"]
                    )
                    logging.info(
                        colorstring(
                            f"Inserted runtime error for iteration id: {iteration_id}",
                            "blue",
                        )
                    )
            else:
                # Handle syntax errors
                logging.warning(
                    colorstring(f"Syntax error detected:\n{error_message}", "yellow")
                )
                self.code_cache.insert_error(iteration_id, "syntax", error_message)
                logging.info(
                    colorstring(
                        f"Inserted syntax error for iteration id: {iteration_id}",
                        "blue",
                    )
                )

            # Fix the code based on the error
            if (
                self.code_master
                and correction_iteration >= self.max_correction_iterations // 2
            ):
                # Use the master code generator for fixing code if it exists and we're past half the correction iterations
                generated_code = self.code_master.fix_code(
                    generated_code, description, error_message
                )
            else:
                # Otherwise, use the standard code generator for fixing code
                generated_code = self.code_generator.fix_code(
                    generated_code, description, error_message
                )

            if not generated_code:
                logging.error(colorstring("Failed to generate corrected code.", "red"))
                return False, None

            session_id = self.code_cache.get_session_id(iteration_id)
            self.code_cache.insert_iteration(session_id, code=generated_code)
            logging.info(
                colorstring(
                    f"Updated iteration with corrected code, id: {iteration_id}", "blue"
                )
            )

        logging.warning(
            colorstring("Max correction attempts reached. Abandoning code.", "yellow")
        )
        return False, None

    def _mark_iteration_as_runnable(self, iteration_id):
        self.code_cache.update_iteration(iteration_id, is_runnable=True)
        logging.info(
            colorstring(f"Marked iteration {iteration_id} as runnable.", "blue")
        )

    def _render_and_visual_feedback(self, generated_code):
        # TODO: implement file saving and visual validation
        pass


# Usage example
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
        code_llm_config.get("model_name"),
        code_llm_config.get("org_id"),
        load_prompts(args.prompts, "code-llm"),
        **code_llm_config.get("model_kwargs", {}),
    )
    master_code_llm_config = config.get("master-code-llm", None)
    code_master = (
        CodeGenerator(
            master_code_llm_config["api_key"],
            master_code_llm_config.get("api_base_url"),
            master_code_llm_config.get("model_name"),
            master_code_llm_config.get("org_id"),
            load_prompts(args.prompts, "code-llm"),
            **master_code_llm_config.get("model_kwargs", {}),
        )
        if master_code_llm_config
        else None
    )

    code_execution_loop = CodeExecutionLoop(
        code_generator,
        CodeExecutor(),
        CodeCache(db_file="code-generator.db"),
        code_master=code_master,
    )

    description = "Create a simple table design, flat circular top, with 4 straight legs. Each leg is about 45 unit long with circular cross section. and the circular top has a radius of 60 units. This is a big table."

    design_goal = DesignGoal(description)
    output_path = "./results"

    code_execution_loop.run(design_goal, output_path)
