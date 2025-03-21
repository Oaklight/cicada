import argparse
import logging
import os
import tkinter as tk
from tkinter import simpledialog
from typing import List, Literal

from trimesh import load_mesh

from cicada.coding.coder import Coder
from cicada.core.basics import DesignGoal
from cicada.core.utils import (
    colorstring,
    cprint,
    find_files_with_extensions,
    load_config,
    load_prompts,
    setup_logging,
)
from cicada.describe.describer_v2 import Describer
from cicada.feedback.feedback_judge import FeedbackJudge
from cicada.feedback.visual_feedback import VisualFeedback
from cicada.geometry_pipeline.snapshots import (
    generate_snapshots,
    preview_mesh_interactively,
)

logger = logging.getLogger(__name__)


class CodeExecutionLoop:
    def __init__(
        self,
        describer: Describer,
        coder: Coder,
        visual_feedback: VisualFeedback,
        feedback_judge: FeedbackJudge,
        max_design_iterations=10,
        max_coding_iterations=5,
    ):
        self.describer = describer
        self.coder = coder
        self.visual_feedback = visual_feedback
        self.feedback_judge = feedback_judge
        self.max_design_iterations = max_design_iterations
        self.max_coding_iterations = max_coding_iterations

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
            iteration_dir = os.path.join(output_dir, f"iteration_{iteration + 1}")
            os.makedirs(iteration_dir, exist_ok=True)

            # Generate executable code using the Coder class
            logger.info("START [generate_executable_code]")
            generated_code, coding_plan = self.coder.generate_executable_code(
                refined_design_goal,
                feedbacks=best_feedbacks,
                generated_code=best_code,
                coding_plan=best_coding_plan,
            )
            logger.info("DONE [generate_executable_code]")
            if generated_code is None:
                logger.error(
                    f"Iteration {iteration + 1} - No executable code generated."
                )
                iteration += 1
                continue

            # Save generated code
            self.coder.code_generator.save_code_to_file(
                generated_code, os.path.join(iteration_dir, "code.py")
            )

            # render_from_code
            logger.info("START [render_from_code]")
            is_success, messages, render_dir = self.coder.render_from_code(
                generated_code, iteration_dir, format="stl"
            )
            logger.info("DONE [render_from_code]")
            if not is_success:
                logger.error(
                    f"Iteration {iteration + 1} - Rendering failed: {messages}"
                )
                iteration += 1
                continue
            else:
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

            # Update best feedback and code based on feedback evaluation
            logger.info("START [update_best_feedback_and_code]")
            if best_feedbacks is None:
                best_code = generated_code
                best_feedbacks = visual_feedback
                logger.info(
                    colorstring(
                        f"Iteration {iteration + 1} - Initial feedback received",
                        "cyan",
                    )
                )

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
            feedback_file_path = os.path.join(render_dir, "human_feedback.txt")
            with open(feedback_file_path, "w") as f:
                f.write(feedback)
            logger.info(f"Feedback saved to {feedback_file_path}")
        else:
            logger.info("No feedback provided.")

        root.destroy()  # Close the GUI

        return feedback

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
            - coder: Coder instance
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

    # ===== coder agent =====
    coder_config = load_config(config_path, "code-llm")

    try:
        master_code_llm_config = load_config(config_path, "master-code-llm")
    except FileNotFoundError as e:
        master_code_llm_config = None
        logger.warning(f"Master code LLM configuration not found: {e}")

    coder = Coder(
        coder_config.get("api_key"),
        coder_config.get("api_base_url"),
        coder_config.get("model_name"),
        coder_config.get("org_id"),
        load_prompts(prompts_path, "code-llm"),
        code_master_config=master_code_llm_config,
        **coder_config.get("model_kwargs", {}),
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

    return describer, coder, visual_feedback, feedback_judge


def main():
    """
    Main function to run the code execution loop.
    """
    # Parse command-line arguments
    args = parse_args()

    # Initialize models
    describer, coder, visual_feedback, feedback_judge = init_models(
        args.config, args.prompts
    )

    # ===== code execution loop =====
    code_execution_loop = CodeExecutionLoop(
        describer=describer,
        coder=coder,
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
