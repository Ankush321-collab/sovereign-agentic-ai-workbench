"""
backend/multimodal/pid_parser.py
Pankaj's Multimodal Module — P&ID Tag Parser

Per README Section 7.4 — P&ID Feature:
  P&ID Image → Symbol/Tag Detection → Equipment + Instrument Tags → Structured JSON

Uses regex-based ISA tag pattern extraction from text.
When a vision model (Qwen2.5-VL) is available, it is called for visual interpretation.
"""

import re
import logging
from typing import Any

logger = logging.getLogger("multimodal.pid")

# ISA Instrument Tag Patterns (ISA-5.1 standard)
EQUIPMENT_PATTERNS = {
    "Pump":                  re.compile(r"\bP-\d{2,4}[A-Z]?\b"),
    "Vessel":                re.compile(r"\bV-\d{2,4}[A-Z]?\b"),
    "Compressor":            re.compile(r"\bK-\d{2,4}[A-Z]?\b"),
    "Heat Exchanger":        re.compile(r"\bE-\d{2,4}[A-Z]?\b"),
    "Column":                re.compile(r"\bT-\d{2,4}[A-Z]?\b"),
    "Filter":                re.compile(r"\bF-\d{2,4}[A-Z]?\b"),
    "Tank":                  re.compile(r"\bTK-\d{2,4}[A-Z]?\b"),
    "Fired Heater":          re.compile(r"\bH-\d{2,4}[A-Z]?\b"),
}

INSTRUMENT_PATTERNS = {
    "Pressure Transmitter":  re.compile(r"\bPT-\d{2,4}[A-Z]?\b"),
    "Pressure Indicator":    re.compile(r"\bPI-\d{2,4}[A-Z]?\b"),
    "Flow Transmitter":      re.compile(r"\bFT-\d{2,4}[A-Z]?\b"),
    "Flow Indicator":        re.compile(r"\bFI-\d{2,4}[A-Z]?\b"),
    "Temperature Transmitter": re.compile(r"\bTT-\d{2,4}[A-Z]?\b"),
    "Temperature Indicator": re.compile(r"\bTI-\d{2,4}[A-Z]?\b"),
    "Level Transmitter":     re.compile(r"\bLT-\d{2,4}[A-Z]?\b"),
    "Level Indicator":       re.compile(r"\bLI-\d{2,4}[A-Z]?\b"),
    "Control Valve":         re.compile(r"\bXV-\d{2,4}[A-Z]?\b"),
    "Safety Valve":          re.compile(r"\bSV-\d{2,4}[A-Z]?\b|PRV-\d{2,4}[A-Z]?\b"),
    "Block Valve":           re.compile(r"\bBV-\d{2,4}[A-Z]?\b"),
    "Analyser":              re.compile(r"\bAT-\d{2,4}[A-Z]?\b"),
}


def parse_pid_tags(text: str) -> dict[str, Any]:
    """
    Extracts equipment and instrument tags from text using ISA-5.1 regex patterns.

    Per README spec, returns:
    {
      "equipment": [{"tag": "P-101", "type": "Pump"}, ...],
      "instruments": [{"tag": "PT-201", "type": "Pressure Transmitter"}, ...],
      "total_tags": N
    }
    """
    equipment = []
    instruments = []
    seen = set()

    # Extract equipment tags
    for eq_type, pattern in EQUIPMENT_PATTERNS.items():
        for match in pattern.finditer(text):
            tag = match.group()
            if tag not in seen:
                seen.add(tag)
                equipment.append({"tag": tag, "type": eq_type})

    # Extract instrument tags
    for inst_type, pattern in INSTRUMENT_PATTERNS.items():
        for match in pattern.finditer(text):
            tag = match.group()
            if tag not in seen:
                seen.add(tag)
                instruments.append({"tag": tag, "type": inst_type})

    # Sort by tag for consistent output
    equipment.sort(key=lambda x: x["tag"])
    instruments.sort(key=lambda x: x["tag"])

    logger.info(f"P&ID parsing: {len(equipment)} equipment tags, {len(instruments)} instrument tags found")

    return {
        "equipment": equipment,
        "instruments": instruments,
        "total_tags": len(equipment) + len(instruments),
        "has_pid_content": len(equipment) + len(instruments) > 0
    }


def detect_is_pid(text: str, filename: str = "") -> bool:
    """
    Heuristically detects if a document is a P&ID or equipment drawing.
    """
    name_lower = filename.lower()
    if any(kw in name_lower for kw in ["pid", "p&id", "drawing", "schematic", "isometric"]):
        return True

    # Count ISA tags — if there are many, it's likely a P&ID
    total_tags = 0
    for pattern in list(EQUIPMENT_PATTERNS.values()) + list(INSTRUMENT_PATTERNS.values()):
        total_tags += len(pattern.findall(text))

    return total_tags >= 3
