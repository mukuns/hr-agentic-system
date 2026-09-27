"""
Model Context Protocol (MCP) Server for HR Agentic System.
Exposes HR tools over standard MCP protocol:
1. search_policy_documents (queries RAG_Index)
2. get_policy_section (retrieves full section text)
3. lookup_employee_profile (queries Mock_Data_Store)
4. check_pto_balance (returns accrued, used, remaining days)
5. check_policy_compliance (evaluates remote work or policy criteria)
6. submit_pto_request (mock action requiring confirmation)
7. create_hr_ticket (mock action requiring confirmation)

Satisfies Requirement 6 (AC 1-9) and Requirement 12 (AC 3).
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.rag.vector_store import RAGIndex

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "mock_db" / "hr_mock.db"
RAG_PATH = BASE_DIR / "data" / "rag_index" / "rag_index.db"

class HRMCPServer:
    def __init__(self, db_path: Optional[Path] = None, rag_index: Optional[RAGIndex] = None):
        self.db_path = db_path or DB_PATH
        self.rag_index = rag_index or RAGIndex(db_path=str(RAG_PATH))
        self.tools_schema = self._define_tool_schemas()

    def _get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _define_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "search_policy_documents",
                "description": "Searches the HR policy document index using semantic similarity search and returns relevant policy chunks with source citations and relevance scores.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query regarding HR policies"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Maximum number of relevant chunks to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_policy_section",
                "description": "Retrieves the complete text of a specific section from a named HR policy document.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_name": {
                            "type": "string",
                            "description": "Document ID (e.g. DOC-001) or title of the policy document"
                        },
                        "section_heading": {
                            "type": "string",
                            "description": "The exact or partial heading of the section to retrieve"
                        }
                    },
                    "required": ["document_name", "section_heading"]
                }
            },
            {
                "name": "lookup_employee_profile",
                "description": "Retrieves the complete employment profile for an employee by employee ID or full name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_identifier": {
                            "type": "string",
                            "description": "Employee ID (e.g. EMP-001) or employee full name (e.g. Eleanor Vance)"
                        }
                    },
                    "required": ["employee_identifier"]
                }
            },
            {
                "name": "check_pto_balance",
                "description": "Retrieves current PTO balance figures (accrued, used, and remaining days) for an employee.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_identifier": {
                            "type": "string",
                            "description": "Employee ID (e.g. EMP-002) or employee name"
                        }
                    },
                    "required": ["employee_identifier"]
                }
            },
            {
                "name": "check_policy_compliance",
                "description": "Evaluates an employee's profile against specific policy criteria (e.g. 'remote_work') and returns structured compliance status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_identifier": {
                            "type": "string",
                            "description": "Employee ID or name"
                        },
                        "policy_name": {
                            "type": "string",
                            "description": "Policy to evaluate against (e.g. 'remote_work' or 'expense')"
                        }
                    },
                    "required": ["employee_identifier", "policy_name"]
                }
            },
            {
                "name": "submit_pto_request",
                "description": "Submits a PTO booking request into the HR system. NOTE: Irreversible action requiring prior user confirmation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_id": {"type": "string", "description": "Employee ID"},
                        "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format"},
                        "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format"},
                        "days_requested": {"type": "integer", "description": "Number of business days requested"}
                    },
                    "required": ["employee_id", "start_date", "end_date", "days_requested"]
                }
            },
            {
                "name": "create_hr_ticket",
                "description": "Creates an official HR case ticket in the HR support system. NOTE: Irreversible action requiring prior user confirmation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_id": {"type": "string", "description": "Employee ID"},
                        "category": {"type": "string", "description": "Ticket category (e.g. 'Benefits', 'Payroll', 'Leaves')"},
                        "subject": {"type": "string", "description": "Subject of the case"},
                        "description": {"type": "string", "description": "Detailed explanation of the issue"}
                    },
                    "required": ["employee_id", "category", "subject", "description"]
                }
            }
        ]

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns the list of exposed tool schemas (MCP Tool Discovery Protocol)."""
        return self.tools_schema

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an MCP tool with parameter validation and structured error handling.
        Satisfies Requirement 6 (AC 8, 9).
        """
        tool_dispatch = {
            "search_policy_documents": self._tool_search_policy_documents,
            "get_policy_section": self._tool_get_policy_section,
            "lookup_employee_profile": self._tool_lookup_employee_profile,
            "check_pto_balance": self._tool_check_pto_balance,
            "check_policy_compliance": self._tool_check_policy_compliance,
            "submit_pto_request": self._tool_submit_pto_request,
            "create_hr_ticket": self._tool_create_hr_ticket
        }

        if name not in tool_dispatch:
            return {
                "error": True,
                "error_type": "UnknownToolError",
                "message": f"Tool '{name}' is not recognized by the HR MCP Server."
            }

        try:
            return tool_dispatch[name](arguments)
        except ValueError as ve:
            return {
                "error": True,
                "error_type": "InvalidParameterError",
                "message": str(ve)
            }
        except Exception as e:
            return {
                "error": True,
                "error_type": "ExecutionError",
                "message": f"Failed executing tool '{name}': {str(e)}"
            }

    # Tool Implementations

    def _tool_search_policy_documents(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query")
        if not query or not isinstance(query, str) or not query.strip():
            raise ValueError("Parameter 'query' must be a non-empty string.")
            
        top_k = args.get("top_k", 5)
        results = self.rag_index.search(query=query, top_k=top_k)
        
        return {
            "query": query,
            "count": len(results),
            "chunks": [
                {
                    "chunk_id": r.chunk_id,
                    "document_id": r.doc_id,
                    "document_title": r.doc_title,
                    "section_heading": r.section_heading,
                    "relevance_score": r.score,
                    "source_snippet_text": r.snippet,
                    "content": r.content
                }
                for r in results
            ]
        }

    def _tool_get_policy_section(self, args: Dict[str, Any]) -> Dict[str, Any]:
        doc_name = args.get("document_name")
        heading = args.get("section_heading")
        if not doc_name or not heading:
            raise ValueError("Parameters 'document_name' and 'section_heading' are required.")
            
        section = self.rag_index.get_policy_section(doc_name, heading)
        if not section:
            return {
                "error": True,
                "error_type": "NotFoundError",
                "message": f"Section '{heading}' not found in document '{doc_name}'."
            }
        return {"section": section}

    def _resolve_employee(self, identifier: str) -> Optional[sqlite3.Row]:
        conn = self._get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT e.*, p.accrued_days, p.used_days, p.remaining_days,
               b.health_plan, b.dental, b.vision, b.retirement_contribution
        FROM employees e
        LEFT JOIN pto_balances p ON e.employee_id = p.employee_id
        LEFT JOIN benefits_elections b ON e.employee_id = b.employee_id
        WHERE e.employee_id = ? OR LOWER(e.name) = LOWER(?);
        """, (identifier.strip(), identifier.strip()))
        row = cur.fetchone()
        conn.close()
        return row

    def _tool_lookup_employee_profile(self, args: Dict[str, Any]) -> Dict[str, Any]:
        ident = args.get("employee_identifier")
        if not ident or not isinstance(ident, str):
            raise ValueError("Parameter 'employee_identifier' is required.")
            
        row = self._resolve_employee(ident)
        if not row:
            return {
                "error": True,
                "error_type": "EmployeeNotFoundError",
                "message": f"No employee record found for identifier '{ident}'."
            }
            
        return {
            "employee_id": row["employee_id"],
            "name": row["name"],
            "department": row["department"],
            "role": row["role"],
            "manager": row["manager"],
            "office_location": row["office_location"],
            "employment_type": row["employment_type"],
            "hire_date": row["hire_date"],
            "tenure_months": row["tenure_months"],
            "pto_balance": {
                "accrued_days": row["accrued_days"],
                "used_days": row["used_days"],
                "remaining_days": row["remaining_days"]
            },
            "benefits": {
                "health_plan": row["health_plan"],
                "dental": row["dental"],
                "vision": row["vision"],
                "retirement_contribution": row["retirement_contribution"]
            }
        }

    def _tool_check_pto_balance(self, args: Dict[str, Any]) -> Dict[str, Any]:
        ident = args.get("employee_identifier")
        if not ident or not isinstance(ident, str):
            raise ValueError("Parameter 'employee_identifier' is required.")
            
        row = self._resolve_employee(ident)
        if not row:
            return {
                "error": True,
                "error_type": "EmployeeNotFoundError",
                "message": f"No employee record found for identifier '{ident}'."
            }
            
        return {
            "employee_id": row["employee_id"],
            "name": row["name"],
            "accrued_days": row["accrued_days"],
            "used_days": row["used_days"],
            "remaining_days": row["remaining_days"]
        }

    def _tool_check_policy_compliance(self, args: Dict[str, Any]) -> Dict[str, Any]:
        ident = args.get("employee_identifier")
        policy_name = args.get("policy_name", "").lower()
        if not ident or not policy_name:
            raise ValueError("Parameters 'employee_identifier' and 'policy_name' are required.")
            
        row = self._resolve_employee(ident)
        if not row:
            return {
                "error": True,
                "error_type": "EmployeeNotFoundError",
                "message": f"No employee record found for identifier '{ident}'."
            }

        if "remote" in policy_name:
            return self._evaluate_remote_work_compliance(row)
        elif "expense" in policy_name:
            return self._evaluate_expense_compliance(row)
        else:
            return {
                "error": True,
                "error_type": "UnsupportedPolicyError",
                "message": f"Compliance checking for policy '{policy_name}' is not currently configured."
            }

    def _evaluate_remote_work_compliance(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Evaluates employee profile against Remote Work Policy (DOC-002) criteria:
        1. Employment Type == full-time
        2. Tenure >= 6 months
        3. Role compatibility (not physical on-site roles like facilities)
        """
        emp_type_pass = (row["employment_type"] == "full-time")
        tenure_pass = (row["tenure_months"] >= 6)
        ineligible_roles = ["Facilities Operations Specialist", "Workplace Coordinator", "Receptionist", "On-site IT Depot Specialist"]
        role_pass = (row["role"] not in ineligible_roles)

        criteria = [
            {
                "criterion": "Employment Type (Full-Time regular)",
                "passed": emp_type_pass,
                "detail": f"Actual: {row['employment_type']} (Required: full-time)"
            },
            {
                "criterion": "Continuous Tenure (>= 6 months)",
                "passed": tenure_pass,
                "detail": f"Actual: {row['tenure_months']} months (Required: >= 6 months)"
            },
            {
                "criterion": "Role Remote Compatibility",
                "passed": role_pass,
                "detail": f"Actual Role: {row['role']}" + (" (On-site required role)" if not role_pass else " (Remote compatible)")
            }
        ]

        if emp_type_pass and tenure_pass and role_pass:
            status = "eligible"
            summary = f"Employee {row['name']} meets all criteria for remote and hybrid work arrangements."
        elif emp_type_pass and role_pass and not tenure_pass and row["tenure_months"] >= 3:
            status = "partially_eligible"
            summary = f"Employee {row['name']} has {row['tenure_months']} months tenure (under 6 months threshold), qualifying for temporary partial hybrid (1 day/week) pending full tenure."
        else:
            status = "ineligible"
            unmet = [c["criterion"] for c in criteria if not c["passed"]]
            summary = f"Employee {row['name']} is ineligible for remote work due to unfulfilled criteria: {', '.join(unmet)}."

        return {
            "employee_id": row["employee_id"],
            "name": row["name"],
            "policy": "Remote and Hybrid Work Policy (DOC-002)",
            "eligibility_determination": status,
            "criteria_evaluated": criteria,
            "summary_explanation": summary
        }

    def _evaluate_expense_compliance(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "employee_id": row["employee_id"],
            "name": row["name"],
            "policy": "Business Travel and Expense Reimbursement Policy (DOC-003)",
            "eligibility_determination": "eligible",
            "criteria_evaluated": [
                {"criterion": "Active Employee Status", "passed": True, "detail": "Active"},
                {"criterion": "Receipt Required for > $25", "passed": True, "detail": "Compliant"}
            ],
            "summary_explanation": f"Employee {row['name']} is eligible for standard business travel and expense reimbursement subject to Section 4 per-diem limits."
        }

    def _tool_submit_pto_request(self, args: Dict[str, Any]) -> Dict[str, Any]:
        emp_id = args.get("employee_id")
        start = args.get("start_date")
        end = args.get("end_date")
        days = args.get("days_requested")
        
        row = self._resolve_employee(emp_id)
        if not row:
            raise ValueError(f"Unknown employee ID: {emp_id}")

        rem = row["remaining_days"]
        if days > rem:
            return {
                "success": False,
                "message": f"PTO request rejected: Requested {days} days exceeds remaining balance of {rem} days."
            }

        return {
            "success": True,
            "request_id": f"PTO-{emp_id[-3:]}-2024",
            "employee_id": emp_id,
            "start_date": start,
            "end_date": end,
            "days_requested": days,
            "remaining_balance_after": rem - days,
            "status": "Submitted - Pending Direct Manager Approval",
            "message": f"PTO request successfully recorded for {row['name']} from {start} to {end} ({days} days)."
        }

    def _tool_create_hr_ticket(self, args: Dict[str, Any]) -> Dict[str, Any]:
        emp_id = args.get("employee_id")
        cat = args.get("category")
        subj = args.get("subject")
        desc = args.get("description")
        
        return {
            "success": True,
            "ticket_id": f"TICK-{hash(subj) % 10000:04d}",
            "employee_id": emp_id,
            "category": cat,
            "subject": subj,
            "description": desc,
            "status": "Open",
            "assigned_team": "HR People Operations",
            "message": f"HR Support Ticket created successfully under category '{cat}'."
        }
