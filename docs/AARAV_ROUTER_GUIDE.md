# 🛡️ Aarav's Module — Multi-Model Router & Model Serving

## Overview

Aarav's module serves as the **Model Router & Model Serving Layer** of the **Sovereign AI Workbench**. It provides a local, configuration-driven routing mechanism that dynamically selects the right local AI model for every user query while ensuring zero external network calls.

---

## 🏗️ Architecture & Component Design

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

backend/api/
└── router_api.py         # FastAPI routes (POST /route, GET /models, GET /routing/history)
```

---

## ⚙️ How It Works

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

## 🔌 API Endpoints

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

### 3. `GET /routing/history`
- **Response**:
  ```json
  {
    "history": [
      {
        "task_type": "coding",
        "model": "qwen-coder",
        "reason": "Coding/debugging request detected from keyword 'traceback'",
        "endpoint": "http://localhost:11434"
      }
    ]
  }
  ```

---

## 🚀 How Aarav's Module Helps the Entire Project

1. **Powers Model Selection for Ankush (LangGraph Agent)**:
   - Provides Ankush's agent orchestrator with instantaneous model selection and populates `selected_model` and `routing_reason` in the shared `AgentState`.

2. **Supports Roshan's React Frontend & Sovereignty View**:
   - Supplies `/models` and `/routing/history` endpoints to populate the **Model Routing Panel** on the UI.
   - Provides clear, transparent `reason` fields showing users why each local model was chosen.

3. **Ensures Reliability with Zero Cloud Dependency**:
   - Operates 100% locally with zero external API calls, satisfying strict air-gapped sovereignty requirements for confidential industrial environments.

4. **Prevents Resource Waste & Hardware Overload**:
   - Directs code queries to fast coder models, vision tasks to vision-capable models, and analytical queries to reasoning models, ensuring hardware resources are utilized efficiently.

5. **Configuration-Driven Flexibility**:
   - Models and endpoints can be swapped in `model_registry.yaml` without changing application code or breaking upstream services.
