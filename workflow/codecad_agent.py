import argparse
import logging
import os
import sys
import tkinter as tk
from tkinter import simpledialog
from typing import List, Literal

from trimesh import load_mesh

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])


from coding.code_cache import CodeCache
from coding.code_executor import CodeExecutor
from coding.code_generator import CodeGenerator
from common.basics import DesignGoal
from common.utils import (
    colorstring,
    cprint,
    find_files_with_extensions,
    load_config,
    load_prompts,
    setup_logging,
)
from describe.describer_v2 import Describer
from feedbacks.feedback_judge import FeedbackJudge
from feedbacks.visual_feedback import VisualFeedback
from geometry_pipeline.snapshots import generate_snapshots, preview_mesh_interactively

logger = logging.getLogger(__name__)


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
        max_design_iterations=10,
        max_coding_iterations=5,
    ):
        self.code_generator = code_generator
        self.code_executor = code_executor
        self.visual_feedback = visual_feedback
        self.feedback_judge = feedback_judge
        self.code_cache = code_cache
        self.describer = describer
        self.max_design_iterations = max_design_iterations
        self.max_coding_iterations = max_coding_iterations
        self.code_master = code_master

    def run(
        self,
        design_goal: DesignGoal,
        output_dir: str,
        max_design_iterations: int = 10,
        stop_threshold: float = 0.8,
    ):
        # step 0: prepare output directory
        os.makedirs(output_dir, exist_ok=True)

        # Save initial design goal and refined design goal to output directory
        self._save_design_goal(
            design_goal,
            os.path.join(output_dir, "initial_design_goal.json"),
        )

        # Step 1: Refine the design goal using the Describer
        logger.info("START [refine_design_goal]")
        refined_design_goal = self._refine_design_goal(design_goal)
        logger.info("DONE [refine_design_goal]")
        self._save_design_goal(
            refined_design_goal,
            os.path.join(output_dir, "refined_design_goal.json"),
        )

        iteration = 0
        best_code = None
        best_feedbacks = None
        best_coding_plan = None
        is_completed = False

        # Step 2: Proceed with the code generation and execution loop using the refined design goal
        while iteration < max_design_iterations:
            # Create iteration-specific directory
            iteration_dir = os.path.join(output_dir, f"iteration_{iteration + 1}")
            os.makedirs(iteration_dir, exist_ok=True)

            # generate_executable_code
            logger.info("START [generate_executable_code]")
            generated_code, coding_plan = self._generate_executable_code(
                refined_design_goal,
                feedbacks=best_feedbacks,
                generated_code=best_code,
                coding_plan=best_coding_plan,
            )
            logger.info("DONE [generate_executable_code]")
            if generated_code is None:
                logger.error(
                    colorstring(
                        f"Iteration {iteration + 1} - No executable code generated.",
                        "red",
                    )
                )
                iteration += 1
                continue

            # Save generated code
            self.code_generator.save_code_to_file(
                generated_code, os.path.join(iteration_dir, "code.py")
            )

            # render_from_code
            logger.info("START [render_from_code]")
            is_success, messages, render_dir = self._render_from_code(
                generated_code, iteration_dir, format="stl"
            )
            logger.info("DONE [render_from_code]")
            if not is_success:
                logger.error(
                    colorstring(
                        f"Iteration {iteration + 1} - Rendering failed: {messages}",
                        "red",
                    )
                )
                iteration += 1
                continue
            else:
                # Preview the mesh interactively after successful render
                human_feedback = self._preview_mesh(render_dir)

            # get_visual_feedback
            logger.info("START [get_visual_feedback]")
            is_success, visual_feedback = self._get_visual_feedback(
                refined_design_goal, render_dir, snapshot_directions="omni"
            )
            logger.info("DONE [get_visual_feedback]")
            if not is_success:
                logger.error(
                    colorstring(
                        f"Iteration {iteration + 1} - Visual feedback failed", "red"
                    )
                )
                iteration += 1
                continue

            # Save visual feedback
            with open(os.path.join(iteration_dir, "visual_feedback.txt"), "w") as f:
                f.write(visual_feedback)

            # Check if the current feedback is better than the best feedback so far
            logger.info("START [check_feedback]")
            if best_feedbacks is None:
                best_code = generated_code
                best_feedbacks = visual_feedback
                logger.info(
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

                logger.info(
                    colorstring(
                        f"Iteration {iteration + 1} - Improved feedback received",
                        "cyan",
                    )
                )
            logger.info("DONE [check_feedback]")

            # Check if the design goal has been achieved
            logger.info("START [check_design_goal]")
            is_achieved, score = self.feedback_judge.is_design_goal_achieved(
                visual_feedback, refined_design_goal.text
            )
            logger.info("DONE [check_design_goal]")
            if is_achieved or score >= stop_threshold:
                best_code = generated_code
                best_feedbacks = visual_feedback
                best_coding_plan = coding_plan
                logger.info(
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
                f"SUCCESS!"
                f"Design task completed after {iteration} iterations."
                f"Best code: {best_code}"
                f"Best feedbacks: {best_feedbacks}"
                f"Best coding plan: {best_coding_plan}"
            )
            msg_color = "bright_green"
        else:
            finish_message = f"Design task not completed after {iteration} iterations."
            msg_color = "bright_red"

        logger.info(colorstring(finish_message, msg_color))
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
            logger.error("No rendered object found in the render path.")
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
        logger.info(colorstring(f"Snapshot paths: {snapshot_paths}", "magenta"))

        # compare with design_goal and generate feedbacks
        visual_feedback = self.visual_feedback.generate_feedback_paragraph(
            design_goal.text, design_goal.images, snapshot_paths
        )

        logger.info(colorstring(f"Visual feedback: {visual_feedback}", "white"))

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
        and then executes the patched code to generate the output files. The output files are saved in the specified
        output directory. Both the original and patched versions of the code are saved for reference.

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
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Patch the code with export function
        # code_with_export, _ = self.code_generator.patch_code_to_export(
        #     code=code, format=format, target_output_dir= os.path.abspath(output_dir)
        # )
        code_with_export, _ = self.code_generator.patch_code_to_export(
            code=code, format=format
        )

        # Save both code versions
        self.code_generator.save_code_to_file(code, os.path.join(output_dir, "code.py"))
        self.code_generator.save_code_to_file(
            code_with_export, os.path.join(output_dir, "code_with_export.py")
        )

        # Execute the code
        is_valid, messages = self.code_executor.execute_and_save(
            code_with_export, output_dir
        )

        if not is_valid:
            logger.error(
                colorstring(f"Code is not valid during export: {messages}", "red")
            )
        else:
            logger.info(
                colorstring(f"Code is valid during export: {messages}", "bright_blue")
            )

        return is_valid, messages, output_dir

    def _preview_mesh(self, render_dir: str) -> str | None:
        """
        Preview the rendered mesh interactively and collect human feedback.

        Args:
            render_dir (str): The directory containing the rendered mesh file.

        Returns:
            str | None: The human feedback provided by the user as a string.
                    Returns `None` if no feedback is provided or if no rendered object is found.
        """
        # Find the rendered mesh file
        rendered_obj_path = find_files_with_extensions(
            render_dir, ["stl", "step", "obj"], return_all=False
        )

        if rendered_obj_path is None:
            logger.error("No rendered object found in the render path.")
            return None

        # Load the mesh
        mesh = load_mesh(rendered_obj_path)

        # Preview the mesh interactively
        preview_mesh_interactively(
            mesh,
            direction="front",
            reaxis_gravity=True,
            mesh_color=[0, 102, 204],  # Example color
        )

        # Create a simple GUI to collect human feedback
        root = tk.Tk()
        root.withdraw()  # Hide the root window

        # Show an input dialog to collect feedback
        feedback = simpledialog.askstring(
            "Feedback", "Please provide your feedback on the mesh:"
        )

        if feedback:
            logger.info(f"Human feedback received: {feedback}")
            # Process the feedback as needed
            # For example, you can save it to a file or use it in further processing
            feedback_file_path = os.path.join(render_dir, "human_feedback.txt")
            with open(feedback_file_path, "w") as f:
                f.write(feedback)
            logger.info(f"Feedback saved to {feedback_file_path}")
        else:
            logger.info("No feedback provided.")

        root.destroy()  # Close the GUI

        return feedback

    def _generate_executable_code(
        self,
        design_goal: DesignGoal,
        feedbacks: str = None,
        generated_code: str = None,
        coding_plan: dict = None,
    ) -> tuple[str, dict] | None:
        """
        Generates executable code based on the provided design goal.

        Args:
            design_goal (DesignGoal): The design goal containing the text description and optional images.
            feedbacks (str, optional): Feedback from the previous iteration. Defaults to None.
            generated_code (str, optional): The code generated in the previous iteration. Defaults to None.
            coding_plan (dict, optional): The coding plan generated in the previous iteration. Defaults to None.

        Returns:
            tuple[str, dict] | None: A tuple containing the generated code and a dictionary of coding_plan.
        """
        # Generate plan
        if self.code_master:
            coding_plan = self.code_master.plan_code(
                design_goal,
                feedbacks=feedbacks,
                previous_plan=coding_plan,
            )
        else:
            coding_plan = self.code_generator.plan_code(
                design_goal,
                feedbacks=feedbacks,
                previous_plan=coding_plan,
            )
        logger.info(colorstring(f"Coding plan:\n{coding_plan}", "white"))

        use_master = False
        # Iterate to generate executable code
        for i in range(self.max_coding_iterations):
            logger.info(
                f"[code generation] Iteration {i + 1}/{self.max_coding_iterations}"
            )
            if i >= 2 / 3 * self.max_coding_iterations:
                use_master = True

            # Generate or fix code
            generator = (
                self.code_master
                if use_master and self.code_master
                else self.code_generator
            )
            generated_code = generator.generate_or_fix_code(
                design_goal,
                coding_plan,
                existing_code=generated_code,
                feedbacks=feedbacks,
            )

            # Validate
            is_valid, errors = self.code_executor.validate_code(generated_code)
            if not is_valid:
                feedbacks = errors
                logger.warning(colorstring(f"Code is not valid:\n{errors}", "yellow"))
                continue

            # Execute
            is_runnable, results = self.code_executor.execute_code(
                generated_code, test_run=True
            )

            if not is_runnable:
                feedbacks = results
                logger.warning(
                    colorstring(f"Code is not runnable:\n{results}", "yellow")
                )
                continue

            logger.info(
                colorstring(
                    f"Executable code generated:\n{generated_code}", "bright_blue"
                )
            )

            return generated_code, coding_plan

        # If we reach here, the maximum number of iterations was exceeded
        logger.warning(
            colorstring(
                f"[code generation] Maximum iterations ({self.max_coding_iterations}) reached without generating valid and executable code.",
                "red",
            )
        )
        return (None, None)

    def _mark_iteration_as_runnable(self, iteration_id):
        self.code_cache.update_iteration(iteration_id, is_runnable=True)
        logger.info(
            colorstring(f"Marked iteration {iteration_id} as runnable.", "bright_blue")
        )

    def _save_design_goal(self, design_goal: DesignGoal, file_path: str):
        """
        Save the design goal (text and reference images) as a JSON file.

        Args:
            design_goal (DesignGoal): The design goal to save.
            file_path (str): The path to save the JSON file.
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        try:
            with open(file_path, "w") as f:
                f.write(design_goal.to_json())
            logger.info(f"Design goal saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save design goal to {file_path}: {e}")
            cprint(design_goal, "bright_yellow")
            raise e


def parse_args():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Assistive Large Language Model")
    parser.add_argument(
        "--config",
        default="config",
        help="Path to the configuration YAML folder",
    )
    parser.add_argument(
        "--prompts",
        default="prompts",
        help="Path to the prompts YAML folder",
    )
    parser.add_argument(
        "design_task",
        help="Description of the design task (e.g., 'create a simple skateboard')",
    )
    parser.add_argument(
        "-img",
        "--ref_images",
        type=str,
        default=None,
        help="Paths to reference images for the design",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        default="./design_task_results",
        help="Directory to save the results of the design task",
    )
    return parser.parse_args()


def init_models(config_path: str, prompts_path: str):
    """
    Initialize all models and components required for the code execution loop.

    Args:
        config_path (str): Path to the configuration YAML file or folder.
        prompts_path (str): Path to the prompts YAML file or folder.

    Returns:
        tuple: A tuple containing the initialized components:
            - describer: Describer instance
            - code_generator: CodeGenerator instance
            - code_master: CodeGenerator instance (optional)
            - visual_feedback: VisualFeedback instance
            - feedback_judge: FeedbackJudge instance
    """
    # ===== describer agent =====
    describer_config = load_config(config_path, "describe-vlm")
    describer = Describer(
        describer_config["api_key"],
        describer_config.get("api_base_url"),
        describer_config.get("model_name"),
        describer_config.get("org_id"),
        load_prompts(prompts_path, "describe-vlm"),
        **describer_config.get("model_kwargs", {}),
    )

    # ===== coding agents =====
    code_llm_config = load_config(config_path, "code-llm")
    code_generator = CodeGenerator(
        code_llm_config["api_key"],
        code_llm_config.get("api_base_url"),
        code_llm_config.get("model_name"),
        code_llm_config.get("org_id"),
        load_prompts(prompts_path, "code-llm"),
        **code_llm_config.get("model_kwargs", {}),
    )

    master_code_llm_config = load_config(config_path, "master-code-llm")
    code_master = (
        CodeGenerator(
            master_code_llm_config["api_key"],
            master_code_llm_config.get("api_base_url"),
            master_code_llm_config.get("model_name"),
            master_code_llm_config.get("org_id"),
            load_prompts(prompts_path, "code-llm"),
            **master_code_llm_config.get("model_kwargs", {}),
        )
        if master_code_llm_config
        else None
    )

    # ===== visual feedback =====
    visual_feedback_config = load_config(config_path, "visual_feedback")
    visual_feedback = VisualFeedback(
        visual_feedback_config["api_key"],
        visual_feedback_config.get("api_base_url"),
        visual_feedback_config.get("model_name"),
        visual_feedback_config.get("org_id"),
        load_prompts(prompts_path, "visual_feedback"),
        **visual_feedback_config.get("model_kwargs", {}),
    )

    # ===== feedback judge =====
    feedback_judge_config = load_config(config_path, "feedback_judge")
    feedback_judge = FeedbackJudge(
        feedback_judge_config["api_key"],
        feedback_judge_config.get("api_base_url"),
        feedback_judge_config.get("model_name"),
        feedback_judge_config.get("org_id"),
        load_prompts(prompts_path, "feedback_judge"),
        **feedback_judge_config.get("model_kwargs", {}),
    )

    return describer, code_generator, code_master, visual_feedback, feedback_judge


def main():
    """
    Main function to run the code execution loop.
    """
    # Parse command-line arguments
    args = parse_args()

    # Initialize models
    describer, code_generator, code_master, visual_feedback, feedback_judge = (
        init_models(args.config, args.prompts)
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

    # Create the design goal
    design_goal = DesignGoal(args.design_task, args.ref_images)

    # Use the output directory specified in the command-line arguments
    output_dir = args.output_dir

    # Run the code execution loop
    code_execution_loop.run(design_goal, output_dir)


if __name__ == "__main__":
    setup_logging()
    main()
