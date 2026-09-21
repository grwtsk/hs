"""Read-only inspection of the original Hs mark (issue #4).

This is a bounded decoder for this archive's IHDR/IDAT/IEND, RGBA8,
non-interlaced PNG profile, not a general image loader or an interface.
PNG filters/alpha: https://www.w3.org/TR/png-3/ sections 4.5, 9, 10, 11.
Integrity and raw sample counts do not establish authorship or accessibility.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys
from typing import Any
import zlib

ASSET = "sources/assets/grwtsk-original.png"
MANIFEST = "sources/assets/grwtsk-original.manifest.json"
REPORT = "sources/assets/grwtsk-original.measurements.json"
EXPECTED_SHA256 = "e197a1263819ae2c03a9776ac16076de75618aa9af7778d4acb266c6d5774692"
EXPECTED_LENGTH = 34918
EXPECTED_REPORT_SHA256 = "51524cc7a5f24e04ac97a565b0ae41678dd44399acd04f2468b8671e7227dc32"
MAX_FILE_BYTES = 100000
MAX_PIXELS = 1420 * 1420
SIGNATURE = b"\x89PNG\r\n\x1a\n"


class MarkError(ValueError):
    """Fixed-code failure; no automatic repair or source substitution."""


def require(ok: bool, code: str) -> None:
    if not ok:
        raise MarkError(code)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bounded(root: Path, name: str) -> bytes:
    base = root.resolve()
    path = root / name
    require(not path.is_symlink(), "SYMLINK_REJECTED")
    require(path.resolve().is_relative_to(base), "PATH_ESCAPE")
    with path.open("rb") as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    require(len(data) <= MAX_FILE_BYTES, "FILE_LIMIT")
    return data


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise MarkError("NONFINITE_JSON")


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    da, db, dc = abs(p - a), abs(p - b), abs(p - c)
    return a if da <= db and da <= dc else b if db <= dc else c


def decode_rgba(data: bytes) -> tuple[int, int, bytes, dict[int, int]]:
    """Validate the small archive profile and reverse PNG filters without color conversion.

    The caller must check the frozen source hash before accepting any real asset.
    This helper also permits small, source-free test fixtures. Size bounds precede
    inflation. Only one bounded zlib stream and the three declared chunks are read.
    """
    require(len(data) <= MAX_FILE_BYTES, "FILE_LIMIT")
    require(data.startswith(SIGNATURE), "PNG_SIGNATURE")
    chunks: list[tuple[bytes, bytes]] = []
    offset = 8
    while offset < len(data):
        require(len(chunks) < 3, "CHUNK_PROFILE")
        require(offset + 12 <= len(data), "TRUNCATED_CHUNK")
        length = struct.unpack_from(">I", data, offset)[0]
        end = offset + length + 12
        require(end <= len(data), "TRUNCATED_CHUNK")
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:end - 4]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        require(zlib.crc32(kind + payload) & 0xffffffff == crc, "CHUNK_CRC")
        chunks.append((kind, payload))
        offset = end
    require([k for k, _ in chunks] == [b"IHDR", b"IDAT", b"IEND"], "CHUNK_PROFILE")
    require(len(chunks[0][1]) == 13 and not chunks[-1][1], "CHUNK_LENGTH")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", chunks[0][1])
    require(0 < width <= 1420 and 0 < height <= 1420
            and width * height <= MAX_PIXELS, "DIMENSION_LIMIT")
    require((depth, color, compression, filtering, interlace) == (8, 6, 0, 0, 0),
            "UNSUPPORTED_PNG_PROFILE")
    stride = 4 * width
    expected = height * (stride + 1)
    inflater = zlib.decompressobj()
    try:
        raw = inflater.decompress(chunks[1][1], expected + 1)
    except zlib.error as exc:
        raise MarkError("INVALID_ZLIB") from exc
    require(len(raw) == expected, "INFLATED_LENGTH")
    require(inflater.eof and not inflater.unused_data and not inflater.unconsumed_tail,
            "ZLIB_STREAM_BOUNDARY")
    previous = bytes(stride)
    decoded = bytearray()
    filters: Counter[int] = Counter()
    for y in range(height):
        start = y * (stride + 1)
        mode = raw[start]
        require(mode <= 4, "UNKNOWN_FILTER")
        filters[mode] += 1
        row = bytearray(raw[start + 1:start + 1 + stride])
        if mode == 2:
            row = bytearray((x + up) & 255 for x, up in zip(row, previous))
        elif mode:
            for x in range(stride):
                left = row[x - 4] if x >= 4 else 0
                up = previous[x]
                upper_left = previous[x - 4] if x >= 4 else 0
                predictor = (left if mode == 1 else (left + up) // 2 if mode == 3
                             else paeth(left, up, upper_left))
                row[x] = (row[x] + predictor) & 255
        decoded.extend(row)
        previous = row
    return width, height, bytes(decoded), dict(sorted(filters.items()))


def measurements(data: bytes) -> dict[str, Any]:
    require(len(data) == EXPECTED_LENGTH and digest(data) == EXPECTED_SHA256,
            "SOURCE_IDENTITY_CHANGED")
    width, height, rgba, filters = decode_rgba(data)
    pixels = Counter(struct.iter_unpack("BBBB", rgba))
    alpha: Counter[int] = Counter()
    for pixel, count in pixels.items():
        alpha[pixel[3]] += count
    return {
        "schema_version": 1,
        "source_sha256": EXPECTED_SHA256,
        "source_bytes": len(data),
        "pixel_dimensions": {"width": width, "height": height},
        "sample_format": "8-bit RGBA, non-interlaced, unassociated alpha",
        "chunks": ["IHDR", "IDAT", "IEND"],
        "embedded_color_metadata": [],
        "color_conversion": "none; encoded RGB samples are counted without an assigned profile",
        "compositing": "none; no background, global opacity, scaling or contrast calculation",
        "decoded_rgba_sha256": digest(rgba),
        "pixel_count": width * height,
        "distinct_rgba_samples": len(pixels),
        "opaque_pixel_count": alpha[255],
        "fully_transparent_pixel_count": alpha[0],
        "partially_transparent_pixel_count": sum(n for a, n in alpha.items() if 0 < a < 255),
        "alpha_min": min(alpha),
        "alpha_max": max(alpha),
        "most_common_rgba": [
            {"rgba": list(pixel), "count": count}
            for pixel, count in sorted(pixels.items(), key=lambda item: (-item[1], item[0]))[:3]
        ],
        "alpha_histogram": {str(a): n for a, n in sorted(alpha.items())},
        "scanline_filters": [{"filter": f, "rows": n} for f, n in filters.items()],
        "interpretive_limit": "Raw sample ratios are not perceived density, cognitive load or an accessibility finding.",
        "authority_effect": "none",
    }


def expected_manifest() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source_id": "HS-ASSET-01",
        "path": ASSET,
        "sha256": EXPECTED_SHA256,
        "byte_length": EXPECTED_LENGTH,
        "source_filename": "grwtsk.png",
        "source_role": "original_author_supplied_asset",
        "capture_method": "Lossless copy of the mounted conversation attachment; compared with the source-handoff ZIP entry.",
        "provenance_issue": "https://github.com/grwtsk/hs/issues/4",
        "source_attachment_id_recorded_at_intake": "file_00000000d5ec81fdb43abd33341ed48f",
        "inspection_basis": "File identity matches the issue-4 intake digest and the original attachment bytes available during this task.",
        "measurements_path": REPORT,
        "prescribed_resting_extent": {"width": 144, "height": 144, "unit": "CSS px", "kind": "author_instruction_not_intrinsic_size"},
        "rights": {"scope": "Source preservation for Hs under the author's commission", "license": "not_selected", "human_issue": 6},
        "visual_decisions": {"issue": 9, "disagreement": "DG-06", "outcome_from_this_archive": "none"},
        "revisit_issue": 75,
        "identity_policy": "Preserve this original; a later supplied revision gets a new identity and an explicit delta, never a silent replacement.",
        "authority_effect": "none",
    }


def metadata(root: Path) -> dict[str, Any]:
    """Check reference records only; this does not inspect or admit the PNG."""
    raw = read_bounded(root, MANIFEST)
    parsed = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
    require(type(parsed) is dict, "INVALID_MANIFEST")
    require(json_bytes(parsed) == json_bytes(expected_manifest()), "MANIFEST_CHANGED")
    report = read_bounded(root, REPORT)
    require(digest(report) == EXPECTED_REPORT_SHA256, "MEASUREMENT_REPORT_CHANGED")
    return parsed


def inspect(root: Path) -> dict[str, Any]:
    metadata(root)
    try:
        data = read_bounded(root, ASSET)
    except FileNotFoundError as exc:
        raise MarkError("ORIGINAL_PNG_PENDING_HUMAN_UPLOAD") from exc
    return measurements(data)


def check(root: Path) -> dict[str, Any]:
    result = inspect(root)
    require(read_bounded(root, REPORT) == json_bytes(result), "MEASUREMENT_REPORT_CHANGED")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "report", "metadata"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        if args.command == "metadata":
            metadata(args.root)
            print("MARK_METADATA_OK source=HS-ASSET-01 original=not_checked authority=none")
        elif args.command == "report":
            sys.stdout.buffer.write(json_bytes(inspect(args.root)))
        else:
            result = check(args.root)
            print(f"MARK_INTEGRITY_OK source=HS-ASSET-01 bytes={result['source_bytes']} "
                  f"pixels={result['pixel_count']} authority=none")
    except (MarkError, OSError, ValueError, RecursionError) as exc:
        code = str(exc) if isinstance(exc, MarkError) else "READ_OR_FORMAT_ERROR"
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
