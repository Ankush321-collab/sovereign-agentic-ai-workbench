from backend.tools.docker_sandbox import DockerSandbox

def run_code(code: str, language: str = "python") -> dict:
    """
    Executes code in a sandboxed execution environment.
    """
    if language.lower() in ["python", "py"]:
        return DockerSandbox.execute_python_code(code)
    else:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Language '{language}' execution not supported. Supported: python.",
            "execution_environment": "Sandbox"
        }
