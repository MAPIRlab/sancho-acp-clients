# ACP TCP Stdio Bridge

This directory contains a **stdio-to-TCP bridge** for the Sancho ACP server. Since many clients and editors (such as `acp-ui` or other integration tools) only support communication with ACP agents via standard input/output (stdio), this tool communicates locally using stdin/stdout pipes and bidirectionally redirects data to the TCP network socket where the main `sancho_acp` server runs on the robot.

## Repository Structure

- `acp_tcp_stdio_adapter.py`: A native Python script (no external dependencies) that bidirectionally redirects streams between `stdin`/`stdout` and the TCP Socket.
- `run_acp_tcp_stdio_adapter.sh`: An optimized launcher bash script to resolve relative paths and isolate the Python environment from potential library path collisions.
- `test_adapter.py`: An automated unit testing suite to verify the bridge's local operation.
- `.env`: Optional configuration file for default values (host and port).

## Client Configuration (acp-ui)

To add the agent to the **acp-ui** client on your local machine, edit or create the configuration file at `~/.config/acp-ui/agents.json` and include the agent definition:

```json
{
  "agents": {
    "Sancho ACP Agent": {
      "command": "/path/to/your/repository/sancho-acp-clients/acp_tcp_stdio_bridge/run_acp_tcp_stdio_adapter.sh",
      "args": [
        "--host", "sancho.isa.uma.es",
        "--port", "9100",
        "--connect-retries", "120",
        "--retry-delay", "0.5"
      ],
      "env": {}
    }
  }
}
```

## Running & Testing

### Local Unit Tests
You can run the suite of local unit tests using:
```bash
python3 test_adapter.py
```

### Manual Execution from Terminal
To manually verify that the adapter successfully connects to the remote robot:
```bash
./run_acp_tcp_stdio_adapter.sh --host sancho.isa.uma.es --port 9100 --connect-retries 5 --retry-delay 0.5 --verbose < /dev/null
```

---

## Troubleshooting

### 1. Python Error in AppImage (`Fatal Python error: init_fs_encoding`)
- **Problem**: When launching the agent from `acp-ui`, it closed immediately with the error `ModuleNotFoundError: No module named 'encodings'`.
- **Cause**: The `acp-ui` AppImage injects environment variables like `PYTHONHOME` and `PYTHONPATH` pointing to its temporary mount. When the adapter script attempted to invoke the system's `python3`, it inherited these incorrect paths and failed to load base modules.
- **Solution**: The `run_acp_tcp_stdio_adapter.sh` script clears these variables (`unset PYTHONHOME` and `unset PYTHONPATH`) before invoking Python, isolating the execution and letting the interpreter work with your system's standard library.

### 2. Client Error (`Agent not found: <UUID>`)
- **Problem**: `acp-ui` displays an error saying that it cannot find the agent by its UUID identifier.
- **Cause**: The local database and Tauri/localstorage cache in `acp-ui` can get corrupted due to previous connection attempts, keeping obsolete UUID mappings instead of reloading the physical config file.
- **Solution**:
  1. Close `acp-ui` completely.
  2. Clear the configuration folder and Tauri local storage:
     ```bash
     rm -rf ~/.config/acp-ui/ ~/.local/share/formulahendry.acp-ui/
     ```
  3. Recreate the configuration directory:
     ```bash
     mkdir -p ~/.config/acp-ui/
     ```
  4. Save the `agents.json` file again with the desired configuration and restart `acp-ui`.
