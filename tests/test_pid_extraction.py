import pytest
from pathlib import Path
from PIL import Image

from multimodal.pid_regex import PIDRegexExtractor
from multimodal.pid_extractor import PIDExtractor
from multimodal.schemas import ExtractionResult

def test_pid_regex_extractor():
    sample_text = (
        "Main Pumping Skid:\n"
        "Slurry Feed Pump P-101A and Standby Pump P-101B.\n"
        "Discharge enters High Pressure Separator Vessel V-204.\n"
        "Sensors installed: PT-201 (0-200 PSI) on inflow, FT-102 on discharge line, TT-305 on outlet, LCV-301 valve."
    )
    equipment, instruments = PIDRegexExtractor.extract_from_text(sample_text)

    eq_tags = {e.tag for e in equipment}
    assert "P-101A" in eq_tags
    assert "P-101B" in eq_tags
    assert "V-204" in eq_tags

    inst_tags = {i.tag for i in instruments}
    assert "PT-201" in inst_tags
    assert "FT-102" in inst_tags
    assert "TT-305" in inst_tags
    assert "LCV-301" in inst_tags

@pytest.fixture
def sample_pid_image(tmp_path):
    img_path = tmp_path / "pid_unit100.png"
    img = Image.new("RGB", (300, 200), color=(240, 240, 240))
    img.save(str(img_path))
    return str(img_path)

@pytest.mark.asyncio
async def test_pid_extractor_pipeline(sample_pid_image):
    extractor = PIDExtractor()
    res = await extractor.extract(sample_pid_image)
    assert isinstance(res, ExtractionResult)
    assert res.type == "p_and_id_drawing"
    assert len(res.equipment) >= 1
    assert len(res.instruments) >= 1
    assert "P-101A" in [e.tag for e in res.equipment]
    assert "PT-201" in [i.tag for i in res.instruments]
    assert res.confidence > 0.0
