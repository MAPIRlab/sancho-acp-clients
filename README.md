# Sancho ACP Clients

This repository contains a set of heterogeneous clients designed to interact with the cognitive agent of the mobile robot **Sancho** through the **ACP (Agent Client Protocol)**.

## Available Clients

The repository is organized into three main components:

### 1. [sancho_cli](sancho_cli/) (Console Client)
An interactive terminal-based command-line interface (CLI) client.
* **Features**: Direct TCP connection, support for multiline input (using `\`), real-time display of the agent's thoughts (`💭`), plans, and tools, as well as interactive management of permission requests.

### 2. [sancho_mobile](sancho_mobile/) (Mobile Client)
A mobile phone simulation GUI client, developed using **Flet** (Material Design 3 framework for Python).
* **Features**: Modern chat interface, streaming thought display, dynamic cards showing the status of tool executions, and interactive popups to authorize or deny protected agent actions.

### 3. [acp_tcp_stdio_bridge](acp_tcp_stdio_bridge/) (TCP-Stdio Bridge)
A bidirectional adapter/bridge between standard input/output (stdio) and TCP network sockets.
* **Purpose**: Allows the use of open-source ACP clients that only support stdio-based communication (such as **acp-ui**) over the network by bidirectionally redirecting data streams to the TCP port where the Sancho server is running.

---

## Prerequisites

Ensure you have Python 3 installed and a virtual environment configured in each folder as described in their respective README files.

To test the general connection with the robot:
* Default Host: `sancho.isa.uma.es`
* Default Port: `9100`
