import ast
import importlib.util
import logging
import os
import shutil
import subprocess
import tempfile
from subprocess import run, TimeoutExpired

from cicada.core.utils import colorstring

logger = logging.getLogger(__name__)


class CodeExecutor:
    def execute_code(
        self,
        code: str,
        timeout: int = 10,
        test_run: bool = False,
    ) -> tuple[bool, dict]:
        """
        Executes the provided Python code in a temporary directory and returns the results.

        Args:
            code (str): The Python code to execute.
            timeout (int, optional): The maximum time (in seconds) to allow for the execution. Defaults to 10.

        Returns:
            tuple[bool, dict]: A tuple where the first element is a boolean indicating success (True) or failure (False), and the second element is a dictionary containing the results. If successful, the dictionary will contain the standard output and any generated files. If unsuccessful, it will contain an error message.
        """
        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, "script.py")
        with open(script_path, "w") as f:
            f.write(code)

        try:
            completed_process = run(
                ["python", script_path],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if completed_process.returncode != 0:
                error_message = completed_process.stderr
                return False, {"error": error_message}
            else:
                if test_run:
                    logger.info("Test run successful.")
                    return True, {"output": completed_process.stdout}
                else:
                    # Collect all files generated during execution.
                    output_files = {}
                    for root, _, files in os.walk(temp_dir):
                        for filename in files:
                            file_path = os.path.join(root, filename)
                            rel_path = os.path.relpath(file_path, temp_dir)
                            with open(file_path, "rb") as f:
                                content = f.read()
                                output_files[rel_path] = content
                    logger.info("Execution successful. Collecting output files.")
                    return True, {
                        "output": completed_process.stdout,
                        "files": output_files,
                    }
        except TimeoutExpired:
            return False, {"error": "Execution timed out."}
        finally:
            shutil.rmtree(temp_dir)

    def execute_and_save(
        self,
        code: str,
        output_path: str,
        certain_file_types: list[str] | None = None,
        timeout: int = 10,
    ) -> tuple[bool, str]:
        """
        Executes the provided code and saves the output artifacts to the specified directory.

        Args:
            code (str): The Python code to execute.
            output_path (str): The directory where the output artifacts should be saved.
            certain_file_types (list, optional): A list of file extensions to save. If None, all files are saved.
            timeout (int, optional): The maximum execution time in seconds. Defaults to 10 seconds.

        Returns:
            tuple: A tuple containing a boolean indicating success and a message string.
        """
        success, result = self.execute_code(code, timeout=timeout)
        if not success:
            return False, result["error"]

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        files = result.get("files", {})
        logging.debug(f"Output files: {files}")
        for file_path, content in files.items():
            if certain_file_types is not None and not file_path.endswith(
                tuple(certain_file_types)
            ):
                continue
            file_output_path = os.path.join(output_path, file_path)
            os.makedirs(os.path.dirname(file_output_path), exist_ok=True)
            with open(file_output_path, "wb") as f:
                f.write(content)

        stdout = result.get("output", "")
        output_log_path = os.path.join(output_path, "output.log")
        with open(output_log_path, "w") as f:
            f.write(stdout)

        return True, "Artifacts saved successfully to {}".format(output_path)

    def check_syntax(self, code: str) -> tuple[bool, str | None]:
        try:
            compile(code, "<string>", "exec")
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def check_grammar(self, code: str) -> tuple[bool, str | None]:
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def check_imports(self, code: str) -> tuple[bool, str | None]:
        missing_modules = []
        lines = code.splitlines()
        for line in lines:
            if line.startswith("import ") or line.startswith("from "):
                module = line.split()[1].split(".")[0]  # Extract the module name
                if importlib.util.find_spec(module) is None:
                    missing_modules.append(module)

        if missing_modules:
            return False, f"Missing Modules: {', '.join(missing_modules)}"
        else:
            return True, None

    def validate_code(self, code: str) -> tuple[bool, str | None]:
        syntax_result, syntax_error = self.check_syntax(code)
        if not syntax_result:
            return False, f"Syntax Error: {syntax_error}"

        grammar_result, grammar_error = self.check_grammar(code)
        if not grammar_result:
            return False, f"Grammar Error: {grammar_error}"

        imports_result, imports_error = self.check_imports(code)
        if not imports_result:
            return False, f"Import Error: {imports_error}"

        return True, None


if __name__ == "__main__":
    from cicada.core.utils import colorstring, setup_logging

    setup_logging()

    code_executor = CodeExecutor()

    # code_file = (
    #     "/home/pding/projects/codecad/codecad-rag/code-generate/reproduce-mech-part.py"
    # )
    # with open(code_file, "r") as f:
    #     code = f.read()

    # result = code_executor.execute_code(code)
    # print(result)

    # Test cases
    test_cases = [
        {
            "name": "Valid Python Code",
            "code": """
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
""",
        },
        {
            "name": "Syntax Error: Missing Colon",
            "code": """
def add(a, b)
    return a + b

result = add(1, 2)
print(result)
""",
        },
        {
            "name": "Syntax Error: Indentation Error",
            "code": """
def add(a, b):
return a + b

result = add(1, 2)
print(result)
""",
        },
        {
            "name": "Syntax Error: Invalid Syntax",
            "code": """
if True
    print("Hello, World!")
""",
        },
    ]

    for case in test_cases:
        print(f"Testing: {case['name']}")
        is_valid, error_message = code_executor.validate_code(case["code"])
        if is_valid:
            print("Syntax is valid.")
        else:
            print(f"Syntax error detected: {error_message}")
        print("-" * 40)

    with open("/tmp/cicada/code_examples/patched_code.py") as f:
        patched_code = f.read()

    code_executor.execute_and_save(patched_code, "/tmp/cicada/stl_examples")
