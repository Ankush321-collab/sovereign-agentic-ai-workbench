import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import HOST, PORT
from backend.api import chat, upload, agent_api, router_api, network_api, files_api
from backend.rag import rag_api
from backend.multimodal import multimodal_api

app = FastAPI(
    title="Sovereign AI Workbench — Agentic Backend",
    description="On-Premise / Air-Gapped Multi-Model Agentic AI System for Confidential Industrial Environments",
    version="1.0.0"
)

# Enable CORS for React Frontend (Roshan's component)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(agent_api.router)
app.include_router(router_api.router)
app.include_router(network_api.router)
app.include_router(files_api.router)
app.include_router(rag_api.router)
app.include_router(multimodal_api.router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "system": "Sovereign AI Workbench",
        "version": "1.0.0",
        "airgap_mode": True,
        "external_connections": 0
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
