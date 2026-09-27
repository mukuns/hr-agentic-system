"""
MCP Client for the Agent Orchestrator.
Discovers tools dynamically from the MCP Server and executes tool calls exclusively through
the MCP interface layer.
Satisfies Requirement 6 (AC 7, 8).
"""

import time
import logging
from typing import Dict, Any, List, Optional
from src.mcp_server.server import HRMCPServer

logger = logging.getLogger(__name__)

class HRMCPClient:
    def __init__(self, server: Optional[HRMCPServer] = None):
        self.server = server or HRMCPServer()
        self.discovered_tools: Dict[str, Dict[str, Any]] = {}
        self._connected = False
        self._startup_discovery()

    def _startup_discovery(self):
        """
        Discovers available tools and confirms at least 5 tools are exposed within 10 seconds.
        Satisfies Requirement 6 (AC 7).
        """
        start_time = time.time()
        tools_list = self.server.list_tools()
        elapsed = time.time() - start_time
        
        if elapsed > 10.0:
            logger.error(f"MCP Tool discovery exceeded 10-second threshold ({elapsed:.2f}s).")
            self._connected = False
            return

        for tool in tools_list:
            self.discovered_tools[tool["name"]] = tool

        if len(self.discovered_tools) >= 5:
            self._connected = True
            logger.info(f"MCP Client connected: {len(self.discovered_tools)} tools discovered in {elapsed*1000:.1f}ms.")
        else:
            self._connected = False
            logger.warning(f"MCP Client discovered only {len(self.discovered_tools)} tools (< 5 required).")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def get_tool_names(self) -> List[str]:
        return list(self.discovered_tools.keys())

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return list(self.discovered_tools.values())

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a tool call through the MCP interface layer.
        Satisfies Requirement 6 (AC 8).
        """
        if tool_name not in self.discovered_tools:
            return {
                "error": True,
                "error_type": "ToolNotDiscoveredError",
                "message": f"Tool '{tool_name}' has not been discovered on the MCP Server."
            }

        return self.server.call_tool(tool_name, arguments)
