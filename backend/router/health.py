import urllib.request
import urllib.error
import json
from typing import Dict, Any

class ModelHealthChecker:
    """
    Checks if a model endpoint is reachable and responding without expensive generation calls.
    """

    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout

    def check_health(self, endpoint: str, model_name: str) -> bool:
        """
        Check health of an endpoint.
        Supports standard HTTP endpoint checks and Ollama local API (/api/tags).
        """
        if not endpoint:
            return False

        # Trim trailing slash
        base_endpoint = endpoint.rstrip("/")

        # Check Ollama endpoint first if standard port/url
        try:
            # Try Ollama /api/tags
            url = f"{base_endpoint}/api/tags"
            req = urllib.request.Request(url, headers={"User-Agent": "AaravRouterHealth/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    models = data.get("models", [])
                    # If model_name is configured, check if model exists or at least endpoint is healthy
                    model_names = [m.get("name", "") for m in models]
                    if any(model_name in name or name in model_name for name in model_names):
                        return True
                    # If endpoint is active and returns tags, endpoint itself is alive
                    return True
        except Exception:
            pass

        # Generic root/health check fallback
        try:
            req = urllib.request.Request(base_endpoint, headers={"User-Agent": "AaravRouterHealth/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return response.status in (200, 204, 404, 405)
        except urllib.error.HTTPError as e:
            # Some servers return 404 or 405 on root, which still means the service is reachable
            return e.code in (200, 204, 404, 405)
        except Exception:
            return False
