#!/usr/bin/env python3
"""
Test script for Agent Shop Talk tool discovery and usage.
Demonstrates a model discovering tools from a directory and using them via MCP.
"""

import os
import sys
import json
import asyncio
import requests
import importlib.util
from typing import Dict, List, Any, Optional, Callable
import re

from src.work_log import work_log
from src.mcp_server import MCPServer


# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"  # Using model available on the system
MAX_TOKENS = 1000
TOOLS_DIRECTORY = "tools"


class ToolRegistry:
    """Registry for tools loaded from the tools directory."""
    
    def __init__(self, tools_dir: str = TOOLS_DIRECTORY):
        """Initialize the tool registry.
        
        Args:
            tools_dir: Directory containing tool modules
        """
        self.tools_dir = tools_dir
        self.tools: Dict[str, Dict[str, Any]] = {}
        
    def discover_tools(self) -> Dict[str, Dict[str, Any]]:
        """Discover tools from the tools directory.
        
        Returns:
            Dictionary of tool_name -> tool_info
        """
        print(f"Discovering tools in {self.tools_dir}...")
        
        # Ensure the tools directory exists
        if not os.path.exists(self.tools_dir):
            os.makedirs(self.tools_dir)
            print(f"Created tools directory: {self.tools_dir}")
        
        # Find all Python files in the tools directory
        tool_files = []
        for root, _, files in os.walk(self.tools_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    tool_files.append(os.path.join(root, file))
        
        print(f"Found {len(tool_files)} potential tool files")
        
        # Load each tool
        for tool_file in tool_files:
            try:
                # Get the module name
                module_name = os.path.splitext(os.path.basename(tool_file))[0]
                
                # Load the module
                spec = importlib.util.spec_from_file_location(module_name, tool_file)
                if spec is None or spec.loader is None:
                    print(f"Failed to load module from {tool_file}")
                    continue
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check if the module has a tool_info dictionary
                if not hasattr(module, "tool_info"):
                    print(f"Module {module_name} does not have a tool_info dictionary")
                    continue
                
                # Check if the module has a tool_function function
                if not hasattr(module, "tool_function"):
                    print(f"Module {module_name} does not have a tool_function")
                    continue
                
                # Add the tool to the registry
                tool_info = module.tool_info
                tool_info["function"] = module.tool_function
                tool_info["module_name"] = module_name
                tool_info["file_path"] = tool_file
                
                self.tools[tool_info["name"]] = tool_info
                
                print(f"Loaded tool: {tool_info['name']} from {module_name}")
                
                # Log the tool addition
                work_log.log_system_event(
                    event_name="tool_discovered",
                    details={
                        "tool_name": tool_info["name"],
                        "description": tool_info.get("description", ""),
                        "version": tool_info.get("version", "1.0.0"),
                        "module_name": module_name,
                        "file_path": tool_file
                    }
                )
                
            except Exception as e:
                print(f"Error loading tool from {tool_file}: {e}")
        
        return self.tools
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all tools.
        
        Returns:
            List of tool schemas in MCP format
        """
        schemas = []
        
        for tool_name, tool_info in self.tools.items():
            schema = {
                "name": tool_name,
                "description": tool_info.get("description", ""),
                "parameters": tool_info.get("parameters", {}),
                "returns": tool_info.get("returns", {})
            }
            schemas.append(schema)
        
        return schemas
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], agent_id: str, agent_name: str) -> Dict[str, Any]:
        """Execute a tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            agent_id: ID of the agent executing the tool
            agent_name: Name of the agent executing the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If the tool is not found
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool_info = self.tools[tool_name]
        tool_function: Callable = tool_info["function"]
        
        try:
            # Execute the tool
            result = tool_function(**parameters)
            
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


def create_sample_tools():
    """Create sample tools in the tools directory."""
    print("Creating sample tools...")
    
    # Ensure the tools directory exists
    if not os.path.exists(TOOLS_DIRECTORY):
        os.makedirs(TOOLS_DIRECTORY)
    
    # Create a calculator tool
    calculator_code = """
# Calculator Tool
tool_info = {
    "name": "calculator",
    "description": "A simple calculator that can perform basic arithmetic operations",
    "version": "1.0.0",
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "The arithmetic operation to perform"
            },
            "a": {
                "type": "number",
                "description": "The first operand"
            },
            "b": {
                "type": "number",
                "description": "The second operand"
            }
        },
        "required": ["operation", "a", "b"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "result": {
                "type": "number",
                "description": "The result of the arithmetic operation"
            }
        }
    }
}

def tool_function(operation, a, b):
    \"\"\"Perform an arithmetic operation.
    
    Args:
        operation: The arithmetic operation to perform
        a: The first operand
        b: The second operand
        
    Returns:
        The result of the operation
    \"\"\"
    if operation == "add":
        return {"result": a + b}
    elif operation == "subtract":
        return {"result": a - b}
    elif operation == "multiply":
        return {"result": a * b}
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return {"result": a / b}
    else:
        raise ValueError(f"Unknown operation: {operation}")
"""
    
    with open(os.path.join(TOOLS_DIRECTORY, "calculator.py"), "w") as f:
        f.write(calculator_code)
    
    # Create a text analysis tool
    text_analysis_code = """
# Text Analysis Tool
tool_info = {
    "name": "text_analyzer",
    "description": "A tool for analyzing text, including word count, character count, and sentiment",
    "version": "1.0.0",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to analyze"
            },
            "analyze_sentiment": {
                "type": "boolean",
                "description": "Whether to analyze sentiment",
                "default": False
            }
        },
        "required": ["text"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "word_count": {
                "type": "integer",
                "description": "The number of words in the text"
            },
            "character_count": {
                "type": "integer",
                "description": "The number of characters in the text"
            },
            "sentiment": {
                "type": "string",
                "description": "The sentiment of the text (positive, neutral, or negative)",
                "enum": ["positive", "neutral", "negative"]
            }
        }
    }
}

def tool_function(text, analyze_sentiment=False):
    \"\"\"Analyze text.
    
    Args:
        text: The text to analyze
        analyze_sentiment: Whether to analyze sentiment
        
    Returns:
        Analysis results
    \"\"\"
    # Basic analysis
    result = {
        "word_count": len(text.split()),
        "character_count": len(text)
    }
    
    # Sentiment analysis (very simplistic)
    if analyze_sentiment:
        positive_words = ["good", "great", "excellent", "happy", "positive", "wonderful", "best", "love"]
        negative_words = ["bad", "terrible", "awful", "sad", "negative", "worst", "hate"]
        
        positive_count = sum(1 for word in text.lower().split() if word in positive_words)
        negative_count = sum(1 for word in text.lower().split() if word in negative_words)
        
        if positive_count > negative_count:
            result["sentiment"] = "positive"
        elif negative_count > positive_count:
            result["sentiment"] = "negative"
        else:
            result["sentiment"] = "neutral"
    
    return result
"""
    
    with open(os.path.join(TOOLS_DIRECTORY, "text_analyzer.py"), "w") as f:
        f.write(text_analysis_code)
    
    # Create a weather tool
    weather_code = """
# Weather Tool
tool_info = {
    "name": "weather",
    "description": "A tool for getting weather information for a location",
    "version": "1.0.0",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location to get weather for (city, state, country)"
            },
            "units": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "description": "The units to use for temperature (metric or imperial)",
                "default": "metric"
            }
        },
        "required": ["location"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location the weather is for"
            },
            "temperature": {
                "type": "number",
                "description": "The current temperature"
            },
            "conditions": {
                "type": "string",
                "description": "The current weather conditions"
            },
            "units": {
                "type": "string",
                "description": "The units used for temperature (C or F)"
            }
        }
    }
}

def tool_function(location, units="metric"):
    \"\"\"Get weather information.
    
    Args:
        location: The location to get weather for
        units: The units to use for temperature
        
    Returns:
        Weather information
    \"\"\"
    # This is a mock implementation - in a real tool, you would call a weather API
    import random
    
    # Random temperature based on units
    if units == "metric":
        temperature = round(random.uniform(0, 30), 1)
        units_label = "C"
    else:
        temperature = round(random.uniform(32, 90), 1)
        units_label = "F"
    
    # Random conditions
    conditions = random.choice([
        "Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Stormy", "Snowy", "Foggy", "Windy"
    ])
    
    return {
        "location": location,
        "temperature": temperature,
        "conditions": conditions,
        "units": units_label
    }
"""
    
    with open(os.path.join(TOOLS_DIRECTORY, "weather.py"), "w") as f:
        f.write(weather_code)
    
    print(f"Created sample tools in {TOOLS_DIRECTORY}")


def call_ollama(prompt: str, system_prompt: str = None, model_name: str = MODEL_NAME) -> str:
    """Call Ollama API with the given prompt.
    
    Args:
        prompt: The user prompt to send to the model
        system_prompt: Optional system prompt for context
        model_name: The name of the model to use
        
    Returns:
        The model's response
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


def extract_tool_calls_from_response(response: str) -> List[Dict[str, Any]]:
    """Extract tool calls from the model's response.
    
    Args:
        response: The model's response
        
    Returns:
        List of parsed tool calls
    """
    tool_calls = []
    
    # Pattern to find JSON objects in markdown code blocks
    json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(json_pattern, response)
    
    for match in matches:
        try:
            # Try to parse as JSON
            tool_call = json.loads(match.strip())
            
            # Check if it has the expected structure
            if isinstance(tool_call, dict) and "name" in tool_call and "parameters" in tool_call:
                tool_calls.append(tool_call)
        except json.JSONDecodeError:
            continue
    
    # If no markdown code blocks, try to find JSON objects directly
    if not tool_calls:
        json_pattern = r"({[\s\S]*?})"
        matches = re.findall(json_pattern, response)
        
        for match in matches:
            try:
                tool_call = json.loads(match.strip())
                if isinstance(tool_call, dict) and "name" in tool_call and "parameters" in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
    
    return tool_calls


async def run_tool_discovery_test():
    """Run the tool discovery test."""
    print("Agent Shop Talk - Tool Discovery Test")
    print("=" * 60)
    
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
    
    # Create sample tools
    create_sample_tools()
    
    # Initialize the tool registry
    registry = ToolRegistry()
    registry.discover_tools()
    
    # Get tool schemas
    tool_schemas = registry.get_tool_schemas()
    
    # Start MCP server
    mcp_server = MCPServer(registry.execute_tool)
    await mcp_server.start()
    
    print(f"MCP server started with {len(tool_schemas)} tools")
    
    # Create prompts for the model
    system_prompt = (
        "You are an AI assistant with access to a set of tools. "
        "When asked to perform a task, you should call the appropriate tool. "
        "You will analyze the user's request and select the most suitable tool. "
        "Format your response with a JSON object in a code block with the following structure:\n"
        "```json\n"
        "{\n"
        '  "name": "tool_name",\n'
        '  "parameters": {\n'
        '    "param1": value1,\n'
        '    "param2": value2\n'
        '  }\n'
        "}\n"
        "```\n"
        "Only call one tool at a time. If the user request doesn't clearly map to a tool, "
        "respond conversationally instead."
    )
    
    # Define a few test cases
    test_cases = [
        "What's 25 plus 17?",
        "Can you analyze this text: 'The quick brown fox jumps over the lazy dog.'?",
        "What's the weather like in San Francisco?",
        "Calculate 50 divided by 10",
        "Analyze the sentiment of this text: 'I really love this product, it's amazing!'"
    ]
    
    print("\nRunning test cases...")
    
    for i, user_query in enumerate(test_cases):
        print(f"\nTest Case {i+1}: '{user_query}'")
        
        # Send the query to the model
        response = call_ollama(user_query, system_prompt, model_to_use)
        print("Model response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        # Extract tool calls
        tool_calls = extract_tool_calls_from_response(response)
        
        if tool_calls:
            print(f"Extracted {len(tool_calls)} tool call(s)")
            
            # Execute each tool call
            for j, tool_call in enumerate(tool_calls):
                print(f"\nExecuting tool call {j+1}:")
                print(f"  Tool: {tool_call['name']}")
                print(f"  Parameters: {json.dumps(tool_call['parameters'])}")
                
                try:
                    # Execute the tool
                    result = registry.execute_tool(
                        tool_name=tool_call["name"],
                        parameters=tool_call["parameters"],
                        agent_id="ollama_agent",
                        agent_name=f"Ollama ({model_to_use})"
                    )
                    
                    print(f"  Result: {json.dumps(result)}")
                    
                except Exception as e:
                    print(f"  Error: {e}")
        else:
            print("No tool calls extracted from the response")
    
    # Stop MCP server
    await mcp_server.stop()
    print("\nMCP server stopped")
    
    # Print work log summary
    tool_executions = work_log.get_tool_executions()
    print(f"\nLogged {len(tool_executions)} tool executions")
    
    # Show success rate
    successful = [log for log in tool_executions if log["status"] == "success"]
    failed = [log for log in tool_executions if log["status"] == "failure"]
    
    print(f"  Successful executions: {len(successful)}")
    print(f"  Failed executions: {len(failed)}")
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(run_tool_discovery_test())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {e}")
        sys.exit(1) 