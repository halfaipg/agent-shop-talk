"""
MCP Toolset for connecting to Model Context Protocol servers.

This module provides the core functionality for Agent Shop Talk to connect to
and interact with MCP-compliant servers, allowing discovery and execution of
tools exposed by those servers.
"""

import asyncio
import json
import subprocess
import sys
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Tuple, Union


class ConnectionParams(ABC):
    """Abstract base class for MCP server connection parameters."""
    
    @abstractmethod
    async def establish_connection(self, exit_stack: AsyncExitStack):
        """Establish a connection to the MCP server.
        
        Args:
            exit_stack: An AsyncExitStack for managing resources that need cleanup
            
        Returns:
            A tuple of (read_stream, write_stream) for communicating with the server
        """
        pass


class StdioServerParameters(ConnectionParams):
    """Parameters for connecting to an MCP server via standard I/O."""
    
    def __init__(self, command: str, args: List[str] = None):
        """Initialize parameters for an MCP server that communicates via stdio.
        
        Args:
            command: The command to execute (e.g., 'python', 'npx')
            args: List of arguments to pass to the command
        """
        self.command = command
        self.args = args or []
    
    async def establish_connection(self, exit_stack: AsyncExitStack):
        """Start the process and return streams for communication.
        
        Args:
            exit_stack: An AsyncExitStack for managing process cleanup
            
        Returns:
            Tuple of (read_stream, write_stream)
        """
        process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Register cleanup
        exit_stack.callback(lambda: process.terminate())
        
        return process.stdout, process.stdin


class SseServerParams(ConnectionParams):
    """Parameters for connecting to an MCP server via Server-Sent Events (SSE)."""
    
    def __init__(self, url: str, headers: Dict[str, str] = None):
        """Initialize parameters for an MCP server that communicates via SSE.
        
        Args:
            url: The URL of the SSE endpoint
            headers: Optional HTTP headers for the connection
        """
        self.url = url
        self.headers = headers or {}
    
    async def establish_connection(self, exit_stack: AsyncExitStack):
        """Establish an SSE connection.
        
        Note: This is a placeholder. Actual implementation would use aiohttp or similar.
        
        Args:
            exit_stack: An AsyncExitStack for managing connection cleanup
            
        Returns:
            Tuple of (read_stream, write_stream)
        """
        # This is a placeholder for SSE connection logic
        # In a real implementation, this would use aiohttp or similar for SSE handling
        raise NotImplementedError("SSE connections not yet implemented")


class McpTool:
    """Represents a tool discovered from an MCP server."""
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        parameters: Dict[str, Any], 
        returns: Dict[str, Any],
        toolset: 'MCPToolset'
    ):
        """Initialize an MCP tool.
        
        Args:
            name: The tool name
            description: The tool description
            parameters: Parameter schema for the tool
            returns: Return value schema for the tool
            toolset: The MCPToolset instance that discovered this tool
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.returns = returns
        self.toolset = toolset
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute this tool with the provided parameters.
        
        Args:
            **kwargs: Parameters to pass to the tool
            
        Returns:
            The result of the tool execution
        """
        return await self.toolset.call_tool(self.name, kwargs)


class MCPToolset:
    """Manages connections to MCP servers and exposes their tools."""
    
    def __init__(self, connection_params: ConnectionParams):
        """Initialize the MCP toolset.
        
        Args:
            connection_params: Parameters for connecting to the MCP server
        """
        self.connection_params = connection_params
        self.tools = []
        self.exit_stack = AsyncExitStack()
        self.read_stream = None
        self.write_stream = None
        self.request_id = 1  # Counter for JSON-RPC request IDs
        
    @classmethod
    async def from_server(cls, connection_params: ConnectionParams) -> Tuple[List['McpTool'], AsyncExitStack]:
        """Create an MCPToolset from server connection parameters.
        
        Args:
            connection_params: Parameters for connecting to the MCP server
            
        Returns:
            Tuple of (tools_list, exit_stack)
        """
        toolset = cls(connection_params)
        exit_stack = AsyncExitStack()
        
        await toolset._connect(exit_stack)
        await toolset._discover_tools()
        
        return toolset.tools, exit_stack
    
    async def _connect(self, exit_stack: AsyncExitStack):
        """Establish connection to the MCP server.
        
        Args:
            exit_stack: An AsyncExitStack for managing resource cleanup
        """
        self.exit_stack = exit_stack
        self.read_stream, self.write_stream = await self.connection_params.establish_connection(exit_stack)
        
        # Perform MCP handshake (simplified)
        handshake_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "initialize",
            "params": {
                "client_name": "agent-shop-talk",
                "client_version": "0.1.0",
                # Additional initialization parameters would go here
            }
        }
        
        await self._send_request(handshake_request)
        response = await self._read_response()
        
        # Process handshake response
        print(f"Connected to MCP server: {response.get('result', {}).get('server_name', 'unknown')}")
    
    async def _discover_tools(self):
        """Discover available tools from the MCP server."""
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "list_tools",
            "params": {}
        }
        
        await self._send_request(list_tools_request)
        response = await self._read_response()
        
        # Process tool list
        tools_data = response.get("result", {}).get("tools", [])
        self.tools = [
            self._create_tool_from_schema(tool_data)
            for tool_data in tools_data
        ]
    
    def _create_tool_from_schema(self, tool_data: Dict[str, Any]) -> McpTool:
        """Create a McpTool instance from schema data.
        
        Args:
            tool_data: The tool schema data from the MCP server
            
        Returns:
            A McpTool instance
        """
        name = tool_data.get("name", "unknown_tool")
        description = tool_data.get("description", "")
        parameters = tool_data.get("parameters", {})
        returns = tool_data.get("returns", {})
        
        return McpTool(name, description, parameters, returns, self)
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server.
        
        Args:
            tool_name: The name of the tool to call
            parameters: Parameters to pass to the tool
            
        Returns:
            The result of the tool execution
            
        Raises:
            ValueError: If the tool execution fails or returns an error
        """
        call_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "call_tool",
            "params": {
                "name": tool_name,
                "parameters": parameters
            }
        }
        
        await self._send_request(call_request)
        response = await self._read_response()
        
        # Check for errors
        if "error" in response:
            error = response["error"]
            raise ValueError(f"Tool execution failed: {error.get('message', 'Unknown error')}")
        
        # Return result
        return response.get("result", {}).get("result", {})
    
    def _get_next_id(self) -> int:
        """Get the next request ID and increment the counter.
        
        Returns:
            The next request ID
        """
        current_id = self.request_id
        self.request_id += 1
        return current_id
    
    async def _send_request(self, request: Dict[str, Any]):
        """Send a request to the MCP server.
        
        Args:
            request: The request object to send
        """
        request_json = json.dumps(request) + "\n"
        self.write_stream.write(request_json.encode())
        await self.write_stream.drain()
    
    async def _read_response(self) -> Dict[str, Any]:
        """Read a response from the MCP server.
        
        Returns:
            The parsed response object
        """
        response_line = await self.read_stream.readline()
        if not response_line:
            return {"error": "Empty response from server"}
        
        return json.loads(response_line.decode()) 