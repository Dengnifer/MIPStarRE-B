#!/usr/bin/env python3
"""Reject clipped blueprint text and verify planned Lean identifiers survive PDF extraction."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMMAND_TIMEOUT_SECONDS = 30
BOUNDARY_TOLERANCE_POINTS = 0.01


def validate_bbox(xml_text: str) -> tuple[int, list[str]]:
    root = ET.fromstring(xml_text)
    pages = root.findall(".//{*}page")
    errors: list[str] = []
    for page_number, page in enumerate(pages, start=1):
        try:
            width = float(page.attrib["width"])
            height = float(page.attrib["height"])
        except (KeyError, ValueError):
            errors.append(f"page {page_number}: malformed page geometry")
            continue
        if not all(math.isfinite(value) and value > 0 for value in (width, height)):
            errors.append(f"page {page_number}: invalid page dimensions")
            continue
        for word in page.findall(".//{*}word"):
            text = "".join(word.itertext())
            try:
                x_min = float(word.attrib["xMin"])
                x_max = float(word.attrib["xMax"])
                y_min = float(word.attrib["yMin"])
                y_max = float(word.attrib["yMax"])
            except (KeyError, ValueError):
                errors.append(f"page {page_number}: malformed word box: {text}")
                continue
            coordinates = (x_min, x_max, y_min, y_max)
            if not all(math.isfinite(value) for value in coordinates):
                errors.append(f"page {page_number}: non-finite word box: {text}")
                continue
            if x_min > x_max or y_min > y_max:
                errors.append(f"page {page_number}: inverted word box: {text}")
                continue
            edge_violations = (
                ("left", x_min < -BOUNDARY_TOLERANCE_POINTS, x_min, 0.0),
                ("right", x_max > width + BOUNDARY_TOLERANCE_POINTS, x_max, width),
                ("bottom", y_min < -BOUNDARY_TOLERANCE_POINTS, y_min, 0.0),
                ("top", y_max > height + BOUNDARY_TOLERANCE_POINTS, y_max, height),
            )
            for edge, violated, coordinate, boundary in edge_violations:
                if not violated:
                    continue
                errors.append(
                    f"page {page_number}: text crosses {edge} page boundary "
                    f"({coordinate:.3f} outside 0..{boundary:.3f}): {text}"
                )
    return len(pages), errors


def planned_identifiers(metadata_path: Path) -> list[str]:
    document = json.loads(metadata_path.read_text(encoding="utf-8"))
    return sorted({
        identifier
        for node in document["nodes"]
        for identifier in [node["lean"]["module"], *node["lean"]["names"]]
    })


def extracted_identifier_errors(text: str, identifiers: list[str]) -> list[str]:
    compact = "".join(text.split())
    return [f"planned Lean identifier is not extractable: {identifier}"
            for identifier in identifiers if identifier not in compact]


def run_pdftotext(pdf: Path, mode: str) -> str:
    process = subprocess.run(
        ["pdftotext", mode, str(pdf), "-"],
        check=False,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )
    if process.returncode != 0:
        raise RuntimeError(f"pdftotext {mode} failed with exit {process.returncode}")
    return process.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--metadata", type=Path, default=ROOT / "metadata/nodes.json")
    args = parser.parse_args()
    try:
        bbox = run_pdftotext(args.pdf, "-bbox-layout")
        text = run_pdftotext(args.pdf, "-layout")
        page_count, errors = validate_bbox(bbox)
        identifiers = planned_identifiers(args.metadata)
        errors.extend(extracted_identifier_errors(text, identifiers))
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ET.ParseError, ValueError) as error:
        print(f"ERROR: PDF validation failed: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {page_count} PDF pages; {len(identifiers)} planned Lean identifiers extractable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
