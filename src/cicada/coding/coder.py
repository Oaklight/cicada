import argparse
import logging
import os

from cicada.coding.code_cache import CodeCache
from cicada.coding.code_executor import CodeExecutor
from cicada.coding.code_generator import CodeGenerator
from cicada.core.basics import DesignGoal
from cicada.core.utils import colorstring, cprint

logger = logging.getLogger(__name__)


class Coder:
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_templates,
        code_master_config: dict = None,
        max_coding_iterations: int = 10,
        **model_kwargs,
    ):
        # Initialize components
        code_executor = CodeExecutor()
        code_cache = CodeCache(db_file="code-generator.db")

        code_generator = CodeGenerator(
            api_key,
            api_base_url,
            model_name,
            org_id,
            prompt_templates,
            **model_kwargs,
        )

        if code_master_config:
            code_master = CodeGenerator(
                code_master_config.get("api_key", api_key),
                code_master_config.get("api_base_url", api_base_url),
                code_master_config.get("model_name", model_name),
                code_master_config.get("org_id", org_id),
                prompt_templates,
                **code_master_config.get("model_kwargs", model_kwargs),
            )
        else:
            code_master = None

        self.code_generator = code_generator
        self.code_executor = code_executor
        self.code_cache = code_cache
        self.code_master = code_master
        self.max_coding_iterations = max_coding_iterations

    def generate_executable_code(
        self,
        design_goal: DesignGoal,
        feedbacks: str = None,
        generated_code: str = None,
        coding_plan: dict = None,
    ) -> tuple[str, dict] | None:

        # Generate plan
        coding_plan = self.code_generator.plan_code(
            design_goal, feedbacks=feedbacks, previous_plan=coding_plan
        )
        cprint(f"Coding plan:\n{coding_plan}", "bright_blue")

        use_master = False
        # Iterate to generate executable code
        for i in range(self.max_coding_iterations):
            cprint(
                f"[code generation] Iteration {i + 1}/{self.max_coding_iterations}",
                "magenta",
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
                cprint(f"Code is not valid:\n{errors}", "bright_yellow")
                continue

            # Execute
            is_runnable, results = self.code_executor.execute_code(
                generated_code, test_run=True
            )

            if not is_runnable:
                feedbacks = results
                cprint(f"Code is not runnable:\n{results}", "bright_yellow")
                continue

            # return the code if it is valid and executable
            cprint(f"Executable code generated:\n{generated_code}", "bright_green")
            return generated_code, coding_plan

        # If we reach here, it means we failed to generate valid and executable code after max_coding_iterations iterations.
        cprint(
            f"[code generation] Maximum iterations ({self.max_coding_iterations}) reached without generating valid and executable code.",
            "bright_red",
        )
        return None, None

    def render_from_code(
        self, code: str, output_dir: str, format: str = "stl"
    ) -> tuple[bool, str, str]:
        os.makedirs(output_dir, exist_ok=True)

        # Patch the code with export function
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
            logger.error(f"Code is not valid during export: {messages}")
        else:
            logger.info(f"Code is valid during export: {messages}")

        return is_valid, messages, output_dir

    def _mark_iteration_as_runnable(self, iteration_id):
        self.code_cache.update_iteration(iteration_id, is_runnable=True)
        logger.info(
            colorstring(f"Marked iteration {iteration_id} as runnable.", "bright_blue")
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Test the Coder Class.")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to the configuration YAML folder",
    )
    parser.add_argument(
        "--master_config_path",
        default="config.yaml",
        help="Path to the master configuration YAML folder",
    )
    parser.add_argument(
        "--prompts",
        default="prompts.yaml",
        help="Path to the prompts YAML folder",
    )
    parser.add_argument(
        "design_goal",
        type=str,
        help="Path to the design goal JSON file",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        default="./coder_test_results",
        help="Directory to save the results of the test",
    )
    return parser.parse_args()


if __name__ == "__main__":
    from cicada.core.utils import load_config, load_prompts, setup_logging

    args = parse_args()
    setup_logging()

    # Load configuration and prompts
    coder_config = load_config(args.config, "code-llm")
    master_code_llm_config = load_config(args.config, "master-code-llm")
    prompts = load_prompts(args.prompts, "code-llm")

    try:
        master_code_llm_config = load_config(args.master_config_path, "master-code-llm")
    except FileNotFoundError as e:
        master_code_llm_config = None
        logger.warning(f"Master code LLM configuration not found: {e}")

    coder = Coder(
        coder_config.get("api_key"),
        coder_config.get("api_base_url"),
        coder_config.get("model_name"),
        coder_config.get("org_id"),
        prompts,
        code_master_config=master_code_llm_config,
        max_coding_iterations=coder_config.get("max_coding_iterations", 10),
        **coder_config.get("model_kwargs", {}),
    )

    # Create a design goal
    design_goal = DesignGoal.from_json(args.design_goal)

    # Generate executable code
    best_code, best_coding_plan = coder.generate_executable_code(design_goal)

    if best_code:
        # Render the code
        is_success, message, render_dir = coder.render_from_code(
            best_code, args.output_dir, format="stl"
        )
        if is_success:
            logger.info(f"Code rendered successfully: {render_dir}")
        else:
            logger.error(f"Failed to render code: {message}")
    else:
        logger.error("Failed to generate any executable code.")
