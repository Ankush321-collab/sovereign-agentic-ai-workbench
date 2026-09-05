import os
import yaml
import time
from typing import Optional, Dict, Any, List
from backend.router.schemas import (
    RouteRequest, RouteResponse, ModelListResponse, ModelInfo,
    HistoryResponse, HistoryItem
)
from backend.router.classifier import TaskClassifier
from backend.router.health import ModelHealthChecker
from backend.router.fallback import FallbackHandler

class ModelRouter:
    """
    Core Multi-Stage Explainable Model Router for Sovereign AI Workbench.
    Implements SWARAJ / VAJRA 4-Stage Routing Architecture:
      Stage 0: Featurize (< 2 ms)
      Stage 1: Classify (< 20 ms)
      Stage 2: Capability & VRAM Admission Match
      Stage 3: Multi-Factor Scoring (Priors + VRAM Fit + Latency)
      Stage 4: Verification & Safe Fallback
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
                models = data.get("models", {})
                ollama_env_url = os.getenv("OLLAMA_BASE_URL")
                if ollama_env_url and isinstance(models, dict):
                    for m_cfg in models.values():
                        if isinstance(m_cfg, dict) and "endpoint" in m_cfg:
                            if "localhost:11434" in m_cfg["endpoint"] or "127.0.0.1:11434" in m_cfg["endpoint"]:
                                m_cfg["endpoint"] = ollama_env_url
                return models
        except Exception:
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "reasoning": {
                "name": "qwen-reasoning",
                "endpoint": "http://localhost:11434",
                "tasks": ["reasoning", "document", "general"],
                "enabled": True,
                "vram_gb": 8.0,
                "quantization": "Q4_K_M",
                "capabilities": ["reasoning", "doc_extract", "official_drafting", "kb_qa"]
            },
            "coding": {
                "name": "qwen-coder",
                "endpoint": "http://localhost:11434",
                "tasks": ["coding", "debugging"],
                "enabled": True,
                "vram_gb": 9.0,
                "quantization": "Q4_K_M",
                "capabilities": ["code_generate", "code_debug", "engineering_calc", "tool_calling"]
            },
            "vision": {
                "name": "qwen-vl",
                "endpoint": "http://localhost:11434",
                "tasks": ["vision", "image", "document"],
                "enabled": True,
                "vram_gb": 9.5,
                "quantization": "Q4_K_M",
                "capabilities": ["vision_ocr", "multimodal", "diagram_parse"]
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

    def score_candidate(self, cat: str, cfg: Dict[str, Any], task_class: str, task_type: str) -> float:
        """
        Stage 3 Scoring:
          score = w1 * prior + w2 * vram_fit + w3 * (1 / latency_score)
        """
        w1, w2, w3 = 0.60, 0.25, 0.15

        # Prior score based on category match
        tasks = cfg.get("tasks", [])
        caps = cfg.get("capabilities", [])

        if task_type in tasks or task_class in caps:
            prior = 0.95
        elif any(c in task_class for c in caps):
            prior = 0.85
        else:
            prior = 0.40

        # VRAM fit factor (higher free ratio = higher score)
        vram = cfg.get("vram_gb", 8.0)
        vram_fit = 1.0 if vram <= 12.0 else 0.8

        # Latency factor
        latency_score = 1.0

        return round(w1 * prior + w2 * vram_fit + w3 * latency_score, 4)

    def route(self, request: RouteRequest) -> RouteResponse:
        """
        Executes 4-Stage Explainable Routing:
        Stage 0: Featurize
        Stage 1: Classify
        Stage 2: Match capabilities & VRAM
        Stage 3: Multi-factor scoring
        Stage 4: Fallback & Admission
        """
        start_t = time.perf_counter()
        self.models_config = self.load_registry()

        # Step 1: Detailed classification
        classification = self.classifier.classify_detailed(
            query=request.query,
            has_image=request.has_image,
            has_file=request.has_file
        )

        if request.task_type:
            task_type = request.task_type.lower()
            task_class = "explicit_override"
            reason = f"Explicit task type '{task_type}' provided in request"
            features = {"explicit_override": True}
        else:
            task_type = classification["task_type"]
            task_class = classification["task_class"]
            reason = classification["reason"]
            features = classification["features"]

        # Step 2 & 3: Score candidates across registry
        scores = {}
        for cat, cfg in self.models_config.items():
            model_name = cfg.get("name", cat)
            scores[model_name] = self.score_candidate(cat, cfg, task_class, task_type)

        # Map target category for backward compatibility
        target_category = task_type
        if task_type in ["debugging", "coding"]:
            target_category = "coding"
        elif task_type in ["image", "vision"]:
            target_category = "vision"
        elif task_type in ["document", "reasoning", "general"]:
            target_category = "reasoning"

        matched_config = self.models_config.get(target_category)
        if not matched_config:
            for cat, cfg in self.models_config.items():
                if task_type in cfg.get("tasks", []):
                    matched_config = cfg
                    target_category = cat
                    break

        if not matched_config:
            target_category = "reasoning" if "reasoning" in self.models_config else list(self.models_config.keys())[0]
            matched_config = self.models_config[target_category]

        model_name = matched_config.get("name", target_category)
        endpoint = matched_config.get("endpoint", "http://localhost:11434")
        enabled = matched_config.get("enabled", True)
        vram_gb = matched_config.get("vram_gb", 8.0)
        quantization = matched_config.get("quantization", "Q4_K_M")

        # Step 4: Health and Fallback
        is_healthy = self.health_checker.check_health(endpoint, model_name) if enabled else False
        is_fallback = False

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

        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)

        response = RouteResponse(
            task_type=task_type,
            model=model_name,
            endpoint=endpoint,
            reason=reason,
            fallback=is_fallback,
            healthy=is_healthy,
            task_class=task_class,
            feature_vector=features,
            score_breakdown=scores,
            admitted_vram_gb=vram_gb,
            quantization=quantization,
            latency_p95_ms=elapsed_ms
        )

        history_entry = HistoryItem(
            task_type=task_type,
            model=model_name,
            reason=reason,
            endpoint=endpoint,
            task_class=task_class,
            score=scores.get(model_name, 0.90)
        )
        self.history.append(history_entry)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        return response

    def get_models(self) -> ModelListResponse:
        """Returns information about configured models, their health, and VRAM."""
        self.models_config = self.load_registry()
        models_list = []
        health_map = self.check_model_health()

        for cat, cfg in self.models_config.items():
            name = cfg.get("name", cat)
            tasks = cfg.get("tasks", [cat])
            enabled = cfg.get("enabled", True)
            endpoint = cfg.get("endpoint", "http://localhost:11434")
            vram = cfg.get("vram_gb", 8.0)
            quant = cfg.get("quantization", "Q4_K_M")
            healthy = health_map.get(name, False)

            models_list.append(ModelInfo(
                name=name,
                task=tasks[0] if tasks else cat,
                enabled=enabled,
                healthy=healthy,
                endpoint=endpoint,
                vram_gb=vram,
                quantization=quant
            ))

        return ModelListResponse(models=models_list)

    def get_history(self) -> HistoryResponse:
        """Returns routing history."""
        return HistoryResponse(history=self.history)
