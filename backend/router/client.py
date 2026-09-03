import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

class LocalModelClient:
    """
    Abstraction layer for communicating with local model endpoints (e.g., Ollama, vLLM).
    Keeps model generation isolated from routing logic.
    """

    def __init__(self, default_endpoint: str = "http://localhost:11434"):
        self.default_endpoint = default_endpoint.rstrip("/")

    def generate(self, model_name: str, prompt: str, endpoint: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Sends generation request to local Ollama/OpenAI-compatible endpoint.
        """
        target_endpoint = (endpoint or self.default_endpoint).rstrip("/")
        url = f"{target_endpoint}/api/generate"

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=30.0) as response:
                res_body = response.read().decode('utf-8')
                return json.loads(res_body)
        except urllib.error.URLError as e:
            return {
                "error": True,
                "message": f"Failed to connect to local model endpoint {target_endpoint}: {str(e)}"
            }
        except Exception as e:
            return {
                "error": True,
                "message": f"Generation error: {str(e)}"
            }
