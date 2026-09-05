import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import HOST, PORT
from backend.api import chat, upload, agent_api, router_api, network_api, files_api
from backend.rag import rag_api
from backend.multimodal import multimodal_api

app = FastAPI(
    title="VAJRA / SWARAJ Sovereign AI Workbench",
    description="On-Premise 100% Air-Gapped Multi-Model Agentic AI System for PSU & Defence (SIH 2026 Problem Statement 26117)",
    version="2.0.0"
)

# Enable CORS for React Frontend and Open WebUI bridge
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core API routers
# NOTE: router_api has its own prefix="/api/router" built-in
# NOTE: network_api registers both /network/* and /api/network/* paths directly
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(agent_api.router)
app.include_router(router_api.router)        # prefix="/api/router" (built-in)
app.include_router(router_api.legacy_router) # /route, /routing, /models (unprefixed fallback)
app.include_router(network_api.router)       # registers /network/status + /api/network/status
app.include_router(files_api.router)
app.include_router(rag_api.router)
app.include_router(multimodal_api.router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "system": "VAJRA / SWARAJ Sovereign AI Workbench",
        "version": "2.0.0",
        "airgap_mode": True,
        "external_connections": 0,
        "endpoints": {
            "network_status": "/api/network/status",
            "forensic_audit": "/api/network/audit-export",
            "route_query":    "/api/router/route",
            "list_models":    "/api/router/models",
            "agent_run":      "/api/agent/run",
            "docs":           "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
