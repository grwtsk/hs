# Source-transfer recovery — 2026-09-21

## Current instruction and scope

The author instructed: “Undo the harm to the repo@GitHub Make all checkins other
than the PNG. I will upload that. and provide you with the checkin after you are
done”. This recovery brings the pending source-review PR #76 and all six non-PNG
files in the prepared source-transfer payload into Git, with explicit upload
status and corrected documentation. It does not upload the PNG, accept the book,
resolve disagreements or implement an interface. The upload remains the human's
act; inspection of the future commit remains work, not a result claimed now.

## Correct the diagnosis, not the historical evidence

The earlier conclusion that the owner needed to repair the GitHub connection was
unsupported. The subsequent diagnostic authenticated `grwtsk`, observed repository
push permission, and successfully exercised the connector's blob-write endpoint
using the existing README bytes. The working container's Git/DNS failure is a
separate transport limitation; it does not establish connector authentication
failure. Earlier incorrect PNG submissions were payload-integrity failures, not
proof of expired authorization. Their recorded hashes were not added to a branch
or PR. No reset, force push or deletion of established source history is justified.

The previous instruction to run `transfer_mark.py --publish-branch` is withdrawn
as the active handoff. That optional workaround was never repository source and
is not installed here. Do not request credentials, repeat manual base64 uploads,
or replace the user's chosen upload with an automatic transfer. Earlier handoff
archives remain historical records, not current execution instructions.

## Delivered and excluded

All six non-PNG payload paths are accounted for: asset-local `.gitattributes`,
asset README, reference manifest, reference measurements, read-only inspector and
its tests. The README now states that the PNG is absent. Inspector/test changes
make that absence explicit without weakening byte identity once a file is present.
New custody status, this correction and actual local logs complete the handoff.

The PNG is excluded entirely, including encoded copies and archive containers.
No placeholder occupies its path. The `.gitattributes` rule marks the future file
binary but does not create or ignore it. The old transfer launcher and its
transport-only tests are not product/source dependencies and are superseded by
the user's upload. No private external sources are copied. Separate RG-01 draft
packets remain available through #74; this asset recovery does not relabel them
as an accepted chapter or alter their existing source identities.

## Checks actually run for this recovery

In the prepared non-PNG workspace: 33 new-tool tests discovered; **20 passed,
13 explicitly skipped** because the original is not in the candidate. There were
no failures. The skipped checks are exactly the original-dependent test class;
the decoder and pending-state checks still ran. `metadata` returned success with
`original=not_checked`. `check`/`report` rejected missing PNG without writing a file.

In a separate local validation copy containing the supplied original: **33 tests
passed, none skipped**. Full image inspection passed for 34,918 bytes and 2,016,400
pixels. The recomputed measurement report matched the reference byte-for-byte.
The local original was never put in the repository candidate or tool upload.

The corresponding logs are `mark-pending-upload-tests.log` and
`mark-local-original-tests.log`. These are scoped local tests of the new inspector,
not hosted CI, independent verification, the unchanged 51-test archive suite or
verification of a future GitHub PNG. The existing archive code/tests are unchanged.
PR #76's four-file diff was read in full, with no review comments and no active
ruleset/branch protection observed; its recorded checks are historical, not reruns.

## Human upload handoff

Target: `sources/assets/grwtsk-original.png`.
Expected SHA256: `e197a1263819ae2c03a9776ac16076de75618aa9af7778d4acb266c6d5774692`.
Expected bytes: 34,918. No format conversion, flattening or resave is needed.

After the user supplies the commit, inspect the exact file in that commit, compare
its bytes/hash, run the inspector and complete source suite, and record the actual
outcomes. Update `upload-status.json` only with that evidence. Keep #4 open until
its full acceptance criteria are met. #75 remains the source-revisit obligation.
