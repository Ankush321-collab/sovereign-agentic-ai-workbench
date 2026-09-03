import os
import pytest
from pathlib import Path
from PIL import Image

from multimodal.converter import DocumentConverter
from multimodal.ocr_engine import OCREngine
from multimodal.image_processing import ImageProcessor
from multimodal.document_pipeline import DocumentPipeline
from multimodal.schemas import ExtractionResult

@pytest.fixture
def sample_text_file(tmp_path):
    f = tmp_path / "sample_inspection.txt"
    f.write_text(
        "CONFIDENTIAL INSPECTION REPORT\n"
        "Plant Area: Distillation Column\n"
        "| Tag | Measurement | Status |\n"
        "|---|---|---|\n"
        "| FL-402 | 3.8mm | ALERT |\n"
        "| V-102 | 145 PSI | NORMAL |\n\n"
        "Findings:\n"
        "- Wall thickness below minimum tolerance threshold\n"
        "- Immediate maintenance recommended"
    )
    return str(f)

@pytest.fixture
def sample_image_file(tmp_path):
    img_path = tmp_path / "inspection_report.png"
    img = Image.new("RGB", (300, 100), color=(255, 255, 255))
    img.save(str(img_path))
    return str(img_path)

def test_document_converter_plain_text(sample_text_file):
    converter = DocumentConverter()
    md = converter.convert_to_markdown(sample_text_file)
    assert "CONFIDENTIAL INSPECTION REPORT" in md
    assert "FL-402" in md

def test_ocr_engine_table_parsing():
    ocr = OCREngine()
    text = (
        "| Equipment | Status |\n"
        "|---|---|\n"
        "| Pump P-101 | Running |\n"
        "| Valve V-204 | Closed |"
    )
    tables = ocr.extract_tables_from_text(text)
    assert len(tables) == 1
    assert tables[0].headers == ["Equipment", "Status"]
    assert len(tables[0].rows) == 2

def test_image_processor_base64(sample_image_file):
    b64 = ImageProcessor.to_base64(sample_image_file)
    assert isinstance(b64, str)
    assert len(b64) > 0

def test_document_pipeline_execution(sample_text_file, sample_image_file):
    pipeline = DocumentPipeline()
    res_text = pipeline.process(sample_text_file)
    assert isinstance(res_text, ExtractionResult)
    assert len(res_text.tables) >= 1
    assert len(res_text.findings) >= 1

    res_img = pipeline.process(sample_image_file)
    assert isinstance(res_img, ExtractionResult)
    assert res_img.confidence > 0.0
