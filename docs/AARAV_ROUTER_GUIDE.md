# 🛡️ Aarav's Module — Multi-Model Router, Model Serving & Sovereign Document Generation (PDF Artifact Pipeline)

## Overview

Aarav's module serves two core roles in the **Sovereign AI Workbench**:
1. **Model Router & Model Serving Layer**: Provides a local, configuration-driven routing mechanism that dynamically selects the right local AI model for every user query while ensuring zero external network calls.
2. **Sovereign PDF Generation & Verification Pipeline**: Implements an air-gapped, deterministic PDF generation engine (`backend/documents/pdf_renderer.py`) that converts structured JSON outputs produced by the local LLM pipeline (Qwen) into official, publication-grade `Approval_Note.pdf` artifacts.

---

## 🏗️ Architecture & Component Design

### 1. Multi-Model Router Architecture
```text
                     FastAPI / LangGraph Agent
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │     AARAV ROUTER      │
                     └───────────┬───────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
   Task Classifier        Model Registry          Health Checker
  (Rule-based classification) (model_registry.yaml)   (Urllib check)
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │    Model Selection    │
                     └───────────┬───────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
  Reasoning Model           Coding Model            Vision Model
  (Sarvam / Qwen)          (Qwen2.5-Coder)          (Qwen2.5-VL)
```

### 2. Sovereign PDF Generation & Validation Pipeline
```text
                     Existing AI / LangGraph Agent
                                  │
                                  ▼
           [1] Context Grounding & Tool Results Execution
         (RAG Chunks + MarkItDown Text + Sandboxed Python Calc)
                                  │
                                  ▼
           [2] Local Qwen Ollama Call ("format": "json")
                                  │
                                  ▼
                        Raw JSON Text Output
                                  │
                                  ▼
                        [3] Strict Validation
               json.loads() → PDFApprovalData.model_validate()
                                  │
                                  ▼
                        [4] Dict Handoff
                           model_dump()
                                  │
                                  ▼
                   [5] Local ReportLab Renderer
               (backend/documents/pdf_renderer.py)
                                  │
                                  ▼
                          Approval_Note.pdf
                     (data/outputs/Approval_Note.pdf)
                                  │
                                  ▼
                   [6] Post-Generation Verification
              (pypdf.PdfReader Reopen, Text & Page Check)
                                  │
                                  ▼
               [7] SHA-256 Hash & ArtifactResult
               {filename, path, sha256, validation_status}
```

---

## 📂 Module Structure

```text
backend/router/
├── __init__.py           # Package initializer
├── model_registry.yaml   # Configuration file defining models, tasks, endpoints, and status
├── schemas.py            # Pydantic input/output request and response schemas
├── classifier.py         # Lightweight rule-based task classifier
├── health.py             # Endpoint health checker for Ollama/local endpoints
├── fallback.py           # Compatible fallback handler when primary models are unavailable
├── client.py             # Local model generation client abstraction
└── router.py             # Core ModelRouter orchestrator and history manager

backend/documents/
├── __init__.py           # Package initializer
├── schemas.py            # PDFApprovalData, InspectionFinding, & ArtifactResult schemas
└── pdf_renderer.py       # Deterministic ReportLab renderer and pypdf verification engine

backend/tools/
├── document_tool.py      # generate_pdf_note tool wrapper
└── registry.py           # Central Tool Registry mapping generate_pdf_note

backend/api/
└── router_api.py         # FastAPI routes (POST /route, GET /models, GET /routing/history)
```

---

## ⚙️ How It Works

### A. Multi-Model Router Flow
1. **Request Intake (`POST /route`)**:
   Accepts a `RouteRequest` payload containing the prompt query, `has_image`, `has_file`, or an explicit `task_type`.

2. **Task Classification (`classifier.py`)**:
   - Analyzes keywords and attachment metadata deterministically without relying on external cloud LLMs.
   - Categorizes requests into: `coding`, `debugging`, `document`, `reasoning`, `vision`, `image`, or `general`.

3. **Registry Lookup (`model_registry.yaml`)**:
   - Maps the classified task category to the designated local model (e.g., `qwen-coder` for coding, `qwen-vl` for vision, `qwen-reasoning` for text/reasoning).

4. **Health Verification & Fallback (`health.py`, `fallback.py`)**:
   - Performs lightweight endpoint checks on the targeted model service.
   - If the primary model is unavailable or disabled, it selects a task-compatible fallback model and sets `fallback: true` in the output.

5. **Explanatory Response (`schemas.py`)**:
   - Returns structured JSON containing the chosen model, endpoint, task type, health status, and human-readable explanation (`reason`).

6. **Routing History (`router.py`)**:
   - Maintains a lightweight history log exposed via `GET /routing/history` for visualization in the UI.

---

### B. PDF Generation & Verification Pipeline
1. **Structured Input Generation (`_generate_structured_pdf_data`)**:
   - Synthesizes user query, RAG context, MarkItDown document extractions, and deterministic calculation outputs (`run_code` stdout).
   - Invokes local Qwen model using Ollama's `"format": "json"` mode with strict system prompts forbidding hallucinated measurements or dates.

2. **Strict Schema Validation**:
   - Qwen output is parsed via `json.loads()`.
   - Validated against the `PDFApprovalData` Pydantic schema, including nested `InspectionFinding` models (`Component`, `Nominal`, `Measured`, `Status`).
   - If validation fails, execution halts cleanly and records a failure event without passing corrupt data to the renderer.

3. **Deterministic ReportLab Rendering (`pdf_renderer.py`)**:
   - Converts `PDFApprovalData.model_dump()` into a styled PDF with standard document margins, header metadata, styled sections, and alternating-row inspection tables.
   - Runs 100% locally with zero network calls.

4. **Mandatory Post-Generation Verification**:
   - Immediately re-opens the output `Approval_Note.pdf`.
   - Verifies file existence, size > 0, and page count > 0 using `pypdf.PdfReader`.
   - Extracts Page 1 text to ensure expected header strings (`INDIAN OIL` / `NOTE SHEET`) are present.
   - Computes a SHA-256 cryptographic hash of the PDF binary.

5. **Artifact Result Packaging**:
   - Returns a structured `ArtifactResult` dictionary containing `filename`, `path`, `sha256`, `validation_status` (`"success"` or `"degraded/failed"`), and `warnings`.

---

## 🔌 API Endpoints & Tool Registrations

### 1. `POST /route`
- **Request**:
  ```json
  {
    "query": "Fix this Python function traceback",
    "has_image": false,
    "has_file": false
  }
  ```
- **Response**:
  ```json
  {
    "task_type": "coding",
    "model": "qwen-coder",
    "endpoint": "http://localhost:11434",
    "reason": "Coding/debugging request detected from keyword 'traceback'",
    "fallback": false,
    "healthy": true
  }
  ```

### 2. `GET /models`
- **Response**:
  ```json
  {
    "models": [
      {
        "name": "qwen-reasoning",
        "task": "reasoning",
        "enabled": true,
        "healthy": true,
        "endpoint": "http://localhost:11434"
      },
      {
        "name": "qwen-coder",
        "task": "coding",
        "enabled": true,
        "healthy": true,
        "endpoint": "http://localhost:11434"
      },
      {
        "name": "qwen-vl",
        "task": "vision",
        "enabled": true,
        "healthy": true,
        "endpoint": "http://localhost:11434"
      }
    ]
  }
  ```

### 3. `generate_pdf_note` Tool Call
- **Input Parameters**: `data` (dict following `PDFApprovalData`), `output_filename` (`Approval_Note.pdf`)
- **Output Response**: `ArtifactResult` dictionary:
  ```json
  {
    "filename": "Approval_Note.pdf",
    "file_type": "pdf",
    "path": "C:\\fullstack\\sovereign-agentic-ai-workbench\\data\\outputs\\Approval_Note.pdf",
    "sha256": "e8f7e29ed25375393c24c4b46bd474781c50f8eb46858833768f0199511a1e9b",
    "validation_status": "success",
    "source_evidence_ids": [],
    "warnings": []
  }
  ```

---

## 🚀 How Aarav's Module Helps the Entire Project

1. **Powers Model Selection & Deliverables for LangGraph Agent**:
   - Provides Ankush's agent orchestrator with instantaneous model routing and automates end-to-end PDF deliverable generation.

2. **Supports Roshan's React Frontend & Sovereignty View**:
   - Supplies `/models` and `/routing/history` endpoints to populate the **Model Routing Panel** on the UI.
   - Outputs verified `Approval_Note.pdf` artifacts that show up directly in the UI Deliverables pane.

3. **Ensures Reliability with Zero Cloud Dependency**:
   - Operates 100% locally with zero external API calls, satisfying strict air-gapped sovereignty requirements for confidential industrial environments.

4. **Guarantees Artifact Integrity**:
   - Strict Pydantic validation prevents LLM hallucinations from corrupting document generation.
   - Reopens generated PDFs to confirm structural integrity and calculate cryptographic SHA-256 hashes before reporting success.
