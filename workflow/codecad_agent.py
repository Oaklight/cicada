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
    DesignGoal,
    colorstring,
    find_files_with_extensions,
    load_config,
    load_prompts,
)
from feedbacks.feedback_judge import FeedbackJudge
from feedbacks.visual_feedback import VisualFeedback
from geometry_pipeline.snapshots import generate_snapshots
from describe.describer_v2 import Describer

logging.basicConfig(level=logging.INFO)


class CodeExecutionLoop:
    def __init__(
        self,
        describer: Describer,
        code_generator: CodeGenerator,
        code_executor: CodeExecutor,
        code_cache: CodeCache,
        visual_feedback: VisualFeedback,
        feedback_judge: FeedbackJudge,
        code_master: CodeGenerator = None,
        max_iterations=5,
        max_correction_iterations=3,
    ):
        self.code_generator = code_generator
        self.code_executor = code_executor
        self.visual_feedback = visual_feedback
        self.feedback_judge = feedback_judge
        self.code_cache = code_cache
        self.describer = describer
        self.max_iterations = max_iterations
        self.max_correction_iterations = max_correction_iterations
        self.code_master = code_master

    def run(
        self,
        design_goal: DesignGoal,
        output_dir: str,
        max_iterations: int = 10,
        stop_threshold: float = 0.8,
    ):
        # Step 1: Refine the design goal using the Describer
        logging.info("START [refine_design_goal]")
        refined_design_goal = self._refine_design_goal(design_goal)
        logging.info("DONE [refine_design_goal]")

        iteration = 0
        best_code = None
        best_feedbacks = None
        best_coding_plan = None
        is_completed = False

        # Step 2: Proceed with the code generation and execution loop using the refined design goal
        while iteration < max_iterations:
            # generate_executable_code
            logging.info("START [generate_executable_code]")
            generated_code, coding_plan = self._generate_executable_code(
                refined_design_goal,
                feedbacks=best_feedbacks,
                generated_code=best_code,
                coding_plan=best_coding_plan,
            )
            logging.info("DONE [generate_executable_code]")
            if generated_code is None:
                logging.error(
                    colorstring(
                        f"Iteration {iteration + 1} - No executable code generated.",
                        "red",
                    )
                )
                iteration += 1
                continue

            # render_from_code
            logging.info("START [render_from_code]")
            is_success, messages, render_dir = self._render_from_code(
                generated_code, output_dir, format="stl"
            )
            logging.info("DONE [render_from_code]")
            if not is_success:
                logging.error(
                    colorstring(
                        f"Iteration {iteration + 1} - Rendering failed: {messages}",
                        "red",
                    )
                )
                iteration += 1
                continue

            # get_visual_feedback
            logging.info("START [get_visual_feedback]")
            is_success, visual_feedback = self._get_visual_feedback(
                refined_design_goal, render_dir, snapshot_directions="omni"
            )
            logging.info("DONE [get_visual_feedback]")
            if not is_success:
                logging.error(
                    colorstring(
                        f"Iteration {iteration + 1} - Visual feedback failed", "red"
                    )
                )
                iteration += 1
                continue

            # Check if the current feedback is better than the best feedback so far
            logging.info("START [check_feedback]")
            if best_feedbacks is None:
                best_code = generated_code
                best_feedbacks = visual_feedback
                logging.info(
                    colorstring(
                        f"Iteration {iteration + 1} - Initial feedback received",
                        "cyan",
                    )
                )
            elif self.feedback_judge.is_feedback_better(
                visual_feedback, best_feedbacks, refined_design_goal.text
            ):
                best_code = generated_code
                best_feedbacks = visual_feedback
                best_coding_plan = coding_plan

                logging.info(
                    colorstring(
                        f"Iteration {iteration + 1} - Improved feedback received",
                        "cyan",
                    )
                )
            logging.info("DONE [check_feedback]")

            # Check if the design goal has been achieved
            logging.info("START [check_design_goal]")
            is_achieved, score = self.feedback_judge.is_design_goal_achieved(
                visual_feedback, refined_design_goal.text
            )
            logging.info("DONE [check_design_goal]")
            if is_achieved or score >= stop_threshold:
                best_code = generated_code
                best_feedbacks = visual_feedback
                best_coding_plan = coding_plan
                logging.info(
                    colorstring(
                        f"Iteration {iteration + 1} - Design goal achieved! (Score: {score})",
                        "white",
                    )
                )
                is_completed = True
                break

            iteration += 1

        if is_completed:
            finish_message = (
                f"SUCCESS!",
                f"Design task completed after {iteration} iterations.",
                f"Best code: {best_code}",
                f"Best feedbacks: {best_feedbacks}",
                f"Best coding plan: {best_coding_plan}",
            )
            msg_color = "bright_green"
        else:
            finish_message = f"Design task not completed after {iteration} iterations."
            msg_color = "bright_red"

        logging.info(colorstring(finish_message, msg_color))
        return best_code, best_feedbacks, best_coding_plan

    def _refine_design_goal(self, design_goal: DesignGoal) -> DesignGoal:
        """
        Refines the design goal using the Describer.

        Args:
            design_goal (DesignGoal): The original design goal to be refined.

        Returns:
            DesignGoal: The refined design goal.
        """
        # Use the Describer to refine the design goal
        refined_design_goal = self.describer.design_feedback_loop(design_goal)

        return refined_design_goal

    # The rest of the methods remain unchanged...

    def _get_visual_feedback(
        self,
        design_goal: DesignGoal,
        render_dir: str,
        snapshot_directions: str | Literal["common", "box", "omni"] = "common",
    ) -> tuple[bool, str]:
        """
        find out rendered object inside render_dir, then take snapshots according to snapshot_directions, then compare with design_goal and generate feedbacks
        """
        # prefer stl if available, otherwise obj, otherwise step. return only one
        rendered_obj_path = find_files_with_extensions(
            render_dir, ["stl", "step", "obj"], return_all=False
        )

        if rendered_obj_path is None:
            logging.error("No rendered object found in the render path.")
            return False, "No rendered object found in the render path."

        # take snapshots
        snapshots_dir = os.path.join(render_dir, "snapshots")
        os.makedirs(snapshots_dir, exist_ok=True)  # Ensure the directory exists
        snapshot_paths = generate_snapshots(
            file_path=rendered_obj_path,
            output_dir=snapshots_dir,
            direction=snapshot_directions,
            mesh_color=[0, 102, 204],
            reaxis_gravity=True,
        )
        logging.info(colorstring(f"Snapshot paths: {snapshot_paths}", "magenta"))

        # compare with design_goal and generate feedbacks
        visual_feedback = self.visual_feedback.generate_feedback_paragraph(
            design_goal.text, design_goal.images, snapshot_paths
        )

        logging.info(colorstring(f"Visual feedback: {visual_feedback}", "white"))

        return True, visual_feedback

    def _render_from_code(
        self,
        code: str,
        output_dir: str = "./results",
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
            output_dir (str): The path to save the output files. Defaults to "./results".
            format (Literal["stl", "step"]): The format of the output files. Defaults to "stl".

        Returns:
            tuple[bool, str, str]: A tuple containing:
                - A boolean indicating whether the code execution was successful.
                - A message or error from the execution process.
                - The path to the directory where the output files are saved.
        """
        random_name = f"render_{str(uuid.uuid4())[:8]}"
        absolute_output_dir = os.path.abspath(output_dir)
        render_dir = os.path.join(absolute_output_dir, random_name)
        os.makedirs(render_dir, exist_ok=True)

        # patch the code with export function
        code_with_export, _ = self.code_generator.patch_code_to_export(
            code=code, format=format, target_output_dir=render_dir
        )

        # save both code versions
        self.code_generator.save_code_to_file(code, os.path.join(render_dir, "code.py"))
        self.code_generator.save_code_to_file(
            code_with_export, os.path.join(render_dir, "code_with_export.py")
        )

        # execute the code
        is_valid, messages = self.code_executor.execute_and_save(
            code_with_export, render_dir
        )

        if not is_valid:
            logging.error(
                colorstring(f"Code is not valid during export: {messages}", "red")
            )
        else:
            logging.info(
                colorstring(f"Code is valid during export: {messages}", "bright_blue")
            )

        return is_valid, messages, render_dir

    def _generate_executable_code(
        self,
        design_goal: DesignGoal,
        feedbacks: str = None,
        generated_code: str = None,
        coding_plan: dict = None,
    ) -> tuple[str, dict] | None:
        """
        Generates executable code based on the provided design goal.

        This method first generates a coding plan using the design goal's text. It then iteratively
        generates or fixes code, validates it, and attempts to execute it. If the code is not valid
        or fails to execute, feedback is collected and used to improve the code in subsequent iterations.
        The process continues until valid and executable code is generated or the maximum number of
        iterations is reached.
        Args:
            design_goal (DesignGoal): The design goal containing the text description and optional images.
            feedbacks (str, optional): Feedback from the previous iteration. Defaults to None.
            generated_code (str, optional): The code generated in the previous iteration. Defaults to None.
            coding_plan (dict, optional): The coding plan generated in the previous iteration. Defaults to None.

        Returns:
            tuple[str, dict] | None: A tuple containing the generated code and a dictionary of coding_plan,
        """
        # generate plan (using text only)
        # if self.code_master:
        #     coding_plan = self.code_master.plan_code(
        #         design_goal.text,
        #         feedbacks=feedbacks,
        #         previous_plan=coding_plan,
        #     )
        # else:
        coding_plan = self.code_generator.plan_code(
            design_goal.text,
            feedbacks=feedbacks,
            previous_plan=coding_plan,
        )
        logging.info(colorstring(f"Coding plan:\n{coding_plan}", "white"))

        use_master = False
        # iterate to generate executable code
        for i in range(self.max_iterations):
            logging.info(f"[code generation] Iteration {i + 1}/{self.max_iterations}")
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

            logging.info(
                colorstring(
                    f"Executeable code generated:\n{generated_code}", "bright_blue"
                )
            )

            return generated_code, coding_plan

        # If we reach here, the maximum number of iterations was exceeded
        logging.warning(
            colorstring(
                f"[code generation] Maximum iterations ({self.max_iterations}) reached without generating valid and executable code.",
                "red",
            )
        )
        return None

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

    def _mark_iteration_as_runnable(self, iteration_id):
        self.code_cache.update_iteration(iteration_id, is_runnable=True)
        logging.info(
            colorstring(f"Marked iteration {iteration_id} as runnable.", "bright_blue")
        )


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
    # ===== describer agent =====
    describer_config = config["describe-vlm"]
    describer = Describer(
        describer_config["api_key"],
        describer_config.get("api_base_url"),
        describer_config.get("model_name"),
        describer_config.get("org_id"),
        load_prompts(args.prompts, "describe-vlm"),
        **describer_config.get("model_kwargs", {}),
    )

    # ===== coding agents =====
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

    # ===== visual feedback =====
    visual_feedback_config = config.get("visual_feedback")

    visual_feedback = VisualFeedback(
        visual_feedback_config["api_key"],
        visual_feedback_config.get("api_base_url"),
        visual_feedback_config.get("model_name"),
        visual_feedback_config.get("org_id"),
        load_prompts(args.prompts, "visual_feedback"),
        **visual_feedback_config.get("model_kwargs", {}),
    )

    feedback_judge_config = config.get("feedback_judge")
    feedback_judge = FeedbackJudge(
        feedback_judge_config["api_key"],
        feedback_judge_config.get("api_base_url"),
        feedback_judge_config.get("model_name"),
        feedback_judge_config.get("org_id"),
        load_prompts(args.prompts, "feedback_judge"),
        **feedback_judge_config.get("model_kwargs", {}),
    )

    # ===== code execution loop =====
    code_execution_loop = CodeExecutionLoop(
        describer=describer,
        code_generator=code_generator,
        code_executor=CodeExecutor(),
        code_cache=CodeCache(db_file="code-generator.db"),
        code_master=code_master,
        visual_feedback=visual_feedback,
        feedback_judge=feedback_judge,
    )

    # description = "Create a simple table design, flat circular top, with 4 straight legs. Each leg is about 45 unit long with circular cross section. and the circular top has a radius of 60 units. This is a big table."
    description = "create a simple skateboard"

    design_goal = DesignGoal(description)
    output_dir = "./design_task_1"

    code_execution_loop.run(design_goal, output_dir)
