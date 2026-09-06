# 🛡️ Sovereign AI Workbench — SIH 2026

**Smart India Hackathon 2026 | Problem Statement 26117 | Team: Quanta Codes**

> A fully local, multi-model, agentic AI workbench for confidential industrial work that can understand documents/images, use local knowledge, execute tools, generate real deliverables, and provide visible proof that data does not leave the organization's environment.

---

## 1. 📌 Project Overview

The **Sovereign AI Workbench** is an on-premise/air-gapped Agentic AI system designed for confidential industrial environments such as refineries, PSUs, defence manufacturers, and government organizations.

The system is designed around:

- Local/open-weight AI models
- No external LLM/API dependency
- Local RAG over SOPs, manuals, and internal documents
- Multimodal document understanding
- Agentic planning and tool execution
- Sandboxed code execution
- Word/Excel/PPT deliverable generation
- Explainable model routing
- P&ID-aware processing
- Live network/sovereignty monitoring
- Auditable execution traces

The proposed architecture uses **React + Tailwind**, **FastAPI + LangGraph**, local model serving through **vLLM/Ollama**, **ChromaDB** for RAG, **Docling/Tesseract** for document processing, and Docker-based sandboxing.

---

# 2. 🎯 Team Members & Responsibilities

| Member      | Primary Responsibility                         | Branch                             |
| ----------- | ---------------------------------------------- | ---------------------------------- |
| **Ankush**  | Agentic Backend + LangGraph + Integration Lead | `feature/ankush-agent-backend`     |
| **Aarav**   | Multi-Model Router + Model Serving             | `feature/aarav-model-router`       |
| **Krishna** | RAG + Local Knowledge Base                     | `feature/krishna-rag`              |
| **Pankaj**  | Multimodal AI + OCR + P&ID                     | `feature/pankaj-multimodal`        |
| **Roshan**  | React Frontend + Sovereignty Dashboard         | `feature/roshan-frontend-security` |

> **Important:** Each member owns their module, but the final application is one integrated system. Do not independently redesign shared APIs or the agent state without discussing it with the team.

---

# 3. 🏗️ Overall Architecture

```text
                         ┌──────────────────────────────┐
                         │       React + Tailwind       │
                         │          FRONTEND            │
                         │  Chat / Upload / Dashboard   │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │       FastAPI BACKEND        │
                         │                              │
                         │       LangGraph Agent        │
                         └──────┬──────┬──────┬─────────┘
                                │      │      │
              ┌─────────────────┘      │      └─────────────────┐
              ▼                        ▼                        ▼
      ┌───────────────┐       ┌───────────────┐       ┌────────────────┐
      │ Model Router  │       │      RAG      │       │  Multimodal    │
      │    Aarav      │       │    Krishna    │       │     Pankaj     │
      └───────┬───────┘       └───────────────┘       └────────────────┘
              │
       ┌──────┼──────────┐
       ▼      ▼          ▼
    Reasoning Coding   Vision
      Model    Model     Model

                         ┌──────────────────────────────┐
                         │       Local Tools             │
                         │ read/write/run/generate       │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │     Docker Sandbox           │
                         │       --network none         │
                         └──────────────────────────────┘

                         ┌──────────────────────────────┐
                         │ Sovereignty / Network Monitor│
                         │       Roshan + Ankush        │
                         └──────────────────────────────┘
```

---

# 4. 👨‍💻 ANKUSH — Agentic Backend & Integration Lead

## Branch

```bash
feature/ankush-agent-backend
```

## Primary Goal

Build the **brain/orchestrator** of the entire application.

Ankush is responsible for connecting the Router, RAG, Multimodal pipeline, tools, sandbox, and frontend APIs.

## Main Technologies

- Python
- FastAPI
- LangGraph
- Pydantic
- WebSockets where required
- Docker integration
- Python logging

## Responsibilities

### 4.1 FastAPI Backend

Create the central API.

Expected endpoints:

```text
POST /chat
POST /upload
POST /agent/run
GET  /agent/status
GET  /routing
GET  /network/status
GET  /files
```

Suggested structure:

```text
backend/
├── main.py
├── config.py
├── api/
│   ├── chat.py
│   ├── upload.py
│   ├── agent.py
│   └── status.py
├── agent/
│   ├── graph.py
│   ├── state.py
│   ├── nodes.py
│   └── prompts.py
├── tools/
│   ├── file_tool.py
│   ├── code_tool.py
│   └── document_tool.py
└── services/
```

### 4.2 LangGraph Agent

Implement:

```text
User Request
     ↓
Understand
     ↓
Plan
     ↓
Select Tool
     ↓
Execute
     ↓
Observe
     ↓
Reflect
     ↓
 ┌───┴────┐
 │        │
Loop    Finish
```

Required nodes:

```text
planner
router
tool_selector
tool_executor
reflection
finalizer
```

### 4.3 Shared Agent State

Create a common state object:

```python
class AgentState(TypedDict):
    user_query: str
    uploaded_file: str | None
    task_type: str
    selected_model: str
    routing_reason: str
    context: list
    tool_calls: list
    tool_results: list
    final_response: str
    generated_files: list
    audit_log: list
```

All other modules should work with this contract.

### 4.4 Tools

Integrate:

```text
read_file
write_file
search_knowledge_base
run_code
edit_spreadsheet
generate_docx
generate_pptx
ocr_document
```

### 4.5 Audit Trace

Every important operation should be logged:

```json
{
  "step": "RAG",
  "action": "search_knowledge_base",
  "status": "success"
}
```

The frontend will display this trace.

## Ankush Deliverables

- Working FastAPI server
- LangGraph agent
- Shared AgentState
- Tool interface
- Audit logging
- API documentation
- Integration of all modules
- Final merge coordination
- End-to-end testing

## Definition of Done

Ankush's module is complete when:

- FastAPI starts successfully
- `/chat` works
- LangGraph executes a multi-step task
- Tools can be called
- Tool results return to the graph
- Agent can loop/refine
- Audit events are generated
- Router/RAG/Multimodal services can be plugged in

---

# 5. 🧠 AARAV — Multi-Model Router & Model Serving

## Branch

```bash
feature/aarav-model-router
```

## Primary Goal

Build the **Model Router** that automatically decides which local AI model should handle a request.

The project needs multiple models and transparent routing.

## Main Technologies

- Python
- vLLM / Ollama
- OpenAI-compatible local APIs where applicable
- YAML/JSON
- Classification logic
- HTTP clients

## Models

Target architecture:

```text
Reasoning / Document → Sarvam-30B or Qwen
Coding              → Qwen2.5-Coder
Vision              → Qwen2.5-VL
```

Hardware limitations should determine the final model sizes.

## 5.1 Model Registry

Create:

```text
router/model_registry.yaml
```

Example:

```yaml
models:
  reasoning:
    name: sarvam
    endpoint: http://localhost:8001
    tasks:
      - reasoning
      - document
      - general

  coding:
    name: qwen-coder
    endpoint: http://localhost:8002
    tasks:
      - coding
      - debugging

  vision:
    name: qwen-vl
    endpoint: http://localhost:8003
    tasks:
      - vision
      - image
      - document
```

## 5.2 Task Classification

Example:

```text
"Fix this Python error"
        ↓
      CODING
        ↓
 Qwen Coder
```

```text
"Summarize this SOP"
        ↓
    DOCUMENT
        ↓
Reasoning Model
```

```text
"Read this P&ID"
        ↓
     VISION
        ↓
Qwen-VL
```

## 5.3 Routing Explanation

Every routing decision must provide a reason:

```json
{
  "task": "coding",
  "model": "Qwen-Coder",
  "reason": "Request contains Python code and a traceback"
}
```

This will be shown in the frontend.

## 5.4 Router API

Expose:

```text
POST /route
GET /models
GET /routing/history
```

Input:

```json
{
  "query": "Fix this Python code",
  "has_image": false,
  "has_file": true
}
```

Output:

```json
{
  "task": "coding",
  "model": "qwen-coder",
  "endpoint": "http://localhost:8002",
  "reason": "Coding request detected"
}
```

## Aarav Deliverables

- Local model serving
- Model registry
- Task classifier
- Router
- Routing reason
- Router API
- Model health check
- Fallback model handling
- Capability-aware routing for text, vision, OCR escalation, coding, and document generation
- One shared routing contract used by the LangGraph agent and frontend
- Verified model availability from the local Ollama/vLLM registry
- Selected model propagation from routing through final generation
- Local-only network validation for every model endpoint

## Definition of Done

- At least 2 local models work
- Router correctly identifies basic task types
- Routing decision is returned as structured JSON
- Model can be changed through configuration
- Backend can call the router
- No cloud LLM dependency
- The selected model is actually used by the generation client
- Vision tasks are routed to a vision-capable model and coding tasks to a coding-capable model
- Unavailable models produce a visible local fallback decision
- Router tests prove that no external endpoint is contacted

---

# 6. 📚 KRISHNA — RAG & Local Knowledge Base

## Branch

```bash
feature/krishna-rag
```

## Primary Goal

Build the **local knowledge system** that allows the AI to answer using organizational SOPs, manuals, and documents.

## Main Technologies

- Python
- ChromaDB
- bge-m3 / Qwen embeddings
- Document loaders
- Chunking
- Retrieval

## 6.1 Document Ingestion

Input:

```text
SOP.pdf
Manual.pdf
Safety.pdf
Inspection_Report.pdf
```

Pipeline:

```text
Documents
   ↓
Text Extraction
   ↓
Cleaning
   ↓
Chunking
   ↓
Embeddings
   ↓
ChromaDB
```

## 6.2 Chunking

Store metadata:

```json
{
  "source": "safety_manual.pdf",
  "page": 12,
  "section": "Emergency Procedure"
}
```

This allows citations.

## 6.3 Retrieval

Function:

```python
search_knowledge_base(query)
```

Expected result:

```json
{
  "documents": [
    {
      "text": "...",
      "source": "SOP.pdf",
      "page": 12,
      "score": 0.87
    }
  ]
}
```

## 6.4 RAG Pipeline

```text
User Question
      ↓
Query Embedding
      ↓
ChromaDB
      ↓
Top-K Documents
      ↓
Context
      ↓
Reasoning Model
      ↓
Grounded Answer
```

## 6.5 Citation System

The answer should identify the source:

```text
According to Safety SOP...

Source:
Safety_SOP.pdf — Page 12
```

## Krishna Deliverables

- Document ingestion pipeline
- Chunking system
- Embedding system
- ChromaDB setup
- Retriever
- Metadata/citation system
- RAG API
- Sample knowledge base

## Definition of Done

- 5–10 sample documents indexed
- Search returns relevant chunks
- Metadata is preserved
- Source citations are returned
- FastAPI/agent can call RAG
- Everything works locally

---

# 7. 👁️ PANKAJ — Multimodal AI, OCR & P&ID

## Branch

```bash
feature/pankaj-multimodal
```

## Primary Goal

Build the system that understands:

- Scanned PDFs
- Photos
- Handwriting
- Industrial drawings
- P&IDs
- Tables
- Visual information

## Main Technologies

- Python
- Docling
- Tesseract
- Qwen2.5-VL
- OpenCV
- YOLO/object detection if feasible

## 7.1 Document Pipeline

```text
PDF / Image
     ↓
  Docling
     ↓
Layout + Text
     ↓
 OCR if required
     ↓
 Qwen-VL
     ↓
Structured JSON
```

## 7.2 OCR

Create:

```python
ocr_document(file)
```

Output:

```json
{
  "text": "...",
  "pages": 3,
  "tables": [],
  "confidence": 0.91
}
```

## 7.3 Vision Understanding

Input:

```text
inspection.jpg
```

Output:

```json
{
  "type": "inspection_report",
  "findings": ["Corrosion observed", "Valve requires inspection"],
  "values": []
}
```

## 7.4 P&ID Feature

This is one of the team's major uniqueness features.

Pipeline:

```text
P&ID Image
    ↓
Symbol / Tag Detection
    ↓
Equipment + Instrument Tags
    ↓
Qwen-VL
    ↓
Interpretation
    ↓
Structured JSON
```

Example:

```json
{
  "equipment": [
    {
      "tag": "P-101",
      "type": "Pump"
    }
  ],
  "instruments": [
    {
      "tag": "PT-201",
      "type": "Pressure Transmitter"
    }
  ]
}
```

If a full YOLO detector is too time-consuming, implement a simpler demonstrable P&ID extraction pipeline first and treat advanced detection as an enhancement.

## Pankaj Deliverables

- Docling integration
- OCR pipeline
- Vision model integration
- Image preprocessing
- Structured output schema
- P&ID prototype
- Multimodal API

## Definition of Done

- Scanned PDF can be processed
- Image can be understood
- OCR output is available
- Vision model receives image data
- Structured JSON is returned
- Agent can call the multimodal pipeline

---

# 8. 🎨 ROSHAN — Local Ollama Models + Frontend + Sovereignty Dashboard

## Branch

```bash
feature/roshan-local-models-frontend
```

## Primary Goal

Roshan owns the **local Ollama AI environment on his laptop** and the **React frontend**.

The two Qwen models downloaded on Roshan's laptop are:

```text
1. Qwen Text Model
2. Qwen Vision Model
```

Roshan must make sure both models work locally through Ollama and are accessible to the project backend.

He also owns the user-facing interface, including the chat, file upload, model information, agent trace, generated files, and sovereignty dashboard.

> **Important separation:** Roshan owns the local Ollama setup and frontend. Aarav owns the model-routing logic. Pankaj owns the multimodal/OCR pipeline. Ankush owns LangGraph and backend orchestration.

---

## Main Technologies

- Ollama
- Qwen Text Model
- Qwen Vision Model
- React
- Tailwind CSS
- JavaScript/TypeScript
- REST API
- WebSocket where required
- Localhost networking

---

## 8.1 Ollama Setup

Roshan must install and configure Ollama on his laptop.

Target setup:

```text
                         ROSHAN LAPTOP
                              │
                         ┌────▼────┐
                         │ Ollama  │
                         └────┬────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
          Qwen Text Model            Qwen Vision Model
                 │                         │
          Text / reasoning          Image understanding
                 │                         │
                 └────────────┬────────────┘
                              │
                         Local API
                              │
                              ▼
                         FastAPI Backend
```

### Roshan must:

1. Install Ollama.
2. Download the agreed Qwen text model.
3. Download the agreed Qwen vision model.
4. Verify both models using Ollama.
5. Test text generation.
6. Test image/vision input.
7. Record the exact model names/tags.
8. Verify the Ollama local API.
9. Share the model names and setup steps with the entire team.

Check installed models:

```bash
ollama list
```

Test the text model:

```bash
ollama run <QWEN_TEXT_MODEL>
```

Test the vision model:

```bash
ollama run <QWEN_VISION_MODEL>
```

Replace the placeholders with the exact model tags actually installed.

---

## 8.2 Ollama Configuration

Keep the Ollama configuration in one place.

Example:

```yaml
ollama:
  base_url: http://localhost:11434

models:
  text:
    name: <QWEN_TEXT_MODEL>

  vision:
    name: <QWEN_VISION_MODEL>
```

Do not hard-code model names in multiple Python files.

The team should be able to change the model by editing configuration.

---

## 8.3 Text Model Responsibility

Roshan is responsible for ensuring that the Qwen text model can be called locally.

Test:

```text
Prompt
  ↓
Ollama
  ↓
Qwen Text Model
  ↓
Response
```

Create a small test script if required:

```text
tests/
└── test_ollama_text.py
```

The test should verify:

- Ollama is running.
- Model exists.
- Prompt can be sent.
- Response is received.
- No external LLM API is required.

---

## 8.4 Vision Model Responsibility

Roshan is also responsible for the Qwen vision model environment.

Test:

```text
Image
  ↓
Ollama
  ↓
Qwen Vision Model
  ↓
Description / extracted information
```

Use test images such as:

- Normal photograph
- Scanned document
- Inspection image
- Sample P&ID

Pankaj will build the complete OCR/multimodal pipeline. Roshan's responsibility is to ensure the **vision model itself is installed, running, and accessible through Ollama**.

---

## 8.5 Handoff to Other Members

Roshan must give the following information to Ankush and Aarav:

```text
Ollama Base URL:
http://localhost:11434

Text Model:
<exact installed model tag>

Vision Model:
<exact installed model tag>
```

Also provide the commands needed to reproduce the setup.

Example:

```text
Install Ollama
↓
Download text model
↓
Download vision model
↓
ollama list
↓
Run both models
↓
Verify local API
```

---

# 8.6 React Frontend

After the local Ollama environment is working, Roshan builds the main user interface.

Required screens/components:

```text
Dashboard
Chat
File Upload
Agent Trace
Model Routing
RAG Sources
Generated Files
Network Status
```

Suggested UI:

```text
┌──────────────────────────────────────────────┐
│       SOVEREIGN AI WORKBENCH                │
├───────────────────────┬──────────────────────┤
│                       │ MODEL ROUTING         │
│ Chat                  │ Model: Qwen          │
│                       │ Type: Vision/Text    │
│ User: Analyze report  │ Reason: ...          │
│                       │ Execution: LOCAL     │
│ AI: ...               ├──────────────────────┤
│                       │ AGENT TRACE           │
│                       │ ✓ Planning            │
│                       │ ✓ Router              │
│                       │ ✓ RAG                 │
│                       │ ✓ Tool execution      │
│                       │ ✓ Final response      │
│                       ├──────────────────────┤
│                       │ 🔒 SOVEREIGNTY        │
│                       │ External: 0           │
│                       │ Local: Active         │
└───────────────────────┴──────────────────────┘
```

---

# 8.7 Model Routing Panel

Aarav provides the actual routing decision.

Roshan displays it.

Example:

```text
MODEL ROUTING

Selected Model:
Qwen Text

Task:
Document

Reason:
Document request detected

Execution:
LOCAL ✓
```

Vision example:

```text
MODEL ROUTING

Selected Model:
Qwen Vision

Task:
Vision

Reason:
Image attachment detected

Execution:
LOCAL ✓
```

**Do not implement routing logic in the frontend.**

---

# 8.8 Agent Trace

Ankush's backend/LangGraph will produce the agent events.

Roshan displays them:

```text
AGENT TRACE

✓ User request received
✓ Task classified
✓ Model selected
✓ Knowledge base searched
✓ Tool executed
✓ Result verified
✓ Deliverable generated
```

Roshan should focus on visualization rather than implementing the LangGraph logic.

---

# 8.9 Sovereignty Dashboard

Build a visible security/sovereignty panel.

Example:

```text
NETWORK STATUS

External Connections: 0

Local Connections: 4

Internet Access: BLOCKED

AI Models:
LOCAL ✓

Data Processing:
LOCAL ONLY ✓
```

If the backend exposes:

```http
GET /network/status
```

the frontend should consume the endpoint and display the returned values.

The dashboard is intended to make the project's **zero-external-call claim visible during the SIH demo**.

---

# 8.10 Generated Files

Display files returned by the backend:

```text
GENERATED FILES

📄 Approval_Note.docx
📊 Calculation.xlsx
📑 Report.pptx
```

Provide buttons such as:

```text
[Open]
[Download]
```

The actual document generation belongs to the backend/tooling side; Roshan owns the presentation of the generated files.

---

# 8.11 Frontend API Integration

Roshan integrates React with Ankush's FastAPI backend.

Expected endpoints:

```text
POST /chat
POST /upload
POST /agent/run
GET  /routing
GET  /network/status
GET  /files
```

Flow:

```text
React
  ↓
FastAPI
  ↓
Agent / Router / RAG / Multimodal
  ↓
Response
  ↓
React Dashboard
```

Roshan must coordinate with Ankush before changing API request/response formats.

---

# 8.12 Suggested Frontend Structure

```text
frontend/
├── src/
│   ├── components/
│   │   ├── Chat.jsx
│   │   ├── FileUpload.jsx
│   │   ├── AgentTrace.jsx
│   │   ├── ModelRouting.jsx
│   │   ├── Sources.jsx
│   │   ├── GeneratedFiles.jsx
│   │   └── NetworkStatus.jsx
│   │
│   ├── pages/
│   │   └── Dashboard.jsx
│   │
│   ├── services/
│   │   └── api.js
│   │
│   └── App.jsx
│
└── package.json
```

---

# 8.13 Roshan Deliverables

## Local AI

- [ ] Ollama installed
- [ ] Qwen text model downloaded
- [ ] Qwen vision model downloaded
- [ ] Text model tested
- [ ] Vision model tested
- [ ] Exact model names documented
- [ ] Ollama API verified
- [ ] Setup instructions documented

## Frontend

- [ ] React application
- [ ] Tailwind UI
- [ ] Dashboard
- [ ] Chat interface
- [ ] File upload
- [ ] Agent trace
- [ ] Model routing panel
- [ ] RAG source display
- [ ] Generated-file display
- [ ] Network status panel
- [ ] FastAPI integration

## Integration

- [ ] React → FastAPI works
- [ ] FastAPI → Ollama works
- [ ] Qwen text model works locally
- [ ] Qwen vision model works locally
- [ ] Routing information appears in UI
- [ ] Agent trace appears in UI
- [ ] Network status appears in UI

---

# 8.14 Definition of Done

Roshan's module is complete when the following flow works:

```text
User
 ↓
React UI
 ↓
FastAPI
 ↓
Ollama
 ├── Qwen Text ✓
 └── Qwen Vision ✓
 ↓
Response
 ↓
React UI
```

And the UI can show:

```text
✓ User request
✓ Selected model
✓ Agent progress
✓ RAG sources
✓ Generated files
✓ Local execution
✓ Network status
```

# 9. 🔗 Shared API Contract

Everyone MUST follow these common contracts.

## Chat

```http
POST /chat
```

Request:

```json
{
  "message": "Summarize this document",
  "file_id": null
}
```

Response:

```json
{
  "response": "...",
  "task_type": "document",
  "model": "reasoning",
  "routing_reason": "Document summarization request",
  "sources": [],
  "files": [],
  "trace": []
}
```

---

## Routing

```http
POST /route
```

```json
{
  "task_type": "coding",
  "model": "qwen-coder",
  "reason": "Coding request detected"
}
```

---

## RAG

```http
POST /rag/search
```

```json
{
  "query": "What is the emergency shutdown procedure?"
}
```

Response:

```json
{
  "results": [
    {
      "text": "...",
      "source": "Safety_SOP.pdf",
      "page": 12,
      "score": 0.91
    }
  ]
}
```

---

## Multimodal

```http
POST /multimodal/process
```

Response:

```json
{
  "type": "inspection_report",
  "text": "...",
  "findings": [],
  "entities": []
}
```

---

## Network

```http
GET /network/status
```

Response:

```json
{
  "external_connections": 0,
  "local_connections": 4,
  "internet_blocked": true
}
```

---

# 10. 📂 Recommended Repository Structure

```text
sovereign-ai-workbench/
│
├── backend/
│   ├── main.py
│   ├── api/
│   ├── agent/
│   ├── router/
│   ├── rag/
│   ├── multimodal/
│   ├── tools/
│   └── services/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── hooks/
│   └── package.json
│
├── data/
│   ├── documents/
│   ├── images/
│   └── sample_pid/
│
├── models/
│
├── docker/
│
├── tests/
│
├── docs/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 11. 🌿 Git Workflow

## Clone Repository

```bash
git clone <GITHUB_REPOSITORY_URL>
cd sovereign-ai-workbench
```

## Create Your Branch

### Ankush

```bash
git checkout -b feature/ankush-agent-backend
```

### Aarav

```bash
git checkout -b feature/aarav-model-router
```

### Krishna

```bash
git checkout -b feature/krishna-rag
```

### Pankaj

```bash
git checkout -b feature/pankaj-multimodal
```

### Roshan

```bash
git checkout -b feature/roshan-frontend-security
```

---

# 12. 📤 Commit Rules

Use meaningful commits.

Good:

```bash
git commit -m "feat: add LangGraph agent"
git commit -m "feat: implement model router"
git commit -m "feat: add ChromaDB retrieval"
git commit -m "feat: integrate OCR pipeline"
git commit -m "feat: add network status dashboard"
```

Avoid:

```bash
git commit -m "done"
git commit -m "changes"
git commit -m "final"
```

---

# 13. 🚀 Push Your Branch

```bash
git add .
git commit -m "feat: implement <your feature>"
git push origin <your-branch>
```

Example:

```bash
git push origin feature/krishna-rag
```

Then create a **Pull Request** into:

```text
main
```

---

# 14. ⚠️ Important Git Rules

### Rule 1 — Don't directly push to main

Only merge through Pull Requests.

### Rule 2 — Don't modify another person's module without discussion

For example:

```text
Krishna → owns rag/
Pankaj  → owns multimodal/
Aarav   → owns router/
```

### Rule 3 — Shared files require communication

Be careful with:

```text
requirements.txt
docker-compose.yml
.env.example
main.py
AgentState
README.md
```

### Rule 4 — Pull before starting new work

```bash
git checkout main
git pull origin main
```

Then update your branch.

### Rule 5 — Test before Pull Request

```bash
pytest
```

and make sure your service starts.

---

# 15. 🔄 Integration Strategy

The modules should eventually connect like this:

```text
                       USER
                         │
                         ▼
                  React Frontend
                     Roshan
                         │
                         ▼
                    FastAPI
                     Ankush
                         │
                         ▼
                  LangGraph Agent
                     Ankush
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
           Router       RAG      Multimodal
           Aarav       Krishna      Pankaj
              │          │          │
              └──────────┼──────────┘
                         ▼
                    Local Models
                         │
                         ▼
                  Local Tools
                         │
                         ▼
                  Docker Sandbox
                         │
                         ▼
                 Final Deliverable
                         │
                         ▼
                  Audit + Network
                       Status
```

---

# 16. 🧪 Testing Responsibilities

## Ankush

Integration tests:

```text
Frontend → API → Agent → Tool → Response
```

## Aarav

Test:

```text
Coding → Coding Model
Document → Reasoning Model
Image → Vision Model
```

## Krishna

Test:

```text
Document → Embedding → ChromaDB → Relevant Context
```

## Pankaj

Test:

```text
Image → OCR/Vision → Structured Output
```

## Roshan

Test:

```text
Upload → API
Chat → API
Trace → UI
Network status → UI
```

---

# 17. 🏆 Final SIH Demo Flow

The team should demonstrate one complete scenario rather than showing disconnected features.

## Scenario

```text
1. Upload scanned inspection report
             ↓
2. Pankaj's OCR/Vision pipeline processes it
             ↓
3. Ankush's LangGraph agent creates a plan
             ↓
4. Aarav's router selects the appropriate model
             ↓
5. Krishna's RAG searches the local SOP/manual
             ↓
6. Agent combines findings + SOP information
             ↓
7. Tool generates approval Word document
             ↓
8. Agent verifies the result
             ↓
9. Roshan's UI displays the complete trace
             ↓
10. Sovereignty panel shows:
        External Connections = 0
```

This maps directly to the proposed SIH demo path: scanned inspection report → OCR/Vision → agent plan → RAG/tool calls → verified Word approval note → live network proof.

---

# 18. ⭐ Priority Levels

## 🔴 MUST HAVE

Everyone should prioritize these first.

### Ankush

- FastAPI
- LangGraph
- Agent loop
- Tool calling

### Aarav

- 2 local models
- Basic router
- Routing explanation

### Krishna

- ChromaDB
- Document ingestion
- Retrieval
- Citations

### Pankaj

- OCR
- Vision model
- Scanned document processing

### Roshan

- Chat UI
- File upload
- Agent trace
- Routing panel

---

## 🟡 SHOULD HAVE

- Third model
- DOCX generation
- Excel generation
- Network dashboard
- Better RAG
- Better OCR
- Docker sandbox

---

## 🟢 ADVANCED / IF TIME ALLOWS

- Sarvam-30B integration
- P&ID symbol detector
- Advanced routing classifier
- PPT generation
- Advanced network telemetry
- Better UI animations
- Full offline/air-gapped demo

The project plan itself recommends starting with a small demo-ready local stack and then adding RAG, agent tools, P&ID parsing, and sovereignty proof as high-value differentiators.

---

# 19. 📅 Suggested 5-Day Team Plan

## DAY 1 — Foundation

**Ankush**

- FastAPI
- LangGraph skeleton

**Aarav**

- Local models
- Model serving

**Krishna**

- ChromaDB
- Sample documents

**Pankaj**

- Docling
- Tesseract
- Qwen-VL setup

**Roshan**

- React
- Dashboard skeleton

---

## DAY 2 — Individual Modules

**Ankush**

- Agent nodes
- Tool interface

**Aarav**

- Router
- Classification

**Krishna**

- Retrieval
- Citations

**Pankaj**

- OCR + Vision

**Roshan**

- Chat
- Upload
- Routing UI

---

## DAY 3 — Integration

```text
Frontend
   ↓
FastAPI
   ↓
LangGraph
   ↓
Router + RAG + Vision
```

Everyone fixes integration problems.

---

## DAY 4 — Differentiators

Add:

```text
✓ Sovereignty dashboard
✓ Routing explanation
✓ P&ID prototype
✓ Docker sandbox
✓ DOCX generation
✓ Audit trace
```

---

## DAY 5 — Demo Hardening

Run the exact demo repeatedly.

Prepare:

```text
✓ Sample scanned report
✓ Sample SOP
✓ Sample P&ID
✓ Coding task
✓ Generated Word document
✓ Network proof
✓ Backup demo/video
```

---

# 20. 🧑‍🤝‍🧑 Team Ownership Summary

```text
ANKUSH
↓
"The Brain"
FastAPI + LangGraph + Agent + Integration

AARAV
↓
"The Model Manager"
vLLM/Ollama + Router + Model Selection

KRISHNA
↓
"The Memory"
ChromaDB + Embeddings + RAG + Citations

PANKAJ
↓
"The Eyes"
OCR + Vision + P&ID + Multimodal

ROSHAN
↓
"The Interface & Security View"
React + Dashboard + Network/Sovereignty UI
```

---

# 21. 🎯 Final Goal

The five modules must become **one product**, not five separate projects.

The final system should demonstrate:

```text
CONFIDENTIAL INPUT
        ↓
LOCAL AI
        ↓
UNDERSTAND
        ↓
ROUTE
        ↓
RETRIEVE
        ↓
PLAN
        ↓
ACT
        ↓
VERIFY
        ↓
DELIVER
        ↓
AUDIT
        ↓
PROVE ZERO EXTERNAL CALLS
```

**The most important rule for the team: build independently, but integrate continuously.**

---

# 22. 🚀 Complete Implementation Workflow — Problem Statement 26117

This is the implementation contract for the final product. OCR, routing, RAG, agent execution, file generation, and sovereignty proof must be delivered as one connected workflow.

## 22.1 Required End-to-End Flow

```text
Upload scanned inspection PDF or image
  ↓
Validate, quarantine, hash, and identify file type
  ↓
Native PDF extraction or local page rasterization
  ↓
Local OCR for printed text and English printed handwriting
  ↓
Low-confidence regions sent to local vision model
  ↓
Structured evidence with page, region, unit, and confidence
  ↓
Aarav's local model router selects the capable model
  ↓
LangGraph agent plans the task
  ↓
Local RAG retrieves SOPs, manuals, and standards
  ↓
Inspection facts and measurements are normalized
  ↓
Deterministic engineering calculation in Docker sandbox
  ↓
Validation and contradiction check
  ↓
Approval or human-review checkpoint
  ↓
Generate verified PDF, DOCX, and XLSX deliverables
  ↓
Final response with citations, calculations, files, and trace
  ↓
Enforced network policy and audit proof
```

The first demo scope is English printed text and English printed handwriting. Indian-language handwriting is out of scope for the first release and must be reported as unsupported rather than silently misread.

## 22.2 Shared Contracts

Before integration, Ankush, Aarav, Krishna, Pankaj, and Roshan must agree on these typed objects:

```text
DocumentPage
  page_number, text, tables, regions, confidence, extraction_method

EvidenceItem
  evidence_id, source_file, page, region, field_name, value, unit, confidence

InspectionData
  equipment_tag, nominal_thickness, measured_thickness,
  minimum_allowable_thickness, corrosion_rate, operating_pressure,
  source_evidence_ids, validation_status

CalculationResult
  formula, inputs, units, outputs, compliance_status,
  execution_environment, source_evidence_ids

RoutingDecision
  task, model_tag, endpoint, capabilities, healthy,
  fallback_used, reason, local_only

ArtifactResult
  filename, file_type, path, sha256, validation_status,
  source_evidence_ids, warnings
```

`AgentState` must carry these structured objects. Do not pass important measurements, citations, or routing data only as unvalidated strings.

## 22.3 Build Order

### Step 1 — Secure file intake

Owner: Ankush, with Roshan integration.

- Generate server-side file IDs.
- Store the original filename as metadata only.
- Enforce file size and type limits.
- Allow PDF, PNG, JPG, JPEG, TXT, DOCX, XLSX, and PPTX.
- Quarantine uploads before processing.
- Store SHA-256, MIME type, and processing status.
- Reject path traversal and unsupported files.

`POST /upload` must return a server ID, stored path, hash, file type, and quarantine status.

### Step 2 — Canonical document understanding

Owner: Pankaj. Aarav supplies model capabilities. Ankush integrates the service.

Use one active pipeline for all PDFs and images. It must:

1. Detect file type.
2. Extract native PDF text and tables.
3. Detect scanned or low-text pages.
4. Rasterize scanned pages locally.
5. Run local OCR page by page.
6. Detect handwriting and low-confidence regions.
7. Escalate those regions to the local vision model.
8. Merge OCR and vision results with page and region provenance.
9. Extract tags, measurements, findings, dates, and recommendations.
10. Return confidence and extraction method for every field.

Create or consolidate around:

```text
backend/documents/schemas.py
backend/documents/understanding.py
backend/documents/provenance.py
backend/documents/pdf_renderer.py
```

### Step 3 — Aarav's model-routing assignment

Owner: **Aarav — Multi-Model Router, Local Model Serving, and Capability Integration**.

Aarav must deliver:

```text
[ ] One configuration-driven model registry.
[ ] Deterministic classification for coding, document, reasoning, vision, OCR escalation, and general tasks.
[ ] Local Ollama/vLLM health and installed-model checks.
[ ] Capability-aware fallback selection.
[ ] Rejection of non-local endpoints and cloud URLs.
[ ] Structured RoutingDecision response.
[ ] POST /route, GET /models, and GET /routing/history.
[ ] Generation client that accepts the selected model tag.
[ ] Selected model propagation into AgentState and final generation.
[ ] Routing reason and fallback status in the audit trace.
[ ] Tests for coding, document, vision, escalation, fallback, and endpoint rejection.
[ ] Docker GPU-server preload instructions.
```

Registry shape:

```yaml
models:
  text:
    tag: qwen2.5:7b-instruct
    endpoint: http://ollama:11434
    capabilities: [reasoning, document, general, summarization]
    enabled: true
  vision:
    tag: qwen2.5vl:7b
    endpoint: http://ollama:11434
    capabilities: [vision, image, ocr, pid, handwriting_escalation]
    enabled: true
  coding:
    tag: qwen2.5-coder:latest
    endpoint: http://ollama:11434
    capabilities: [coding, debugging, code_generation]
    enabled: true
```

Required route response:

```json
{
  "task": "vision",
  "model_tag": "qwen2.5vl:7b",
  "endpoint": "http://ollama:11434",
  "capabilities": ["vision", "ocr", "handwriting_escalation"],
  "healthy": true,
  "fallback_used": false,
  "reason": "Scanned image requires visual interpretation",
  "local_only": true
}
```

Aarav must update and integrate:

```text
backend/router/router.py
backend/router/classifier.py
backend/router/client.py
backend/router/health.py
backend/router/fallback.py
backend/router/model_registry.yaml
backend/services/router_service.py
backend/api/router_api.py
backend/agent/nodes.py
config/ollama_config.yaml
```

The selected model tag must reach the actual local generation call. No module may replace it with a hard-coded model name. Aarav must not implement document rendering or engineering calculations.

Aarav's definition of done:

```text
Coding request → configured coding model
SOP/document request → configured text model
Scanned image/P&ID → configured vision model
Low OCR confidence → visible vision escalation
Unavailable primary → healthy local fallback
Non-local endpoint → rejected before execution
/models → real health status
/routing/history → decision and reason
All routing tests pass without internet
```

### Step 4 — Local RAG and evidence grounding

Owner: Krishna, integrated by Ankush.

- Ingest SOPs, manuals, standards, and sample correspondence locally.
- Persist embeddings in local ChromaDB.
- Return source, page, section, and score metadata.
- Assign reusable evidence IDs.
- Preserve evidence into calculations, responses, and generated artifacts.
- Never use cloud embeddings or hosted vector databases.

### Step 5 — Replace synthetic inspection data

Owner: Ankush and Pankaj, with Aarav model support.

Remove hard-coded FL-402 measurements, financial values, risk statements, and recommendations from the active workflow. Populate `InspectionData` from the uploaded document and evidence store.

Required fields:

```text
Equipment/component tag
Nominal thickness
Measured thickness
Minimum allowable thickness
Corrosion rate
Operating pressure
Inspection date
Observed defect
Recommended action
```

Rules:

- Never invent missing values.
- Preserve original and normalized units.
- Mark conflicting values for review.
- Separate extracted facts from model inferences.
- Block approval-note generation below the confidence threshold.

### Step 6 — Deterministic calculation sandbox

Owner: Ankush, with Docker support.

The LLM may explain a formula, but deterministic code must calculate the result. The sandbox must use Docker with no network, non-root execution, read-only root filesystem, dropped capabilities, resource limits, isolated temporary storage, explicit mounts, and no runtime image pulling. Fail closed when isolation is unavailable.

Every result must include formula, inputs, units, output, compliance status, execution environment, and evidence IDs.

### Step 7 — Generate real PDF and office artifacts

Owner: Ankush, with Roshan for display and downloads.

Required main-demo outputs:

```text
Approval_Note.pdf
Approval_Note.docx
Calculation.xlsx
```

Optional: `Executive_Brief.pptx`.

Qwen must produce structured content, not PDF bytes. Use a deterministic local PDF renderer such as ReportLab or a pinned local HTML-to-PDF renderer. Reopen every generated artifact and verify its type, headings, tables, measurements, calculations, citations, and non-empty content. A degraded fallback must be reported as degraded, not successful.

### Step 8 — Conditional agent workflow

Owner: Ankush.

Replace the current strictly linear graph with:

```text
planner
  ↓
understand_document → retrieve_evidence → extract_structured_data
  ↓
calculate → validate
  ├── missing/contradictory → request review
  ├── low confidence → OCR/vision escalation
  └── valid → approval checkpoint
       ↓
       generate_artifacts
       ↓
       verify_artifacts
       ├── failure → repair/regenerate
       └── success → finalizer
```

Persist jobs by ID. Do not use one global last-state object for concurrent users. The UI must display the current stage, warnings, approval state, and artifact verification state.

### Step 9 — Enforce sovereignty

Owner: Roshan and Ankush, with Aarav validating model endpoints.

- Preload models before the air-gapped demo.
- Disable model pulls during runtime.
- Use Docker default-deny networking.
- Permit only required internal destinations.
- Reject public URLs in model, OCR, embedding, and rendering configuration.
- Log allowed and denied egress attempts.
- Monitor backend, Ollama, workers, and sandbox processes.
- Export a hash-verified audit record.

The UI must distinguish observed connections from enforced policy:

```text
Observed external connections: 0
Enforced external egress policy: ACTIVE
Denied external attempts: 0
Local services: backend, Ollama, ChromaDB, sandbox
```

### Step 10 — Frontend integration

Owner: Roshan, with Ankush API support.

The final demo must run with `VITE_USE_MOCK=false` and display upload status, agent stage, routing decision, selected model, evidence citations, calculation inputs/outputs, approval state, generated files, artifact verification, full trace, and enforced sovereignty status.

## 22.4 Required Fixtures and Tests

Create local fixtures:

```text
tests/fixtures/scanned_inspection.pdf
tests/fixtures/handwritten_inspection.png
tests/fixtures/sample_pid.png
tests/fixtures/safety_sop.txt
```

Required tests:

```text
Upload → validation → stored file
Scanned PDF → page text, tables, confidence, provenance
Handwritten image → OCR/vision escalation → structured text
P&ID image → tags and confidence
Coding/document/vision → correct local model
Inspection evidence → deterministic calculation
Missing/contradictory evidence → approval blocked
Calculation → PDF/DOCX/XLSX
Generated files → reopened and verified
Sandbox → network/filesystem escape blocked
External endpoint → rejected
Audit → local-only proof exported
Frontend mock disabled → real workflow succeeds
```

## 22.5 Final Acceptance Checklist

```text
[ ] Docker starts with preloaded local models.
[ ] Runtime requires no model download.
[ ] Scanned inspection PDF is understood locally.
[ ] English printed handwriting is processed or clearly flagged with confidence.
[ ] P&ID image produces structured tags.
[ ] Document, coding, and vision routing is visible.
[ ] RAG returns local citations.
[ ] Agent uses extracted values rather than hard-coded FL-402 data.
[ ] Calculation runs in an isolated sandbox.
[ ] Missing or contradictory measurements block approval generation.
[ ] PDF, DOCX, and XLSX deliverables are generated and verified.
[ ] Artifacts include evidence and calculation references.
[ ] Audit trace shows every important operation.
[ ] Network policy is enforced, not only observed.
[ ] Complete demo runs repeatedly from a clean deployment.
[ ] Backup recording and fixture set are available.
```
