# Original mark: the human supplies the PNG

The non-PNG source work for [issue #4](https://github.com/grwtsk/hs/issues/4)
is checked in here. **The original PNG is intentionally absent from this
check-in.** The author will upload it and supply its commit reference.
Do not create a placeholder, redraw it, embed it in text, or run a transfer script.

Upload the unchanged file to:

```text
sources/assets/grwtsk-original.png
```

Expected length: **34,918 bytes**. Expected SHA256:

```text
e197a1263819ae2c03a9776ac16076de75618aa9af7778d4acb266c6d5774692
```

The manifest describes the locally inspected original, not proof of its presence
in Git. The measurements are an exact reference report from that local source.
[upload-status.json](upload-status.json) records the pending human handoff. After
the upload, inspect the actual commit and read back its exact bytes before updating
that status or closing #4. An existing local original is not remote verification.

## Inspection without a misleading pass

From the repository root, Python 3.10 or later:

```sh
python3 -B tools/book/inspect_mark.py metadata
python3 -B -m unittest discover -s tests -p test_mark_asset.py -v
```

`metadata` validates the reference manifest and report only. Its output explicitly
says `original=not_checked`. With no PNG, the 14 synthetic decoder tests and six
metadata/pending-upload tests run; 13 original-dependent tests explicitly skip.
They automatically run when the original is present. A corrupt or substituted
file is not skipped. Do not describe skipped checks as successful verification.

After the upload:

```sh
python3 -B tools/book/inspect_mark.py check
python3 -B tools/book/inspect_mark.py report > /tmp/hs-mark-report.json
cmp sources/assets/grwtsk-original.measurements.json /tmp/hs-mark-report.json
python3 -B -m unittest discover -s tests -v
```

`check` and `report` require the original. Its absence returns nonzero with
`ORIGINAL_PNG_PENDING_HUMAN_UPLOAD`; neither command fabricates or downloads it.
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
