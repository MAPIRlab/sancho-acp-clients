"""Entry point for ``python -m sancho_cli`` and the ``sancho-cli`` console script."""

from __future__ import annotations

import argparse
import asyncio
import logging

from .app import SanchoCLI


def main() -> None:
    """Parse CLI arguments and launch the interactive application."""
    parser = argparse.ArgumentParser(
        prog="sancho-cli",
        description="Terminal-based ACP client for the Sancho robot agent.",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Auto-connect to this ACP server host on startup.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="TCP port of the ACP server.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    app = SanchoCLI()
    try:
        asyncio.run(app.run(auto_host=args.host, auto_port=args.port))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
