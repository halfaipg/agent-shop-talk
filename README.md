# Agent Shop Talk

A central command center and tool chest for LLM models in enterprise environments.

## Overview

Agent Shop Talk provides a professional-grade infrastructure for AI agent systems, enabling multiple LLMs to discover and utilize tools, communicate asynchronously, and maintain comprehensive audit trails of their activities. 

This platform is designed for enterprises that need robust, scalable infrastructure for their AI systems with an emphasis on security, reliability, and auditability.

## Key Components

### MCP Proxy Server

The Model Context Protocol (MCP) Proxy Server is the core component that aggregates and serves multiple MCP resource servers through a single interface. It acts as a central hub that:

- Connects to and manages multiple MCP resource servers
- Routes tool requests to the appropriate backend servers
- Provides a unified WebSocket interface for clients
- Logs all tool discovery and execution activities

The MCP Proxy Server supports multiple transport types:

- **Command-based servers**: Started as child processes with stdin/stdout communication
- **WebSocket-based servers**: Connected to via WebSocket protocol
- **HTTP-based servers**: Connected to via HTTP API calls

### Tool Directory

The Tool Directory is a central registry where tools from various MCP servers are cataloged and made available for discovery:

- **Automatic Tool Discovery**: When an MCP server connects to the proxy, its tools are automatically added to the directory
- **Dynamic Updates**: Tools are added or removed as MCP servers connect or disconnect
- **Tool Metadata**: Each tool entry includes name, description, parameter schema, and return schema
- **Hierarchical Namespacing**: Tools are organized by server (e.g., `calculator.add`, `weather.forecast`)

Models can interact with the Tool Directory through the MCP Proxy Server's WebSocket interface:

```python
# List all available tools
await ws.send(json.dumps({"type": "discover_tools"}))
response = await ws.recv()
tools = json.loads(response)["tools"]

# Filter tools by capability
calculator_tools = [tool for tool in tools if tool["name"].startswith("calculator.")]
```

New MCP servers can be added to the directory by:
1. Adding their configuration to `config/mcp_proxy_config.json`
2. Restarting the MCP Proxy Server, or
3. Using the dynamic server registration API at runtime

### A2A Bulletin Board

The Agent-to-Agent (A2A) Bulletin Board enables asynchronous communication between models, allowing them to:

- Post messages to specific topics
- Subscribe to topics of interest
- Target messages to specific agents
- Attach structured metadata to messages
- Retrieve message history with filtering options

### Work Log System

The Work Log maintains a comprehensive audit trail of all system activities, including:

- Tool executions (successful and failed)
- Task completions
- System events
- Agent communications

The logs can be exported in multiple formats (JSON, CSV, TXT) for analysis, reporting, and compliance purposes.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Agent Shop Talk Platform                   │
├──────────────────────────────────────────────────────────────┤
│ ┌───────────────┐  ┌───────────────┐  ┌────────────────────┐ │
│ │  MCP Proxy    │  │ A2A Bulletin  │  │     Work Log       │ │
│ │   Server      │  │     Board     │  │      System        │ │
│ └───────┬───────┘  └───────┬───────┘  └────────────────────┘ │
│         │                  │                    ▲             │
└─────────┼──────────────────┼────────────────────┼─────────────┘
          │                  │                    │
          ▼                  ▼                    │
┌─────────────────┐  ┌─────────────────┐          │
│  MCP Servers    │  │     Agents      │          │
├─────────────────┤  ├─────────────────┤          │
│ ┌─────────────┐ │  │ ┌─────────────┐ │          │
│ │ Calculator  │ │  │ │    LLM 1    │ │          │
│ └─────────────┘ │  │ └─────────────┘ │          │
│ ┌─────────────┐ │  │ ┌─────────────┐ │          │
│ │  Weather    │ │  │ │    LLM 2    │ ├──────────┘
│ └─────────────┘ │  │ └─────────────┘ │
│ ┌─────────────┐ │  │ ┌─────────────┐ │
│ │Text Analysis│ │  │ │    LLM 3    │ │
│ └─────────────┘ │  │ └─────────────┘ │
└─────────────────┘  └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-org/ai-shop-talk.git
   cd ai-shop-talk
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure your MCP servers in `config/mcp_proxy_config.json`:
   ```json
   {
     "servers": [
       {
         "name": "Calculator Server",
         "transport": {
           "command": "python3",
           "args": ["tools/calculator/calculator_server.py"],
           "env": ["API_KEY"]
         }
       }
     ]
   }
   ```

## Usage

### Starting the Proxy Server

```python
from src.mcp_proxy_server import MCPProxyServer

# Initialize and start the server
proxy_server = MCPProxyServer(config_path="config/mcp_proxy_config.json")
await proxy_server.start()
```

### Connecting to the Proxy Server (Client)

```python
import websockets
import json

# Connect to the proxy
async with websockets.connect("ws://localhost:8765") as ws:
    # Discover available tools
    await ws.send(json.dumps({"type": "discover_tools"}))
    response = await ws.recv()
    tools = json.loads(response)["tools"]
    
    # Execute a tool
    await ws.send(json.dumps({
        "type": "execute_tool",
        "tool_name": "calculator.add",
        "parameters": {"a": 5, "b": 3},
        "agent_id": "my_agent",
        "agent_name": "My Agent"
    }))
    result = await ws.recv()
    print(json.loads(result))
```

### Using the A2A Bulletin Board

```python
from src.a2a_bulletin_board import bulletin_board, Message

# Post a message
message_id = bulletin_board.post_message(
    Message(
        content="Task completed successfully",
        sender_id="agent1",
        sender_name="Processing Agent",
        topic="status_updates",
        tags=["task", "completed"]
    )
)

# Subscribe to topics
bulletin_board.subscribe("agent2", ["status_updates", "tasks"])

# Get messages for an agent
messages = bulletin_board.get_subscribed_messages("agent2")
```

### Using the Work Log

```python
from src.work_log import work_log

# Log a tool execution
log_id = work_log.log_tool_execution(
    agent_id="agent1",
    agent_name="Processing Agent",
    tool_name="calculator.add",
    parameters={"a": 5, "b": 3},
    result={"result": 8},
    status="success"
)

# Export logs
logs_json = work_log.export_log(format_type="json")
```

## Testing

Run the proxy server test:
```
python test_mcp_proxy.py
```

Run the A2A bulletin board test:
```
python test_ollama_bulletin_board.py
```

Run the work log test:
```
python test_work_log.py
```

## Creating MCP Tools

To create a new MCP tool server, follow the pattern in `tools/calculator/calculator_server.py`. Each tool server should:

1. Define tool schemas with name, description, parameters, and return types
2. Implement tool execution logic
3. Handle MCP message types (discover_tools, execute_tool)
4. Communicate using the appropriate transport (stdout/stdin, WebSocket, or HTTP)

## Enterprise Features

- **Security**: Transport-level security options for all communications
- **Audit Trail**: Comprehensive logging of all actions and communications
- **High Availability**: Support for multiple server configurations
- **Scalability**: Modular design allows for adding new tool servers without code changes
- **Integration**: Supports various transport mechanisms for diverse IT environments

## Roadmap

- Authentication and authorization for tool access
- Tool versioning and lifecycle management
- Federation across multiple Agent Shop Talk instances
- Advanced monitoring and alerting
- Enterprise SSO integration
- Containerized deployment options

## License

[MIT License](LICENSE)

---

Made by Your Organization © 2025
