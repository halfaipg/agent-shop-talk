#!/usr/bin/env python3
"""
Calculator MCP Server for testing the MCP Proxy Server.
Provides basic arithmetic operations as tools.
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, List, Optional


class CalculatorServer:
    """Simple MCP-compatible calculator server."""
    
    def __init__(self):
        """Initialize the calculator server."""
        self.tools = {
            "calculator.add": {
                "name": "calculator.add",
                "description": "Add two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number"
                        }
                    },
                    "required": ["a", "b"]
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "number",
                            "description": "Sum of a and b"
                        }
                    }
                }
            },
            "calculator.subtract": {
                "name": "calculator.subtract",
                "description": "Subtract one number from another",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "Number to subtract from"
                        },
                        "b": {
                            "type": "number",
                            "description": "Number to subtract"
                        }
                    },
                    "required": ["a", "b"]
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "number",
                            "description": "Result of a - b"
                        }
                    }
                }
            },
            "calculator.multiply": {
                "name": "calculator.multiply",
                "description": "Multiply two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number"
                        }
                    },
                    "required": ["a", "b"]
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "number",
                            "description": "Product of a and b"
                        }
                    }
                }
            },
            "calculator.divide": {
                "name": "calculator.divide",
                "description": "Divide one number by another",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "Numerator"
                        },
                        "b": {
                            "type": "number",
                            "description": "Denominator"
                        }
                    },
                    "required": ["a", "b"]
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "number",
                            "description": "Result of a / b"
                        }
                    }
                }
            }
        }
    
    async def run(self):
        """Run the calculator server using standard input/output."""
        # Use stdin/stdout for communication
        stdin = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(stdin)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        stdout = sys.stdout
        
        print("Calculator MCP Server started", file=sys.stderr)
        
        while True:
            try:
                # Read a line from stdin
                line = await stdin.readline()
                if not line:
                    break
                
                # Parse the message
                message = json.loads(line.decode())
                
                # Handle the message
                response = await self._handle_message(message)
                
                # Send the response
                if response:
                    stdout.write(json.dumps(response) + "\n")
                    stdout.flush()
                
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                
                # Try to send an error response
                error_response = {
                    "type": "error",
                    "error": str(e)
                }
                stdout.write(json.dumps(error_response) + "\n")
                stdout.flush()
    
    async def _handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a message from the client.
        
        Args:
            message: The message from the client
            
        Returns:
            Response to send back to the client
        """
        message_type = message.get("type")
        
        if message_type == "discover_tools":
            return await self._handle_discover_tools(message)
            
        elif message_type == "execute_tool":
            return await self._handle_execute_tool(message)
            
        else:
            return {
                "type": "error",
                "error": f"Unknown message type: {message_type}"
            }
    
    async def _handle_discover_tools(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a discover_tools message.
        
        Args:
            message: The discover_tools message
            
        Returns:
            Tool discovery result
        """
        return {
            "type": "tool_discovery_result",
            "tools": list(self.tools.values())
        }
    
    async def _handle_execute_tool(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an execute_tool message.
        
        Args:
            message: The execute_tool message
            
        Returns:
            Tool execution result
        """
        tool_name = message.get("tool_name")
        parameters = message.get("parameters", {})
        
        # Check if the tool exists
        if tool_name not in self.tools:
            return {
                "type": "tool_execution_result",
                "tool_name": tool_name,
                "success": False,
                "error": f"Tool not found: {tool_name}"
            }
        
        try:
            # Execute the tool
            result = await self._execute_tool(tool_name, parameters)
            
            return {
                "type": "tool_execution_result",
                "tool_name": tool_name,
                "success": True,
                "result": result
            }
            
        except Exception as e:
            return {
                "type": "tool_execution_result",
                "tool_name": tool_name,
                "success": False,
                "error": str(e)
            }
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If the tool execution fails
        """
        # Validate parameters
        tool_info = self.tools[tool_name]
        required_params = tool_info["parameters"].get("required", [])
        
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Execute the tool based on its name
        if tool_name == "calculator.add":
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)
            return {"result": a + b}
            
        elif tool_name == "calculator.subtract":
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)
            return {"result": a - b}
            
        elif tool_name == "calculator.multiply":
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)
            return {"result": a * b}
            
        elif tool_name == "calculator.divide":
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)
            
            if b == 0:
                raise ValueError("Division by zero")
                
            return {"result": a / b}
            
        else:
            raise ValueError(f"Unknown tool: {tool_name}")


if __name__ == "__main__":
    # Set up directories
    os.makedirs("tools/calculator", exist_ok=True)
    
    # Run the calculator server
    server = CalculatorServer()
    asyncio.run(server.run()) 