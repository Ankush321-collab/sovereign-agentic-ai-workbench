from typing import Callable, Dict, Any
from backend.tools.file_tool import read_file, write_file
from backend.tools.code_tool import run_code
from backend.tools.document_tool import generate_docx, generate_pptx, edit_spreadsheet, ocr_document
from backend.services.rag_service import RAGService

# Central Tool Registry mapping tool name to tool function and schema metadata
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "read_file": {
        "function": read_file,
        "description": "Read content from a local file securely.",
        "parameters": ["file_path"]
    },
    "write_file": {
        "function": write_file,
        "description": "Write text content to a file in outputs directory.",
        "parameters": ["file_path", "content"]
    },
    "search_knowledge_base": {
        "function": RAGService.search_knowledge_base,
        "description": "Search local ChromaDB SOP and document knowledge base.",
        "parameters": ["query"]
    },
    "run_code": {
        "function": run_code,
        "description": "Run Python code inside an isolated Docker sandbox (--network none).",
        "parameters": ["code", "language"]
    },
    "generate_docx": {
        "function": generate_docx,
        "description": "Generate an executive/industrial Word (.docx) approval note or document.",
        "parameters": ["title", "content", "output_filename"]
    },
    "generate_pptx": {
        "function": generate_pptx,
        "description": "Generate a PowerPoint (.pptx) presentation deck.",
        "parameters": ["title", "slide_titles", "slide_contents", "output_filename"]
    },
    "edit_spreadsheet": {
        "function": edit_spreadsheet,
        "description": "Generate or edit an Excel (.xlsx) spreadsheet deliverable.",
        "parameters": ["rows", "output_filename"]
    },
    "ocr_document": {
        "function": ocr_document,
        "description": "Run OCR document parsing and visual P&ID / inspection analysis.",
        "parameters": ["file_path"]
    }
}

def get_tool(tool_name: str) -> Callable | None:
    tool_info = TOOL_REGISTRY.get(tool_name)
    return tool_info["function"] if tool_info else None
