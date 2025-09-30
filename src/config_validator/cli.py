"""Command line entry point for the Config Validation Suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .suite import ConfigValidationSuite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="config-validator",
        description="Validate configuration files across JSON, TOML, and INI formats.",
    )
    parser.add_argument("config", type=Path, help="Path to the configuration file to validate.")
    parser.add_argument(
        "--schema",
        type=Path,
        help="Optional path to a JSON schema subset describing the expected structure.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing files as errors rather than warnings.",
    )
    return parser


def load_schema(path: Path | None) -> Any | None:
    if not path:
        return None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    suite = ConfigValidationSuite(strict=args.strict)
    schema = load_schema(args.schema)
    result = suite.validate(args.config, schema=schema)

    print(result.summary())
    for error in result.errors:
        print(f"ERROR: {error}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")

    return 0 if result.valid else 1


if __name__ == "__main__":  # pragma: no cover - manual execution
    raise SystemExit(main())
