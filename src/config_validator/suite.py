"""Core validation logic for the Config Validation Suite."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Mapping, Sequence
import configparser
import json
import tomllib


SUPPORTED_FORMATS = {".json", ".toml", ".ini"}


class ValidationError(Exception):
    """Raised when validation fails fatally."""


@dataclass(slots=True)
class ValidationResult:
    """Container for validation results."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def raise_for_errors(self) -> None:
        """Raise :class:`ValidationError` if the result contains errors."""

        if self.errors:
            raise ValidationError("; ".join(self.errors))

    def summary(self) -> str:
        """Return a human readable summary of the validation result."""

        status = "PASS" if self.valid else "FAIL"
        parts = [f"Validation {status}"]
        if self.errors:
            parts.append(f"Errors: {len(self.errors)}")
        if self.warnings:
            parts.append(f"Warnings: {len(self.warnings)}")
        return " | ".join(parts)


class ConfigValidationSuite:
    """Validate configuration files against simple schemas."""

    def __init__(self, *, strict: bool = False) -> None:
        self.strict = strict

    def validate(self, config_path: Path | str, schema: Mapping[str, Any] | None = None) -> ValidationResult:
        """Validate *config_path* optionally against *schema*.

        Parameters
        ----------
        config_path:
            Path to the configuration file.
        schema:
            Optional schema describing the expected structure. The schema format
            is a subset of JSON Schema, supporting ``type``, ``required``,
            ``properties``, ``items``, and ``enum`` keywords.
        """

        path = Path(config_path)
        errors: List[str] = []
        warnings: List[str] = []

        if not path.exists():
            msg = f"Config file '{path}' does not exist."
            if self.strict:
                errors.append(msg)
            else:
                warnings.append(msg)
            return ValidationResult(valid=not errors, errors=errors, warnings=warnings)

        if path.suffix.lower() not in SUPPORTED_FORMATS:
            errors.append(
                f"Unsupported config format '{path.suffix}'. Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}."
            )
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        try:
            data = _load_config(path)
        except (OSError, ValueError) as exc:
            errors.append(f"Failed to load config: {exc}")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        if schema:
            schema_errors = _validate_schema(data, schema)
            errors.extend(schema_errors)

        return ValidationResult(valid=not errors, errors=errors, warnings=warnings)


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def _load_config(path: Path) -> Mapping[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    if suffix == ".toml":
        with path.open("rb") as fh:
            return tomllib.load(fh)
    if suffix == ".ini":
        parser = configparser.ConfigParser()
        with path.open("r", encoding="utf-8") as fh:
            parser.read_file(fh)
        return {section: dict(parser[section]) for section in parser.sections()}
    raise ValidationError(f"Unsupported format: {path.suffix}")


# ---------------------------------------------------------------------------
# Schema validation helpers
# ---------------------------------------------------------------------------

def _validate_schema(data: Any, schema: Mapping[str, Any], *, path: str = "$") -> List[str]:
    errors: List[str] = []
    schema_type = schema.get("type")
    if schema_type:
        type_error = _check_type(data, schema_type)
        if type_error:
            errors.append(f"{path}: {type_error}")
            # If the type check fails there is no point recursing further.
            return errors

    enum_values = schema.get("enum")
    if enum_values is not None and data not in enum_values:
        errors.append(f"{path}: value {data!r} is not in allowed set {enum_values!r}")

    if schema_type == "object" and isinstance(data, Mapping):
        errors.extend(_validate_object(data, schema, path=path))
    elif schema_type == "array" and isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        item_schema = schema.get("items")
        if item_schema:
            for index, value in enumerate(data):
                errors.extend(
                    _validate_schema(value, item_schema, path=f"{path}[{index}]")
                )
    return errors


def _validate_object(data: Mapping[str, Any], schema: Mapping[str, Any], *, path: str) -> List[str]:
    errors: List[str] = []
    required = schema.get("required", [])
    for key in required:
        if key not in data:
            errors.append(f"{path}: missing required key '{key}'")

    properties = schema.get("properties", {})
    for key, subschema in properties.items():
        if key in data:
            errors.extend(_validate_schema(data[key], subschema, path=f"{path}.{key}"))

    additional = schema.get("additionalProperties", True)
    if additional is False:
        allowed_keys = set(properties.keys())
        unexpected = sorted(k for k in data.keys() if k not in allowed_keys)
        for key in unexpected:
            errors.append(f"{path}: unexpected key '{key}'")
    return errors


def _check_type(value: Any, expected: str) -> str | None:
    checkers = {
        "string": lambda x: isinstance(x, str),
        "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
        "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
        "boolean": lambda x: isinstance(x, bool),
        "array": lambda x: isinstance(x, Sequence) and not isinstance(x, (str, bytes, bytearray)),
        "object": lambda x: isinstance(x, Mapping),
        "null": lambda x: x is None,
    }
    checker = checkers.get(expected)
    if checker is None:
        return f"Unknown schema type '{expected}'"
    if not checker(value):
        return f"Expected type '{expected}' but received value {value!r}"
    return None


__all__ = [
    "ConfigValidationSuite",
    "ValidationError",
    "ValidationResult",
]
