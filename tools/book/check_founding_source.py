"""Read-only integrity and passage lookup for the frozen HS-U01 transcription.

This checks archived bytes, not authorship, philosophical acceptance or truth.
No network access, source rewriting, or approval transition occurs here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

SOURCE = "sources/conversation/01-founding-manifesto.md"
MANIFEST = "sources/conversation/01-founding-manifesto.manifest.json"
INDEX = "sources/conversation/01-founding-manifesto.index.tsv"
SOURCE_ID = "HS-U01"
EXPECTED_SHA256 = "0e156479b9d8617e23d992403dc4fcf6d65b2e2a77b6461178993becf359baf4"
EXPECTED_BYTES = 17779
HEADINGS = (
    "## I. Begin with almost nothing",
    "## II. Be silent until chosen",
    "## III. Give movement a stable meaning",
    "## IV. Treat density as the whole burden",
    "## V. Make accessibility a property of the material",
    "## VI. Let resistance deform the shape, not the contract",
    "## VII. Change faces without passing through unreadability",
    "## VIII. Let expression change; make claims answer to evidence",
    "## IX. Let locality suggest, never command",
    "## X. Keep the human at the boundary",
)
COLUMNS = (
    "id", "kind", "section", "line_start", "line_end",
    "byte_start", "byte_end", "sha256",
)


class ArchiveError(ValueError):
    """A bounded archive check failed; never replace the source to fix it."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ArchiveError(reason)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_file(root: Path, name: str, limit: int) -> bytes:
    path = root / name
    require(not path.is_symlink(), "ARCHIVE_SYMLINK")
    require(path.resolve().is_relative_to(root.resolve()), "ARCHIVE_PATH_ESCAPE")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, "ARCHIVE_FILE_TOO_LARGE")
    return data


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_MANIFEST_KEY")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ArchiveError("NONFINITE_MANIFEST_VALUE")


def passages(data: bytes) -> list[dict[str, Any]]:
    """Index maximal nonblank blocks without altering any source bytes.

    Lines are one-based/inclusive. Byte spans are zero-based/half-open UTF-8
    ranges, excluding the final line separator. Ordinal IDs belong only to
    this frozen source; later versions must not reassign them.
    """
    data.decode("utf-8", errors="strict")
    require(b"\r" not in data, "UNEXPECTED_LINE_ENDING")
    rows: list[dict[str, Any]] = []
    section = "PREAMBLE"
    offset = 0
    current: tuple[int, int, int, int] | None = None

    def finish() -> None:
        nonlocal current, section
        if current is None:
            return
        start, end, first_line, last_line = current
        block = data[start:end]
        text = block.decode("utf-8")
        kind = "paragraph"
        if text.startswith("# "):
            kind = "title"
        elif text.startswith("## "):
            kind = "heading"
            require(text in HEADINGS, "UNEXPECTED_SECTION")
            section = text.split(" ", 2)[1].removesuffix(".")
        elif text.startswith("When content manifests it does so with disposition."):
            section = "ADDENDUM"
        rows.append(dict(zip(COLUMNS, (
            f"{SOURCE_ID}-B{len(rows) + 1:03d}", kind, section,
            first_line, last_line, start, end, sha256(block),
        ))))
        current = None

    for line_number, line in enumerate(data.splitlines(keepends=True), 1):
        content = line[:-1] if line.endswith(b"\n") else line
        if content.strip(b" \t"):
            first = current[0] if current else offset
            first_line = current[2] if current else line_number
            current = (first, offset + len(content), first_line, line_number)
        else:
            finish()
        offset += len(line)
    finish()
    return rows


def index_bytes(rows: list[dict[str, Any]]) -> bytes:
    lines = ["\t".join(COLUMNS)]
    lines.extend("\t".join(str(row[key]) for key in COLUMNS) for row in rows)
    return ("\n".join(lines) + "\n").encode("utf-8")


def checked_source(root: Path) -> tuple[bytes, list[dict[str, Any]]]:
    raw_manifest = read_file(root, MANIFEST, 16384)
    manifest = json.loads(raw_manifest, object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
    require(type(manifest) is dict, "INVALID_MANIFEST")
    require(type(manifest.get("schema_version")) is int
            and manifest["schema_version"] == 1, "UNSUPPORTED_MANIFEST")
    expected = {
        "source_id": SOURCE_ID, "path": SOURCE, "index_path": INDEX,
        "sha256": EXPECTED_SHA256, "byte_length": EXPECTED_BYTES,
        "encoding": "utf-8", "line_endings": "LF", "final_newline": False,
        "source_role": "historical_author_text",
        "capture_role": "agent_transcription_of_issue_copy",
        "authority_effect": "none",
    }
    for key, value in expected.items():
        actual = manifest.get(key)
        require(type(actual) is type(value) and actual == value,
                "MANIFEST_IDENTITY_OR_ROLE_CHANGED")
    data = read_file(root, SOURCE, 100000)
    require(len(data) == EXPECTED_BYTES and sha256(data) == EXPECTED_SHA256,
            "SOURCE_BYTES_CHANGED")
    rows = passages(data)
    headings = tuple(data[r["byte_start"]:r["byte_end"]].decode("utf-8")
                     for r in rows if r["kind"] == "heading")
    require(headings == HEADINGS, "SECTION_COVERAGE_CHANGED")
    require(type(manifest.get("passage_count")) is int
            and manifest["passage_count"] == len(rows), "PASSAGE_COUNT_CHANGED")
    require([r["section"] for r in rows[-2:]] == ["ADDENDUM", "ADDENDUM"],
            "ADDENDUM_COVERAGE_CHANGED")
    return data, rows


def check(root: Path) -> tuple[bytes, list[dict[str, Any]]]:
    data, rows = checked_source(root)
    actual_index = read_file(root, INDEX, 100000)
    require(actual_index == index_bytes(rows), "PASSAGE_INDEX_CHANGED")
    return data, rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "index", "show"))
    parser.add_argument("passage_id", nargs="?")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    if (args.command == "show") != (args.passage_id is not None):
        parser.error("show requires one passage ID; check/index take none")
    try:
        if args.command == "index":
            _, rows = checked_source(args.root)
            sys.stdout.buffer.write(index_bytes(rows))
        else:
            data, rows = check(args.root)
            if args.command == "show":
                row = next((r for r in rows if r["id"] == args.passage_id), None)
                require(row is not None, "UNKNOWN_PASSAGE_ID")
                sys.stdout.buffer.write(data[row["byte_start"]:row["byte_end"]])
            else:
                print(f"ARCHIVE_INTEGRITY_OK source={SOURCE_ID} bytes={len(data)} "
                      f"passages={len(rows)} sections=10 addendum=2 authority=none")
    except (ArchiveError, OSError, ValueError, RecursionError) as exc:
        reason = str(exc) if isinstance(exc, ArchiveError) else "ARCHIVE_READ_OR_FORMAT_ERROR"
        print(reason, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
