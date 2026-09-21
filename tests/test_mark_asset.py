"""Source-free PNG edge cases and fixed-original custody checks; no UI assertions."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/book/inspect_mark.py"
spec = importlib.util.spec_from_file_location("hs_mark", SCRIPT)
assert spec is not None and spec.loader is not None
mark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mark)


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))


def png(raw: bytes, *, width: int = 2, height: int = 2,
        profile: tuple[int, ...] = (8, 6, 0, 0, 0), compressed: bytes | None = None) -> bytes:
    return (mark.SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, *profile))
            + chunk(b"IDAT", zlib.compress(raw) if compressed is None else compressed)
            + chunk(b"IEND", b""))


class PngProfileTests(unittest.TestCase):
    # Hand-specified filtered rows for the same 2x2 RGBA plane. The reference
    # encoder is not implemented by calling the decoder being tested.
    PLANE = bytes([10, 20, 30, 255, 40, 50, 60, 128,
                   50, 60, 70, 100, 90, 100, 110, 200])
    ROWS = {
        0: [10,20,30,255,40,50,60,128, 50,60,70,100,90,100,110,200],
        1: [10,20,30,255,30,30,30,129, 50,60,70,100,40,40,40,100],
        2: [10,20,30,255,40,50,60,128, 40,40,40,101,50,50,50,72],
        3: [10,20,30,255,35,40,45,1, 45,50,55,229,45,45,45,86],
        4: [10,20,30,255,30,30,30,129, 40,40,40,101,40,40,40,100],
    }

    def raw(self, mode: int = 0) -> bytes:
        row = self.ROWS[mode]
        return bytes([mode] + row[:8] + [mode] + row[8:])

    def test_all_five_filters_recover_exact_rgba(self) -> None:
        for mode in range(5):
            with self.subTest(mode=mode):
                w, h, plane, filters = mark.decode_rgba(png(self.raw(mode)))
                self.assertEqual((w, h, plane, filters), (2, 2, self.PLANE, {mode: 2}))

    def test_paeth_tie_order_and_branches(self) -> None:
        for a, b, c, expected in [(0, 0, 0, 0), (10, 20, 10, 20),
                                   (40, 50, 60, 40), (30, 60, 40, 60), (30, 60, 45, 45)]:
            self.assertEqual(mark.paeth(a, b, c), expected)

    def test_crc_corruption(self) -> None:
        data = bytearray(png(self.raw())); data[-1] ^= 1
        with self.assertRaisesRegex(mark.MarkError, "CHUNK_CRC"):
            mark.decode_rgba(bytes(data))

    def test_truncation(self) -> None:
        data = png(self.raw())
        for cut in (9, 15, len(data)-1):
            with self.subTest(cut=cut), self.assertRaises(mark.MarkError):
                mark.decode_rgba(data[:cut])

    def test_wrong_signature(self) -> None:
        with self.assertRaisesRegex(mark.MarkError, "PNG_SIGNATURE"):
            mark.decode_rgba(b"not a png")

    def test_wrong_order_or_extra_chunks(self) -> None:
        data = png(self.raw())
        for changed in (data + chunk(b"tEXt", b"private"),
                        data[:8] + chunk(b"sRGB", b"\0") + data[8:],
                        data[:8] + data[33:] + data[8:33]):
            with self.subTest(length=len(changed)), self.assertRaises(mark.MarkError):
                mark.decode_rgba(changed)

    def test_dimension_limit_before_inflation(self) -> None:
        for width, height in [(0, 2), (2, 0), (1421, 1), (1, 1421)]:
            with self.subTest(width=width, height=height), self.assertRaisesRegex(
                    mark.MarkError, "DIMENSION_LIMIT"):
                mark.decode_rgba(png(b"", width=width, height=height, compressed=b"invalid"))

    def test_unsupported_profile(self) -> None:
        for profile in [(16,6,0,0,0), (8,2,0,0,0), (8,6,0,0,1),
                        (8,6,1,0,0), (8,6,0,1,0)]:
            with self.subTest(profile=profile), self.assertRaisesRegex(
                    mark.MarkError, "UNSUPPORTED_PNG_PROFILE"):
                mark.decode_rgba(png(self.raw(), profile=profile))

    def test_short_or_expanded_stream(self) -> None:
        for raw in (b"", self.raw()[:-1], self.raw()+b"\0", b"\0"*1000000):
            with self.subTest(length=len(raw)), self.assertRaisesRegex(
                    mark.MarkError, "INFLATED_LENGTH"):
                mark.decode_rgba(png(raw))

    def test_concatenated_or_trailing_zlib(self) -> None:
        stream = zlib.compress(self.raw())
        for suffix in (b"trailing", zlib.compress(b"more")):
            with self.subTest(suffix=suffix), self.assertRaisesRegex(
                    mark.MarkError, "ZLIB_STREAM_BOUNDARY"):
                mark.decode_rgba(png(b"", compressed=stream+suffix))

    def test_corrupt_zlib(self) -> None:
        with self.assertRaisesRegex(mark.MarkError, "INVALID_ZLIB"):
            mark.decode_rgba(png(b"", compressed=b"broken"))

    def test_unknown_filter(self) -> None:
        with self.assertRaisesRegex(mark.MarkError, "UNKNOWN_FILTER"):
            mark.decode_rgba(png(bytes([5])+self.raw()[1:]))

    def test_nonempty_iend(self) -> None:
        data = png(self.raw())[:-12] + chunk(b"IEND", b"x")
        with self.assertRaisesRegex(mark.MarkError, "CHUNK_LENGTH"):
            mark.decode_rgba(data)

    def test_input_limit(self) -> None:
        with self.assertRaisesRegex(mark.MarkError, "FILE_LIMIT"):
            mark.decode_rgba(b"x"*(mark.MAX_FILE_BYTES+1))


class MarkArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        if not (ROOT / mark.ASSET).exists() and not (ROOT / mark.ASSET).is_symlink():
            self.skipTest("Original PNG pending human upload under issue #4; not verified")
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in (mark.ASSET, mark.MANIFEST, mark.REPORT):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def cli(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *args,
                               "--root", str(self.root)], capture_output=True,
                              timeout=15, check=False)

    def test_original_report_matches_intake(self) -> None:
        result = mark.check(self.root)
        self.assertEqual(result['pixel_dimensions'], {'width':1420, 'height':1420})
        self.assertEqual(result['pixel_count'], 2016400)
        self.assertEqual(result['distinct_rgba_samples'], 769)
        self.assertEqual(result['opaque_pixel_count'], 453085)
        self.assertEqual(result['fully_transparent_pixel_count'], 0)
        self.assertEqual(result['alpha_min'], 3)
        self.assertEqual([item['count'] for item in result['most_common_rgba']],
                         [1560547, 321848, 130189])
        self.assertEqual(result['decoded_rgba_sha256'],
                         '0591a73ef1fbfad571f25de730670f1040456d6c002e82fce3a63281cde8be9f')
        self.assertEqual(sum(result['alpha_histogram'].values()), 2016400)

    def test_source_mutation(self) -> None:
        path = self.root / mark.ASSET
        data = bytearray(path.read_bytes()); data[-1] ^= 1; path.write_bytes(data)
        with self.assertRaisesRegex(mark.MarkError, "SOURCE_IDENTITY_CHANGED"):
            mark.check(self.root)

    def test_reencoding_same_image_is_not_original_bytes(self) -> None:
        data = (self.root / mark.ASSET).read_bytes()
        compressed = data[41:-16]
        stream = zlib.compress(zlib.decompress(compressed), level=1)
        replacement = data[:33] + chunk(b"IDAT", stream) + data[-12:]
        self.assertNotEqual(replacement, data)
        with self.assertRaisesRegex(mark.MarkError, "SOURCE_IDENTITY_CHANGED"):
            mark.measurements(replacement)

    def test_coedited_manifest_cannot_rebase_source(self) -> None:
        (self.root / mark.ASSET).write_bytes(b"replacement")
        value = mark.expected_manifest(); value['sha256'] = mark.digest(b"replacement")
        (self.root / mark.MANIFEST).write_bytes(mark.json_bytes(value))
        with self.assertRaisesRegex(mark.MarkError, "MANIFEST_CHANGED"):
            mark.check(self.root)

    def test_roles_rights_dimensions_and_authority_are_not_promoted(self) -> None:
        for key, value in [('authority_effect','G1 accepted'), ('rights',{'license':'CC0'}),
                           ('source_role','redrawn'), ('schema_version',True),
                           ('path','../../outside'), ('unexpected','extra')]:
            with self.subTest(key=key):
                record = mark.expected_manifest(); record[key] = value
                (self.root / mark.MANIFEST).write_bytes(mark.json_bytes(record))
                with self.assertRaisesRegex(mark.MarkError, "MANIFEST_CHANGED"):
                    mark.check(self.root)

    def test_duplicate_and_nonfinite_json_rejected(self) -> None:
        for raw, code in [(b'{"a":1,"a":1}', 'DUPLICATE_JSON_KEY'),
                          (b'{"a":NaN}', 'NONFINITE_JSON')]:
            with self.subTest(raw=raw):
                (self.root / mark.MANIFEST).write_bytes(raw)
                with self.assertRaisesRegex(mark.MarkError, code):
                    mark.check(self.root)

    def test_changed_report_rejected(self) -> None:
        (self.root / mark.REPORT).write_bytes(b'{}\n')
        with self.assertRaisesRegex(mark.MarkError, "MEASUREMENT_REPORT_CHANGED"):
            mark.check(self.root)

    def test_symlink_rejected(self) -> None:
        path = self.root / mark.ASSET; path.unlink(); path.symlink_to(ROOT / mark.ASSET)
        with self.assertRaisesRegex(mark.MarkError, "SYMLINK_REJECTED"):
            mark.check(self.root)

    def test_parent_escape_rejected(self) -> None:
        shutil.rmtree(self.root / 'sources/assets')
        (self.root / 'sources/assets').symlink_to(ROOT / 'sources/assets', target_is_directory=True)
        with self.assertRaisesRegex(mark.MarkError, "PATH_ESCAPE"):
            mark.check(self.root)

    def test_missing_source_fails_without_repair(self) -> None:
        (self.root / mark.ASSET).unlink()
        result = self.cli('check')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'ORIGINAL_PNG_PENDING_HUMAN_UPLOAD', result.stderr)
        self.assertFalse((self.root / mark.ASSET).exists())

    def test_commands_read_only_report_reproducible(self) -> None:
        paths = [mark.ASSET, mark.MANIFEST, mark.REPORT]
        before = {p:(self.root/p).read_bytes() for p in paths}
        result = self.cli('check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b'authority=none', result.stdout)
        result = self.cli('report')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, before[mark.REPORT])
        self.assertEqual(before, {p:(self.root/p).read_bytes() for p in paths})

    def test_malformed_json_and_invalid_usage(self) -> None:
        (self.root / mark.MANIFEST).write_bytes(b'{broken')
        self.assertEqual(self.cli('check').returncode, 1)
        self.assertEqual(self.cli('repair').returncode, 2)
        self.assertEqual(self.cli('check','extra').returncode, 2)

    def test_archive_size_bound(self) -> None:
        (self.root / mark.MANIFEST).write_bytes(b' '*(mark.MAX_FILE_BYTES+1))
        with self.assertRaisesRegex(mark.MarkError, 'FILE_LIMIT'):
            mark.check(self.root)


class PendingUploadTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name in (mark.MANIFEST, mark.REPORT):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)

    def cli(self, command: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run([sys.executable, "-B", str(SCRIPT), command,
                               "--root", str(self.root)], capture_output=True,
                              timeout=15, check=False)

    def test_metadata_does_not_claim_binary_verification(self) -> None:
        result = self.cli("metadata")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"original=not_checked", result.stdout)
        self.assertNotIn(b"MARK_INTEGRITY_OK", result.stdout)
        self.assertFalse((self.root / mark.ASSET).exists())

    def test_absent_original_check_fails_explicitly(self) -> None:
        result = self.cli("check")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr.strip(), b"ORIGINAL_PNG_PENDING_HUMAN_UPLOAD")
        self.assertFalse((self.root / mark.ASSET).exists())

    def test_absent_original_cannot_generate_report(self) -> None:
        result = self.cli("report")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")

    def test_reference_manifest_cannot_change_authority(self) -> None:
        value = mark.expected_manifest()
        value["authority_effect"] = "approved"
        (self.root / mark.MANIFEST).write_bytes(mark.json_bytes(value))
        self.assertEqual(self.cli("metadata").returncode, 1)

    def test_reference_report_cannot_be_rebased(self) -> None:
        (self.root / mark.REPORT).write_bytes(b"{}\n")
        result = self.cli("metadata")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"MEASUREMENT_REPORT_CHANGED", result.stderr)

    def test_commands_never_create_or_rewrite_files(self) -> None:
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob("*") if p.is_file()}
        for command in ("metadata", "check", "report"):
            self.cli(command)
        after = {p.relative_to(self.root): p.read_bytes()
                 for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
