import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from multimodal.config import HOST, PORT, OLLAMA_BASE_URL, VISION_MODEL
from multimodal.schemas import ProcessRequest, ExtractionResult
from multimodal.service import MultimodalEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("multimodal.api")

app = FastAPI(
    title="Sovereign AI Workbench - Multimodal & OCR Service",
    description="Local, air-gapped service for document OCR, markdown conversion, visual defect analysis, and P&ID tag extraction.",
    version="1.0.0"
)

# Enable CORS for local integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = MultimodalEngine()


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "Sovereign AI Workbench - Multimodal Service",
        "owner": "Pankaj",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/multimodal/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "service": "multimodal",
        "version": "1.0.0",
        "ocr_engine_available": engine.document_pipeline.ocr_engine.available,
        "vision_endpoint": OLLAMA_BASE_URL,
        "vision_model": VISION_MODEL
    }


@app.post("/multimodal/process", response_model=ExtractionResult, tags=["Processing"])
async def process_document(request: ProcessRequest):
    """
    Process local document, scan, inspection photo, or P&ID schematic.
    Returns structured markdown text, confidence score, tables, findings, or equipment tags.
    """
    try:
        result = await engine.process_file(request.file_path, options=request.options)
        return result
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Multimodal processing error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Extraction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("multimodal.main:app", host=HOST, port=PORT, reload=True)
