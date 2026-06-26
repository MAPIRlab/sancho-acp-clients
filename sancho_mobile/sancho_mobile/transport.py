"""TCP transport for connecting to an ACP server over a raw TCP socket."""

from __future__ import annotations

import asyncio
import logging

log = logging.getLogger(__name__)

DEFAULT_CONNECT_RETRIES = 40
DEFAULT_RETRY_DELAY = 0.5
DEFAULT_CONNECT_TIMEOUT = 10.0


async def connect_tcp(
    host: str,
    port: int,
    *,
    retries: int = DEFAULT_CONNECT_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
    verbose: bool = False,
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Open a TCP connection with configurable retry logic.

    Returns the ``(reader, writer)`` pair that can be passed directly to
    :func:`acp.connect_to_agent`.

    Raises:
        ConnectionError: After exhausting all retry attempts.
    """
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=connect_timeout,
            )
            if verbose:
                log.info("Connected to %s:%s on attempt %d", host, port, attempt)
            return reader, writer
        except (OSError, asyncio.TimeoutError) as exc:
            last_error = exc
            if verbose:
                log.warning(
                    "Connection attempt %d/%d to %s:%s failed: %s",
                    attempt,
                    retries,
                    host,
                    port,
                    exc,
                )
            if attempt < retries:
                await asyncio.sleep(retry_delay)

    raise ConnectionError(
        f"Failed to connect to {host}:{port} after {retries} attempts"
    ) from last_error


async def close_tcp(writer: asyncio.StreamWriter) -> None:
    """Gracefully close a TCP stream writer."""
    try:
        if not writer.is_closing():
            writer.close()
            await writer.wait_closed()
    except OSError:
        pass  # Socket may already be closed by the remote side.
