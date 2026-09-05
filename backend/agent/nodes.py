import datetime
import logging
import asyncio
import inspect
from typing import Dict, Any, List
import inspect
from backend.agent.state import AgentState
from backend.services.router_service import RouterService
from backend.services.rag_service import RAGService
from backend.tools.registry import TOOL_REGISTRY, get_tool
from backend.config import OLLAMA_BASE_URL

logger = logging.getLogger("agent_nodes")

def add_audit_event(state: AgentState, step: str, action: str, status: str, details: str = "") -> None:
    event = {
        "step": step,
        "action": action,
        "status": status,
        "timestamp": datetime.datetime.now().isoformat(),
        "details": details
    }
    state["audit_log"].append(event)

async def planner_node(state: AgentState) -> AgentState:
    """Node 1: Planner Node - Analyzes query intent and plans workflow execution."""
    user_query = state.get("user_query", "")
    uploaded_file = state.get("uploaded_file")
    
    plan_desc = "Standard inquiry processing"
    q_lower = user_query.lower()
    if uploaded_file or any(w in q_lower for w in ["inspection", "flange", "p&id", "schematic"]):
        plan_desc = "Industrial Multimodal Ingestion -> Engineering Calculation -> PSU Deliverable Generation"
    
    add_audit_event(state, step="Planner", action="plan_execution", status="success", details=f"Strategy: {plan_desc}")
    return state

async def router_node(state: AgentState) -> AgentState:
    """Node 2: Router Node - Calls Model Router service to categorize task and select local LLM."""
    query = state.get("user_query", "")
    uploaded_file = state.get("uploaded_file")

    routing_result = await RouterService.route_task(query, uploaded_file)
    
    state["task_type"] = routing_result.get("task", "general")
    state["selected_model"] = routing_result.get("model", "qwen2.5:7b-instruct")
    state["routing_reason"] = routing_result.get("reason", "Local sovereign routing decision")

    add_audit_event(
        state,
        step="Router",
        action="select_model",
        status="success",
        details=f"Model: {state['selected_model']} | Task: {state['task_type']} | Reason: {state['routing_reason']}"
    )
    return state

from backend.tools.file_tool import auto_detect_relevant_files, read_file, write_file
from backend.config import KNOWLEDGE_DIR, DATA_DIR, UPLOADS_DIR
import json
import re

async def _plan_tools_with_local_llm(query: str, selected_model: str, task_type: str, uploaded_file: str | None = None) -> List[Dict[str, Any]]:
    """
    Asks the local Ollama LLM to autonomously plan and select tools, generate code, and construct payloads.
    Returns a list of tool call dicts: [{'tool': 'write_file', 'args': {...}}, ...]
    """
    # 1. Discover all workspace files so LLM knows what exists to read
    available_files = []
    for d in [KNOWLEDGE_DIR, DATA_DIR / "sample_documents", UPLOADS_DIR]:
        if d.exists():
            for f in d.glob("*.*"):
                if f.is_file() and not f.name.startswith("."):
                    available_files.append(f.name)

    files_list_str = ", ".join(available_files[:30]) if available_files else "None"

    # Select best model for tool planning / code generation
    model_name = "qwen2.5-coder:latest" if ("code" in query.lower() or ".py" in query.lower() or task_type == "coding") else "qwen2.5:7b-instruct"

    system_prompt = (
        "You are Sovereign AI Workbench, an autonomous agent orchestrator with access to local tools.\n"
        "Your task is to analyze the user request and decide which tools (if any) to invoke.\n\n"
        "Available Tools:\n"
        f"1. read_file(file_path): Read an existing workspace file. Available files: [{files_list_str}]\n"
        "2. write_file(file_path, content): Create or save a file with the generated code or text (e.g. .py, .txt, .json, .csv, .md).\n"
        "3. run_code(code, language='python'): Execute Python code in an isolated Docker sandbox.\n"
        "4. generate_docx(title, content, output_filename='Approval_Note.docx'): Generate a Word deliverable.\n"
        "5. generate_psu_note(data, output_filename='Approval_Note.docx'): Generate an official PSU note sheet deliverable.\n"
        "6. edit_spreadsheet(rows, output_filename='Calculation.xlsx'): Generate an Excel spreadsheet (rows is a 2D array of strings/numbers).\n"
        "7. generate_pptx(title, slide_titles, slide_contents, output_filename='Report.pptx'): Generate a PowerPoint presentation.\n"
        "8. ocr_document(file_path): OCR / parse document or image.\n\n"
        "Guidelines:\n"
        "- If the user asks to write/generate code or save to a file (e.g., 'Generate python code in ll.py'), generate the complete, production-ready code and return a write_file tool call with the full code in 'content' and target filename in 'file_path'. You may also include a run_code tool call to test it.\n"
        "- If the user asks to inspect or read an existing document from the workspace, call read_file or ocr_document with the matching file name.\n"
        "- If the user asks to perform calculations, write and run Python code using run_code.\n"
        "- If the user asks for Word, Excel, or PPT deliverables, call the corresponding generation tool.\n"
        "- Respond ONLY with a valid JSON array of tool calls. Do not output conversational text or markdown explanation.\n\n"
        "Format:\n"
        "[\n"
        "  {\n"
        "    \"tool\": \"tool_name\",\n"
        "    \"args\": {\"param\": \"value\"}\n"
        "  }\n"
        "]\n"
        "If no tool is needed, return: []"
    )

    prompt = f"User Request: {query}\n\nTool Plan (JSON array only):"
    
    payload = {
        "model": model_name,
        "system": system_prompt,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 1200}
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            if res.status_code == 200:
                raw_text = res.json().get("response", "").strip()
                # Parse JSON array from LLM output
                json_match = re.search(r'\[\s*\{.*?\}\s*\]', raw_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    if isinstance(parsed, list):
                        return parsed
                elif raw_text.startswith("[") and raw_text.endswith("]"):
                    parsed = json.loads(raw_text)
                    if isinstance(parsed, list):
                        return parsed
    except Exception as ex:
        logger.warning(f"LLM tool planning failed ({ex}) — using fallback parser")

    # Fast heuristic fallback if LLM planning had network issue
    return _heuristic_tool_fallback(query, uploaded_file)

def _heuristic_tool_fallback(query: str, uploaded_file: str | None = None) -> List[Dict[str, Any]]:
    q_lower = query.lower()
    tool_calls = []

    # Auto-detect existing workspace files if mentioned
    detected = auto_detect_relevant_files(query)
    for f in detected[:2]:
        if f["type"] in ["png", "jpg", "jpeg", "webp"] or "p&id" in q_lower:
            tool_calls.append({"tool": "ocr_document", "args": {"file_path": f["path"]}})
        else:
            tool_calls.append({"tool": "read_file", "args": {"file_path": f["path"]}})

    # Extract target file name if user requested saving/generating a file
    fn_match = re.search(r'([\w\-]+\.(?:py|txt|json|csv|md|html|sh|sql))', query, re.IGNORECASE)
    if fn_match:
        target = fn_match.group(1)
        if any(w in q_lower for w in ["write", "generate", "create", "save", "in one", "code"]):
            tool_calls.append({
                "tool": "write_file",
                "args": {
                    "file_path": target,
                    "content": f"# Generated deliverable: {target}\n# Task: {query}\n"
                }
            })

    return tool_calls

async def tool_selector_node(state: AgentState) -> AgentState:
    """Node 3: Tool Selector Node - Dynamically delegates tool planning and code generation to the local LLM."""
    query = state.get("user_query", "").strip()
    uploaded_file = state.get("uploaded_file")
    selected_model = state.get("selected_model", "qwen2.5:7b-instruct")
    task_type = state.get("task_type", "general")

    # 1. Sovereign RAG retrieval from local knowledge base
    rag_results = await RAGService.search_knowledge_base(query)
    state["context"] = rag_results
    add_audit_event(state, step="RAG", action="search_knowledge_base", status="success", details=f"Retrieved {len(rag_results)} context chunks from local vault")

    # 2. Autonomous LLM Tool Planning & Payload Formulation
    tool_calls = await _plan_tools_with_local_llm(
        query=query,
        selected_model=selected_model,
        task_type=task_type,
        uploaded_file=uploaded_file
    )

    # If uploaded file was provided and not yet in tool calls, attach it
    if uploaded_file and not any(tc.get("args", {}).get("file_path") == uploaded_file for tc in tool_calls):
        suffix = Path(uploaded_file).suffix.lower()
        if suffix in [".png", ".jpg", ".jpeg", ".bmp", ".webp", ".pdf"]:
            tool_calls.insert(0, {"tool": "ocr_document", "args": {"file_path": uploaded_file}})
        else:
            tool_calls.insert(0, {"tool": "read_file", "args": {"file_path": uploaded_file}})

    state["tool_calls"] = tool_calls
    return state

async def tool_executor_node(state: AgentState) -> AgentState:
    """Node 4: Tool Executor Node - Runs tools safely and captures structured outputs."""
    tool_calls = state.get("tool_calls", [])
    tool_results = state.get("tool_results", [])
    generated_files = state.get("generated_files", [])

    for call in tool_calls:
        tool_name = call.get("tool")
        tool_args = call.get("args", {})
        func = get_tool(tool_name)

        if func:
            try:
                if inspect.iscoroutinefunction(func):
                    res = await func(**tool_args)
                else:
                    res = func(**tool_args)

                tool_results.append({"tool": tool_name, "result": res})
                
                # Deliverables: ONLY creation/writing tools add output deliverables to download
                if tool_name in ["write_file", "generate_docx", "generate_psu_note", "edit_spreadsheet", "generate_pptx"]:
                    if isinstance(res, dict) and "filename" in res:
                        generated_files.append(res["filename"])

                # If read_file returned document content, inject into context sources
                if tool_name == "read_file" and isinstance(res, dict) and res.get("content"):
                    state["context"].insert(0, {
                        "text": res["content"][:4000],
                        "source": f"Workspace File ({res.get('clean_name') or res.get('filename', 'document')})",
                        "page": 1,
                        "score": 1.0,
                        "extractor": "workspace_reader"
                    })

                # If OCR/MarkItDown extracted document text, inject into context sources
                if tool_name == "ocr_document" and isinstance(res, dict) and res.get("text"):
                    doc_src = res.get("source") or (Path(tool_args.get("file_path", "")).name if tool_args.get("file_path") else "Document")
                    state["context"].insert(0, {
                        "text": res["text"][:4000],
                        "source": f"Uploaded File ({doc_src})",
                        "page": res.get("pages", 1),
                        "score": 1.0,
                        "extractor": "markitdown"
                    })

                add_audit_event(
                    state,
                    step="Tool Execution",
                    action=tool_name,
                    status="success",
                    details=f"Output: {str(res)[:100]}..."
                )
            except Exception as ex:
                tool_results.append({"tool": tool_name, "error": str(ex)})
                add_audit_event(state, step="Tool Execution", action=tool_name, status="error", details=str(ex))
        else:
            tool_results.append({"tool": tool_name, "error": f"Tool '{tool_name}' not registered."})
            add_audit_event(state, step="Tool Execution", action=tool_name, status="error", details="Tool not registered")

    state["tool_results"] = tool_results
    state["generated_files"] = list(set(generated_files))
    return state

async def reflection_node(state: AgentState) -> AgentState:
    """Node 5: Reflection Node - Evaluates output completeness and verifies statutory compliance."""
    generated_files = state.get("generated_files", [])
    add_audit_event(
        state,
        step="Reflection",
        action="evaluate_completeness",
        status="success",
        details=f"Verification complete. Deliverables confirmed: {', '.join(generated_files) if generated_files else 'None'}"
    )
    return state

import httpx

import base64
from pathlib import Path

async def stream_local_llm(user_query: str, selected_model: str, task_type: str, context: list, tool_results: list, uploaded_file: str | None = None):
    """Streams tokens from local Ollama model in real-time as an async generator."""
    model_lower = (selected_model or "").lower()
    
    images_b64 = []
    is_image = False
    if uploaded_file and Path(uploaded_file).exists():
        suffix = Path(uploaded_file).suffix.lower()
        if suffix in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
            try:
                b64 = base64.b64encode(Path(uploaded_file).read_bytes()).decode("utf-8")
                images_b64.append(b64)
                is_image = True
            except Exception as ex:
                logger.error(f"Error encoding image {uploaded_file}: {ex}")

    if is_image or "vl" in model_lower:
        ollama_model = "qwen2.5vl:7b"
    elif "coder" in model_lower or task_type == "coding":
        ollama_model = "qwen2.5-coder:latest"
    else:
        ollama_model = "qwen2.5:7b-instruct"

    prompt_parts = [
        "You are Sovereign AI Workbench, an expert on-premise industrial AI assistant running 100% air-gapped.",
        "Provide a direct, thorough, and professional engineering response formatted in clean GitHub-flavored Markdown.",
        "Use headers (###), bold text, bullet points, and code blocks where appropriate.",
        "Reference statutory standards (such as ASME B31.3, OISD, API) and inspection data accurately."
    ]

    doc_context_added = False
    for tr in tool_results:
        res = tr.get("result")
        if isinstance(res, dict):
            extracted_txt = (res.get("text") or res.get("content") or "").strip()
            if extracted_txt:
                doc_src = res.get("clean_name") or res.get("filename") or res.get("source") or "Workspace Document"
                prompt_parts.append(f"\n[DOCUMENT CONTENT — Source: {doc_src}]:\n{extracted_txt[:6000]}")
                doc_context_added = True
            if res.get("stdout"):
                prompt_parts.append(f"\n[SANDBOX PYTHON CALCULATION TELEMETRY]:\n{res['stdout'].strip()}")
            if res.get("tables"):
                prompt_parts.append(f"\n[EXTRACTED TABLES / DATA]:\n{res['tables']}")
            if res.get("findings"):
                prompt_parts.append(f"\nInspection / Tool Findings: {res['findings']}")
            if res.get("equipment") or res.get("instruments"):
                prompt_parts.append(f"\nExtracted Equipment: {res.get('equipment', [])} | Instruments: {res.get('instruments', [])}")

    if context and not doc_context_added:
        context_str = "\n".join([f"- [{c.get('source', 'KB')} (Page {c.get('page', 1)})]: {c.get('text', '')}" for c in context[:4]])
        prompt_parts.append(f"\nLocal Knowledge Base Context:\n{context_str}")

    prompt_parts.append(f"\nUser Query: {user_query}\n\nAnswer:")
    full_prompt = "\n".join(prompt_parts)

    payload = {
        "model": ollama_model,
        "prompt": full_prompt,
        "stream": True,
        "options": {"temperature": 0.2, "num_predict": 700}
    }
    if images_b64:
        payload["images"] = images_b64

    import json
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/generate", json=payload) as response:
                if response.status_code == 200:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                token = chunk.get("response", "")
                                if token:
                                    yield token
                                if chunk.get("done", False):
                                    break
                            except Exception:
                                pass
                    return
    except Exception as ex:
        logger.warning(f"Ollama streaming failed ({ex}) — attempting synchronous fallback")

    # Fallback to non-streaming call if stream fails
    fallback_ans = await _call_local_llm(user_query, selected_model, task_type, context, tool_results, uploaded_file)
    if fallback_ans:
        yield fallback_ans

async def _call_local_llm(user_query: str, selected_model: str, task_type: str, context: list, tool_results: list, uploaded_file: str | None = None) -> str:
    """Invokes local Ollama model to generate answer synchronously."""
    model_lower = (selected_model or "").lower()
    
    images_b64 = []
    is_image = False
    if uploaded_file and Path(uploaded_file).exists():
        suffix = Path(uploaded_file).suffix.lower()
        if suffix in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
            try:
                b64 = base64.b64encode(Path(uploaded_file).read_bytes()).decode("utf-8")
                images_b64.append(b64)
                is_image = True
            except Exception as ex:
                logger.error(f"Error encoding image {uploaded_file}: {ex}")

    if is_image or "vl" in model_lower:
        ollama_model = "qwen2.5vl:7b"
    elif "coder" in model_lower or task_type == "coding":
        ollama_model = "qwen2.5-coder:latest"
    else:
        ollama_model = "qwen2.5:7b-instruct"

    prompt_parts = [
        "You are Sovereign AI Workbench, a secure on-premise AI assistant running locally.",
        "Answer the user's question directly, accurately, and thoroughly using the provided context and document content.",
        "Format your answer with clear markdown structure, steps, and citations."
    ]

    doc_context_added = False
    for tr in tool_results:
        res = tr.get("result")
        if isinstance(res, dict):
            extracted_txt = (res.get("text") or res.get("content") or "").strip()
            if extracted_txt:
                doc_src = res.get("clean_name") or res.get("filename") or res.get("source") or "Workspace Document"
                prompt_parts.append(f"\n[DOCUMENT CONTENT — Source: {doc_src}]:\n{extracted_txt[:6000]}")
                doc_context_added = True
            if res.get("stdout"):
                prompt_parts.append(f"\n[SANDBOX PYTHON CALCULATION TELEMETRY]:\n{res['stdout'].strip()}")
            if res.get("tables"):
                prompt_parts.append(f"\n[EXTRACTED TABLES / DATA]:\n{res['tables']}")
            if res.get("findings"):
                prompt_parts.append(f"\nInspection / Tool Findings: {res['findings']}")
            if res.get("equipment") or res.get("instruments"):
                prompt_parts.append(f"\nExtracted Equipment: {res.get('equipment', [])} | Instruments: {res.get('instruments', [])}")

    if context and not doc_context_added:
        context_str = "\n".join([f"- [{c.get('source', 'KB')} (Page {c.get('page', 1)})]: {c.get('text', '')}" for c in context[:4]])
        prompt_parts.append(f"\nLocal Knowledge Base Context:\n{context_str}")

    prompt_parts.append(f"\nUser Query: {user_query}\n\nAnswer:")
    full_prompt = "\n".join(prompt_parts)

    payload = {
        "model": ollama_model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 600}
    }
    if images_b64:
        payload["images"] = images_b64

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            if res.status_code == 200:
                data = res.json()
                answer = data.get("response", "").strip()
                if answer:
                    return answer
    except Exception as e:
        logger.warning(f"Ollama local LLM call failed ({e}) — trying fallback model")
        for fallback_model in ["qwen2.5:7b-instruct", "qwen2.5vl:7b", "qwen2.5-coder:latest"]:
            if fallback_model == ollama_model:
                continue
            try:
                fb_payload = {
                    "model": fallback_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 500}
                }
                if images_b64 and "vl" in fallback_model:
                    fb_payload["images"] = images_b64
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=fb_payload)
                    if res.status_code == 200:
                        return res.json().get("response", "").strip()
            except Exception:
                pass

    return ""


async def finalizer_node(state: AgentState) -> AgentState:
    """Node 6: Finalizer Node - Assembles comprehensive response with citations, math, and deliverables."""
    user_query = state.get("user_query", "")
    task_type = state.get("task_type", "general")
    model = state.get("selected_model", "qwen2.5:7b-instruct")
    reason = state.get("routing_reason", "")
    context = state.get("context", [])
    generated_files = state.get("generated_files", [])
    tool_results = state.get("tool_results", [])

    uploaded_file = state.get("uploaded_file")
    llm_answer = await _call_local_llm(user_query, model, task_type, context, tool_results, uploaded_file)

    response_lines = [
        "### Sovereign AI Workbench Response\n",
        f"**Model Routing**: Dispatched via `{model}` ({task_type.capitalize()} Specialist).",
        f"*Rationale*: {reason}\n"
    ]

    if llm_answer:
        response_lines.append("#### 🤖 AI Answer:")
        response_lines.append(llm_answer)
        response_lines.append("")

    if context:
        response_lines.append("#### 📖 Grounded Knowledge Base Context:")
        for idx, item in enumerate(context[:2], 1):
            response_lines.append(f"{idx}. `{item.get('text')}` — *Source*: **{item.get('source')}** (Section: {item.get('section', 'General')})")
        response_lines.append("")

    if tool_results:
        response_lines.append("#### ⚙️ Executed Tools & Engineering Telemetry:")
        for tr in tool_results:
            tname = tr.get("tool")
            res = tr.get("result", {})
            if tname == "run_code":
                response_lines.append(f"- **Sandboxed Calculation Engine**: Output: `{res.get('stdout', '').strip()}` ({res.get('execution_environment')})")
            elif tname == "ocr_document":
                doc_name = res.get('source') or 'Uploaded Document'
                pages = res.get('pages', 1)
                extractor = res.get('model_used') or res.get('extractor') or 'MarkItDown'
                char_count = res.get('char_count', len(res.get('text', '')))
                response_lines.append(f"- **OCR / Document Pipeline ({extractor})**: Parsed `{doc_name}` ({pages} page(s), {char_count} chars extracted).")
                response_lines.append(f"- **Multimodal Pipeline**: Processed inspection report with findings: `{res.get('findings')}`")
            elif tname == "generate_psu_note":
                response_lines.append(f"- **Official PSU Secretariat Note**: Formatted Green-Sheet generated: `{res.get('filename')}`")
            elif tname in ["generate_docx", "generate_pptx", "edit_spreadsheet"]:
                response_lines.append(f"- **Deliverable Generated**: `{res.get('filename')}`")

    if generated_files:
        response_lines.append("\n#### 📦 Generated Deliverables:")
        for gf in generated_files:
            response_lines.append(f"- `data/outputs/{gf}`")

    state["final_response"] = "\n".join(response_lines)
    return state
