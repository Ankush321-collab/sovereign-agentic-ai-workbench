# Roshan's Module — Setup Instructions
**Branch:** `feature/roshan-local-models-frontend`

> Share this with Ankush and Aarav so they can replicate the local AI environment.

---

## Ollama Handoff Information

| Item | Value |
|---|---|
| Ollama Base URL | `http://localhost:11434` |
| Text / Reasoning Model | `qwen2.5:7b-instruct` |
| Vision Model | `qwen2.5vl:7b` |
| Coding Model | `qwen2.5-coder:latest` |

---

## To Replicate This Setup on Another Machine

### Step 1 — Install Ollama
Download from https://ollama.com and install.

### Step 2 — Pull the models
```bash
ollama pull qwen2.5:7b-instruct
ollama pull qwen2.5vl:7b
ollama pull qwen2.5-coder:latest
```

### Step 3 — Verify
```bash
ollama list
```
Expected output:
```
NAME                    ID              SIZE
qwen2.5vl:7b            5ced39dfa4ba    6.0 GB
qwen2.5:7b-instruct     845dbda0ea48    4.7 GB
qwen2.5-coder:latest    dae161e27b0e    4.7 GB
```

### Step 4 — Start Ollama API
```bash
ollama serve
```
API is now available at `http://localhost:11434`

### Step 5 — Verify API
```bash
curl http://localhost:11434/api/tags
```

### Step 6 — Run test scripts
```bash
# From project root
python -X utf8 tests/test_ollama_text.py
python -X utf8 tests/test_ollama_vision.py
```
Both should show all tests PASSED.

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
Opens at `http://localhost:5173`

### Toggle Mock vs Real API
Edit `frontend/.env`:
```env
VITE_USE_MOCK=false       # set to false when Ankush's backend is ready
VITE_API_URL=http://localhost:8000
```

---

## Config File
All model names are centralized in:
```
config/ollama_config.yaml
```
**Do not hard-code model names in Python files.** Load from this YAML.

---

## Test Results (Verified on Roshan's Machine)

| Test | Result |
|---|---|
| `test_ollama_text.py` | 4/4 PASSED — response in 61.5s |
| `test_ollama_vision.py` | 5/5 PASSED — image input in 16.9s |
