"""Tests for the TCP transport module."""

from __future__ import annotations

import asyncio
import socket
import threading

import pytest
import pytest_asyncio

from sancho_mobile.transport import close_tcp, connect_tcp


def _find_free_port() -> int:
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_echo_server(port: int, ready: threading.Event, stop: threading.Event) -> None:
    """Minimal TCP server that accepts one connection and echoes data back."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port))
        srv.listen(1)
        srv.settimeout(5.0)
        ready.set()
        try:
            conn, _ = srv.accept()
            with conn:
                conn.settimeout(2.0)
                while not stop.is_set():
                    try:
                        data = conn.recv(1024)
                        if not data:
                            break
                        conn.sendall(data)
                    except socket.timeout:
                        continue
        except socket.timeout:
            pass


# ── Tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_connect_tcp_success() -> None:
    """Connecting to a running server should succeed on the first attempt."""
    port = _find_free_port()
    ready = threading.Event()
    stop = threading.Event()
    thread = threading.Thread(target=_run_echo_server, args=(port, ready, stop), daemon=True)
    thread.start()
    ready.wait(timeout=2)

    try:
        reader, writer = await connect_tcp(
            "127.0.0.1", port, retries=3, retry_delay=0.1
        )
        # Verify round-trip data.
        writer.write(b"hello\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.readline(), timeout=2)
        assert data == b"hello\n"

        await close_tcp(writer)
    finally:
        stop.set()
        thread.join(timeout=2)


@pytest.mark.asyncio
async def test_connect_tcp_failure() -> None:
    """Connecting to a non-existent server should raise ConnectionError."""
    port = _find_free_port()  # Nobody is listening on this port.
    with pytest.raises(ConnectionError, match="Failed to connect"):
        await connect_tcp("127.0.0.1", port, retries=2, retry_delay=0.05)


@pytest.mark.asyncio
async def test_close_tcp_idempotent() -> None:
    """Closing an already-closed writer should not raise."""
    port = _find_free_port()
    ready = threading.Event()
    stop = threading.Event()
    thread = threading.Thread(target=_run_echo_server, args=(port, ready, stop), daemon=True)
    thread.start()
    ready.wait(timeout=2)

    try:
        _reader, writer = await connect_tcp(
            "127.0.0.1", port, retries=3, retry_delay=0.1
        )
        await close_tcp(writer)
        # Calling close again should be safe.
        await close_tcp(writer)
    finally:
        stop.set()
        thread.join(timeout=2)
