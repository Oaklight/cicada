import ast
import importlib.util
import logging
import os
import shutil
import subprocess
import sys
import tempfile

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from common.utils import colorstring

logging.basicConfig(level=logging.INFO)


class CodeExecutor:
    def execute_code(self, code, timeout=10) -> tuple[bool, dict]:
        # Initialize a new temporary directory for each execution
        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, "script.py")
        with open(script_path, "w") as f:
            f.write(code)

        try:
            completed_process = subprocess.run(
                ["python", script_path],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,  # Set the timeout based on the parameter
            )
            if completed_process.returncode != 0:
                error_message = completed_process.stderr
                return False, {"error": error_message}
            else:
                output_files = {}
                for filename in os.listdir(temp_dir):
                    if filename != "script.py":
                        with open(os.path.join(temp_dir, filename), "rb") as f:
                            content = f.read()
                            output_files[filename] = content
                return True, {"output": completed_process.stdout, "files": output_files}
        except subprocess.TimeoutExpired:
            return False, {"error": "Execution timed out."}
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)

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

    def validate_code_with_flake8(self, code: str) -> tuple[bool, str | None]:
        """
        Check the syntax of the generated code using flake8.

        Args:
            code (str): The generated code to be checked.

        Returns:
            tuple[bool, str | None]: A tuple containing:
                - bool: True if the code is syntactically correct, False otherwise.
                - str | None: Error message if there is a syntax error, None otherwise.
        """
        # Create a temporary directory for syntax check
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, "temp_code.py")

        try:
            # Write the code to a temporary file in the temp directory
            with open(temp_file_path, "w") as temp_file:
                temp_file.write(code)

            # Run flake8 on the temporary file
            result = subprocess.run(
                ["flake8", "--select=F", temp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # If flake8 returns any output, there are errors
            if result.stdout:
                logging.error(
                    colorstring(f"Flake8 found syntax errors:\n{result.stdout}", "red")
                )
                return False, result.stdout

            logging.info(
                colorstring("Flake8 check passed: no syntax errors found.", "blue")
            )
            return True, None

        except Exception as e:
            logging.error(colorstring(f"Error running flake8: {e}", "yellow"))
            return False, str(e)
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)


"""
Final Decision
Avoid Error Formatting for MVP:

- Do not implement the format_error function in the CodeExecutor class.
- Return the raw error message captured from stderr.

Rationale:

- Python error messages vary significantly by error type (SyntaxError, ImportError, NameError, etc.).
- Parsing these messages reliably would require a complex and error-prone system.
- For an MVP, simplicity and reliability are paramount.

Future Enhancements:

- Consider implementing a more robust error parsing mechanism using regular expressions or existing libraries.
- Explore executing code in a controlled environment where exception objects can be accessed directly.
"""


if __name__ == "__main__":
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
        {
            "name": "Valid Python Code with Flake8 Warning",
            "code": """
def add(a, b):
    return a + b

result = add(1, 2)
print(result)

# This line is too long for PEP8
a_very_long_variable_name_that_exceeds_the_limit_of_seventy_nine_characters = 1
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
