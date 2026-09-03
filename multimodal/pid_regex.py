import re
from typing import List, Tuple, Dict, Any, Optional
from multimodal.schemas import PIDEquipment, PIDInstrument


class PIDRegexExtractor:
    """Deterministic ISA-5.1 tag extractor for engineering schematics and P&IDs."""

    # Standard ISA-5.1 First Letter (Measured Variable)
    MEASURED_VARIABLES = {
        "P": "Pressure",
        "F": "Flow",
        "T": "Temperature",
        "L": "Level",
        "A": "Analytical / Analyzer",
        "D": "Density",
        "E": "Voltage",
        "I": "Current",
        "J": "Power",
        "S": "Speed / Frequency",
        "V": "Vibration",
        "Z": "Position",
        "H": "Hand / Manual",
        "M": "Moisture / Humidity",
        "W": "Weight / Force",
    }

    # Standard ISA-5.1 Succeeding Letters (Readout / Output Function)
    FUNCTION_MODIFIERS = {
        "T": "Transmitter",
        "I": "Indicator",
        "C": "Controller",
        "V": "Control Valve",
        "S": "Switch",
        "E": "Sensor / Element",
        "G": "Gauge",
        "A": "Alarm",
        "CV": "Control Valve",
        "SV": "Safety Relief Valve",
        "XV": "Isolation Shutdown Valve",
        "IC": "Indicating Controller",
        "IT": "Indicating Transmitter",
        "TC": "Transmitter Controller",
    }

    # Standard Equipment Tag Patterns (e.g., P-101A, V-204, E-102, TK-10)
    EQUIPMENT_PATTERNS = [
        (r"\b(P|PU|PUMP)-?([0-9]{2,4}[A-Z]?)\b", "Centrifugal / Slurry Pump"),
        (r"\b(V|VSL|VESSEL)-?([0-9]{2,4}[A-Z]?)\b", "Separator / Pressure Vessel"),
        (r"\b(TK|TANK)-?([0-9]{2,4}[A-Z]?)\b", "Storage Tank"),
        (r"\b(E|HEX|HE)-?([0-9]{2,4}[A-Z]?)\b", "Shell & Tube Heat Exchanger"),
        (r"\b(C|COMP|K)-?([0-9]{2,4}[A-Z]?)\b", "Gas Compressor"),
        (r"\b(T|TWR|COL)-?([0-9]{2,4}[A-Z]?)\b", "Distillation / Absorption Column"),
        (r"\b(R|RX)-?([0-9]{2,4}[A-Z]?)\b", "Chemical Reactor"),
        (r"\b(F|FLT|STR)-?([0-9]{2,4}[A-Z]?)\b", "Cartridge Filter / Strainer"),
    ]

    # ISA-5.1 Full Tag Pattern: 2 to 4 letters followed by optional hyphen and loop number
    INSTRUMENT_TAG_REGEX = re.compile(r"\b([A-Z]{2,5})-?([0-9]{2,4}[A-Z]?)\b")

    @classmethod
    def extract_from_text(cls, text: str) -> Tuple[List[PIDEquipment], List[PIDInstrument]]:
        """Scan text and extract ISA-5.1 compliant equipment and instrumentation items."""
        equipment_map: Dict[str, PIDEquipment] = {}
        instrument_map: Dict[str, PIDInstrument] = {}

        # 1. Match Equipment Tags
        for pattern, default_type in cls.EQUIPMENT_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                prefix, num = match.groups()
                tag = f"{prefix.upper()}-{num.upper()}"
                if tag not in equipment_map:
                    equipment_map[tag] = PIDEquipment(
                        tag=tag,
                        type=default_type,
                        description=f"Standard Industrial {default_type}",
                        status="Operational"
                    )

        # 2. Match Instrument Tags
        for match in cls.INSTRUMENT_TAG_REGEX.finditer(text):
            letter_prefix, loop_num = match.groups()
            letter_prefix = letter_prefix.upper()
            loop_num = loop_num.upper()

            # The first letter is the primary measured variable
            var_char = letter_prefix[0]
            func_chars = letter_prefix[1:]

            if var_char in cls.MEASURED_VARIABLES:
                tag = f"{letter_prefix}-{loop_num}"

                # Skip if already identified as equipment
                if tag in equipment_map:
                    continue

                var_desc = cls.MEASURED_VARIABLES[var_char]
                func_desc = cls.FUNCTION_MODIFIERS.get(func_chars, f"{func_chars} Instrument")
                inst_type = f"{var_desc} {func_desc}"

                if tag not in instrument_map:
                    instrument_map[tag] = PIDInstrument(
                        tag=tag,
                        type=inst_type,
                        loop_id=loop_num,
                        range=""
                    )

        return list(equipment_map.values()), list(instrument_map.values())
