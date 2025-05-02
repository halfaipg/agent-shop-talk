#!/usr/bin/env python3
"""
MCP Proxy Server implementation for Agent Shop Talk.
Connects to multiple MCP servers, aggregates their tools, and routes requests.
"""

import os
import json
import asyncio
import websockets
import subprocess
import requests
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
import logging

from src.work_log import work_log


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_proxy")


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""
    name: str
    type: str  # "command", "websocket", "http"
    
    # For command-based servers
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    
    # For websocket-based servers
    url: Optional[str] = None
    
    # For HTTP-based servers
    http_url: Optional[str] = None
    
    # Optional settings
    timeout: int = 30
    keep_alive: bool = True


class MCPServerConnection:
    """Represents a connection to a single MCP server."""
    
    def __init__(self, config: MCPServerConfig):
        """Initialize an MCP server connection.
        
        Args:
            config: The server configuration
        """
        self.config = config
        self.process = None
        self.websocket = None
        self.tools = {}
        self.connected = False
        
    async def connect(self) -> bool:
        """Connect to the MCP server.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            if self.config.type == "command":
                await self._connect_command()
            elif self.config.type == "websocket":
                await self._connect_websocket()
            elif self.config.type == "http":
                await self._connect_http()
            else:
                logger.error(f"Unknown server type: {self.config.type}")
                return False
            
            # Log the connection
            work_log.log_system_event(
                event_name="mcp_server_connected",
                details={
                    "server_name": self.config.name,
                    "server_type": self.config.type
                }
            )
            
            # Discover tools
            await self.discover_tools()
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MCP server {self.config.name}: {e}")
            return False
    
    async def _connect_command(self):
        """Connect to a command-based MCP server."""
        if not self.config.command:
            raise ValueError("Command is required for command-based servers")
        
        # Prepare environment
        env = os.environ.copy()
        if self.config.env:
            env.update(self.config.env)
        
        # Start the process
        self.process = subprocess.Popen(
            [self.config.command] + (self.config.args or []),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        logger.info(f"Started command-based MCP server: {self.config.name}")
    
    async def _connect_websocket(self):
        """Connect to a websocket-based MCP server."""
        if not self.config.url:
            raise ValueError("URL is required for websocket-based servers")
        
        # Connect to the websocket
        self.websocket = await websockets.connect(self.config.url)
        
        logger.info(f"Connected to websocket-based MCP server: {self.config.name}")
    
    async def _connect_http(self):
        """Connect to an HTTP-based MCP server."""
        if not self.config.http_url:
            raise ValueError("HTTP URL is required for HTTP-based servers")
        
        # Test the connection
        response = requests.get(f"{self.config.http_url}/ping")
        if response.status_code != 200:
            raise ValueError(f"Failed to connect to HTTP server: {response.status_code}")
        
        logger.info(f"Connected to HTTP-based MCP server: {self.config.name}")
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        try:
            if self.config.type == "command" and self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                
                self.process = None
                
            elif self.config.type == "websocket" and self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            self.connected = False
            
            # Log the disconnection
            work_log.log_system_event(
                event_name="mcp_server_disconnected",
                details={
                    "server_name": self.config.name,
                    "server_type": self.config.type
                }
            )
            
            logger.info(f"Disconnected from MCP server: {self.config.name}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server {self.config.name}: {e}")
    
    async def discover_tools(self) -> Dict[str, Any]:
        """Discover tools from the MCP server.
        
        Returns:
            Dictionary of tool_name -> tool_info
        """
        try:
            if self.config.type == "command":
                tools = await self._discover_tools_command()
            elif self.config.type == "websocket":
                tools = await self._discover_tools_websocket()
            elif self.config.type == "http":
                tools = await self._discover_tools_http()
            else:
                logger.error(f"Unknown server type: {self.config.type}")
                return {}
            
            # Update the tools dictionary
            self.tools = tools
            
            # Log the tool discovery
            work_log.log_system_event(
                event_name="mcp_server_tools_discovered",
                details={
                    "server_name": self.config.name,
                    "num_tools": len(tools),
                    "tools": list(tools.keys())
                }
            )
            
            logger.info(f"Discovered {len(tools)} tools from {self.config.name}")
            
            return tools
            
        except Exception as e:
            logger.error(f"Error discovering tools from MCP server {self.config.name}: {e}")
            return {}
    
    async def _discover_tools_command(self) -> Dict[str, Any]:
        """Discover tools from a command-based MCP server."""
        if not self.process:
            raise ValueError("Not connected to command-based server")
        
        # Send a discover_tools request
        request = {
            "type": "discover_tools"
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Read the response
        response_line = self.process.stdout.readline()
        response = json.loads(response_line)
        
        if response.get("type") != "tool_discovery_result":
            raise ValueError(f"Unexpected response type: {response.get('type')}")
        
        # Extract the tools
        tools = {}
        for tool in response.get("tools", []):
            tools[tool["name"]] = {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {}),
                "returns": tool.get("returns", {}),
                "server": self.config.name
            }
        
        return tools
    
    async def _discover_tools_websocket(self) -> Dict[str, Any]:
        """Discover tools from a websocket-based MCP server."""
        if not self.websocket:
            raise ValueError("Not connected to websocket-based server")
        
        # Send a discover_tools request
        request = {
            "type": "discover_tools"
        }
        
        await self.websocket.send(json.dumps(request))
        
        # Read the response
        response_text = await self.websocket.recv()
        response = json.loads(response_text)
        
        if response.get("type") != "tool_discovery_result":
            raise ValueError(f"Unexpected response type: {response.get('type')}")
        
        # Extract the tools
        tools = {}
        for tool in response.get("tools", []):
            tools[tool["name"]] = {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {}),
                "returns": tool.get("returns", {}),
                "server": self.config.name
            }
        
        return tools
    
    async def _discover_tools_http(self) -> Dict[str, Any]:
        """Discover tools from an HTTP-based MCP server."""
        if not self.config.http_url:
            raise ValueError("Not connected to HTTP-based server")
        
        # Send a discover_tools request
        response = requests.post(
            f"{self.config.http_url}/discover_tools",
            json={"type": "discover_tools"}
        )
        
        if response.status_code != 200:
            raise ValueError(f"Error discovering tools: {response.status_code}")
        
        response_data = response.json()
        
        if response_data.get("type") != "tool_discovery_result":
            raise ValueError(f"Unexpected response type: {response_data.get('type')}")
        
        # Extract the tools
        tools = {}
        for tool in response_data.get("tools", []):
            tools[tool["name"]] = {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {}),
                "returns": tool.get("returns", {}),
                "server": self.config.name
            }
        
        return tools
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], agent_id: str, agent_name: str) -> Dict[str, Any]:
        """Execute a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            agent_id: ID of the agent executing the tool
            agent_name: Name of the agent executing the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If the tool is not found or execution fails
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found on server {self.config.name}")
        
        try:
            if self.config.type == "command":
                result = await self._execute_tool_command(tool_name, parameters, agent_id, agent_name)
            elif self.config.type == "websocket":
                result = await self._execute_tool_websocket(tool_name, parameters, agent_id, agent_name)
            elif self.config.type == "http":
                result = await self._execute_tool_http(tool_name, parameters, agent_id, agent_name)
            else:
                raise ValueError(f"Unknown server type: {self.config.type}")
            
            # Log the tool execution
            work_log.log_tool_execution(
                agent_id=agent_id,
                agent_name=agent_name,
                tool_name=tool_name,
                parameters=parameters,
                result=result,
                status="success"
            )
            
            return result
            
        except Exception as e:
            # Log the failed execution
            work_log.log_tool_execution(
                agent_id=agent_id,
                agent_name=agent_name,
                tool_name=tool_name,
                parameters=parameters,
                result=None,
                status="failure",
                error_message=str(e)
            )
            
            raise
    
    async def _execute_tool_command(self, tool_name: str, parameters: Dict[str, Any], agent_id: str, agent_name: str) -> Dict[str, Any]:
        """Execute a tool on a command-based MCP server."""
        if not self.process:
            raise ValueError("Not connected to command-based server")
        
        # Send an execute_tool request
        request = {
            "type": "execute_tool",
            "tool_name": tool_name,
            "parameters": parameters,
            "agent_id": agent_id,
            "agent_name": agent_name
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Read the response
        response_line = self.process.stdout.readline()
        response = json.loads(response_line)
        
        if response.get("type") != "tool_execution_result":
            raise ValueError(f"Unexpected response type: {response.get('type')}")
        
        if not response.get("success", False):
            raise ValueError(f"Tool execution failed: {response.get('error')}")
        
        return response.get("result", {})
    
    async def _execute_tool_websocket(self, tool_name: str, parameters: Dict[str, Any], agent_id: str, agent_name: str) -> Dict[str, Any]:
        """Execute a tool on a websocket-based MCP server."""
        if not self.websocket:
            raise ValueError("Not connected to websocket-based server")
        
        # Send an execute_tool request
        request = {
            "type": "execute_tool",
            "tool_name": tool_name,
            "parameters": parameters,
            "agent_id": agent_id,
            "agent_name": agent_name
        }
        
        await self.websocket.send(json.dumps(request))
        
        # Read the response
        response_text = await self.websocket.recv()
        response = json.loads(response_text)
        
        if response.get("type") != "tool_execution_result":
            raise ValueError(f"Unexpected response type: {response.get('type')}")
        
        if not response.get("success", False):
            raise ValueError(f"Tool execution failed: {response.get('error')}")
        
        return response.get("result", {})
    
    async def _execute_tool_http(self, tool_name: str, parameters: Dict[str, Any], agent_id: str, agent_name: str) -> Dict[str, Any]:
        """Execute a tool on an HTTP-based MCP server."""
        if not self.config.http_url:
            raise ValueError("Not connected to HTTP-based server")
        
        # Send an execute_tool request
        response = requests.post(
            f"{self.config.http_url}/execute_tool",
            json={
                "type": "execute_tool",
                "tool_name": tool_name,
                "parameters": parameters,
                "agent_id": agent_id,
                "agent_name": agent_name
            }
        )
        
        if response.status_code != 200:
            raise ValueError(f"Error executing tool: {response.status_code}")
        
        response_data = response.json()
        
        if response_data.get("type") != "tool_execution_result":
            raise ValueError(f"Unexpected response type: {response_data.get('type')}")
        
        if not response_data.get("success", False):
            raise ValueError(f"Tool execution failed: {response_data.get('error')}")
        
        return response_data.get("result", {})


class MCPProxyServer:
    """MCP Proxy Server that connects to multiple MCP servers."""
    
    def __init__(self, config_path: Optional[str] = None, port: int = 8765):
        """Initialize the MCP Proxy Server.
        
        Args:
            config_path: Path to the server configuration file
            port: Port to run the proxy server on
        """
        self.config_path = config_path
        self.port = port
        self.server = None
        self.connections: Dict[str, MCPServerConnection] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
    
    def load_config(self, config_path: Optional[str] = None) -> List[MCPServerConfig]:
        """Load the server configuration.
        
        Args:
            config_path: Path to the server configuration file
            
        Returns:
            List of server configurations
        """
        if config_path:
            self.config_path = config_path
            
        if not self.config_path:
            logger.warning("No configuration file provided, using empty config")
            return []
        
        try:
            with open(self.config_path, "r") as f:
                config_data = json.load(f)
            
            servers = []
            for server_config in config_data.get("servers", []):
                # Extract the server type
                transport = server_config.get("transport", {})
                
                if "command" in transport:
                    server_type = "command"
                    command = transport["command"]
                    args = transport.get("args", [])
                    env = {}
                    
                    # Extract environment variables
                    for env_var in transport.get("env", []):
                        if env_var in os.environ:
                            env[env_var] = os.environ[env_var]
                    
                    servers.append(MCPServerConfig(
                        name=server_config["name"],
                        type=server_type,
                        command=command,
                        args=args,
                        env=env
                    ))
                    
                elif "type" in transport and transport["type"] == "sse":
                    server_type = "websocket"
                    url = transport["url"]
                    
                    servers.append(MCPServerConfig(
                        name=server_config["name"],
                        type=server_type,
                        url=url
                    ))
                    
                elif "url" in transport:
                    server_type = "http"
                    http_url = transport["url"]
                    
                    servers.append(MCPServerConfig(
                        name=server_config["name"],
                        type=server_type,
                        http_url=http_url
                    ))
            
            logger.info(f"Loaded {len(servers)} server configurations")
            return servers
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return []
    
    async def start(self):
        """Start the MCP Proxy Server."""
        # Load server configurations
        server_configs = self.load_config()
        
        # Connect to servers
        for config in server_configs:
            connection = MCPServerConnection(config)
            success = await connection.connect()
            
            if success:
                self.connections[config.name] = connection
                
                # Add tools to the global tool registry
                for tool_name, tool_info in connection.tools.items():
                    self.tools[tool_name] = tool_info
        
        # Start the websocket server
        self.server = await websockets.serve(self._handle_client, "localhost", self.port)
        
        # Log server start
        work_log.log_system_event(
            event_name="mcp_proxy_server_started",
            details={
                "port": self.port,
                "num_servers": len(self.connections),
                "num_tools": len(self.tools)
            }
        )
        
        logger.info(f"MCP Proxy Server started on port {self.port}")
        logger.info(f"Connected to {len(self.connections)} servers with {len(self.tools)} tools")
    
    async def stop(self):
        """Stop the MCP Proxy Server."""
        # Disconnect from all servers
        for connection in self.connections.values():
            await connection.disconnect()
        
        self.connections.clear()
        self.tools.clear()
        
        # Stop the websocket server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # Log server stop
        work_log.log_system_event(
            event_name="mcp_proxy_server_stopped",
            details={
                "port": self.port
            }
        )
        
        logger.info("MCP Proxy Server stopped")
    
    async def _handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str = ''):
        """Handle a client connection.
        
        Args:
            websocket: The client websocket connection
            path: The connection path (optional, defaults to empty string)
        """
        # Add the client to the set
        self.clients.add(websocket)
        
        # Generate a unique ID for this connection
        connection_id = id(websocket)
        
        # Log the connection
        work_log.log_system_event(
            event_name="mcp_client_connected",
            details={
                "connection_id": str(connection_id),
                "path": path
            }
        )
        
        try:
            async for message in websocket:
                await self._handle_message(websocket, message, connection_id)
                
        except websockets.exceptions.ConnectionClosed:
            pass
            
        finally:
            # Remove the client from the set
            self.clients.remove(websocket)
            
            # Log the disconnection
            work_log.log_system_event(
                event_name="mcp_client_disconnected",
                details={
                    "connection_id": str(connection_id)
                }
            )
    
    async def _handle_message(self, websocket: websockets.WebSocketServerProtocol, message: str, connection_id: int):
        """Handle a message from a client.
        
        Args:
            websocket: The client websocket connection
            message: The message from the client
            connection_id: ID of the connection
        """
        try:
            # Parse the message
            data = json.loads(message)
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "discover_tools":
                await self._handle_discover_tools(websocket, data, connection_id)
                
            elif message_type == "execute_tool":
                await self._handle_execute_tool(websocket, data, connection_id)
                
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
    
    async def _handle_discover_tools(self, websocket: websockets.WebSocketServerProtocol, data: Dict[str, Any], connection_id: int):
        """Handle a discover_tools message.
        
        Args:
            websocket: The client websocket connection
            data: The message data
            connection_id: ID of the connection
        """
        # Return all tools
        tool_schemas = []
        for tool_info in self.tools.values():
            # Create a clean copy without the server field
            schema = {
                "name": tool_info["name"],
                "description": tool_info.get("description", ""),
                "parameters": tool_info.get("parameters", {}),
                "returns": tool_info.get("returns", {})
            }
            tool_schemas.append(schema)
        
        # Send the response
        response = {
            "type": "tool_discovery_result",
            "tools": tool_schemas
        }
        await websocket.send(json.dumps(response))
        
        # Log the tool discovery
        work_log.log_system_event(
            event_name="tools_discovered",
            details={
                "connection_id": str(connection_id),
                "num_tools": len(tool_schemas),
                "tools": [tool["name"] for tool in tool_schemas]
            }
        )
    
    async def _handle_execute_tool(self, websocket: websockets.WebSocketServerProtocol, data: Dict[str, Any], connection_id: int):
        """Handle an execute_tool message.
        
        Args:
            websocket: The client websocket connection
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
        
        # Find the tool
        if tool_name not in self.tools:
            error_response = {
                "type": "error",
                "error": f"Tool {tool_name} not found"
            }
            await websocket.send(json.dumps(error_response))
            return
        
        # Get the server for this tool
        server_name = self.tools[tool_name]["server"]
        server_connection = self.connections.get(server_name)
        
        if not server_connection:
            error_response = {
                "type": "error",
                "error": f"Server {server_name} not connected"
            }
            await websocket.send(json.dumps(error_response))
            return
        
        try:
            # Execute the tool on the appropriate server
            result = await server_connection.execute_tool(
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
        websockets.broadcast(self.clients, json.dumps(message))
        
        # Log the broadcast
        work_log.log_system_event(
            event_name="mcp_broadcast",
            details={
                "message_type": message.get("type"),
                "num_recipients": len(self.clients)
            }
        ) 