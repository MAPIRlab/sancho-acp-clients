# Sancho ACP CLI

A terminal-based **ACP (Agent Client Protocol)** client for interacting with the Sancho robot agent over a raw TCP connection.

## Features

- 🎨 **Colourful ASCII art banner** at startup
- 🔌 **Direct TCP connection** to an ACP server (no stdio bridge required)
- 💬 **Interactive prompts** — type natural language and see the agent's streaming response
- ✍️ **Multiline input** — end any line with `\` to write multi-line prompts seamlessly
- 💭 **Real-time observability** — see the agent's internal thoughts, tool calls, and plans
- ⚠️ **Permission handling** — interactively approve or reject sensitive actions
- 🛑 **Cancel** a running task with `/cancel`

## Installation

```bash
cd sancho_acp_clients/sancho_cli

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the dependencies
pip install -r requirements.txt
```

## Usage

### Launch the CLI

```bash
# Interactive mode (connect manually with /connect)
python3 -m sancho_cli

# Auto-connect on startup
python3 -m sancho_cli --host sancho.isa.uma.es --port 9100

# With debug logging
python3 -m sancho_cli --host sancho.isa.uma.es --port 9100 --verbose
```

### Multiline Input

To send a multiline message to the agent, end the lines with a backslash `\`. The prompt will change to `... ` to indicate that it is accumulating lines:

```
> Navigate to room 3 and \
... say hello to the users \
... who are there.
```

If you start typing a multiline input and want to cancel it, press `Ctrl+C` or `Ctrl+D` to clear the buffer.

### Available Commands

| Command                    | Description                              |
|----------------------------|------------------------------------------|
| `/connect <host> <port>`   | Connect to an ACP server over TCP        |
| `/disconnect`              | Close the current session and connection |
| `/cancel`                  | Cancel the agent's current task          |
| `/status`                  | Show connection status                   |
| `/help`                    | List all available commands              |
| `/quit` or `/exit`         | Exit the CLI                             |
| `<any other text>`         | Send as a prompt to the agent            |

### Example Session

```
   ███████╗ █████╗ ███╗   ██╗ ██████╗██╗  ██╗ ██████╗
   ██╔════╝██╔══██╗████╗  ██║██╔════╝██║  ██║██╔═══██╗
   ███████╗███████║██╔██╗ ██║██║     ███████║██║   ██║
   ╚════██║██╔══██║██║╚██╗██║██║     ██╔══██║██║   ██║
   ███████║██║  ██║██║ ╚████║╚██████╗██║  ██║╚██████╔╝
   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝
              ACP Client • v0.1.0

  Type /help for available commands, or /connect <host> <port> to start.

> /connect sancho.isa.uma.es 9100
  Connecting to sancho.isa.uma.es:9100…
┌──────────────────────────────────────┐
│ ✅ Connected                         │
│ Host      sancho.isa.uma.es:9100     │
│ Agent     Sancho ACP Agent           │
│ Session   abc123                     │
┌──────────────────────────────────────┐

> Navigate to room 3 and \
... say hello to the users.
💭 I need to navigate to room 3 first, then use the speaker…
⚙️  Executing tool: navigate_to…
┌──────────────────────────────────────┐
│ ⚠️  Permission Required              │
│                                      │
│   Tool: speak                        │
│   Input: {"text": "Hello!"}          │
│                                      │
│   [1] ✅ Allow once  (allow_once)    │
│   [2] ❌ Reject once (reject_once)   │
└──────────────────────────────────────┘
  Select option [1-2]: 1

I've navigated to room 3 and delivered the message.

> /quit
  Disconnecting…
  Goodbye!
```

## Architecture

This CLI is one of the three heterogeneous ACP clients described in the paper *"Human-Robot Interaction in GenAI Architectures via the Agent-Client Protocol"*. It connects directly to the ACP server running on the robot's cognitive layer via TCP, using the official [ACP Python SDK](https://github.com/agentclientprotocol/python-sdk).

```
┌──────────────┐      TCP       ┌──────────────────┐      MCP      ┌─────────────┐
│  sancho_cli  │ ◄──────────►   │   Sancho ACP     │ ◄──────────►  │  ROS 2 /    │
│  (this CLI)  │    JSON-RPC    │   Agent Server   │   JSON-RPC    │  Hardware   │
└──────────────┘                └──────────────────┘               └─────────────┘
   Interface Layer                 Cognitive Layer                   Execution Layer
```

## Running Tests

```bash
python3 -m pytest tests/ -v
```
