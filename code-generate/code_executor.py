import subprocess
import tempfile
import shutil
import os


class CodeExecutor:
    def execute_code(self, code):
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
                timeout=10,  # Set a timeout of 10 seconds
            )
            if completed_process.returncode != 0:
                error_message = completed_process.stderr
                return {"error": error_message}
            else:
                output_files = {}
                for filename in os.listdir(temp_dir):
                    if filename != "script.py":
                        with open(os.path.join(temp_dir, filename), "rb") as f:
                            content = f.read()
                            output_files[filename] = content
                return {"output": completed_process.stdout, "files": output_files}
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out."}
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
    code_file = (
        "/home/pding/projects/codecad/codecad-rag/code-generate/reproduce-mech-part.py"
    )
    with open(code_file, "r") as f:
        code = f.read()

    result = code_executor.execute_code(code)
    print(result)
