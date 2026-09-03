import unittest
from unittest.mock import patch
from backend.router.schemas import RouteRequest
from backend.router.router import ModelRouter

class TestModelRouter(unittest.TestCase):
    def setUp(self):
        self.patcher = patch("backend.router.health.ModelHealthChecker.check_health", return_value=True)
        self.mock_health = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_router_coding_request(self):
        router = ModelRouter()
        req = RouteRequest(query="Fix this Python code exception")
        res = router.route(req)
        self.assertEqual(res.task_type, "coding")
        self.assertEqual(res.model, "qwen-coder")
        self.assertIn("Coding/debugging request detected", res.reason)
        self.assertTrue(res.healthy)
        self.assertFalse(res.fallback)

    def test_router_document_request(self):
        router = ModelRouter()
        req = RouteRequest(query="Summarize this SOP manual", has_file=True)
        res = router.route(req)
        self.assertIn(res.task_type, ["document", "reasoning"])
        self.assertTrue(res.healthy)

    def test_router_vision_request(self):
        router = ModelRouter()
        req = RouteRequest(query="Analyze P&ID image", has_image=True)
        res = router.route(req)
        self.assertEqual(res.task_type, "vision")
        self.assertEqual(res.model, "qwen-vl")

    def test_router_history_and_models(self):
        router = ModelRouter()
        req = RouteRequest(query="Fix bug in python code")
        router.route(req)

        history = router.get_history()
        self.assertGreaterEqual(len(history.history), 1)
        self.assertEqual(history.history[-1].task_type, "coding")

        models_list = router.get_models()
        self.assertGreaterEqual(len(models_list.models), 3)

    def test_router_fallback_when_unhealthy(self):
        # Stop default mock for this test
        self.patcher.stop()

        router = ModelRouter()
        def mock_check(endpoint, model_name):
            if "coder" in model_name:
                return False
            return True

        with patch("backend.router.health.ModelHealthChecker.check_health", side_effect=mock_check):
            req = RouteRequest(query="Fix this python script exception")
            res = router.route(req)
            self.assertEqual(res.task_type, "coding")
            self.assertEqual(res.model, "qwen-reasoning")
            self.assertTrue(res.fallback)
            self.assertTrue(res.healthy)

        # Restart mock for teardown
        self.patcher.start()

if __name__ == "__main__":
    unittest.main()
