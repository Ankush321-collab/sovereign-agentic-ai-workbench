import unittest
from backend.router.health import ModelHealthChecker

class TestModelHealthChecker(unittest.TestCase):
    def test_health_checker_invalid_endpoint(self):
        checker = ModelHealthChecker(timeout=0.5)
        self.assertFalse(checker.check_health("http://localhost:59999", "qwen-coder"))

    def test_health_checker_empty(self):
        checker = ModelHealthChecker()
        self.assertFalse(checker.check_health("", "qwen-coder"))

if __name__ == "__main__":
    unittest.main()
