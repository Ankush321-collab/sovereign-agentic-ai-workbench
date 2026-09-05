from typing import Tuple, Dict, Any, List

class TaskClassifier:
    """
    Lightweight, deterministic, two-stage task featurizer and classifier for local routing.
    Satisfies SWARAJ / VAJRA Section 4.2:
      Stage 0: Featurize (< 2 ms) - tokens, code-fences, domain hits, imperative verbs, modalities
      Stage 1: Classify (< 20 ms) - maps to 9 industrial/PSU classes + macro category
    100% local, air-gapped, and zero external dependency.
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

    ENGINEERING_CALC_KEYWORDS = [
        "barlow", "asme", "b31.3", "thickness", "wall thickness", "mawp",
        "corrosion", "allowable stress", "pipe calculation", "pressure rating", "calc", "calculate"
    ]

    OFFICIAL_DRAFTING_KEYWORDS = [
        "green-sheet", "green sheet", "csmop", "secretariat note", "office memorandum",
        "approval note", "file note", "gazette", "draft note"
    ]

    REASONING_KEYWORDS = [
        "why", "analyze", "explain", "compare", "evaluate", "reason", "logic", "calculate"
    ]

    IMPERATIVE_VERBS = [
        "calculate", "compute", "extract", "summarize", "draft", "verify",
        "debug", "fix", "optimize", "inspect", "audit", "check"
    ]

    DOMAIN_TERMS = [
        "asme", "barlow", "ndt", "ut", "pipeline", "flange", "oisd", "csmop",
        "corrosion", "yield_strength", "psi", "mpa", "mill_tolerance", "iocl", "ongc", "gail"
    ]

    def featurize(self, query: str, has_image: bool = False, has_file: bool = False) -> Dict[str, Any]:
        """
        Stage 0: Extract discrete feature vector for routing explainability.
        Execution latency: < 2 ms.
        """
        lower = query.lower()
        words = lower.split()
        est_tokens = int(len(words) * 1.3)

        detected_verbs = [v for v in self.IMPERATIVE_VERBS if v in lower]
        detected_domains = [d for d in self.DOMAIN_TERMS if d in lower]
        has_code_fence = "```" in query or "def " in query or "class " in query or "import " in query

        explicit_mode = None
        if lower.startswith("/code"):
            explicit_mode = "code"
        elif lower.startswith("/calc"):
            explicit_mode = "calc"
        elif lower.startswith("/vision"):
            explicit_mode = "vision"

        return {
            "has_image": has_image,
            "has_file": has_file,
            "est_tokens": est_tokens,
            "has_code_fence": has_code_fence,
            "imperative_verbs": detected_verbs,
            "domain_terms": detected_domains,
            "explicit_mode": explicit_mode
        }

    def classify_detailed(self, query: str, has_image: bool = False, has_file: bool = False) -> Dict[str, Any]:
        """
        Stage 1: Multi-class classification across 9 fine-grained PSU/industrial classes
        plus macro category mapping.
        """
        features = self.featurize(query, has_image, has_file)
        lower = query.lower()

        # Priority 1: Vision / Image
        if has_image or features["explicit_mode"] == "vision":
            return {
                "task_type": "vision",
                "task_class": "vision_ocr",
                "reason": "Image attachment detected requiring visual analysis",
                "features": features
            }

        for kw in self.VISION_KEYWORDS:
            if kw in lower:
                return {
                    "task_type": "vision",
                    "task_class": "vision_ocr",
                    "reason": f"Vision request detected from keyword '{kw}'",
                    "features": features
                }

        # Priority 2: Coding / Debugging
        for kw in self.CODING_KEYWORDS:
            if kw in lower:
                task_class = "code_debug" if any(d in lower for d in ["bug", "debug", "exception", "traceback", "error"]) else "code_generate"
                return {
                    "task_type": "coding",
                    "task_class": task_class,
                    "reason": f"Coding/debugging request detected from keyword '{kw}'",
                    "features": features
                }

        if features["has_code_fence"] or features["explicit_mode"] == "code":
            return {
                "task_type": "coding",
                "task_class": "code_generate",
                "reason": "Code block / programming construct detected",
                "features": features
            }

        # Priority 3: Engineering Calculation (Barlow / ASME B31.3)
        for kw in self.ENGINEERING_CALC_KEYWORDS:
            if kw in lower and ("thickness" in lower or "pressure" in lower or "barlow" in lower or "calc" in lower):
                return {
                    "task_type": "coding",  # Maps to coder / sandbox executor
                    "task_class": "engineering_calc",
                    "reason": f"Engineering calculation detected from keyword '{kw}'",
                    "features": features
                }

        # Priority 4: Official Secretariat Drafting
        for kw in self.OFFICIAL_DRAFTING_KEYWORDS:
            if kw in lower:
                return {
                    "task_type": "document",
                    "task_class": "official_drafting",
                    "reason": f"Official PSU drafting request detected from keyword '{kw}'",
                    "features": features
                }

        # Priority 5: Document
        if has_file:
            return {
                "task_type": "document",
                "task_class": "doc_extract",
                "reason": "Document attachment detected requiring text analysis",
                "features": features
            }

        for kw in self.DOCUMENT_KEYWORDS:
            if kw in lower:
                task_class = "doc_summarise" if "summar" in lower else "doc_extract"
                return {
                    "task_type": "document",
                    "task_class": task_class,
                    "reason": f"Document request detected from keyword '{kw}'",
                    "features": features
                }

        # Priority 6: Reasoning
        for kw in self.REASONING_KEYWORDS:
            if kw in lower:
                return {
                    "task_type": "reasoning",
                    "task_class": "kb_qa",
                    "reason": f"Analytical/reasoning request detected from keyword '{kw}'",
                    "features": features
                }

        # Default / General
        return {
            "task_type": "general",
            "task_class": "other",
            "reason": "General query detected",
            "features": features
        }

    def classify(self, query: str, has_image: bool = False, has_file: bool = False) -> Tuple[str, str]:
        """
        Backward-compatible classification method returning (task_type, reason).
        """
        res = self.classify_detailed(query, has_image=has_image, has_file=has_file)
        return res["task_type"], res["reason"]
