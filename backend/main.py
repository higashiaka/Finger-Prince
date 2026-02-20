"""
Finger-Prince Backend — FastAPI entry point.
Run: python main.py  (or: uvicorn main:app --reload --port 8000)
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="Finger-Prince API",
    description="핑거 프린스 — DCInside 크롤러 + RAG 검색 엔진",
    version="0.1.0",
)

# Allow requests from Vite dev server and Electron renderer
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "http://localhost:5174",  # Vite alt port
        "app://.",               # Electron production (file:// equiv)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
