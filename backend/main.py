from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.router_api import router as router_api

app = FastAPI(
    title="Sovereign AI Workbench Backend",
    description="Local Multi-Model Router and Agent Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_api)

@app.get("/")
def read_root():
    return {"message": "Sovereign AI Workbench API is running"}
