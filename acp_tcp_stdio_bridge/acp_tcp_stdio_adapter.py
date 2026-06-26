"""Stdio-to-TCP bridge for ACP clients that only support stdio transports."""

import argparse
import os
import socket
import sys
import threading
import time
from contextlib import suppress

BUFFER_SIZE = 65536


def _log(verbose: bool, message: str) -> None:
    if verbose:
        print(f"[acp-stdio-adapter] {message}", file=sys.stderr, flush=True)


def _pump_stdin_to_socket(sock: socket.socket, verbose: bool) -> None:
    try:
        while True:
            chunk = os.read(0, BUFFER_SIZE)
            if not chunk:
                _log(verbose, "stdin closed; shutting down TCP write side")
                with suppress(OSError):
                    sock.shutdown(socket.SHUT_WR)
                break
            sock.sendall(chunk)
    except Exception as exc:
        _log(verbose, f"stdin error: {exc}")


def _pump_socket_to_stdout(sock: socket.socket, verbose: bool) -> None:
    try:
        while True:
            chunk = sock.recv(BUFFER_SIZE)
            if not chunk:
                _log(verbose, "tcp closed by remote")
                break
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
    except BrokenPipeError:
        _log(verbose, "stdout closed by parent process")
    except Exception as exc:
        _log(verbose, f"socket error: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge ACP stdio to TCP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9100)
    parser.add_argument("--connect-retries", type=int, default=40)
    parser.add_argument("--retry-delay", type=float, default=0.5)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    _log(args.verbose, f"connecting to {args.host}:{args.port}")

    sock: socket.socket | None = None
    for attempt in range(1, args.connect_retries + 1):
        try:
            sock = socket.create_connection((args.host, args.port), timeout=10.0)
            break
        except OSError as exc:
            _log(args.verbose, f"connect attempt {attempt}/{args.connect_retries} failed: {exc}")
            if attempt < args.connect_retries:
                time.sleep(args.retry_delay)

    if sock is None:
        print(f"Failed to connect to {args.host}:{args.port} after {args.connect_retries} attempts.", file=sys.stderr)
        return 2

    sock.settimeout(None)
    _log(args.verbose, "connected")

    t_in = threading.Thread(target=_pump_stdin_to_socket, args=(sock, args.verbose), daemon=True)
    t_out = threading.Thread(target=_pump_socket_to_stdout, args=(sock, args.verbose), daemon=True)
    t_in.start()
    t_out.start()

    while t_in.is_alive() and t_out.is_alive():
        time.sleep(0.1)

    with suppress(OSError):
        sock.close()
    _log(args.verbose, "adapter stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
