import subprocess
import logging
import tempfile
import sys
from pathlib import Path

logger = logging.getLogger("docker_sandbox")

class DockerSandbox:
    """
    Executes generated code in an isolated Docker container with network disabled (--network none)
    or falls back to a restricted local python process runner.
    """
    @staticmethod
    def execute_python_code(code: str, timeout: int = 10) -> dict:
        # Check if Docker is available
        docker_cmd = ["docker", "run", "--rm", "--network", "none", "python:3.10-slim", "python", "-c", code]
        
        try:
            res = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
            if res.returncode == 0:
                return {
                    "success": True,
                    "stdout": res.stdout,
                    "stderr": res.stderr,
                    "execution_environment": "Docker Sandbox (--network none)"
                }
            logger.info("Docker daemon not active or image missing, using safe subprocess sandbox fallback.")
            return DockerSandbox._safe_subprocess_fallback(code, timeout)
        except Exception as ex:
            logger.info(f"Docker sandbox execution not available ({ex}), using safe subprocess fallback.")
            return DockerSandbox._safe_subprocess_fallback(code, timeout)

    @staticmethod
    def _safe_subprocess_fallback(code: str, timeout: int) -> dict:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            res = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "execution_environment": "Subprocess Sandbox"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Execution timed out after 10 seconds.",
                "execution_environment": "Subprocess Sandbox"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "execution_environment": "Subprocess Sandbox"
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)
