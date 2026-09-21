"""Read-only integrity check for the frozen HS-NAV-01 capture.

Checks bytes and declared attribution, not original authorship, consent, source
transport fidelity, semantic correctness, or implemented interface behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

SOURCE = "sources/conversation/03-edit-navigation.md"
MANIFEST = "sources/conversation/03-edit-navigation.manifest.json"
EXPECTED_SOURCE = "2d7872e93e3dbac95f5a87e1918ed6f30e745e518f505b9d10265d1cb6eb7eb6"
# The separately reviewed manifest is immutable; new instructions need new IDs.
EXPECTED_MANIFEST = "cff4c815c2305f37cd76a5d89197ae7e4574fb2175016fc67c39c2cc0637b18b"
LIMIT = 20000


class NavigationError(ValueError):
    """Fixed-code failure; never repair a source in response."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise NavigationError(code)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def nonfinite(_: str) -> None:
    raise NavigationError("NONFINITE_JSON")


def read(root: Path, path: str) -> bytes:
    target = root / path
    require(not target.is_symlink(), "SOURCE_SYMLINK")
    require(target.resolve().is_relative_to(root.resolve()), "PATH_ESCAPE")
    with target.open("rb") as stream:
        data = stream.read(LIMIT + 1)
    require(len(data) <= LIMIT, "FILE_LIMIT")
    return data


def validate_ranges(data: bytes, rows: Any, prefix: str) -> None:
    """Validate line-addressed nonempty spans; exercised with synthetic text.

    Lines are one-based. Bytes are UTF-8 zero-based half-open intervals excluding
    LF separators. This capture gives a separate anchor to each nonempty line,
    including its introductory question. No payload byte may go unaddressed.
    """
    data.decode("utf-8", errors="strict")
    require(b"\r" not in data, "LINE_ENDING")
    require(type(rows) is list and bool(rows), "INVALID_PARAGRAPHS")
    expected = []
    offset = 0
    for number, line in enumerate(data.split(b"\n"), 1):
        if line:
            expected.append({"id": f"{prefix}-P{len(expected) + 1:02d}",
                             "line": number, "byte_start": offset,
                             "byte_end": offset + len(line),
                             "sha256": digest(line)})
        offset += len(line) + 1
    require(len(rows) == len(expected), "PARAGRAPH_COVERAGE")
    for row, wanted in zip(rows, expected):
        require(type(row) is dict and set(row) == set(wanted), "PARAGRAPH_FIELDS")
        for key, value in wanted.items():
            require(type(row[key]) is type(value) and row[key] == value,
                    "PARAGRAPH_ID_RANGE_OR_DIGEST")


def check(root: Path) -> None:
    raw = read(root, MANIFEST)
    manifest = json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    require(type(manifest) is dict, "MANIFEST_OBJECT")
    fixed = {"schema_version": 1, "source_id": "HS-NAV-01", "path": SOURCE,
             "sha256": EXPECTED_SOURCE, "byte_length": 1798, "encoding": "utf-8",
             "line_endings": "LF", "final_newline": False,
             "source_role": "author_instruction",
             "capture_role": "agent_transcription_of_visible_conversation",
             "issue": 79, "research_issue": 80}
    for key, value in fixed.items():
        require(type(manifest.get(key)) is type(value) and manifest[key] == value,
                "MANIFEST_IDENTITY_OR_ROLE")
    data = read(root, SOURCE)
    require(len(data) == 1798 and digest(data) == EXPECTED_SOURCE,
            "SOURCE_IDENTITY_CHANGED")
    require(not data.endswith(b"\n"), "FINAL_NEWLINE")
    validate_ranges(data, manifest.get("paragraphs"), "HS-NAV-01")
    require(digest(raw) == EXPECTED_MANIFEST, "MANIFEST_IDENTITY_CHANGED")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check",))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        check(args.root)
    except (NavigationError, OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        code = str(exc) if isinstance(exc, NavigationError) else "NAV_READ_OR_FORMAT_ERROR"
        print(code, file=sys.stderr)
        return 1
    print("NAV_INTEGRITY_OK source=HS-NAV-01 bytes=1798 anchors=3 authority=none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
