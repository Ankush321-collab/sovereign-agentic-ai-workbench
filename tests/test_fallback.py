import unittest
from backend.router.fallback import FallbackHandler

class TestFallbackHandler(unittest.TestCase):
    def setUp(self):
        self.handler = FallbackHandler()

    def test_fallback_selection(self):
        registry_models = {
            "reasoning": {
                "name": "qwen-reasoning",
                "endpoint": "http://localhost:11434",
                "tasks": ["reasoning", "general"],
                "enabled": True
            },
            "coding": {
                "name": "qwen-coder",
                "endpoint": "http://localhost:11434",
                "tasks": ["coding"],
                "enabled": True
            }
        }
        healthy_models = {
            "qwen-reasoning": True,
            "qwen-coder": False
        }

        fallback = self.handler.find_fallback("coding", registry_models, healthy_models)
        self.assertIsNotNone(fallback)
        cat, cfg = fallback
        self.assertEqual(cat, "reasoning")
        self.assertEqual(cfg["name"], "qwen-reasoning")

    def test_fallback_vision_no_silent_fallback(self):
        registry_models = {
            "reasoning": {
                "name": "qwen-reasoning",
                "tasks": ["reasoning"],
                "enabled": True
            }
        }
        healthy_models = {"qwen-reasoning": True}

        fallback = self.handler.find_fallback("vision", registry_models, healthy_models)
        self.assertIsNone(fallback)

if __name__ == "__main__":
    unittest.main()
