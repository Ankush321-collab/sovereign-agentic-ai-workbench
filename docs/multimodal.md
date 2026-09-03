# 👁️ Multimodal AI, OCR & P&ID Service Documentation

**Owner**: Pankaj  
**Module**: `multimodal/`  
**Port**: `8003` (`POST /multimodal/process`, `GET /multimodal/health`)

---

## 1. Overview

The **Multimodal AI, OCR & P&ID Module** is an on-premise, air-gapped pipeline for industrial document understanding, photograph defect analysis, and Piping & Instrumentation Diagram (P&ID) schematic tag extraction.

### Core Capabilities:
- **Multi-Format Document Conversion**: Leverages Microsoft **MarkItDown** (`markitdown`) as the primary converter for converting PDFs, Word, Excel, PowerPoint, and text files into standard Markdown.
- **Scanned OCR & Table Parsing**: OpenCV preprocessing (deskewing, CLAHE contrast enhancement, Otsu binarization) combined with Tesseract OCR to extract text and structured table matrices (`TableData`).
- **Visual Defect Understanding**: Connects to local **Qwen2.5-VL** (via Ollama at `http://localhost:11434` or vLLM at `http://localhost:8003/v1`) to analyze physical damage photos (e.g. galvanic corrosion on flange `FL-402`, cracks, valve wear).
- **Dual-Mode P&ID Tag Extraction**: Combines deep visual diagram reasoning with deterministic ISA-5.1 regex pattern matching to extract equipment tags (`P-101A`, `V-204`) and instrumentation loops (`PT-201`, `FT-102`, `LCV-301`).
- **Unified FastAPI Microservice**: Operates on port `8003` and provides payloads adhering strictly to the backend `AgentState` specification.

---

## 2. Directory Structure

```text
sovereign-agentic-ai-workbench/
├── multimodal/
│   ├── __init__.py
│   ├── config.py              # Ports, model URLs, Tesseract paths, fallbacks
│   ├── schemas.py             # Pydantic models (ExtractionResult, PIDEquipment, TableData)
│   ├── image_processing.py    # OpenCV deskewing, CLAHE contrast, base64 encoding
│   ├── file_loader.py         # MIME inspector and PDF page extraction
│   ├── converter.py           # Microsoft MarkItDown + Docling + modular format converters
│   ├── ocr_engine.py          # Tesseract OCR & markdown table parsing
│   ├── vision_client.py       # Local Qwen2.5-VL client (Ollama/vLLM)
│   ├── inspection_analyzer.py # Visual defect analysis & prompt engineering
│   ├── pid_regex.py           # ISA-5.1 deterministic tag extraction engine
│   ├── pid_extractor.py       # Dual-mode P&ID schematic extractor
│   ├── service.py             # Unified MultimodalEngine orchestrator
│   └── main.py                # Standalone FastAPI server (Port 8003)
├── tests/
│   ├── test_document_ocr.py
│   ├── test_visual_inspection.py
│   ├── test_pid_extraction.py
│   └── test_multimodal_api.py
└── data/sample_documents/
    ├── inspection_report.txt
    ├── sample_flange_corrosion.png
    └── sample_pid_schematic.png
```

---

## 3. Running the Service

Start the FastAPI microservice on port 8003:

```bash
cd sovereign-agentic-ai-workbench
python -m uvicorn multimodal.main:app --host 0.0.0.0 --port 8003 --reload
```

Health Check:

```bash
curl http://localhost:8003/multimodal/health
```

Process a File:

```bash
curl -X POST http://localhost:8003/multimodal/process \
  -H "Content-Type: application/json" \
  -d '{"file_path": "data/sample_documents/inspection_report.txt"}'
```

---

## 4. Running Test Suites

Execute all automated unit and contract tests:

```bash
cd sovereign-agentic-ai-workbench
python -m pytest tests/ -v
```
