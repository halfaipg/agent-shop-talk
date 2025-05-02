#!/usr/bin/env python3
"""
Test script for Agent Shop Talk MCP implementation.
Demonstrates using the calculator tool through the MCP protocol.
"""

import asyncio
import sys
from src.mcp_toolset import MCPToolset, StdioServerParameters


async def test_calculator():
    """Test MCP client interaction with the calculator tool."""
    print("Agent Shop Talk - MCP Calculator Test")
    print("-" * 50)
    
    # Connect to the calculator tool server
    print("Connecting to calculator MCP server...")
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command='python3',
            args=['tools/calculator/tool.py']
        )
    )
    
    try:
        print(f"Connected! Discovered {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        print("\nTesting calculator operations:")
        
        # Test addition
        add_tool = next((tool for tool in tools if tool.name == "add"), None)
        if add_tool:
            a, b = 5, 3
            result = await add_tool.execute(a=a, b=b)
            print(f"  {a} + {b} = {result['value']}")
        
        # Test subtraction
        subtract_tool = next((tool for tool in tools if tool.name == "subtract"), None)
        if subtract_tool:
            a, b = 10, 4
            result = await subtract_tool.execute(a=a, b=b)
            print(f"  {a} - {b} = {result['value']}")
        
        # Test multiplication
        multiply_tool = next((tool for tool in tools if tool.name == "multiply"), None)
        if multiply_tool:
            a, b = 7, 6
            result = await multiply_tool.execute(a=a, b=b)
            print(f"  {a} × {b} = {result['value']}")
        
        # Test division
        divide_tool = next((tool for tool in tools if tool.name == "divide"), None)
        if divide_tool:
            a, b = 20, 4
            result = await divide_tool.execute(a=a, b=b)
            print(f"  {a} ÷ {b} = {result['value']}")
            
            # Test division by zero (should raise an error)
            print("\nTesting error handling (division by zero):")
            try:
                await divide_tool.execute(a=5, b=0)
                print("  Error: Division by zero did not raise an exception!")
            except ValueError as e:
                print(f"  Caught expected error: {e}")
        
        print("\nTest completed successfully!")
    
    finally:
        # Important: Clean up the connection
        print("\nClosing MCP server connection...")
        await exit_stack.aclose()
        print("Connection closed.")


if __name__ == "__main__":
    try:
        asyncio.run(test_calculator())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {e}")
        sys.exit(1) 