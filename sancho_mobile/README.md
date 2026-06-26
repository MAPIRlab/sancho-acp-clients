# Sancho ACP Mobile Client

An Agent Client Protocol (ACP) client with a mobile phone appearance, developed using **Flet** (Material Design 3 framework for Python). It simulates a chat interface to interact with the cognitive robotic agent Sancho.

## Features

- 📱 **Smartphone Simulation** — window preset size mimicking a standard smartphone (390×844 px)
- 🎨 **Modern Dark Theme** — Material Design 3 color palette based on teal
- 🔌 **Dedicated Connection Screen** — clean UI to input the host address and port
- 💬 **Streaming Messages & Thoughts** — real-time display of agent text, media blocks, and internal thoughts (`💭`)
- ⚙️ **Interactive Tool Cards** — visual cards tracking active tool calls, statuses (running, success, error), and outputs
- ⚠️ **Interactive Permission Dialogs** — custom modal popups that ask the user to allow or deny protected agent tool executions
- 🛑 **Task Interruption** — send cancel signals during execution

## Installation

```bash
cd sancho-acp-clients/sancho_mobile

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the dependencies
pip install -r requirements.txt
```

## Usage

### Launch the Application

You can launch the client using the automated script:

```bash
./run.sh
```

Or run the module directly:

```bash
python3 -m sancho_mobile [host] [port] [--verbose]
```

## Running Tests

```bash
pytest tests/ -v
```
