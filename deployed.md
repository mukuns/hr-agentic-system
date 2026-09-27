# Deployment Details

## Deployment Status: Live & Operational ✅

The HR Agentic System is deployed as a unified, free-tier web service on **Render**, integrating the FastAPI application, Agent Orchestrator, Model Context Protocol (MCP) server, SQLite synthetic database, and the policy RAG retrieval index.

---

## Live Endpoints

- **Web Chat Application**: [https://hr-agentic-system.onrender.com/](https://hr-agentic-system.onrender.com/)
- **Health & Connectivity Status**: [https://hr-agentic-system.onrender.com/health](https://hr-agentic-system.onrender.com/health)
- **Primary Chat API**: `POST https://hr-agentic-system.onrender.com/chat`
- **Interactive OpenAPI Documentation**: [https://hr-agentic-system.onrender.com/docs](https://hr-agentic-system.onrender.com/docs)

---

## Live Health Check Verification

A live request to `https://hr-agentic-system.onrender.com/health` returns:

```json
{
  "status": "healthy",
  "mcp_connected": true,
  "tools_discovered": 7,
  "response_time_ms": 0.0
}
```

This confirms:
1. The web service container is healthy and actively serving traffic.
2. The MCP Server is connected and functioning via standard discovery protocol.
3. All 7 HR tools (`search_policy_documents`, `get_policy_section`, `lookup_employee_profile`, `check_pto_balance`, `check_policy_compliance`, `submit_pto_request`, `create_hr_ticket`) are registered and ready for execution.

---

## Deployment Configuration

- **Hosting Platform**: Render (Web Service)
- **Instance Plan**: Free ($0 / month)
- **Runtime**: Python 3
- **Branch**: `main`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn src.api:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: Port bound dynamically via Render `$PORT`.

---

## Free-Tier Cold-Start Notes

Because the service runs on Render's free tier:
- **Idle Spin-Down**: The container automatically spins down after 15 minutes of inactivity to conserve resources.
- **Cold-Start Latency**: The initial incoming request after sleep will take approximately **20–60 seconds** as the container spins up and boots.
- **Warm Performance**: Once initialized, all subsequent API requests respond rapidly within **< 15 ms**.
- **Data Persistence**: The SQLite synthetic database (`data/mock_db/hr_mock.db`) and policy RAG index (`data/rag_index/rag_index.db`) are bundled directly within the repository, ensuring zero data loss across restarts.
