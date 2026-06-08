"""Helpers for deriving ACM-style testcase views from function arguments."""

from __future__ import annotations

import json
import re
from typing import Any

DESIGN_SEQUENCE_SLUGS = {
    "lru-cache",
    "implement-trie-prefix-tree",
    "min-stack",
    "find-median-from-data-stream",
}


def _split_top_level(text: str, separator: str) -> list[str]:
    parts = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        elif char == separator and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return parts


def _without_none(annotation: str) -> str:
    parts = [part.strip() for part in _split_top_level(annotation, "|")]
    concrete = [part for part in parts if part.lower() not in {"none", "null"}]
    return concrete[0] if concrete else "None"


def _list_inner(annotation: str) -> str | None:
    concrete = _without_none(annotation)
    match = re.match(r"^(?:list|List|Sequence|tuple|Tuple)\[(.*)\]$", concrete)
    return match.group(1).strip() if match else None


def _params_from_signature(signature: str) -> list[tuple[str, str]]:
    match = re.search(r"def\s+[A-Za-z_][A-Za-z0-9_]*\s*\((?P<params>.*?)\)\s*(?:->|:|$)", signature)
    if not match:
        return []
    params = []
    for raw in _split_top_level(match.group("params"), ","):
        raw = raw.strip()
        if not raw or raw in {"self", "cls"}:
            continue
        name, _, annotation = raw.partition(":")
        params.append((name.strip(), annotation.split("=", 1)[0].strip() or "Any"))
    return params


def _json_line(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"))


def _input_from_args(args: list[Any]) -> str:
    return "\n".join(_json_line(arg) for arg in args)


def _scalar_acm_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _is_scalar_annotation(annotation: str) -> bool:
    return _without_none(annotation).lower() in {"int", "float", "str", "bool"}


def _matrix_dimensions(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, list):
        return None
    if not value:
        return (0, 0)
    if not all(isinstance(row, list) for row in value):
        return None
    width = len(value[0])
    if any(len(row) != width for row in value):
        return None
    return (len(value), width)


def _is_single_char_grid(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(row, list) for row in value)
        and all(isinstance(cell, str) and len(cell) == 1 for row in value for cell in row)
    )


def _format_arg_as_acm(annotation: str, value: Any) -> list[str] | None:
    concrete = _without_none(annotation)
    inner = _list_inner(concrete)
    if inner is None:
        return [_scalar_acm_value(value)] if _is_scalar_annotation(concrete) else None

    nested_inner = _list_inner(inner)
    if nested_inner is not None:
        dimensions = _matrix_dimensions(value)
        if dimensions is None:
            return None
        rows, cols = dimensions
        lines = [f"{rows} {cols}"]
        if _without_none(nested_inner).lower() == "str":
            if not _is_single_char_grid(value):
                return None
            lines.extend("".join(row) for row in value)
            return lines
        if _is_scalar_annotation(nested_inner):
            lines.extend(" ".join(_scalar_acm_value(cell) for cell in row) for row in value)
            return lines
        return None

    if not isinstance(value, list):
        return None
    if not _is_scalar_annotation(inner):
        return None
    lines = [str(len(value))]
    if value:
        if _without_none(inner).lower() == "str":
            lines.extend(str(item) for item in value)
        else:
            lines.append(" ".join(_scalar_acm_value(item) for item in value))
    return lines


def _two_car_parking_lot_acm_input(args: list[Any]) -> str | None:
    if len(args) != 1:
        return None
    grid = args[0]
    dimensions = _matrix_dimensions(grid)
    if dimensions is None or not _is_single_char_grid(grid):
        return None
    rows, cols = dimensions
    return "\n".join([f"{rows} {cols}", *("".join(row) for row in grid)])


def _design_sequence_acm_input(args: list[Any]) -> str | None:
    if len(args) < 2:
        return None
    operations, call_args = args[0], args[1]
    if not isinstance(operations, list) or not isinstance(call_args, list) or len(operations) != len(call_args):
        return None
    lines = [str(len(operations))]
    for operation, arg in zip(operations, call_args, strict=True):
        lines.append(f"{operation} {json.dumps(arg, separators=(',', ':'))}")
    return "\n".join(lines)


def build_acm_view(slug: str, signature: str, args: list[Any], output_value: str) -> dict[str, str]:
    if slug == "two-car-parking-lot":
        acm_input = _two_car_parking_lot_acm_input(args)
        if acm_input is not None:
            return {"input": acm_input, "output": output_value, "generated_format": "structured-acm"}

    if slug in DESIGN_SEQUENCE_SLUGS:
        acm_input = _design_sequence_acm_input(args)
        if acm_input is not None:
            return {"input": acm_input, "output": output_value, "generated_format": "structured-acm"}

    params = _params_from_signature(signature)
    if len(params) == len(args):
        lines: list[str] = []
        for (_name, annotation), arg in zip(params, args, strict=True):
            formatted = _format_arg_as_acm(annotation, arg)
            if formatted is None:
                break
            lines.extend(formatted)
        else:
            return {"input": "\n".join(lines), "output": output_value, "generated_format": "structured-acm"}

    return {"input": _input_from_args(args), "output": output_value, "generated_format": "json-line"}
