"""
Calculator tool that provides basic arithmetic operations via MCP for Agent Shop Talk.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any

# Add the project root to the Python path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mcp_server import (
    MCPServer,
    ToolDefinition,
    InitializationOptions,
    NotificationOptions,
    create_stdio_server,
)


async def add(a: float, b: float) -> Dict[str, Any]:
    """Add two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Result of a + b
    """
    result = a + b
    return {"value": result}


async def subtract(a: float, b: float) -> Dict[str, Any]:
    """Subtract b from a.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Result of a - b
    """
    result = a - b
    return {"value": result}


async def multiply(a: float, b: float) -> Dict[str, Any]:
    """Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Result of a * b
    """
    result = a * b
    return {"value": result}


async def divide(a: float, b: float) -> Dict[str, Any]:
    """Divide a by b.
    
    Args:
        a: First number (dividend)
        b: Second number (divisor)
        
    Returns:
        Result of a / b
    """
    if b == 0:
        raise ValueError("Division by zero")
    result = a / b
    return {"value": result}


def register_tools(server: MCPServer):
    """Register calculator tools with the MCP server.
    
    Args:
        server: The MCP server instance
    """
    # Common parameter schema for all operations
    number_params = {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"}
        },
        "required": ["a", "b"]
    }
    
    # Common return schema for all operations
    result_schema = {
        "type": "object",
        "properties": {
            "value": {"type": "number", "description": "The result of the operation"}
        }
    }
    
    # Register addition tool
    server.register_tool(
        ToolDefinition(
            name="add",
            description="Add two numbers together",
            parameters=number_params,
            returns=result_schema,
            handler=add
        )
    )
    
    # Register subtraction tool
    server.register_tool(
        ToolDefinition(
            name="subtract",
            description="Subtract the second number from the first",
            parameters=number_params,
            returns=result_schema,
            handler=subtract
        )
    )
    
    # Register multiplication tool
    server.register_tool(
        ToolDefinition(
            name="multiply",
            description="Multiply two numbers together",
            parameters=number_params,
            returns=result_schema,
            handler=multiply
        )
    )
    
    # Register division tool
    server.register_tool(
        ToolDefinition(
            name="divide",
            description="Divide the first number by the second",
            parameters=number_params,
            returns=result_schema,
            handler=divide
        )
    )


async def run_server():
    """Run the calculator MCP server."""
    server = MCPServer(name="calculator")
    register_tools(server)
    
    print("Starting Calculator MCP Server...")
    
    # Define capabilities and options
    notification_options = NotificationOptions(
        supports_progress=False,
        supports_log=True,
        supports_status=True
    )
    
    initialization_options = InitializationOptions(
        server_name="calculator",
        server_version="0.1.0",
        capabilities=server.get_capabilities(
            notification_options=notification_options,
            experimental_capabilities={},
        ),
    )
    
    # Start the server using standard I/O
    await create_stdio_server(server, initialization_options)


if __name__ == "__main__":
    """Run the calculator MCP server when executed directly."""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nCalculator MCP Server stopped by user.")
    except Exception as e:
        print(f"Calculator MCP Server error: {e}") 