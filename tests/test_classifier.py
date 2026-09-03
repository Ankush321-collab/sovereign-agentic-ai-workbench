import unittest
from backend.router.classifier import TaskClassifier

class TestTaskClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = TaskClassifier()

    def test_classifier_coding(self):
        task, reason = self.classifier.classify("Fix this Python traceback error in code")
        self.assertEqual(task, "coding")
        self.assertIn("Coding/debugging request detected", reason)

    def test_classifier_document(self):
        task, reason = self.classifier.classify("Summarize this safety SOP document", has_file=True)
        self.assertEqual(task, "document")
        self.assertIn("Document", reason)

    def test_classifier_vision(self):
        task, reason = self.classifier.classify("Analyze this P&ID diagram", has_image=True)
        self.assertEqual(task, "vision")
        self.assertTrue("Image attachment detected" in reason or "Vision request detected" in reason)

    def test_classifier_reasoning(self):
        task, reason = self.classifier.classify("Why does the temperature fluctuate in reactor B?")
        self.assertEqual(task, "reasoning")
        self.assertIn("Analytical/reasoning request detected", reason)

    def test_classifier_general(self):
        task, reason = self.classifier.classify("Hello there")
        self.assertEqual(task, "general")
        self.assertIn("General query detected", reason)

if __name__ == "__main__":
    unittest.main()
