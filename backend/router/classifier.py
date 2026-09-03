from typing import Tuple

class TaskClassifier:
    """
    Lightweight, deterministic rule-based task classifier for local routing.
    Does not depend on external or cloud LLMs.
    """

    CODING_KEYWORDS = [
        "code", "coding", "python", "java", "c++", "cpp", "javascript", "typescript",
        "traceback", "exception", "error in code", "bug", "debug", "debugging",
        "function", "class", "syntax", "refactor", "algorithm", "script", "fix"
    ]

    DOCUMENT_KEYWORDS = [
        "summarize document", "analyze sop", "read manual", "extract information",
        "sop", "pdf", "manual", "report", "document", "specification", "policy", "clause"
    ]

    VISION_KEYWORDS = [
        "p&id", "diagram", "drawing", "image", "photo", "picture", "scanned", "ocr", "blueprint"
    ]

    REASONING_KEYWORDS = [
        "why", "analyze", "explain", "compare", "evaluate", "reason", "logic", "calculate"
    ]

    def classify(self, query: str, has_image: bool = False, has_file: bool = False) -> Tuple[str, str]:
        """
        Classifies request query and attachments into task_type and explanation reason.
        Returns (task_type, reason).
        """
        lower_query = query.lower()

        # Priority 1: Vision / Image
        if has_image:
            return "vision", "Image attachment detected requiring visual analysis"

        for kw in self.VISION_KEYWORDS:
            if kw in lower_query:
                return "vision", f"Vision request detected from keyword '{kw}'"

        # Priority 2: Coding / Debugging
        for kw in self.CODING_KEYWORDS:
            if kw in lower_query:
                return "coding", f"Coding/debugging request detected from keyword '{kw}'"

        # Priority 3: Document
        if has_file:
            # If has file and not vision/coding, check if document/reasoning
            return "document", "Document attachment detected requiring text analysis"

        for kw in self.DOCUMENT_KEYWORDS:
            if kw in lower_query:
                return "document", f"Document request detected from keyword '{kw}'"

        # Priority 4: Reasoning
        for kw in self.REASONING_KEYWORDS:
            if kw in lower_query:
                return "reasoning", f"Analytical/reasoning request detected from keyword '{kw}'"

        # Default / General
        return "general", "General query detected"
