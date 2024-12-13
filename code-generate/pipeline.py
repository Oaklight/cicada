import argparse
import logging
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, parent_dir])

from code_cache import CodeCache
from code_executor import CodeExecutor
from code_generator import CodeGenerator

from common.utils import colorstring, load_config, load_prompts

logging.basicConfig(level=logging.INFO)


class CodeExecutionLoop:
    def __init__(
        self,
        code_generator: CodeGenerator,
        code_executor: CodeExecutor,
        code_cache: CodeCache,
        max_iterations=5,
        max_correction_iterations=3,
    ):
        self.code_generator = code_generator
        self.code_executor = code_executor
        self.code_cache = code_cache
        self.max_iterations = max_iterations
        self.max_correction_iterations = max_correction_iterations

    def run(self, description):
        iteration = 0
        session_id = self.code_cache.insert_session(description)
        logging.info(colorstring(f"Session started with id: {session_id}", "cyan"))

        while iteration < self.max_iterations:
            logging.info(f"Starting iteration {iteration + 1} of {self.max_iterations}")

            # Generate code
            generated_code = self.code_generator.generate_code(description)
            if not generated_code:
                logging.error(colorstring("Failed to generate code.", "red"))
                break

            logging.info(colorstring(f"Generated code:\n{generated_code}", "cyan"))
            # ================================================
            #                 Check code syntax
            # ================================================
            correction_iteration = 0
            while correction_iteration < self.max_correction_iterations:
                is_valid, error_message = self.code_executor.validate_code(
                    generated_code
                )
                if is_valid:
                    break
                else:
                    logging.warning(
                        colorstring(f"Syntax error detected: {error_message}", "yellow")
                    )
                    # Generate corrected code using the fix_code function
                    generated_code = self.code_generator.fix_code(
                        generated_code, description, error_message
                    )
                    if not generated_code:
                        logging.error(
                            colorstring("Failed to generate corrected code.", "red")
                        )
                        break
                    correction_iteration += 1

            if correction_iteration == self.max_correction_iterations:
                logging.warning(
                    colorstring(
                        "Max correction attempts reached. Abandoning code.", "yellow"
                    )
                )
                iteration += 1
                continue

            # ===============================================
            #           Cache and execute the code
            # ===============================================
            code_id = self.code_cache.insert_code(
                session_id, description, generated_code
            )
            logging.info(colorstring(f"Cached code with id: {code_id}", "cyan"))

            execution_result = self.code_executor.execute_code(generated_code)

            if "error" in execution_result:
                # ================= execution error ==================
                logging.warning(
                    colorstring(f"Execution error: {execution_result['error']}", "red")
                )
                self.code_cache.insert_execution_result(
                    code_id, False, execution_result["error"], None
                )
                logging.info(
                    colorstring(
                        f"Execution result cached for code id: {code_id}", "cyan"
                    )
                )
            else:
                # ================ execution success =================
                logging.info(colorstring("Code executed successfully.", "white"))
                self.code_cache.insert_execution_result(
                    code_id, True, None, execution_result.get("output", "")
                )
                logging.info(
                    colorstring(
                        f"Execution result cached for code id: {code_id}", "cyan"
                    )
                )
                return  # Exit loop on successful execution

            iteration += 1

        logging.info(
            colorstring(f"Loop completed after {iteration} iterations.", "cyan")
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

    code_llm_config = config["code-llm"]
    code_generator = CodeGenerator(
        code_llm_config["api_key"],
        code_llm_config.get("api_base_url"),
        code_llm_config.get("model_name", "gpt-4o-mini"),
        code_llm_config.get("org_id"),
        load_prompts(args.prompts, "code-llm"),
        **code_llm_config.get("model_kwargs", {}),
    )

    code_cache = CodeCache(db_file="code-generator.db")
    code_executor = CodeExecutor()

    code_execution_loop = CodeExecutionLoop(code_generator, code_executor, code_cache)

    # description = "Create 3 simple cubes with side length of 10, 9 and 8 units respectively. Stack them together, with a 1-unit gap between each cube."
    description = "Create a simple table design, flat circular top, with 4 straight legs. Each leg is about 45 unit long with circular cross section. and the circular top has a radius of 60 units. This is a big table."
    code_execution_loop.run(description)
