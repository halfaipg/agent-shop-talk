# Model Context Protocol (MCP)

The Model Context Protocol (MCP) is an open standard designed to standardize how Large Language Models (LLMs) communicate with external applications, data sources, and tools.

## Overview

MCP follows a client-server architecture that defines how:
- **Data** (resources)
- **Interactive templates** (prompts)
- **Actionable functions** (tools)

Are exposed by an **MCP server** and consumed by an **MCP client** (which could be an LLM host application or an AI agent).

## Integration Patterns

Agent Shop Talk supports both key integration patterns:

1. **LLM as MCP Client**: An LLM or agent acts as an MCP client, leveraging tools provided by external MCP servers.
2. **Tool as MCP Server**: Expose tools via an MCP server, making them accessible to any MCP-compliant LLM client.

## Protocol Flow

### Connection Establishment
1. Client initiates connection to the server (via stdio, SSE, or other transport)
2. Handshake occurs with capability negotiation
3. Client receives server's available capabilities

### Tool Discovery
The client can discover available tools using the `list_tools` method, which returns:
- Tool names
- Descriptions
- Parameter specifications
- Return value schemas

### Tool Execution
1. Client calls a tool using the `call_tool` method with:
   - Tool name
   - Parameters matching the tool's schema
2. Server executes the tool with the provided parameters
3. Server returns the result to the client

## Connection Types

MCP supports multiple connection types:

1. **Local Process Communication (stdio)**
   - Used for local tools running in a separate process
   - Parameters passed via `StdioServerParameters`
   - Example: File system tools, local utilities

2. **Remote Server Communication (SSE)**
   - Used for remote tools accessible over HTTP
   - Parameters passed via `SseServerParams`
   - Example: Cloud APIs, web services

## Implementation

In Agent Shop Talk, the MCP protocol is implemented using:

1. **MCPToolset class**: Bridges between MCP servers and LLMs, handling:
   - Connection establishment
   - Tool discovery
   - Call proxying
   - Connection lifecycle management

2. **Tool Registration**: Tools expose themselves via standardized metadata to be discoverable by MCP clients.

3. **Asynchronous Execution**: All MCP operations are designed to be asynchronous, using Python's asyncio library.

## Key Considerations

- **Stateful Sessions**: MCP establishes persistent connections between client and server instances
- **Cleanup**: Proper connection cleanup is essential for resource management
- **Scaling**: For enterprise deployments, consider load balancing, session affinity, and other infrastructure concerns

For more detailed information, refer to the [MCP Specification](https://github.com/model-context-protocol/model-context-protocol) and [MCP Python SDK](https://github.com/model-context-protocol/python-sdk). 