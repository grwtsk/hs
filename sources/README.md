# Source custody: founding manifesto

This is the source-preservation slice for [Hs #2](https://github.com/grwtsk/hs/issues/2),
not the finished book, an edited reading version, or a final interface contract.

`conversation/01-founding-manifesto.md` contains the founding text, including the
opening, sections I–X and the two unnumbered addendum paragraphs. The original
spelling, punctuation, mathematical notation, paragraph boundaries, space-only
second line and lack of an ending newline are deliberately retained. The issue
wrapper is excluded using the exact delimiters recorded in the manifest.

The text was transcribed from the issue copy read through the GitHub connector
and compared textually by the agent. It is not a raw export of the original
user-message transport. The manifest records that provenance and its limitation;
the checksum authenticates neither the author nor the truth of any statement.
No independent human acceptance is recorded by this archive.

## Stable references without editing the source

The sidecar `conversation/01-founding-manifesto.index.tsv` assigns a stable
`HS-U01-Bnnn` ID to every nonblank block: title, heading, and paragraph. Paragraph
IDs are the initial principle references; finer claim/interpretation mapping
belongs to [#14](https://github.com/grwtsk/hs/issues/14), not this mechanical index.
The `ADDENDUM` group is index metadata, not a heading inserted into the source.

Line ranges are one-based and inclusive. UTF-8 byte ranges are zero-based and
half-open; they exclude the final line separator. Whitespace between passages
remains protected by the whole-file checksum. Each passage also has a checksum.
For a citation, retain source ID, block ID, source digest and accepted commit;
do not cite a moving branch as an exact historical record.

From the repository root, with Python 3.10 or later:

```sh
python3 -B tools/book/check_founding_source.py check
python3 -B tools/book/check_founding_source.py show HS-U01-B002
python3 -B tools/book/check_founding_source.py index
python3 -B -m unittest discover -s tests -v
```

`show` emits the exact selected bytes and no extra newline. `index` prints the
reproducible TSV to standard output; it never updates files. Every command first
checks the frozen source identity. `check` and `show` also reject a changed index.
The script has no network access, external dependencies, approval transition,
or automatic source/manifest rewriting. A successful result means archive
integrity only. A coordinated malicious change to source, metadata and checker
still requires external review; these local checks are not a signature.

## Interpretation remains separate

Later instructions and corrections belong in [#3](https://github.com/grwtsk/hs/issues/3)
as separate records that link back to these IDs; they must not overwrite this
historical source. Reading the founding text alone is not sufficient to determine
the current governing instructions. In particular, do not revert later composed
intent-sity to a scalar by treating an earlier formulation as the final contract.

The original image remains a separate custody task in
[#4](https://github.com/grwtsk/hs/issues/4); this archive does not claim to contain
its bytes. Assistant continuations are not included as author text. Rights and
byline decisions remain in [#6](https://github.com/grwtsk/hs/issues/6).

The unresolved interpretation questions remain visible in
[#66](https://github.com/grwtsk/hs/issues/66), with human owners in #6–#11 and #65.
This source work adopts no disputed position, supplies no proof, and changes no
human decision. The later manuscript must keep those distinctions explicit.
Interface implementation still requires both [G1](https://github.com/grwtsk/hs/issues/36)
and [G2](https://github.com/grwtsk/hs/issues/38). Repository-wide gate tooling is
future work in [#5](https://github.com/grwtsk/hs/issues/5), not a capability claimed
by this source checker.

## Later source archive

Issue #3's captured U02–U11 inputs, scoped precedence annotations and separate
assistant-proposal ledger are described in
[the refinement guide](conversation/02-reading-guide.md). This adds ten captured
turns and fifteen author paragraphs without changing any HS-U01 passage. The
guide records the issue-copy provenance, including the U09 punctuation difference
from the available conversation display; it does not claim raw transport identity.

```sh
python3 -B tools/book/check_refinements.py check
python3 -B tools/book/check_refinements.py show HS-U07
```
