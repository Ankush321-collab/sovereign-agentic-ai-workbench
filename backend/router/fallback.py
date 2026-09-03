from typing import Dict, Any, List, Optional, Tuple

class FallbackHandler:
    """
    Handles model selection when primary model is unhealthy or unavailable.
    """

    # Task compatibility mapping
    COMPATIBLE_TASKS = {
        "coding": ["reasoning", "general"],
        "document": ["reasoning", "general"],
        "reasoning": ["general", "document"],
        "general": ["reasoning", "document"],
        "vision": []  # Vision should not silently fallback to non-vision model
    }

    def find_fallback(
        self,
        target_task: str,
        registry_models: Dict[str, Dict[str, Any]],
        healthy_models: Dict[str, bool]
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Finds a healthy compatible model when primary model for target_task is unavailable.
        Returns (category_key, model_config) or None.
        """
        compatible_categories = self.COMPATIBLE_TASKS.get(target_task, ["general", "reasoning"])

        for category in compatible_categories:
            if category in registry_models:
                cfg = registry_models[category]
                if cfg.get("enabled", True):
                    model_name = cfg.get("name", "")
                    if healthy_models.get(model_name, False):
                        return category, cfg

        # If still none, check if any enabled healthy model exists (excluding vision for non-vision tasks unless suitable)
        for cat, cfg in registry_models.items():
            if cat != target_task and cfg.get("enabled", True):
                if target_task == "vision" and "vision" not in cfg.get("tasks", []):
                    continue
                model_name = cfg.get("name", "")
                if healthy_models.get(model_name, False):
                    return cat, cfg

        return None
