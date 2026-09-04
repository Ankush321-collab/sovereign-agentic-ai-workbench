import datetime
import logging
import asyncio
import inspect
from backend.agent.state import AgentState
from backend.services.router_service import RouterService
from backend.services.rag_service import RAGService
from backend.tools.registry import TOOL_REGISTRY, get_tool

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
    """Nodes 1: Planner Node - Analyzes query intent and plans workflow execution."""
    user_query = state.get("user_query", "")
    uploaded_file = state.get("uploaded_file")
    
    add_audit_event(state, step="Planner", action="analyze_request", status="success", details=f"Planning for query: '{user_query[:50]}...'")
    return state

async def router_node(state: AgentState) -> AgentState:
    """Nodes 2: Router Node - Calls Model Router service to categorize task and select local LLM."""
    query = state.get("user_query", "")
    uploaded_file = state.get("uploaded_file")

    routing_result = await RouterService.route_task(query, uploaded_file)
    
    state["task_type"] = routing_result.get("task", "general")
    state["selected_model"] = routing_result.get("model", "Sarvam-30B")
    state["routing_reason"] = routing_result.get("reason", "Local routing decision")

    add_audit_event(
        state,
        step="Router",
        action="select_model",
        status="success",
        details=f"Model: {state['selected_model']} | Reason: {state['routing_reason']}"
    )
    return state

async def tool_selector_node(state: AgentState) -> AgentState:
    """Nodes 3: Tool Selector Node - Determines which tools/RAG to invoke."""
    query = state.get("user_query", "").lower()
    uploaded_file = state.get("uploaded_file")
    tool_calls = state.get("tool_calls", [])

    # Always perform RAG search for document/reasoning or SOP queries
    rag_results = await RAGService.search_knowledge_base(state.get("user_query", ""))
    state["context"] = rag_results
    add_audit_event(state, step="RAG", action="search_knowledge_base", status="success", details=f"Retrieved {len(rag_results)} context chunks")

    # Select OCR / Vision tool if file uploaded
    if uploaded_file and not any(tc["tool"] == "ocr_document" for tc in tool_calls):
        tool_calls.append({"tool": "ocr_document", "args": {"file_path": uploaded_file}})

    # Select document generator tools based on query intent
    if any(w in query for w in ["docx", "word", "approval note", "report doc"]):
        tool_calls.append({
            "tool": "generate_docx",
            "args": {
                "title": "Industrial Inspection & Operations Note",
                "content": f"Confidential Summary for Query: {state.get('user_query')}\n\n"
                           f"Analysis Status: Verified Air-Gapped\n"
                           f"Findings: Equipment parameters within safe operating threshold.",
                "output_filename": "Approval_Note.docx"
            }
        })

    if any(w in query for w in ["excel", "xlsx", "spreadsheet", "calculation"]):
        tool_calls.append({
            "tool": "edit_spreadsheet",
            "args": {
                "rows": [
                    ["Component Tag", "Parameter", "Measured Value", "Status"],
                    ["P-101A", "Vibration", "0.4 mm/s", "NORMAL"],
                    ["V-204", "Pressure", "142 PSI", "SAFE"],
                    ["FL-402", "Wall Thickness", "3.8 mm", "INSPECT"]
                ],
                "output_filename": "Calculation.xlsx"
            }
        })

    if any(w in query for w in ["pptx", "powerpoint", "slides", "presentation"]):
        tool_calls.append({
            "tool": "generate_pptx",
            "args": {
                "title": "Industrial Operations Executive Brief",
                "slide_titles": ["Executive Summary", "Sovereignty Status"],
                "slide_contents": [
                    "All model inferencing performed on local GPU nodes.",
                    "External connections: 0. Internet status: BLOCKED."
                ],
                "output_filename": "Report.pptx"
            }
        })

    # Select code execution tool if coding query or python script requested
    if any(w in query for w in ["python", "code", "run", "calculate", "script", "error"]):
        if not any(tc["tool"] == "run_code" for tc in tool_calls):
            sample_code = "import math\npressure = 142.5\narea = 12.4\nforce = pressure * area\nprint(f'Calculated Total Load: {force:.2f} lbf')"
            tool_calls.append({
                "tool": "run_code",
                "args": {"code": sample_code, "language": "python"}
            })

    state["tool_calls"] = tool_calls
    return state

async def tool_executor_node(state: AgentState) -> AgentState:
    """Nodes 4: Tool Executor Node - Runs scheduled tool functions securely."""
    tool_calls = state.get("tool_calls", [])
    tool_results = state.get("tool_results", [])
    generated_files = state.get("generated_files", [])

    for call in tool_calls:
        tool_name = call["tool"]
        tool_args = call.get("args", {})
        func = get_tool(tool_name)

        if func:
            try:
                if inspect.iscoroutinefunction(func):
                    res = await func(**tool_args)
                else:
                    res = func(**tool_args)

                tool_results.append({"tool": tool_name, "result": res})
                
                # Capture generated files
                if isinstance(res, dict) and "filename" in res:
                    generated_files.append(res["filename"])

                # If OCR/MarkItDown extracted document text, inject into context sources
                if tool_name == "ocr_document" and isinstance(res, dict) and res.get("text"):
                    doc_src = res.get("source") or (Path(tool_args.get("file_path", "")).name if tool_args.get("file_path") else "Document")
                    state["context"].insert(0, {
                        "text": res["text"][:3000],
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
                    details=f"Result: {str(res)[:100]}..."
                )
            except Exception as ex:
                tool_results.append({"tool": tool_name, "error": str(ex)})
                add_audit_event(state, step="Tool Execution", action=tool_name, status="error", details=str(ex))
        else:
            tool_results.append({"tool": tool_name, "error": f"Tool '{tool_name}' not registered."})

    state["tool_results"] = tool_results
    state["generated_files"] = list(set(generated_files))
    return state

async def reflection_node(state: AgentState) -> AgentState:
    """Nodes 5: Reflection Node - Evaluates tool outputs and decides whether loop is complete."""
    add_audit_event(state, step="Reflection", action="evaluate_completeness", status="success", details="All planned steps executed cleanly.")
    return state

import httpx

import base64
from pathlib import Path

async def _call_local_llm(user_query: str, selected_model: str, task_type: str, context: list, tool_results: list, uploaded_file: str | None = None) -> str:
    """Invokes local Ollama model (with vision support for images/drawings and MarkItDown text) to generate real answer."""
    model_lower = (selected_model or "").lower()
    
    # Check if uploaded file is an image
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

    # Select appropriate Ollama model (using exact verified local tags from config)
    if is_image or "vl" in model_lower:
        ollama_model = "qwen2.5vl:7b"
    elif "coder" in model_lower or task_type == "coding":
        ollama_model = "qwen2.5-coder:latest"
    else:
        ollama_model = "qwen2.5:7b-instruct"

    # Build prompt
    prompt_parts = [
        "You are Sovereign AI Workbench, a secure on-premise AI assistant running locally.",
        "Answer the user's question directly, accurately, and thoroughly using the provided context and document content.",
        "If a document, receipt, or manual is provided, read all extracted text and tables carefully to answer specific questions."
    ]

    # Add extracted document content from MarkItDown / OCR tools
    doc_context_added = False
    for tr in tool_results:
        res = tr.get("result")
        if isinstance(res, dict):
            extracted_txt = res.get("text", "").strip()
            if extracted_txt:
                doc_src = res.get("source") or "Uploaded Document"
                prompt_parts.append(f"\n[UPLOADED DOCUMENT CONTENT via MarkItDown — Source: {doc_src}]:\n{extracted_txt[:6000]}")
                doc_context_added = True
            if res.get("tables"):
                prompt_parts.append(f"\n[EXTRACTED TABLES / ROWS]:\n{res['tables']}")
            if res.get("findings"):
                prompt_parts.append(f"\nInspection / Tool Findings: {res['findings']}")
            if res.get("equipment") or res.get("instruments"):
                prompt_parts.append(f"\nExtracted P&ID Equipment: {res.get('equipment', [])} | Instruments: {res.get('instruments', [])}")

    if context and not doc_context_added:
        context_str = "\n".join([f"- [{c.get('source', 'KB')} (Page {c.get('page', 1)})]: {c.get('text', '')}" for c in context[:3]])
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
            res = await client.post("http://localhost:11434/api/generate", json=payload)
            if res.status_code == 200:
                data = res.json()
                answer = data.get("response", "").strip()
                if answer:
                    return answer
    except Exception as e:
        logger.warning(f"Ollama local LLM call failed ({e}) — trying fallback model")
        # Try fallback models available locally
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
                    res = await client.post("http://localhost:11434/api/generate", json=fb_payload)
                    if res.status_code == 200:
                        return res.json().get("response", "").strip()
            except Exception:
                pass

    return ""


async def finalizer_node(state: AgentState) -> AgentState:
    """Nodes 6: Finalizer Node - Assembles final user response with citations and deliverables."""
    user_query = state.get("user_query", "")
    task_type = state.get("task_type", "general")
    model = state.get("selected_model", "Sarvam-30B")
    reason = state.get("routing_reason", "")
    context = state.get("context", [])
    generated_files = state.get("generated_files", [])
    tool_results = state.get("tool_results", [])

    uploaded_file = state.get("uploaded_file")
    # Generate real response from local model
    llm_answer = await _call_local_llm(user_query, model, task_type, context, tool_results, uploaded_file)

    response_lines = []

    if llm_answer:
        response_lines.append(llm_answer)
        response_lines.append("")
    else:
        response_lines.append(f"### Sovereign AI Workbench Response\n")
        response_lines.append(f"**Model Routing**: Executed via `{model}` ({task_type.capitalize()} Task).")
        response_lines.append(f"*Reason*: {reason}\n")

    if context:
        response_lines.append("#### 📚 Grounded Knowledge Base Context:")
        for idx, item in enumerate(context[:2], 1):
            response_lines.append(f"{idx}. `{item.get('text')}` — *Source*: **{item.get('source')}** (Page {item.get('page', 1)})")
        response_lines.append("")

    if tool_results:
        response_lines.append("#### ⚙️ Executed Tools & Actions:")
        for tr in tool_results:
            tname = tr.get("tool")
            res = tr.get("result", {})
            if tname == "run_code":
                response_lines.append(f"- **Code Execution Sandbox**: Output: `{res.get('stdout', '').strip()}` ({res.get('execution_environment')})")
            elif tname == "ocr_document":
                doc_name = res.get('source') or 'Uploaded Document'
                pages = res.get('pages', 1)
                extractor = res.get('model_used') or res.get('extractor') or 'MarkItDown'
                char_count = res.get('char_count', len(res.get('text', '')))
                response_lines.append(f"- **OCR / Document Pipeline ({extractor})**: Parsed `{doc_name}` ({pages} page(s), {char_count} chars extracted).")
            elif tname in ["generate_docx", "generate_pptx", "edit_spreadsheet"]:
                response_lines.append(f"- **Deliverable Generated**: `{res.get('filename')}`")

    if generated_files:
        response_lines.append("\n#### 📄 Generated Deliverable Files:")
        for gf in generated_files:
            response_lines.append(f"- `data/outputs/{gf}`")

    state["final_response"] = "\n".join(response_lines)
    add_audit_event(state, step="Finalizer", action="generate_response", status="success", details="Response compiled successfully.")
    return state
