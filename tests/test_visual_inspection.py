import pytest
from pathlib import Path
from PIL import Image

from multimodal.vision_client import LocalVisionClient
from multimodal.inspection_analyzer import InspectionAnalyzer
from multimodal.schemas import ExtractionResult

@pytest.fixture
def sample_defect_image(tmp_path):
    img_path = tmp_path / "flange_corrosion.png"
    img = Image.new("RGB", (200, 200), color=(180, 80, 50))
    img.save(str(img_path))
    return str(img_path)

@pytest.mark.asyncio
async def test_vision_client_fallback_mode(sample_defect_image):
    client = LocalVisionClient()
    res = await client.analyze_image(sample_defect_image, prompt="Inspect corrosion")
    assert isinstance(res, dict)
    assert "findings" in res
    assert len(res["findings"]) > 0

@pytest.mark.asyncio
async def test_inspection_analyzer_flow(sample_defect_image):
    analyzer = InspectionAnalyzer()
    res = await analyzer.analyze(sample_defect_image)
    assert isinstance(res, ExtractionResult)
    assert res.type == "image_inspection"
    assert len(res.findings) >= 1
    assert "Findings" in res.text
    assert res.confidence > 0.0
