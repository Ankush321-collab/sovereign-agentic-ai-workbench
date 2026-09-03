import os
import yaml
from typing import Dict, Any, List, Optional
from backend.router.schemas import (
    RouteRequest, RouteResponse, ModelInfo, ModelListResponse,
    HistoryItem, HistoryResponse
)
from backend.router.classifier import TaskClassifier
from backend.router.health import ModelHealthChecker
from backend.router.fallback import FallbackHandler

class ModelRouter:
    """
    Core Model Router for Sovereign AI Workbench.
    Decides which local model handles a given request based on task classification,
    model registry configuration, health status, and fallback rules.
    """

    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            registry_path = os.path.join(base_dir, "model_registry.yaml")

        self.registry_path = registry_path
        self.classifier = TaskClassifier()
        self.health_checker = ModelHealthChecker()
        self.fallback_handler = FallbackHandler()
        self.history: List[HistoryItem] = []
        self.max_history = 100

        self.models_config = self.load_registry()

    def load_registry(self) -> Dict[str, Any]:
        """Loads configuration from model_registry.yaml."""
        if not os.path.exists(self.registry_path):
            return self._default_config()

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("models", {})
        except Exception:
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "reasoning": {
                "name": "qwen-reasoning",
                "endpoint": "http://localhost:11434",
                "tasks": ["reasoning", "document", "general"],
                "enabled": True
            },
            "coding": {
                "name": "qwen-coder",
                "endpoint": "http://localhost:11434",
                "tasks": ["coding", "debugging"],
                "enabled": True
            },
            "vision": {
                "name": "qwen-vl",
                "endpoint": "http://localhost:11434",
                "tasks": ["vision", "image", "document"],
                "enabled": True
            }
        }

    def check_model_health(self) -> Dict[str, bool]:
        """Checks health status of all registered models."""
        health_status = {}
        for category, cfg in self.models_config.items():
            model_name = cfg.get("name", category)
            endpoint = cfg.get("endpoint", "http://localhost:11434")
            enabled = cfg.get("enabled", True)
            if not enabled:
                health_status[model_name] = False
            else:
                health_status[model_name] = self.health_checker.check_health(endpoint, model_name)
        return health_status

    def route(self, request: RouteRequest) -> RouteResponse:
        """
        Executes routing logic:
        1. Classify task (or use request.task_type if provided)
        2. Find matching configured model
        3. Check model health
        4. Apply fallback if primary is unhealthy
        5. Return RouteResponse and record history
        """
        # Reload registry to ensure dynamic configuration updates take effect
        self.models_config = self.load_registry()

        # Step 1: Classify or use provided task
        if request.task_type:
            task_type = request.task_type.lower()
            reason = f"Explicit task type '{task_type}' provided in request"
        else:
            task_type, reason = self.classifier.classify(
                query=request.query,
                has_image=request.has_image,
                has_file=request.has_file
            )

        # Step 2: Find matching model category in registry
        target_category = task_type
        # Map sub-tasks if needed
        if task_type in ["debugging", "coding"]:
            target_category = "coding"
        elif task_type in ["image", "vision"]:
            target_category = "vision"
        elif task_type in ["document", "reasoning", "general"]:
            target_category = "reasoning"

        matched_config = self.models_config.get(target_category)

        # If not directly matched, find model listing this task
        if not matched_config:
            for cat, cfg in self.models_config.items():
                if task_type in cfg.get("tasks", []):
                    matched_config = cfg
                    target_category = cat
                    break

        if not matched_config:
            # Fallback to reasoning or first available category
            target_category = "reasoning" if "reasoning" in self.models_config else list(self.models_config.keys())[0]
            matched_config = self.models_config[target_category]

        model_name = matched_config.get("name", target_category)
        endpoint = matched_config.get("endpoint", "http://localhost:11434")
        enabled = matched_config.get("enabled", True)

        # Step 3: Check Health
        is_healthy = self.health_checker.check_health(endpoint, model_name) if enabled else False
        is_fallback = False

        # Step 4: Fallback logic if unhealthy or disabled
        if not is_healthy or not enabled:
            health_map = self.check_model_health()
            fallback_res = self.fallback_handler.find_fallback(
                target_task=task_type,
                registry_models=self.models_config,
                healthy_models=health_map
            )
            if fallback_res:
                fallback_cat, fallback_cfg = fallback_res
                fallback_model = fallback_cfg.get("name", fallback_cat)
                fallback_endpoint = fallback_cfg.get("endpoint", endpoint)
                reason = f"Primary model '{model_name}' for task '{task_type}' is unavailable; using fallback '{fallback_model}'"
                model_name = fallback_model
                endpoint = fallback_endpoint
                is_fallback = True
                is_healthy = True
            else:
                reason = f"Primary model '{model_name}' is unavailable and no compatible healthy fallback was found"
                is_fallback = True
                is_healthy = False

        response = RouteResponse(
            task_type=task_type,
            model=model_name,
            endpoint=endpoint,
            reason=reason,
            fallback=is_fallback,
            healthy=is_healthy
        )

        # Record in history
        history_entry = HistoryItem(
            task_type=task_type,
            model=model_name,
            reason=reason,
            endpoint=endpoint
        )
        self.history.append(history_entry)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        return response

    def get_models(self) -> ModelListResponse:
        """Returns information about configured models and their health."""
        self.models_config = self.load_registry()
        models_list = []
        health_map = self.check_model_health()

        for cat, cfg in self.models_config.items():
            name = cfg.get("name", cat)
            tasks = cfg.get("tasks", [cat])
            enabled = cfg.get("enabled", True)
            endpoint = cfg.get("endpoint", "http://localhost:11434")
            healthy = health_map.get(name, False)

            models_list.append(ModelInfo(
                name=name,
                task=tasks[0] if tasks else cat,
                enabled=enabled,
                healthy=healthy,
                endpoint=endpoint
            ))

        return ModelListResponse(models=models_list)

    def get_history(self) -> HistoryResponse:
        """Returns routing history."""
        return HistoryResponse(history=self.history)
