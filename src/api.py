"""
FastAPI Web Application and API Server for HR Agentic System.
Exposes:
- GET / : Chat UI (serves modern HTML/JS interface)
- POST /chat : JSON chat endpoint returning answer, citations, snippets, tool_call_trace
- GET /health : Health status verifying MCP tool connectivity
Satisfies Requirement 8 (AC 1-8).
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.agent.orchestrator import AgentOrchestrator
from src.mcp_server.client import HRMCPClient

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HR Agentic System",
    description="Agentic RAG & Multi-Step HR Operations with MCP Tool Integration",
    version="1.0.0"
)

# Static files directory
STATIC_DIR = Path(__file__).resolve().parent / "ui" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Shared Agent Orchestrator & Client
orchestrator = AgentOrchestrator()

# Session storage for pending actions (confirmation states)
session_storage: Dict[str, Dict[str, Any]] = {}

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000, description="User message to HR agent")
    session_id: Optional[str] = Field("default", description="Session identifier for multi-turn workflows")

class ChatResponse(BaseModel):
    answer: str
    citations: list
    snippets: list
    tool_call_trace: list
    session_id: str

@app.get("/", response_class=HTMLResponse)
async def serve_chat_ui():
    """Serves the Chat UI at root URL. Satisfies Requirement 8 (AC 1)."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>HR Agentic System UI initializing...</h1>", status_code=200)
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/health")
async def health_check():
    """
    Verifies MCP Server connectivity and returns status.
    Must respond within 5 seconds.
    Satisfies Requirement 8 (AC 4, 5).
    """
    t0 = time.time()
    try:
        # Verify MCP server by running tool discovery check
        tools = orchestrator.mcp_client.server.list_tools()
        mcp_connected = len(tools) >= 5 and (time.time() - t0) <= 5.0
        status = "healthy" if mcp_connected else "degraded"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        status = "degraded"
        mcp_connected = False

    return {
        "status": status,
        "mcp_connected": mcp_connected,
        "tools_discovered": len(tools) if mcp_connected else 0,
        "response_time_ms": round((time.time() - t0) * 1000, 2)
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Primary chat API endpoint.
    Accepts JSON body with message (max 2000 chars).
    Returns answer, citations, snippets, and tool_call_trace within 30 seconds.
    Satisfies Requirement 8 (AC 2, 3, 7, 8).
    """
    # Requirement 8, AC 8: Validate non-empty message
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="A non-empty message field is required."
        )

    session_id = request.session_id or "default"
    session_ctx = session_storage.get(session_id, {})

    t0 = time.time()
    try:
        result = orchestrator.process_message(request.message, session_context=session_ctx)
        
        # Update session context if pending action was generated or cleared
        if "pending_action" in result:
            session_ctx["pending_action"] = result["pending_action"]
            session_storage[session_id] = session_ctx
            
        elapsed = time.time() - t0
        if elapsed > 30.0:
            raise HTTPException(
                status_code=504,
                detail="Request exceeded the 30-second processing limit."
            )

        return ChatResponse(
            answer=result["answer"],
            citations=result.get("citations", []),
            snippets=result.get("snippets", []),
            tool_call_trace=result.get("tool_call_trace", []),
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while processing the request: {str(e)}"
        )
