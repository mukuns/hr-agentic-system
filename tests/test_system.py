"""
Comprehensive Automated Test Suite for HR Agentic System.
Tests:
- Policy Corpus Ingestion & RAG Index
- MCP Server Tool Discovery and Tool Execution
- Multi-Step Workflow Orchestration (PTO, Remote Work, Out of Scope)
- Safety & Confirmation Prompts
- Web API Endpoints (/health, /chat)
Satisfies Requirements 1-12 and CI/CD criteria.
"""

import pytest
from fastapi.testclient import TestClient
from src.api import app, orchestrator
from src.mcp_server.server import HRMCPServer
from src.mcp_server.client import HRMCPClient

client = TestClient(app)

# 1. MCP Server & Discovery Tests (Requirement 6, Requirement 10 AC 3)
def test_mcp_tool_discovery():
    server = HRMCPServer()
    tools = server.list_tools()
    assert len(tools) >= 5, f"Expected at least 5 tools, found {len(tools)}"
    tool_names = [t["name"] for t in tools]
    assert "search_policy_documents" in tool_names
    assert "get_policy_section" in tool_names
    assert "lookup_employee_profile" in tool_names
    assert "check_pto_balance" in tool_names
    assert "check_policy_compliance" in tool_names

def test_mcp_client_discovery():
    client_instance = HRMCPClient()
    assert client_instance.is_connected is True
    assert len(client_instance.get_tool_names()) >= 5

def test_mcp_lookup_employee():
    server = HRMCPServer()
    res = server.call_tool("lookup_employee_profile", {"employee_identifier": "EMP-002"})
    assert "error" not in res
    assert res["employee_id"] == "EMP-002"
    assert res["name"] == "Marcus Chen"
    assert res["role"] == "Lead Software Engineer"

def test_mcp_check_pto_balance():
    server = HRMCPServer()
    res = server.call_tool("check_pto_balance", {"employee_identifier": "EMP-003"})
    assert "error" not in res
    assert res["remaining_days"] == 0 # Sophia Rodriguez has 0 days balance

def test_mcp_invalid_parameter_error():
    server = HRMCPServer()
    res = server.call_tool("lookup_employee_profile", {"employee_identifier": "INVALID-999"})
    assert res.get("error") is True
    assert res.get("error_type") == "EmployeeNotFoundError"

# 2. RAG Index & Ingestion Tests (Requirement 1, Requirement 2)
def test_rag_search_relevance():
    rag = orchestrator.rag_index
    results = rag.search("How many days of PTO can I carry over to next year?")
    assert len(results) > 0
    top = results[0]
    assert "PTO" in top.doc_title or "Paid Time Off" in top.doc_title
    assert "Rollover" in top.section_heading or "Carryover" in top.section_heading or top.score > 0.15

def test_rag_out_of_scope_rejection():
    rag = orchestrator.rag_index
    # Out of scope query should produce no results or very low scores below threshold
    results = rag.search("How do I repair a flat bicycle tire?", score_threshold=0.10)
    assert len(results) == 0

# 3. Agent Orchestrator Workflows (Requirement 4, 5, 12)
def test_agent_pto_workflow_sufficient_balance():
    res = orchestrator.process_message("What is my PTO balance and can I take 3 days off? My ID is EMP-002")
    assert "Marcus Chen" in res["answer"]
    assert "16 days" in res["answer"]
    assert len(res["tool_call_trace"]) == 3
    assert "[ACTION CONFIRMATION REQUIRED]" in res["answer"]

def test_agent_pto_workflow_insufficient_balance():
    res = orchestrator.process_message("I need 5 days of PTO, my ID is EMP-003")
    assert "Insufficient PTO Balance" in res["answer"]
    assert "Shortfall" in res["answer"]
    assert "Option 1 (Unpaid Leave)" in res["answer"]

def test_agent_remote_work_eligible():
    res = orchestrator.process_message("Am I eligible to work remotely? My ID is EMP-002")
    assert "ELIGIBLE" in res["answer"]
    assert "Marcus Chen" in res["answer"]
    assert "Numbered Next Steps" in res["answer"]
    assert len(res["tool_call_trace"]) == 3

def test_agent_remote_work_ineligible_role():
    # EMP-005 Amina Patel is Facilities Operations Specialist
    res = orchestrator.process_message("Can I work from home? My ID is EMP-005")
    assert "INELIGIBLE" in res["answer"]
    assert "Facilities Operations Specialist" in res["answer"] or "On-site" in res["answer"]

def test_agent_remote_work_partial():
    # EMP-004 Liam Gallagher has 3 months tenure
    res = orchestrator.process_message("Check my remote work eligibility, I am EMP-004")
    assert "PARTIALLY ELIGIBLE" in res["answer"]
    assert "3 months" in res["answer"]

def test_agent_out_of_scope_guardrail():
    res = orchestrator.process_message("What is the recipe for beef bourguignon?")
    assert "outside the scope of available company HR policies" in res["answer"]
    assert len(res["tool_call_trace"]) == 0

# 4. Web API Tests (Requirement 8, Requirement 10 AC 4)
def test_api_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["mcp_connected"] is True
    assert data["tools_discovered"] >= 5

def test_api_chat_endpoint_success():
    resp = client.post("/chat", json={"message": "What is the policy on 401(k) retirement matching?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "citations" in data
    assert "tool_call_trace" in data

def test_api_chat_endpoint_empty_message_validation():
    resp = client.post("/chat", json={"message": "   "})
    assert resp.status_code == 400
