#!/usr/bin/env python3
"""
Test script for the MCP Proxy Server.
Demonstrates connecting to multiple MCP servers, discovering tools, and executing tools.
"""

import os
import sys
import json
import asyncio
import requests
import websockets
from typing import Dict, List, Any, Optional
import time
import logging

from src.mcp_proxy_server import MCPProxyServer


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_proxy_test")


# Configuration
CONFIG_PATH = "config/mcp_proxy_config.json"
PROXY_PORT = 8765
CLIENT_TIMEOUT = 30


async def test_client(proxy_url: str):
    """Test the MCP Proxy Server as a client.
    
    Args:
        proxy_url: URL of the proxy server
    """
    try:
        # Connect to the proxy server
        logger.info(f"Connecting to MCP Proxy Server: {proxy_url}")
        ws = await websockets.connect(proxy_url)
        
        # Discover tools
        logger.info("Discovering tools...")
        
        discover_request = {
            "type": "discover_tools"
        }
        await ws.send(json.dumps(discover_request))
        
        response_text = await ws.recv()
        response = json.loads(response_text)
        
        if response.get("type") != "tool_discovery_result":
            logger.error(f"Unexpected response type: {response.get('type')}")
            return
        
        tools = response.get("tools", [])
        logger.info(f"Discovered {len(tools)} tools:")
        
        for i, tool in enumerate(tools):
            logger.info(f"  {i+1}. {tool['name']} - {tool['description']}")
        
        # Execute some tools if any are available
        if tools:
            for tool in tools:
                tool_name = tool["name"]
                
                # Example parameters (simplified)
                parameters = {}
                
                if "calculator" in tool_name.lower():
                    parameters = {
                        "operation": "add",
                        "a": 5,
                        "b": 3
                    }
                elif "weather" in tool_name.lower():
                    parameters = {
                        "location": "New York",
                        "units": "metric"
                    }
                elif "text" in tool_name.lower() or "analyze" in tool_name.lower():
                    parameters = {
                        "text": "Hello, world! This is a test.",
                        "analyze_sentiment": True
                    }
                
                # Execute the tool
                logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
                
                execute_request = {
                    "type": "execute_tool",
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "agent_id": "test_client",
                    "agent_name": "Test Client"
                }
                await ws.send(json.dumps(execute_request))
                
                response_text = await ws.recv()
                response = json.loads(response_text)
                
                if response.get("type") != "tool_execution_result":
                    logger.error(f"Unexpected response type: {response.get('type')}")
                    continue
                
                success = response.get("success", False)
                if success:
                    logger.info(f"  Success! Result: {response.get('result')}")
                else:
                    logger.error(f"  Error: {response.get('error')}")
        
        # Close the connection
        await ws.close()
        
    except Exception as e:
        logger.error(f"Error during test: {e}")


async def run_test():
    """Run the MCP Proxy Server test."""
    logger.info("Starting MCP Proxy Server Test")
    
    # Create the proxy server
    proxy_server = MCPProxyServer(config_path=CONFIG_PATH, port=PROXY_PORT)
    
    try:
        # Start the proxy server
        logger.info("Starting the MCP Proxy Server...")
        await proxy_server.start()
        
        # Give it a moment to initialize
        await asyncio.sleep(2)
        
        # Run a client test
        proxy_url = f"ws://localhost:{PROXY_PORT}"
        await test_client(proxy_url)
        
    finally:
        # Stop the proxy server
        logger.info("Stopping the MCP Proxy Server...")
        await proxy_server.stop()
    
    logger.info("Test completed")


if __name__ == "__main__":
    try:
        # Create directories if they don't exist
        os.makedirs("config", exist_ok=True)
        
        # Run the test
        asyncio.run(run_test())
        
    except KeyboardInterrupt:
        logger.info("Test interrupted")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Uncaught exception: {e}")
        sys.exit(1) 