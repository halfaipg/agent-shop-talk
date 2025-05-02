#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server implementation for Agent Shop Talk.
Allows models to discover and use tools.
"""

import os
import json
import asyncio
import websockets
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict

from src.work_log import work_log


@dataclass
class Tool:
    """Represents a tool that can be discovered and used by models."""
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]


class MCPServer:
    """Implementation of the MCP (Model Context Protocol) server.
    
    This server allows models to discover and use tools through a standardized protocol.
    """
    
    def __init__(self, tool_executor: Callable, port: int = 8765):
        """Initialize the MCP server.
        
        Args:
            tool_executor: Function to execute tool calls
            port: Port to run the server on
        """
        self.port = port
        self.tool_executor = tool_executor
        self.server = None
        self.connections: Set[websockets.WebSocketServerProtocol] = set()
        self.tools: Dict[str, Tool] = {}
    
    async def start(self):
        """Start the MCP server."""
        self.server = await websockets.serve(self.handle_connection, "localhost", self.port)
        
        # Log server start
        work_log.log_system_event(
            event_name="mcp_server_started",
            details={
                "port": self.port,
                "num_tools": len(self.tools)
            }
        )
        
        print(f"MCP server started on port {self.port}")
    
    async def stop(self):
        """Stop the MCP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
            # Log server stop
            work_log.log_system_event(
                event_name="mcp_server_stopped",
                details={
                    "port": self.port
                }
            )
            
            print(f"MCP server stopped on port {self.port}")
    
    def register_tool(self, tool: Tool):
        """Register a tool with the server.
        
        Args:
            tool: The tool to register
        """
        self.tools[tool.name] = tool
        
        # Log tool registration
        work_log.log_system_event(
            event_name="tool_registered",
            details={
                "tool_name": tool.name,
                "description": tool.description
            }
        )
        
        print(f"Registered tool: {tool.name}")
    
    def unregister_tool(self, tool_name: str):
        """Unregister a tool from the server.
        
        Args:
            tool_name: Name of the tool to unregister
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            
            # Log tool unregistration
            work_log.log_system_event(
                event_name="tool_unregistered",
                details={
                    "tool_name": tool_name
                }
            )
            
            print(f"Unregistered tool: {tool_name}")
    
    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle a new client connection.
        
        Args:
            websocket: The WebSocket connection
            path: The connection path
        """
        # Add the connection to the set
        self.connections.add(websocket)
        
        # Generate a unique ID for this connection
        connection_id = id(websocket)
        
        # Log connection
        work_log.log_system_event(
            event_name="mcp_client_connected",
            details={
                "connection_id": str(connection_id),
                "path": path
            }
        )
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message, connection_id)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Remove the connection from the set
            self.connections.remove(websocket)
            
            # Log disconnection
            work_log.log_system_event(
                event_name="mcp_client_disconnected",
                details={
                    "connection_id": str(connection_id)
                }
            )
    
    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, 
                            message: str, connection_id: int):
        """Handle a message from a client.
        
        Args:
            websocket: The WebSocket connection
            message: The message received
            connection_id: ID of the connection
        """
        try:
            # Parse the message
            data = json.loads(message)
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "discover_tools":
                # Client is requesting tool discovery
                await self.handle_discover_tools(websocket, data, connection_id)
                
            elif message_type == "execute_tool":
                # Client is requesting tool execution
                await self.handle_execute_tool(websocket, data, connection_id)
                
            else:
                # Unknown message type
                error_response = {
                    "type": "error",
                    "error": "Unknown message type",
                    "original_type": message_type
                }
                await websocket.send(json.dumps(error_response))
                
        except json.JSONDecodeError:
            # Invalid JSON
            error_response = {
                "type": "error",
                "error": "Invalid JSON"
            }
            await websocket.send(json.dumps(error_response))
            
        except Exception as e:
            # General error
            error_response = {
                "type": "error",
                "error": str(e)
            }
            await websocket.send(json.dumps(error_response))
    
    async def handle_discover_tools(self, websocket: websockets.WebSocketServerProtocol, 
                                  data: Dict[str, Any], connection_id: int):
        """Handle a discover_tools message.
        
        Args:
            websocket: The WebSocket connection
            data: The message data
            connection_id: ID of the connection
        """
        # Create tool schemas
        tool_schemas = []
        for tool in self.tools.values():
            tool_schemas.append(asdict(tool))
        
        # Send the response
        response = {
            "type": "tool_discovery_result",
            "tools": tool_schemas
        }
        await websocket.send(json.dumps(response))
        
        # Log tool discovery
        work_log.log_system_event(
            event_name="tools_discovered",
            details={
                "connection_id": str(connection_id),
                "num_tools": len(tool_schemas),
                "tools": [tool["name"] for tool in tool_schemas]
            }
        )
    
    async def handle_execute_tool(self, websocket: websockets.WebSocketServerProtocol, 
                                data: Dict[str, Any], connection_id: int):
        """Handle an execute_tool message.
        
        Args:
            websocket: The WebSocket connection
            data: The message data
            connection_id: ID of the connection
        """
        # Extract tool name and parameters
        tool_name = data.get("tool_name")
        parameters = data.get("parameters", {})
        agent_id = data.get("agent_id", f"connection_{connection_id}")
        agent_name = data.get("agent_name", f"MCP Client {connection_id}")
        
        if not tool_name:
            # Missing tool name
            error_response = {
                "type": "error",
                "error": "Missing tool_name"
            }
            await websocket.send(json.dumps(error_response))
            return
        
        try:
            # Execute the tool
            result = self.tool_executor(
                tool_name=tool_name,
                parameters=parameters,
                agent_id=agent_id,
                agent_name=agent_name
            )
            
            # Send the response
            response = {
                "type": "tool_execution_result",
                "tool_name": tool_name,
                "success": True,
                "result": result
            }
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            # Tool execution error
            error_response = {
                "type": "tool_execution_result",
                "tool_name": tool_name,
                "success": False,
                "error": str(e)
            }
            await websocket.send(json.dumps(error_response))
    
    def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast
        """
        websockets.broadcast(self.connections, json.dumps(message))
        
        # Log broadcast
        work_log.log_system_event(
            event_name="mcp_broadcast",
            details={
                "message_type": message.get("type"),
                "num_recipients": len(self.connections)
            }
        ) 