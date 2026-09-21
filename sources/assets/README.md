# Original mark: grwtsk.png

The author uploaded the original in commit
`3c45aadb6688b1995a8b8f8a34ff29a9001383f9`, whose message specifies
"Please use grwtsk.png". Its canonical path is shown below. Do not rename,
reencode, duplicate or replace the PNG. No further image upload is requested.

```text
sources/assets/grwtsk.png
```

Expected length: **34,918 bytes**. Expected SHA256:

```text
e197a1263819ae2c03a9776ac16076de75618aa9af7778d4acb266c6d5774692
```

The commit's Git tree identifies a 34,918-byte blob
`b481ca7006ba1bcb8821a75f0cf96c7d22c5f81c`. That Git identity matches the
original attachment, whose SHA256 is given above. This binds the Git object to the
known original under Git's content-identity model. It is not a claim that a fresh
network clone or independent remote SHA256 computation succeeded.
[upload-status.json](upload-status.json) records the exact method and limits.
The measurement report and source hash are unchanged. A code/path correction is
not a new image revision. All 86 repository tests passed with no skips after the
filename correction, including the 51 unchanged archive tests. See the
[verification receipt](../../validation/upload-verification.json) and
[complete test log](../../validation/upload-full-suite.log). This is local
validation of identity-matched code and data, not a hosted-CI run.

## Inspection without a misleading pass

From the repository root, Python 3.10 or later:

```sh
python3 -B tools/book/inspect_mark.py metadata
python3 -B -m unittest discover -s tests -p test_mark_asset.py -v
```

`metadata` validates the reference manifest and report only. Its output explicitly
says `original=not_checked`. The original-dependent test class now requires
`grwtsk.png`: a missing file is a failure, not a successful run with silent skips.
Synthetic missing-file tests remain valid checks of failure handling.

For the committed original:

```sh
python3 -B tools/book/inspect_mark.py check
python3 -B tools/book/inspect_mark.py report > /tmp/hs-mark-report.json
cmp sources/assets/grwtsk-original.measurements.json /tmp/hs-mark-report.json
python3 -B -m unittest discover -s tests -v
```

`check` and `report` require the original. Its absence returns nonzero with
`ORIGINAL_PNG_MISSING`; neither command fabricates or downloads it.
The decoder checks identity, CRCs, bounded inflation, stream boundaries and all
five PNG filter forms within the source's three-chunk RGBA8 profile. It is not a
general image service or a security-certified parser. All commands are read-only.

## Material observations and their limits

The local original is 1420 by 1420 pixels, 8-bit RGBA, non-interlaced. Its most
common samples are `(0,0,0,3)` (1,560,547 pixels), `(226,225,224,255)` (321,848),
and `(30,30,30,255)` (130,189). The principal opaque samples are thus encoded
`#E2E1E0` and `#1E1E1E`. The veil's alpha is 3/255, approximately 1.18%; this is
not a direction to apply that opacity to the entire opaque body.

Only IHDR, IDAT and IEND chunks occur; there is no embedded color-profile
metadata. The report counts raw samples without assigning a profile, compositing,
resizing or calculating contrast. Its pixel proportions do not measure cognitive
load, perceived density or accessibility. PNG filter/alpha context is identified
in the inspector's source reference; no new conformance finding is claimed.

The prescribed 144 by 144 CSS-pixel resting extent is an author instruction,
not the file's intrinsic size. No renderer or interface is introduced here.
Palette/rounding/redaction decisions remain with #9 and DG-06. Rights remain
with #6; preservation selects no license. #75 governs later source revisions.
G1/G2/G3 and every unresolved philosophical disagreement retain their scope.
