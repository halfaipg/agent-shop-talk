#!/usr/bin/env python3
"""
Test script for Agent Shop Talk integration with Ollama LLM.
Demonstrates how an LLM can use tools through MCP protocol.
"""

import asyncio
import json
import sys
import requests
from typing import Dict, Any, List
import re

from src.mcp_toolset import MCPToolset, StdioServerParameters


# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"  # Using model available on the system
MAX_TOKENS = 1000


def call_ollama(prompt: str, system_prompt: str = None, model_name: str = MODEL_NAME) -> str:
    """Call Ollama API with the given prompt.
    
    Args:
        prompt: The user prompt to send to the model
        system_prompt: Optional system prompt for context
        model_name: The name of the model to use (defaults to MODEL_NAME)
        
    Returns:
        The model's response text
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "max_tokens": MAX_TOKENS
    }
    
    if system_prompt:
        payload["system"] = system_prompt
    
    try:
        print(f"Sending request to Ollama API: {OLLAMA_API_URL}")
        response = requests.post(OLLAMA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
        sys.exit(1)


async def get_calculator_tools():
    """Connect to the calculator MCP server and return tools.
    
    Returns:
        Tuple of (tools, exit_stack)
    """
    return await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command='python3',
            args=['tools/calculator/tool.py']
        )
    )


def create_tool_description(tools: List[Any]) -> str:
    """Create a description of available tools for the model.
    
    Args:
        tools: List of tool objects
        
    Returns:
        Formatted string describing the tools
    """
    description = "You have access to these calculator tools:\n\n"
    
    for tool in tools:
        description += f"Tool: {tool.name}\n"
        description += f"Description: {tool.description}\n"
        
        # Add parameter information
        description += "Parameters:\n"
        for param_name, param_info in tool.parameters.get("properties", {}).items():
            param_type = param_info.get("type", "unknown")
            param_desc = param_info.get("description", "")
            description += f"  - {param_name} ({param_type}): {param_desc}\n"
        
        description += "\n"
    
    description += "To use a tool, respond in this format:\n"
    description += "```json\n{\n  \"tool\": \"tool_name\",\n  \"parameters\": {\n    \"param1\": value1,\n    \"param2\": value2\n  }\n}\n```\n"
    return description


async def extract_tool_calls_from_response(response: str) -> List[Dict[str, Any]]:
    """Extract tool calls from the model's response.
    
    Args:
        response: The model's response text
        
    Returns:
        List of extracted tool call dictionaries
    """
    tool_calls = []
    
    # Find all code blocks that might contain JSON
    json_pattern = r"```(?:json)?\n([\s\S]*?)\n```"
    matches = re.findall(json_pattern, response)
    
    for match in matches:
        try:
            tool_call = json.loads(match.strip())
            if "tool" in tool_call and "parameters" in tool_call:
                tool_calls.append(tool_call)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse JSON: {match}")
    
    # If no code blocks found, try to extract JSON directly
    if not tool_calls:
        try:
            # Find the first occurrence of what looks like a valid JSON object
            json_pattern = r"({[\s\S]*?})"
            matches = re.findall(json_pattern, response)
            
            for match in matches:
                try:
                    tool_call = json.loads(match)
                    if "tool" in tool_call and "parameters" in tool_call:
                        tool_calls.append(tool_call)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"Warning: Error extracting JSON: {e}")
    
    return tool_calls


async def execute_tools_from_response(response: str, tools: List[Any]) -> List[Dict[str, Any]]:
    """Parse the model's response and execute the requested tools.
    
    Args:
        response: The model's response text
        tools: List of available tools
        
    Returns:
        List of tool execution results
    """
    results = []
    
    # Extract tool calls
    tool_calls = await extract_tool_calls_from_response(response)
    
    if not tool_calls:
        return [{"error": "No valid tool calls found in response"}]
    
    print(f"Found {len(tool_calls)} tool calls in the response")
    
    # Execute each tool call
    for i, tool_call in enumerate(tool_calls):
        try:
            tool_name = tool_call.get("tool")
            parameters = tool_call.get("parameters", {})
            
            # Find the requested tool
            tool = next((t for t in tools if t.name == tool_name), None)
            if not tool:
                results.append({"error": f"Tool '{tool_name}' not found"})
                continue
            
            # Execute the tool
            print(f"Executing tool {i+1}/{len(tool_calls)}: {tool_name} with parameters: {parameters}")
            result = await tool.execute(**parameters)
            results.append({"tool": tool_name, "parameters": parameters, "result": result})
        
        except Exception as e:
            results.append({"error": f"Error executing tool: {str(e)}"})
    
    return results


async def run_ollama_mcp_test():
    """Run the Ollama MCP integration test."""
    print("Agent Shop Talk - Ollama LLM Integration Test")
    print("-" * 60)
    
    # Check if Ollama is available
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if not response.ok:
            print("Error: Ollama API is not responding. Is Ollama running?")
            return
        
        available_models = [model.get("name") for model in response.json().get("models", [])]
        if not available_models:
            print("Error: No models found in Ollama. Please pull a model first.")
            return
        
        print(f"Available Ollama models: {', '.join(available_models)}")
        
        # Use the declared model or switch to available one if needed
        model_to_use = MODEL_NAME
        if MODEL_NAME not in available_models:
            print(f"Warning: Model {MODEL_NAME} not found in available models. Using {available_models[0]} instead.")
            model_to_use = available_models[0]
        else:
            print(f"Using model: {MODEL_NAME}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Ollama API. Is Ollama running on localhost:11434?")
        return
    
    # Connect to calculator tools
    print("\nConnecting to calculator MCP server...")
    tools, exit_stack = await get_calculator_tools()
    print(f"Connected! Discovered {len(tools)} tools.")
    
    try:
        # Create tool description for the model
        tool_description = create_tool_description(tools)
        
        # System prompt
        system_prompt = (
            "You are a helpful assistant with access to calculator tools. "
            "When asked to perform calculations, you should use the appropriate tool "
            "rather than doing the calculation yourself. "
            "Respond with a JSON object specifying the tool and parameters."
        )
        
        # User prompt with the math problem
        user_prompt = (
            "I need to solve these math problems:\n"
            "1. What's 42 added to 18?\n"
            "2. If I divide 100 by 5, what do I get?\n"
            "3. What's 9 multiplied by 7?\n"
            "\nPlease solve these using the available tools."
        )
        
        # Combine prompts
        full_prompt = f"{tool_description}\n\n{user_prompt}"
        
        print("\nSending request to Ollama...")
        print(f"Model: {model_to_use}")
        print(f"User prompt: {user_prompt}")
        
        # Call Ollama
        model_response = call_ollama(full_prompt, system_prompt, model_to_use)
        print("\nModel response:")
        print("-" * 40)
        print(model_response)
        print("-" * 40)
        
        # Execute tool calls in the response, just handling the first one for simplicity
        print("\nAttempting to execute tool from response...")
        tool_results = await execute_tools_from_response(model_response, tools)
        
        print("\nTool execution results:")
        print(json.dumps(tool_results, indent=2))
        
        # You could now feed this result back to the model for a complete interaction
        # This would be part of a more complete agent implementation
        
        print("\nTest completed successfully!")
    
    finally:
        # Important: Clean up the connection
        print("\nClosing MCP server connection...")
        await exit_stack.aclose()
        print("Connection closed.")


if __name__ == "__main__":
    try:
        asyncio.run(run_ollama_mcp_test())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {e}")
        sys.exit(1) 