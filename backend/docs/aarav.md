Aarav --- Multi-Model Router & Model Serving

Purpose

This document defines Aarav's module only for the Sovereign AI
Workbench.

The goal is to build a configuration-driven local model routing
layer that:

knows which local models are available,

classifies incoming requests,

selects the appropriate model,

explains the routing decision,

checks model health,

provides fallback behavior,

exposes a small API that the shared FastAPI/LangGraph backend can
consume.

Important: This module must remain independent from the other team
members' internal implementations. Integrate through the shared API
contracts instead of modifying their modules.

1. Ownership

Owner: Aarav

Git branch:

feature/aarav-model-router

Module responsibility:

Multi-Model Router + Model Serving

The project document assigns Aarav the model-router and model-serving
responsibility.

2. What Aarav Owns

Aarav owns these components:

router/
├── model_registry.yaml
├── classifier.py
├── router.py
├── health.py
├── fallback.py
├── schemas.py
└── client.py

The exact filenames may be adjusted during implementation, but the
responsibilities should remain separated.

Aarav owns

Model registry

Task classification

Model selection

Routing explanation

Model health checks

Fallback selection

Router API

Local model client abstraction

Routing history data returned by the router

Configuration for local model endpoints

Aarav does NOT own

LangGraph agent orchestration

Shared AgentState

RAG / ChromaDB

OCR

P&ID processing

React UI

Sovereignty dashboard UI

Document generation

General tool execution

These belong to the other modules.

3. High-Level Architecture

The router sits between the agent/backend and the local AI models.

                         FastAPI / LangGraph
                                |
                                | route request
                                v
                     +----------------------+
                     |      AARAV ROUTER    |
                     +----------------------+
                       |       |        |
                       |       |        |
                 classify   registry   health
                       |       |        |
                       +-------+--------+
                               |
                               v
                      Model Selection
                               |
             +-----------------+-----------------+
             |                 |                 |
             v                 v                 v
       Reasoning Model   Coding Model      Vision Model
             |                 |                 |
             +-----------------+-----------------+
                               |
                               v
                         Local Model API

The router should not become the LangGraph orchestrator. LangGraph
decides when routing is needed; Aarav's module decides which model
should be used.

4. Supported Model Categories

The project specification gives this target architecture:

Task                   Target model category

Reasoning / Document   Sarvam-30B or Qwen
Coding / Debugging     Qwen2.5-Coder
Vision / Image         Qwen2.5-VL

Hardware limitations determine the final model sizes.

Do not hard-code a specific final model name throughout the codebase.
The model registry must control the actual model configuration.

5. Model Registry

Create:

router/model_registry.yaml

Example:

models:
  reasoning:
    name: qwen-reasoning
    endpoint: http://localhost:8001
    tasks:
      - reasoning
      - document
      - general
    enabled: true

  coding:
    name: qwen-coder
    endpoint: http://localhost:8002
    tasks:
      - coding
      - debugging
    enabled: true

  vision:
    name: qwen-vl
    endpoint: http://localhost:8003
    tasks:
      - vision
      - image
      - document
    enabled: true

The exact model names and ports must be changed to match the models
actually running on the team's machines.

Rules

Do not hard-code model names in Python files.

Do not hard-code endpoints in multiple places.

Configuration should be the single source of truth.

The backend should be able to change a model through configuration
without changing routing code.

Disabled/unavailable models must not be selected as healthy primary
models.

6. Task Classification

The classifier receives information about the user's request and
determines a task type.

Minimum supported categories:

coding
debugging
document
reasoning
vision
image
general

Examples:

"Fix this Python error"
        ↓
coding
        ↓
Qwen Coder

"Summarize this SOP"
        ↓
document
        ↓
Reasoning Model

"Read this P&ID"
        ↓
vision
        ↓
Qwen-VL

Important

The classifier should be lightweight and deterministic where possible.

Do not make the router depend on an external/cloud LLM just to classify
requests.

A simple rule-based classifier is acceptable for the first SIH version.

A more advanced classifier can be added later without changing the
router API.

7. Input Contract

The router should accept a request equivalent to:

{
  "query": "Fix this Python code",
  "has_image": false,
  "has_file": true
}

Recommended internal schema:

class RouteRequest(BaseModel):
    query: str
    has_image: bool = False
    has_file: bool = False
    task_type: str | None = None

If task_type is supplied by a trusted upstream component, the router
may use it. Otherwise it should classify the request itself.

Do not require frontend-specific fields.

8. Output Contract

The primary routing response must remain compatible with the shared
project contract:

{
  "task_type": "coding",
  "model": "qwen-coder",
  "reason": "Coding request detected"
}

For internal use, additional fields may be included:

{
  "task_type": "coding",
  "model": "qwen-coder",
  "endpoint": "http://localhost:8002",
  "reason": "Python code and debugging request detected",
  "fallback": false,
  "healthy": true
}

Compatibility rule

The following fields must remain stable:

task_type
model
reason

Additional fields should be optional and must not break consumers that
only use the required fields.

9. Router API

Expose the following endpoints:

POST /route
GET  /models
GET  /routing/history

POST /route

Request:

{
  "query": "Fix this Python code",
  "has_image": false,
  "has_file": true
}

Response:

{
  "task_type": "coding",
  "model": "qwen-coder",
  "endpoint": "http://localhost:8002",
  "reason": "Coding request detected"
}

Expected behavior

Request
  ↓
Validate
  ↓
Classify
  ↓
Find configured models
  ↓
Check availability
  ↓
Select healthy model
  ↓
Return structured routing decision

10. GET /models

Return configured model information.

Example:

{
  "models": [
    {
      "name": "qwen-coder",
      "task": "coding",
      "enabled": true,
      "healthy": true
    },
    {
      "name": "qwen-vl",
      "task": "vision",
      "enabled": true,
      "healthy": true
    }
  ]
}

Do not expose secrets or credentials.

11. GET /routing/history

Return recent routing decisions.

Example:

{
  "history": [
    {
      "task_type": "coding",
      "model": "qwen-coder",
      "reason": "Coding request detected"
    },
    {
      "task_type": "vision",
      "model": "qwen-vl",
      "reason": "Image attachment detected"
    }
  ]
}

Keep this history lightweight. It should support the frontend's routing
panel without becoming a second logging system.

12. Routing Logic

Recommended flow:

                    Incoming Request
                           |
                           v
                    Validate input
                           |
                           v
                  Does task_type exist?
                    /             \
                  yes              no
                   |                |
                   |          Classify request
                   |                |
                   +-------+--------+
                           |
                           v
                  Find matching models
                           |
                           v
                    Check health
                           |
                 +---------+---------+
                 |                   |
              Healthy             Unhealthy
                 |                   |
                 v                   v
          Select primary       Select fallback
                 |                   |
                 +---------+---------+
                           |
                           v
                  Build route result
                           |
                           v
                    Return JSON

13. Routing Priority

Use explicit routing rules rather than vague model selection.

Recommended initial priority:

Vision

If:

has_image == true

route to a vision-capable model unless a higher-priority explicit task
requires another model.

Coding

If the request contains clear coding/debugging intent:

coding
debug
debugging
Python
Java
C++
code
traceback
exception
error in code

route to the coding model.

Document

If a document/file is being analyzed or summarized:

summarize document
analyze SOP
read manual
extract information from report

route to the reasoning/document model.

Reasoning

For analytical questions that do not require coding or vision, route to
the reasoning model.

General

Use the configured general/reasoning model.

These are starting rules, not a requirement to use exactly these
keywords.

14. Routing Explanation

Every routing decision must contain a human-readable reason.

Bad:

{
  "model": "qwen-coder",
  "reason": "classification=2"
}

Good:

{
  "model": "qwen-coder",
  "reason": "Coding request detected from Python code and traceback"
}

The frontend will display this reason.

Do not implement frontend rendering inside the router.

15. Model Health Checks

The router must be able to determine whether a configured model is
available.

A health check should verify:

Endpoint reachable
        ↓
Model service responding
        ↓
Model configured
        ↓
Model usable

Recommended internal result:

{
  "model": "qwen-coder",
  "healthy": true
}

Do not perform expensive generation requests for every routing decision.

Use a lightweight health endpoint or inexpensive availability check
where the serving system supports one.

16. Fallback Strategy

If the preferred model is unavailable:

Primary model
     ↓
unhealthy
     ↓
Fallback model
     ↓
Return decision

Example:

{
  "task_type": "reasoning",
  "model": "qwen-general",
  "reason": "Reasoning model unavailable; using configured fallback",
  "fallback": true
}

Fallback behavior must be configuration-driven.

Do not silently route a vision request to a text-only model.

A fallback is valid only if the fallback model can reasonably handle the
requested task.

17. Local Model Client

Keep model communication behind a small abstraction.

Example:

class LocalModelClient:
    def generate(self, model_name: str, prompt: str, **kwargs):
        ...

The router should not contain application-specific generation logic.

The purpose is to allow:

Ollama today
      ↓
vLLM later

without rewriting the classification/routing logic.

18. Separation From Roshan's Work

Roshan owns the local Ollama environment and React frontend.

Aarav owns routing logic.

Roshan provides

Ollama base URL
Exact text model tag
Exact vision model tag
Local model setup information

Aarav consumes/configures

Model name
Endpoint
Task capability
Health status
Fallback configuration

Important

Do not duplicate Ollama setup logic inside the frontend.

Do not put routing logic in React.

The frontend should call:

GET /models
POST /route
GET /routing/history

and display the result.

19. Separation From Ankush's Work

Ankush owns:

FastAPI integration
LangGraph
AgentState
Planner
Tool selector
Tool executor
Reflection
Finalizer

Aarav provides the router as a service/interface.

Expected interaction:

LangGraph
    ↓
POST /route
    ↓
Aarav Router
    ↓
Routing decision
    ↓
LangGraph continues execution

Do not modify Ankush's AgentState without team agreement.

The shared AgentState already defines:

selected_model: str
routing_reason: str

The router should provide values that can populate these fields.

20. Separation From Krishna's RAG

Krishna owns:

Document ingestion
Chunking
Embeddings
ChromaDB
Retrieval
Citations

Aarav does not implement RAG.

The router only decides which model is suitable for a request.

For example:

User asks about Safety SOP
        ↓
Agent requests RAG
        ↓
Krishna returns context
        ↓
Agent/router selects reasoning model

Do not import or duplicate ChromaDB logic into the router.

21. Separation From Pankaj's Multimodal Pipeline

Pankaj owns:

OCR
Docling
Vision processing
Image preprocessing
P&ID processing
Structured multimodal output

Aarav does not implement OCR or P&ID parsing.

Aarav only determines that a request requiring visual understanding
should use a vision-capable model.

Example:

P&ID uploaded
      ↓
Agent / metadata
      ↓
Router sees vision requirement
      ↓
Qwen-VL
      ↓
Pankaj's multimodal pipeline

22. Suggested Directory Structure

Use a self-contained router package:

backend/
├── main.py
├── api/
│   ├── chat.py
│   ├── upload.py
│   ├── agent.py
│   └── status.py
│
├── router/
│   ├── __init__.py
│   ├── model_registry.yaml
│   ├── schemas.py
│   ├── classifier.py
│   ├── router.py
│   ├── health.py
│   ├── fallback.py
│   └── client.py
│
├── agent/
├── rag/
├── multimodal/
└── tools/

If the team already has a backend/router/ directory, use it rather
than creating another router location.

23. Testing

Create router-focused tests.

Recommended:

tests/
├── test_router.py
├── test_classifier.py
├── test_health.py
└── test_fallback.py

Minimum tests:

Coding

"Fix this Python traceback"
→ coding
→ coding model

Document

"Summarize this safety SOP"
→ document
→ reasoning/document model

Vision

"Analyze this P&ID"
+ has_image=true
→ vision
→ vision model

Health

healthy model
→ selected

Fallback

primary unavailable
→ compatible fallback selected

Configuration

change model_registry.yaml
→ router uses new model

No cloud dependency

The router must not require an external LLM API to perform its basic
classification/routing.

24. Shared API Compatibility Rules

To minimize merge conflicts:

Do not modify without agreement

backend/main.py
backend/agent/state.py
docker-compose.yml
requirements.txt
.env.example
README.md

These are shared files in the project.

If a dependency must be added, communicate it to the team before
changing requirements.txt.

Prefer

backend/router/*
tests/test_router*

for Aarav's work.

This keeps the majority of commits isolated to Aarav's module.

25. Git Workflow

Start from updated main:

git checkout main
git pull origin main

Switch to Aarav's branch:

git switch feature/aarav-model-router

Before beginning work:

git pull origin main

Implement and test:

pytest

Commit using meaningful messages:

git add backend/router tests
git commit -m "feat: implement model router"

Push:

git push origin feature/aarav-model-router

Create a Pull Request into:

main

26. Merge-Conflict Prevention

The project is being developed by five people, so conflict prevention is
important.

Rule 1 --- Keep Aarav's code isolated

Prefer modifying:

backend/router/*
tests/test_router*

Rule 2 --- Do not rewrite shared files unnecessarily

Avoid formatting/reorganizing:

main.py
README.md
docker-compose.yml
requirements.txt
AgentState

Rule 3 --- Pull before major work

git checkout main
git pull origin main
git switch feature/aarav-model-router
git merge main

Resolve conflicts locally before opening the PR.

Rule 4 --- Keep API contracts stable

Do not change:

POST /route
GET /models
GET /routing/history

request/response fields without coordinating with Ankush and Roshan.

Rule 5 --- No duplicate implementations

There should be one model registry and one routing implementation.

Do not create alternative routing logic in:

frontend/
agent/
chat.py

27. Recommended Commit Sequence

Keep commits small and logically separated.

feat: add router schemas
feat: add model registry
feat: implement task classifier
feat: implement model selection
feat: add model health checks
feat: add fallback routing
feat: expose routing API
test: add router test coverage
docs: document model router

This makes review and conflict resolution easier.

28. Definition of Done

Aarav's module is complete when:

At least 2 local models work.

Model registry is configuration-driven.

Basic task types are classified correctly.

Router selects an appropriate local model.

Routing result is structured JSON.

Every routing decision contains a reason.

Model health can be checked.

Compatible fallback behavior exists.

/route works.

/models works.

/routing/history works.

Backend can consume the router.

Frontend can display routing information.

No cloud LLM is required.

Router tests pass.

Aarav's code remains isolated from other team modules.

29. Final Integrated Flow

The final application should use Aarav's module like this:

                         USER
                           |
                           v
                       React UI
                           |
                           v
                       FastAPI
                           |
                           v
                     LangGraph
                           |
                           v
                   +---------------+
                   | AARAV ROUTER  |
                   +---------------+
                           |
                 classify + select
                           |
            +--------------+--------------+
            |              |              |
            v              v              v
       Reasoning        Coding         Vision
         Model           Model          Model
            |              |              |
            +--------------+--------------+
                           |
                           v
                    Agent continues
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
         RAG          Multimodal          Tools
          |                |                |
          +----------------+----------------+
                           |
                           v
                       Verify
                           |
                           v
                      Deliverable
                           |
                           v
                     Audit Trace

30. Aarav's Core Principle

Aarav's module should answer one question reliably:

"Given this task and the locally available models, which model
should handle it, why, and is that model currently available?"

Everything else should remain owned by the appropriate team member.

That separation keeps the system modular, makes integration easier, and
significantly reduces merge-conflict risk.