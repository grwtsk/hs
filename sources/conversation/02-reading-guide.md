# Later refinements: source custody and interpretation

This is the source-preservation work for [Hs #3](https://github.com/grwtsk/hs/issues/3).
It is not an edited chapter, a final contract, or a decision packet accepted by
its human owner. The earlier `01-founding-manifesto` files remain byte-identical.

## What is preserved

`02-author-refinements.md` compiles ten author-turn copies, U02–U11, as recorded
in issue #3 and its [source-extension comment](https://github.com/grwtsk/hs/issues/3#issuecomment-5753037599).
The text retains the spelling, punctuation, capitalization, paragraph boundaries
and internal spacing of those copies. U10/U11 lose only the issue's leading
blockquote marker. Their heading level becomes `##` for this compilation.

Every heading is an **editorial wrapper**, not part of a verbatim human utterance.
The sidecar index distinguishes those ten wrappers from fifteen author paragraphs.
The manifest identifies each turn's payload range separately. No assistant
continuation is interleaved as author text.

| Turn | Subject of the archived input | Author paragraphs |
|---|---|---:|
| HS-U02 | Redaction and the white/black endpoints | 1 |
| HS-U03 | Arc, ark, Noah and resistance | 1 |
| HS-U04 | Color, emotion, intensity and innocence | 3 |
| HS-U05 | The cache, argument and resolution | 1 |
| HS-U06 | Organic addresses | 1 |
| HS-U07 | Composed, non-scalar intensity and welcome | 1 |
| HS-U08 | Ark-held routing intelligence and intent-sity | 4 |
| HS-U09 | The complete Hs book and later interface commission | 1 |
| HS-U10 | Research the other repositories, including imperfections | 1 |
| HS-U11 | Extend the issues and explicitly mark disagreements | 1 |

The source is an **agent transcription of issue copies**, compared textually to
the connector readings. It is not a raw original-message export or independent
byte comparison to the conversation transport. In particular, the available
conversation display ends U09 with two periods after `complete`; the issue copy
ends with one. This archive retains the issue copy and records the discrepancy
rather than silently claiming identity to both. Original transport trailing
whitespace is not certified. A later corrected capture must remain a separate
source/version, not an unrecorded change to this one.

The headings, summaries and mappings are editorial apparatus. Their existence,
an owner's GitHub login, an archive checksum, or a merged source PR does not
establish a claim's truth or accept a philosophical interpretation.

## Stable references and read-only commands

With Python 3.10 or later, from the repository root:

```sh
python3 -B tools/book/check_founding_source.py check
python3 -B tools/book/check_refinements.py check
python3 -B tools/book/check_refinements.py show HS-U07
python3 -B tools/book/check_refinements.py show HS-U08-P002
python3 -B tools/book/check_refinements.py index
python3 -B -m unittest discover -s tests -v
```

`HS-U07` names the entire captured turn payload. `HS-U08-P002` names its second
paragraph; `HS-U08-H` names its editorial heading. Index lines are one-based and
inclusive. Byte ranges are zero-based, half-open UTF-8 ranges excluding the last
line separator. `show` emits exact bytes without an added newline. The whole
archive has no final newline. Inter-passage whitespace is bound by its digest.

Every command checks the founding archive, new capture, manifest, index and
annotation references before producing output. No command writes a file, makes
a network request, follows an href, computes a consent score or resolves a DG.
`index` prints the deterministic table for comparison, not automatic repair of
a damaged archive. Invalid input reports a reason and produces no source output.

The manifest digest is pinned in the checker; source and checker still require
external review together. These checks cannot detect a coordinated malicious
rewrite of every trust anchor or authenticate fabricated provenance. The ledger
checks validate structure, references and non-adopted status—not the truth or
adequacy of an interpretation. Repository-wide phase/delegation tooling remains
[#5](https://github.com/grwtsk/hs/issues/5), not a capability supplied here.

## Precedence is scoped, not blanket replacement

`02-precedence.json` records ten **agent-authored annotations**, each tied to
exact new/founding passage references. It does not contain executable grants.

The important explicit constraint is U07's rejection of scalar intensity. It
rules out a scalar reading of U04; it does not imply U04 explicitly prescribed a
scalar, nor does it erase U04's color, consent, rhetorical or dove statements.
U08 elaborates routing and applies intent-sity at the address bar; it does not
supply a proved numerical equivalence between contrast and consent. U09 orders
the philosophical book before the interface. U10/U11 commission research and
visible disagreements; they do not adopt the assistant's research conclusions.

A later clear instruction governs its actual scope. A source tension requiring
interpretation remains linked to its human decision issue. None of the older
passages is rewritten, and no compiler or chronology rule selects a disputed
philosophical outcome. The frozen annotation snapshot may be superseded by a
separately attributed version, not relabeled after the fact.

## Assistant proposals remain proposals

`02-agent-proposals.json` is an attributed synopsis, **not a verbatim archive of
assistant sections XI–XXV**. Its topics come from #3's proposal requirements and
[#66](https://github.com/grwtsk/hs/issues/66). It also marks the later four-record
synthesis and routine-repair suggestion as proposals. Do not quote these
summaries as the original assistant wording or as the author's doctrine.

All twelve entries say `PROPOSED_NOT_ADOPTED`. Each links exact source passages,
applicable DGs and the existing human issues #6–#11/#65. DG-01–DG-12 are all
represented; this is a source-level handoff, not implementation of #66's full
argument/disposition registry. Archive checks cannot turn these entries into
human decisions. Future decisions require their actual human-origin records.

The open topics include preserved distinctions, present/prior/assisted consent,
reader/source boundaries, proof termini, contrast/admission, redaction material,
retention, resolution, manufacturer authority, ark-only orientation, bounded
repair delegation and source-lineage adoption. They are questions and proposed
readings, not fabricated quarrels between named people. The clarification in
[#66's governance comment](https://github.com/grwtsk/hs/issues/66#issuecomment-5753057540)
preserves humans' choice of a collective procedure while distinguishing an
operational vote from proof, universal consent or refutation of dissent.

Source preservation leaves all these choices with their humans. It supplies no
new license, training permission, external-source disclosure, model, app scaffold
or interface. [G1](https://github.com/grwtsk/hs/issues/36) and
[G2](https://github.com/grwtsk/hs/issues/38) still precede interface development;
[G3](https://github.com/grwtsk/hs/issues/61) still controls launch.
