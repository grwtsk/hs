"""Read-only preservation checks for HS-U02--HS-U11 and their agent annotations.

This is source tooling, not a consent evaluator or an interface. Frozen hashes
bind this reviewed capture; they do not authenticate the original conversation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

import check_founding_source as founding

SOURCE = "sources/conversation/02-author-refinements.md"
MANIFEST = "sources/conversation/02-author-refinements.manifest.json"
INDEX = "sources/conversation/02-author-refinements.index.tsv"
PRECEDENCE = "sources/conversation/02-precedence.json"
PROPOSALS = "sources/conversation/02-agent-proposals.json"
EXPECTED_SOURCE_SHA256 = "3d1b7ee54732baa3afe2f97eaac22b914362ce50739dad7479b7b75b7e1e3847"
EXPECTED_MANIFEST_SHA256 = "13fc183aed9b02979853d0b4d8220d8a29baf45e41fe66051d5e8ac10a79b871"
COUNTS = (1, 1, 3, 1, 1, 1, 4, 1, 1, 1)
DG_OWNERS = {
    "DG-01": [65], "DG-02": [8], "DG-03": [6, 7], "DG-04": [7],
    "DG-05": [10, 9], "DG-06": [9], "DG-07": [11], "DG-08": [7],
    "DG-09": [11], "DG-10": [10], "DG-11": [6], "DG-12": [6],
}
COLUMNS = ("id", "turn", "kind", "line_start", "line_end", "byte_start", "byte_end", "sha256")
require = founding.require
sha256 = founding.sha256
ArchiveError = founding.ArchiveError


def load_json(root: Path, path: str) -> Any:
    return json.loads(founding.read_file(root, path, 100000),
                      object_pairs_hook=founding.unique_object,
                      parse_constant=founding.reject_constant)


def scan(data: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Index heading wrappers separately from transcribed human paragraphs."""
    data.decode("utf-8", errors="strict")
    require(b"\r" not in data, "UNEXPECTED_LINE_ENDING")
    lines = data.split(b"\n")
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line) + 1)
    headers = [(i, re.fullmatch(rb"## U(\d{2}) .+", line))
               for i, line in enumerate(lines) if line.startswith(b"## ")]
    require([int(match.group(1)) if match else -1 for _, match in headers]
            == list(range(2, 12)), "TURN_ORDER_CHANGED")
    require(headers[0][0] == 0, "UNEXPECTED_SOURCE_PREFIX")
    rows, turns = [], []

    def row(identity: str, turn: str, kind: str, first: int, last: int) -> dict[str, Any]:
        start, end = offsets[first], offsets[last] + len(lines[last])
        return dict(zip(COLUMNS, (identity, turn, kind, first + 1, last + 1,
                                 start, end, sha256(data[start:end]))))

    for pos, (first, match) in enumerate(headers):
        turn = f"HS-U{int(match.group(1)):02d}"
        rows.append(row(turn + "-H", turn, "editorial_heading", first, first))
        last = headers[pos + 1][0] - 1 if pos + 1 < len(headers) else len(lines) - 1
        while last > first and not lines[last].strip(b" \t"):
            last -= 1
        require(last > first, "MISSING_TURN_PAYLOAD")
        payload = row(turn, turn, "issue_copy_author_text", first + 1, last)
        turns.append(payload)
        cursor, count = first + 1, 0
        while cursor <= last:
            if not lines[cursor].strip(b" \t"):
                cursor += 1
                continue
            start = cursor
            while cursor < last and lines[cursor + 1].strip(b" \t"):
                cursor += 1
            count += 1
            rows.append(row(f"{turn}-P{count:03d}", turn, "author_paragraph", start, cursor))
            cursor += 1
        require(count == COUNTS[pos], "PARAGRAPH_COVERAGE_CHANGED")
    return rows, turns


def index_bytes(rows: list[dict[str, Any]]) -> bytes:
    return ("\t".join(COLUMNS) + "\n" + "".join(
        "\t".join(str(row[key]) for key in COLUMNS) + "\n" for row in rows)).encode()


def check_source(root: Path) -> tuple[bytes, list[dict[str, Any]], list[dict[str, Any]]]:
    data = founding.read_file(root, SOURCE, 100000)
    require(sha256(data) == EXPECTED_SOURCE_SHA256 and len(data) == 5529,
            "REFINEMENTS_BYTES_CHANGED")
    raw = founding.read_file(root, MANIFEST, 100000)
    require(sha256(raw) == EXPECTED_MANIFEST_SHA256, "REFINEMENTS_MANIFEST_CHANGED")
    manifest = load_json(root, MANIFEST)
    rows, turns = scan(data)
    require(manifest["turns"] == turns, "TURN_SPANS_CHANGED")
    require(manifest["authority_effect"] == "none", "ARCHIVE_IS_NOT_APPROVAL")
    require(founding.read_file(root, INDEX, 100000) == index_bytes(rows),
            "REFINEMENTS_INDEX_CHANGED")
    return data, rows, turns


def check_ledger(root: Path, path: str, kind: str, ids: list[str],
                 references: set[str]) -> dict[str, Any]:
    ledger = load_json(root, path)
    require(type(ledger) is dict and set(ledger) == {
        "schema_version", "kind", "annotation_author", "authority_effect", "entries"
    }, "INVALID_LEDGER_FIELDS")
    require(type(ledger["schema_version"]) is int and ledger["schema_version"] == 1,
            "INVALID_LEDGER_VERSION")
    require(ledger["kind"] == kind and ledger["annotation_author"] == "agent"
            and ledger["authority_effect"] == "none", "LEDGER_ROLE_CHANGED")
    require(type(ledger["entries"]) is list, "INVALID_ENTRIES")
    require([e.get("id") if type(e) is dict else None for e in ledger["entries"]] == ids,
            "LEDGER_ENTRY_COVERAGE_CHANGED")
    for entry in ledger["entries"]:
        require(set(entry) == {"id", "source_refs", "earlier_refs", "relation", "summary",
                               "status", "disagreements", "human_issues"}, "INVALID_ENTRY_FIELDS")
        for key in ("source_refs", "earlier_refs"):
            refs = entry[key]
            require(type(refs) is list and all(type(r) is str and r in references for r in refs),
                    "UNKNOWN_SOURCE_REFERENCE")
            require(len(refs) == len(set(refs)), "DUPLICATE_SOURCE_REFERENCE")
        require(bool(entry["source_refs"]), "MISSING_SOURCE_REFERENCE")
        require(type(entry["summary"]) is str and 0 < len(entry["summary"]) <= 3000,
                "INVALID_SUMMARY")
        require(entry["status"] == ("PROPOSED_NOT_ADOPTED" if kind == "agent_proposals"
                                    else "ANNOTATION_NOT_A_DECISION"), "UNAUTHORIZED_STATUS_PROMOTION")
        require(entry["relation"] in ({"assistant_proposal"} if kind == "agent_proposals" else
                {"extends", "explicit_non_scalar_constraint", "commissions", "requires_visible_disagreement"}),
                "INVALID_RELATION")
        dgs, owners = entry["disagreements"], entry["human_issues"]
        require(type(dgs) is list and all(type(d) is str and d in DG_OWNERS for d in dgs),
                "UNKNOWN_DISAGREEMENT")
        require(len(dgs) == len(set(dgs)), "DUPLICATE_DISAGREEMENT")
        require(type(owners) is list and all(type(o) is int and o in {6, 7, 8, 9, 10, 11, 65}
                                           for o in owners), "INVALID_HUMAN_OWNER")
        require(len(owners) == len(set(owners)), "DUPLICATE_HUMAN_OWNER")
        require(all(set(DG_OWNERS[d]) <= set(owners) for d in dgs), "MISSING_HUMAN_OWNER")
        for later in entry["source_refs"]:
            for earlier in entry["earlier_refs"]:
                require(int(earlier[4:6]) < int(later[4:6]), "REVERSED_SOURCE_ORDER")
    return ledger


def check(root: Path) -> tuple[bytes, list[dict[str, Any]], list[dict[str, Any]]]:
    _, original = founding.check(root)
    data, rows, turns = check_source(root)
    refs = {r["id"] for r in original + rows + turns} | {"HS-U01"}
    precedence = check_ledger(root, PRECEDENCE, "precedence_annotations",
                              [f"PR-{i:02d}" for i in range(2, 12)], refs)
    proposals = check_ledger(root, PROPOSALS, "agent_proposals",
                             [f"AP-{i:02d}" for i in range(1, 13)], refs)
    non_scalar = [e for e in precedence["entries"] if e["relation"] == "explicit_non_scalar_constraint"]
    require(len(non_scalar) == 1 and non_scalar[0]["source_refs"] == ["HS-U07-P001"]
            and non_scalar[0]["earlier_refs"] == ["HS-U04-P002", "HS-U04-P003"],
            "NONSCALAR_SOURCE_LINK_CHANGED")
    require(set().union(*(set(e["disagreements"]) for e in proposals["entries"])) == set(DG_OWNERS),
            "DISAGREEMENT_COVERAGE_CHANGED")
    return data, rows, turns


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "index", "show"))
    parser.add_argument("reference", nargs="?")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    if (args.command == "show") != (args.reference is not None):
        parser.error("show requires one reference; check/index take none")
    try:
        data, rows, turns = check(args.root)
        if args.command == "index":
            sys.stdout.buffer.write(index_bytes(rows))
        elif args.command == "show":
            match = next((r for r in rows + turns if r["id"] == args.reference), None)
            require(match is not None, "UNKNOWN_REFERENCE")
            sys.stdout.buffer.write(data[match["byte_start"]:match["byte_end"]])
        else:
            print("REFINEMENTS_INTEGRITY_OK turns=10 author_paragraphs=15 "
                  "editorial_headings=10 proposals=12 disagreements=12 authority=none")
    except (ArchiveError, OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        reason = str(exc) if isinstance(exc, ArchiveError) else "REFINEMENTS_READ_OR_FORMAT_ERROR"
        print(reason, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
