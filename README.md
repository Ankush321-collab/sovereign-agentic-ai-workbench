# 🛡️ Sovereign AI Workbench — SIH 2026



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
      │    Model Router      │       │    RAG    │       │     Multimodal     │
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
                         │       Frontend / Security + Agentic Backend        │
                         └──────────────────────────────┘
```

---

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

### Agentic Backend

```bash
git checkout -b feature/ankush-agent-backend
```

### Model Router

```bash
git checkout -b feature/aarav-model-router
```

### RAG

```bash
git checkout -b feature/krishna-rag
```

### Multimodal

```bash
git checkout -b feature/pankaj-multimodal
```

### Frontend / Security

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
RAG → owns rag/
Multimodal  → owns multimodal/
Model Router   → owns router/
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
                     Frontend / Security
                         │
                         ▼
                    FastAPI
                     Agentic Backend
                         │
                         ▼
                  LangGraph Agent
                     Agentic Backend
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
           Router       RAG      Multimodal
           Model Router       RAG      Multimodal
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

## Agentic Backend

Integration tests:

```text
Frontend → API → Agent → Tool → Response
```

## Model Router

Test:

```text
Coding → Coding Model
Document → Reasoning Model
Image → Vision Model
```

## RAG

Test:

```text
Document → Embedding → ChromaDB → Relevant Context
```

## Multimodal

Test:

```text
Image → OCR/Vision → Structured Output
```

## Frontend / Security

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
2. Multimodal's OCR/Vision pipeline processes it
             ↓
3. Agentic Backend's LangGraph agent creates a plan
             ↓
4. Model Router's router selects the appropriate model
             ↓
5. RAG's RAG searches the local SOP/manual
             ↓
6. Agent combines findings + SOP information
             ↓
7. Tool generates approval Word document
             ↓
8. Agent verifies the result
             ↓
9. Frontend / Security's UI displays the complete trace
             ↓
10. Sovereignty panel shows:
        External Connections = 0
```

This maps directly to the proposed SIH demo path: scanned inspection report → OCR/Vision → agent plan → RAG/tool calls → verified Word approval note → live network proof.

---

# 18. ⭐ Priority Levels

## 🔴 MUST HAVE

Everyone should prioritize these first.

### Agentic Backend
- FastAPI
- LangGraph
- Agent loop
- Tool calling

### Model Router
- 2 local models
- Basic router
- Routing explanation

### RAG
- ChromaDB
- Document ingestion
- Retrieval
- Citations

### Multimodal
- OCR
- Vision model
- Scanned document processing

### Frontend / Security
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

**Agentic Backend**
- FastAPI
- LangGraph skeleton

**Model Router**
- Local models
- Model serving

**RAG**
- ChromaDB
- Sample documents

**Multimodal**
- Docling
- Tesseract
- Qwen-VL setup

**Frontend / Security**
- React
- Dashboard skeleton

---

## DAY 2 — Individual Modules

**Agentic Backend**
- Agent nodes
- Tool interface

**Model Router**
- Router
- Classification

**RAG**
- Retrieval
- Citations

**Multimodal**
- OCR + Vision

**Frontend / Security**
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

# Final Project Goal

al

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
