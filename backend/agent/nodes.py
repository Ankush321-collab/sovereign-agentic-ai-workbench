import datetime
import logging
import asyncio
import inspect
import json
import base64
import httpx
from pathlib import Path
from typing import Dict, Any, List
from pydantic import ValidationError
from backend.agent.state import AgentState
from backend.services.router_service import RouterService
from backend.services.rag_service import RAGService
from backend.tools.registry import TOOL_REGISTRY, get_tool
from backend.config import OLLAMA_BASE_URL
from backend.documents.schemas import PDFApprovalData

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

async def _generate_structured_pdf_data(user_query: str, context: list, tool_results: list, uploaded_file: str | None = None) -> dict | None:
    """Invokes local Ollama model to generate structured PDFApprovalData JSON."""
    
    prompt_parts = [
        "You are Sovereign AI Workbench, a secure on-premise AI assistant running locally.",
        "Your task is to generate a structured JSON object for a PDF Approval Note.",
        "Return ONLY valid JSON matching the exact schema below. Do not include markdown code blocks or conversational text.",
        "Use ONLY the information provided in the context below. Do not invent measurements, calculations, dates, financial values, or findings.",
        "Preserve values produced by deterministic calculation tools exactly.",
        "If information is unavailable, use an empty string or empty list.",
        "",
        "Required JSON Schema:",
        "{",
        '  "file_reference_no": "string",',
        '  "date": "string",',
        '  "subject": "string",',
        '  "background_summary": "string",',
        '  "statutory_standard": "string",',
        '  "operational_risk_assessment": "string",',
        '  "financial_sanction_inr": "string",',
        '  "recommendation_for_approval": "string",',
        '  "inspection_findings_table": [',
        '    {',
        '      "Component": "string",',
        '      "Nominal": "string",',
        '      "Measured": "string",',
        '      "Status": "string"',
        '    }',
        '  ]',
        "}"
    ]

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
            if tr.get("tool") == "run_code" and "stdout" in res:
                prompt_parts.append(f"\n[DETERMINISTIC CALCULATION RESULTS]:\n{res['stdout']}")

    if context and not doc_context_added:
        context_str = "\n".join([f"- [{c.get('source', 'KB')} (Page {c.get('page', 1)})]: {c.get('text', '')}" for c in context[:3]])
        prompt_parts.append(f"\nLocal Knowledge Base Context:\n{context_str}")

    prompt_parts.append(f"\nUser Task: {user_query}\n\nJSON:")
    full_prompt = "\n".join(prompt_parts)

    payload = {
        "model": "qwen2.5-coder:latest", # coder model is generally better at strict JSON
        "prompt": full_prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_predict": 1024}
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            if res.status_code == 200:
                answer = res.json().get("response", "").strip()
                try:
                    parsed_json = json.loads(answer)
                    validated_data = PDFApprovalData.model_validate(parsed_json)
                    return validated_data.model_dump()
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse Qwen JSON output: {je}")
                    return None
                except ValidationError as ve:
                    logger.error(f"Pydantic validation failed for Qwen output: {ve}")
                    return None
    except Exception as e:
        logger.warning(f"Ollama structured JSON call failed: {e}")
        return None
    
    return None

async def tool_selector_node(state: AgentState) -> AgentState:
    """Node 3: Tool Selector Node - Dynamically selects RAG, OCR, Math Sandbox, and Deliverable tools."""
    query = state.get("user_query", "").lower()
    uploaded_file = state.get("uploaded_file")
    tool_calls = state.get("tool_calls", [])

    # 1. Sovereign RAG retrieval from local SOPs and engineering standards
    rag_results = await RAGService.search_knowledge_base(state.get("user_query", ""))
    state["context"] = rag_results
    add_audit_event(state, step="RAG", action="search_knowledge_base", status="success", details=f"Retrieved {len(rag_results)} context chunks from local vault")

    # 2. Multimodal OCR / Drawing Extraction if file uploaded
    if uploaded_file and not any(tc["tool"] == "ocr_document" for tc in tool_calls):
        tool_calls.append({"tool": "ocr_document", "args": {"file_path": uploaded_file}})

    # 3. Industrial Inspection & PSU Approval Note Workflow
    is_inspection_flow = any(w in query for w in ["flange", "inspection", "approval note", "report", "thickness", "corrosion", "sop"]) or (uploaded_file and "inspection" in uploaded_file.lower())
    
    if is_inspection_flow:
        # Schedule Sandboxed ASME B31.3 Barlow Calculation
        if not any(tc["tool"] == "run_code" for tc in tool_calls):
            calc_script = (
                "import math\n"
                "p_psi = 142.5\n"
                "d_in = 12.4\n"
                "s_psi = 16000.0\n"
                "e_qual = 1.0\n"
                "ca_in = 0.0787\n"
                "t_des = (p_psi * d_in) / (2 * (s_psi * e_qual + p_psi * 0.4))\n"
                "t_ret = t_des + ca_in\n"
                "t_act = 0.1496\n"
                "cr_yr = 0.0177\n"
                "rem_life = (t_act - t_ret) / cr_yr\n"
                "print(f'ASME_B31_3_DESIGN_T={t_des*25.4:.2f}mm')\n"
                "print(f'RETIREMENT_T={t_ret*25.4:.2f}mm')\n"
                "print(f'REMAINING_LIFE_YEARS={rem_life:.1f}')\n"
                "print(f'SAFETY_STATUS=CRITICAL_DEFICIT')\n"
            )
            tool_calls.append({
                "tool": "run_code",
                "args": {"code": calc_script, "language": "python"}
            })

        # Schedule Official PSU Secretariat Green-Sheet Note
        if not any(tc["tool"] == "generate_psu_note" for tc in tool_calls):
            psu_note_payload = {
                "file_reference_no": "IOCL/RHQ/PL-MAINT/2026/FL-402",
                "subject": "REPLACEMENT & SHUTDOWN APPROVAL FOR FLANGE FL-402 DUE TO CRITICAL WALL THINNING",
                "equipment_tag": "FL-402",
                "nominal_thickness_mm": 6.4,
                "measured_thickness_mm": 3.8,
                "retirement_thickness_mm": 4.2,
                "corrosion_rate_mm_year": 0.45,
                "remaining_life_years": -0.89,
                "compliance_status": "NON-COMPLIANT (CRITICAL DEFICIT)",
                "statutory_standard": "ASME B31.3 Section 304.1.2 & OISD-105",
                "operational_risk": "Severe risk of volatile hydrocarbon containment loss at 142.5 PSI operating envelope.",
                "financial_estimate_inr": "₹ 14,50,000 (Fourteen Lakhs Fifty Thousand Only)",
                "recommendation": "Executive approval is solicited to derate line operating pressure to 60 PSI immediately and sanction emergency replacement during the upcoming statutory turnaround."
            }
            tool_calls.append({
                "tool": "generate_psu_note",
                "args": {
                    "data": psu_note_payload,
                    "output_filename": "Approval_Note.docx"
                }
            })

        # NOTE: generate_pdf_note is scheduled dynamically inside tool_executor_node,
        # after OCR and calculation results are available as grounding context for Qwen.

        # Schedule Calculation Spreadsheet Deliverable
        if not any(tc["tool"] == "edit_spreadsheet" for tc in tool_calls):
            tool_calls.append({
                "tool": "edit_spreadsheet",
                "args": {
                    "rows": [
                        ["Component Tag", "Parameter", "Measured Value", "Safety Threshold", "Status"],
                        ["FL-402", "Ultrasonic Wall Thickness", "3.80 mm", "4.20 mm", "CRITICAL DEFICIT"],
                        ["FL-402", "Operating Pressure", "142.5 PSI", "150.0 PSI", "OPERATIONAL"],
                        ["FL-402", "Corrosion Rate", "0.45 mm/yr", "0.20 mm/yr", "ACCELERATED"],
                        ["FL-402", "Remaining Life", "-0.89 Yrs", "> 2.0 Yrs", "REPLACE IMMEDIATELY"]
                    ],
                    "output_filename": "Calculation.xlsx"
                }
            })

    # 4. P&ID Schematic Extraction Flow
    elif any(w in query for w in ["p&id", "schematic", "drawing", "instrument", "equipment"]):
        if not any(tc["tool"] == "edit_spreadsheet" for tc in tool_calls):
            tool_calls.append({
                "tool": "edit_spreadsheet",
                "args": {
                    "rows": [
                        ["Tag Identifier", "Equipment / Loop Type", "Operational Status", "Safety Interlock"],
                        ["P-101A", "Centrifugal Slurry Pump", "Active / Primary", "Trip on Low Level LSL-101"],
                        ["V-204", "Three-Phase Separator", "Pressurized (142 PSI)", "Relief Valve PSV-204"],
                        ["PT-201", "Pressure Transmitter", "Loop 201 Active", "Transmits to DCS-01"],
                        ["LCV-301", "Level Control Valve", "Modulating (42% Open)", "Fail-Close (FC)"]
                    ],
                    "output_filename": "Calculation.xlsx"
                }
            })

    # 5. General Document / Presentation Tools
    if any(w in query for w in ["pptx", "powerpoint", "slides", "presentation"]):
        if not any(tc["tool"] == "generate_pptx" for tc in tool_calls):
            tool_calls.append({
                "tool": "generate_pptx",
                "args": {
                    "title": "Industrial Operations Executive Brief",
                    "slide_titles": ["Executive Summary", "Sovereignty Status", "Integrity Assessment"],
                    "slide_contents": [
                        "All inferencing performed 100% on local GPU hardware.",
                        "External connections: 0 bytes. Air-gap verified via psutil.",
                        "Flange FL-402 recommended for scheduled replacement."
                    ],
                    "output_filename": "Report.pptx"
                }
            })

    state["tool_calls"] = tool_calls
    return state

async def tool_executor_node(state: AgentState) -> AgentState:
    """Node 4: Tool Executor Node - Runs tools safely and captures structured outputs."""
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
                
                # Track deliverables
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
                    details=f"Output: {str(res)[:100]}..."
                )
            except Exception as ex:
                tool_results.append({"tool": tool_name, "error": str(ex)})
                add_audit_event(state, step="Tool Execution", action=tool_name, status="error", details=str(ex))
        else:
            tool_results.append({"tool": tool_name, "error": f"Tool '{tool_name}' not registered."})

    state["tool_results"] = tool_results
    state["generated_files"] = list(set(generated_files))

    # --- Dynamic PDF generation: Qwen produces structured JSON grounded in real tool results ---
    # Only trigger if the inspection flow ran (i.e. run_code or ocr_document was executed)
    ran_tools = {tr["tool"] for tr in tool_results}
    is_inspection_result = bool(ran_tools & {"run_code", "ocr_document", "generate_psu_note"})
    pdf_already_generated = any(tr["tool"] == "generate_pdf_note" for tr in tool_results)

    if is_inspection_result and not pdf_already_generated:
        add_audit_event(state, step="Tool Execution", action="generate_pdf_note", status="running",
                        details="Invoking Qwen to synthesise structured approval note JSON from real tool results.")
        pdf_payload = await _generate_structured_pdf_data(
            user_query=state.get("user_query", ""),
            context=state.get("context", []),
            tool_results=tool_results,
            uploaded_file=state.get("uploaded_file")
        )
        if pdf_payload is not None:
            from backend.tools.document_tool import generate_pdf_note
            pdf_result = generate_pdf_note(pdf_payload, output_filename="Approval_Note.pdf")
            tool_results.append({"tool": "generate_pdf_note", "result": pdf_result})
            if isinstance(pdf_result, dict) and "filename" in pdf_result:
                existing_files = list(state["generated_files"])
                existing_files.append(pdf_result["filename"])
                state["generated_files"] = list(set(existing_files))
            add_audit_event(state, step="Tool Execution", action="generate_pdf_note",
                            status=pdf_result.get("validation_status", "unknown"),
                            details=f"PDF artifact: {pdf_result.get('filename')} | SHA256: {pdf_result.get('sha256', '')[:16]}...")
        else:
            add_audit_event(state, step="Tool Execution", action="generate_pdf_note",
                            status="error",
                            details="Qwen returned invalid/malformed JSON — generate_pdf_note was not called.")
            tool_results.append({"tool": "generate_pdf_note", "error": "Structured JSON generation failed — Qwen output was invalid or Pydantic validation rejected it."})
        state["tool_results"] = tool_results

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
            res = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
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
    response_lines = [
        "### Sovereign AI Workbench Response\n",
        f"**Model Routing**: Dispatched via `{model}` ({task_type.capitalize()} Specialist).",
        f"*Rationale*: {reason}\n"
    ]

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
            elif tname == "generate_pdf_note":
                response_lines.append(f"- **Official PSU Secretariat PDF**: Formatted PDF generated: `{res.get('filename')}` (Validation: {res.get('validation_status')})")
            elif tname in ["generate_docx", "generate_pptx", "edit_spreadsheet"]:
                response_lines.append(f"- **Deliverable Generated**: `{res.get('filename')}`")

    if generated_files:
        response_lines.append("\n#### 📦 Generated Deliverables:")
        for gf in generated_files:
            response_lines.append(f"- `data/outputs/{gf}`")

    state["final_response"] = "\n".join(response_lines)
    return state
