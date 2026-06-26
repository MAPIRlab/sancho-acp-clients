#!/usr/bin/env python3
"""Automated test suite for the ACP stdio-to-TCP adapter."""

import subprocess
import socket
import threading
import time
import sys


def run_mock_tcp_server(port: int, stop_event: threading.Event):
    """Starts a mock TCP server that echoes a response to a specific request."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("127.0.0.1", port))
        server_sock.listen(1)
        server_sock.settimeout(2.0)

        try:
            conn, _ = server_sock.accept()
            with conn:
                conn.settimeout(2.0)
                data = conn.recv(1024)
                if data:
                    # Parse and respond
                    assert b"initialize" in data, f"Unexpected request: {data}"
                    response = b'{"jsonrpc":"2.0","id":0,"result":{"agentInfo":{"name":"mock-agent"}}}\n'
                    conn.sendall(response)
        except socket.timeout:
            pass


def main():
    print("Initializing test...")

    # Find a free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    stop_event = threading.Event()
    server_thread = threading.Thread(
        target=run_mock_tcp_server, args=(port, stop_event), daemon=True
    )
    server_thread.start()

    # Wait a moment for server to bind
    time.sleep(0.2)

    # Launch adapter
    print(f"Launching adapter subprocess on port {port}...")
    adapter_cmd = [
        "python3",
        "acp_tcp_stdio_adapter.py",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--connect-retries",
        "5",
        "--retry-delay",
        "0.1",
        "--verbose",
    ]

    proc = subprocess.Popen(
        adapter_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,  # Unbuffered
    )

    try:
        # Send initialize request
        test_request = '{"jsonrpc":"2.0","id":0,"method":"initialize"}\n'
        print(f"Writing request to adapter stdin: {test_request.strip()}")
        proc.stdin.write(test_request)
        proc.stdin.flush()

        # Read response
        print("Reading response from adapter stdout...")
        response = proc.stdout.readline()
        print(f"Received response: {response.strip()}")

        assert (
            "mock-agent" in response
        ), f"Incorrect response received: {response}"
        print("Bidirectional transmission test PASSED!")

        # Close stdin to trigger clean shutdown
        print("Closing stdin to stop the adapter...")
        proc.stdin.close()

        # Wait for process to terminate
        ret_code = proc.wait(timeout=2.0)
        print(f"Adapter exited with code: {ret_code}")
        assert ret_code == 0, f"Adapter exited with non-zero code: {ret_code}"

        print("Adapter clean shutdown test PASSED!")
        print("\nAll tests completed successfully!")
        sys.exit(0)

    except Exception as e:
        print(f"\nTest failed with error: {e}", file=sys.stderr)
        # Capture process output for diagnostics
        try:
            proc.kill()
            stdout, stderr = proc.communicate(timeout=1.0)
            print(f"Subprocess stdout:\n{stdout}", file=sys.stderr)
            print(f"Subprocess stderr:\n{stderr}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
