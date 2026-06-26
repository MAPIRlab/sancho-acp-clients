"""Entry point for running the Sancho Mobile client."""

import argparse
import logging
import flet as ft
from .app import SanchoApp


def main() -> None:
    parser = argparse.ArgumentParser(description="Sancho ACP Mobile Client")
    parser.add_argument(
        "host",
        nargs="?",
        default="127.0.0.1",
        help="Default host to show in Connection view",
    )
    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=9100,
        help="Default port to show in Connection view",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = SanchoApp()
    app.host = args.host
    app.port = args.port

    ft.run(app.start)


if __name__ == "__main__":
    main()
