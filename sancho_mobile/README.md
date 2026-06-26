# Sancho ACP Mobile Client (Flet)

An Agent Client Protocol (ACP) client with a mobile phone appearance, developed using **Flet** (Material Design 3 framework for Python). It simulates a chat interface to interact with the cognitive robotic agent Sancho.

## Features

- **Dedicated Connection Screen**: Clean UI to input the host address and port.
- **Smartphone Simulation**: Window preset size mimicking a standard smartphone (390×844 px).
- **Modern Dark Theme**: Material Design 3 color palette based on teal.
- **Streaming Messages & Thoughts**: Real-time display of agent text, media blocks, and internal thoughts (`💭`).
- **Interactive Tool Execution Cards**: Visual cards tracking active tool calls, statuses (running, success, error), and outputs.
- **Interactive Permission Dialogs**: Custom modal popups that ask the user to allow or deny protected agent tool executions.
- **Task Interruption**: Send cancel signals during execution.

## Installation

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

You can launch the client using the automated script:

```bash
./run.sh
```

Or run the module directly:

```bash
python3 -m sancho_mobile [host] [port] [--verbose]
```

## Running Tests

Run the TCP transport unit tests:

```bash
pytest tests/ -v
```
