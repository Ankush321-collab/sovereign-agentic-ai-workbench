import unittest
from fastapi.testclient import TestClient
from backend.main import app

class TestRouterAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

    def test_route_endpoint(self):
        payload = {
            "query": "Fix this Python function bug and traceback",
            "has_image": False,
            "has_file": False
        }
        response = self.client.post("/route", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["task_type"], "coding")
        self.assertIn("model", data)
        self.assertIn("reason", data)

    def test_models_endpoint(self):
        response = self.client.get("/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("models", data)
        self.assertIsInstance(data["models"], list)

    def test_history_endpoint(self):
        # Call route first
        self.client.post("/route", json={"query": "Summarize this PDF SOP document", "has_file": True})
        response = self.client.get("/routing/history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("history", data)
        self.assertGreaterEqual(len(data["history"]), 1)

if __name__ == "__main__":
    unittest.main()
