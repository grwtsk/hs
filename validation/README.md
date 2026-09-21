# Local validation and its limits

From a complete checkout of the reviewed commit, run:

```sh
python3 -B tools/book/check_founding_source.py check
python3 -B tools/book/check_refinements.py check
python3 -B tools/book/inspect_mark.py check
python3 -B tools/book/check_edit_navigation.py check
python3 -B tools/book/check_foundations.py check
python3 -B -m unittest discover -s tests -v
python3 -B tools/book/check_influence_model.py
git diff --check
```

The foundation checker and regressions use the Python standard library (3.10+).
The optional finite checker uses SymPy; absence is unrun, not success. The source
tools enforce their own original byte identities. No command repairs a source.

## Enforced by this slice

Strict schemas, duplicate keys, nonfinite values, IDs and types; safe local paths;
source/proposal digests; local Markdown links/anchors; actual-issue references;
stage barriers and acyclic prerequisites. Research references do not create
blocking edges. Parent containment is not a child prerequisite. Decision packets
precede disposition without waiting on their own approval.

Twelve DGs retain their owner issues and visible state. Declared human records
require origin, evidence locator, exact proposal/source binding, owner, scope,
conditions, revocation and retained objections. Agent origin, login-only consent,
stale binding, silent resolution and orphan DGs fail. Open questions and retained
dissent may coexist with provisional writing. A disposition can cover a single
passage scope without settling every affected work item.

This bounded slice accepts manuscript-phase work only. Complete-edition G1,
exact-artifact/scoped G2 and release G3 admission validators are not implemented.
Even well-formed proposed gate records cannot enable runtime work here. Those
validators need separate implementation/review; disabling this checker is not an
admission route. Full claim/quotation/rights linting, complete source freshness and
detailed per-issue execution prerequisites remain work under #5/#14/#31/#35.
The graph records known stage barriers, not a claim that every task is ready.

## Trust boundary

Validating a declared approval record does not independently authenticate its
human origin. An invented human declaration needs external review, not faith in
JSON. The owner catalog is a reviewed input, not a live authority query. A filename
scan cannot prove the absence of all interface behavior: Python, workflows and
disguised behavior still need review. This checker has no network; it cannot
establish external reachability, unchanged remote text, source rights or literary
quality. External issue references without exact captured bytes cannot support
approval binding in this slice.

Nonempty provisional prose is not accepted prose. No chapter can be marked
complete by this schema. Relational framing, courage, source fidelity and the
quality of objections require editorial examination, not a keyword classifier.
Synthetic cases test declared structure, not factual truth or human consent.
No private manuscripts, clinical sources or participant details are fixtures.

## Execution evidence

PR81 run 35651045212 tested head `a3f00da9a16e3d373f229a7d10dfbe56310e3a98`,
tree `1e744b8ee049c0cd328d0a9f3397e1c63dced981`: 109 tests, four source/asset
commands, ten finite symbolic checks and whitespace/read-only checks passed.
Merge `361c0f5185224ac18b2b55c21cfdf62cf7e15970` has that tree.
[The run](https://github.com/grwtsk/hs/actions/runs/35651045212) and
[review](https://github.com/grwtsk/hs/pull/81#pullrequestreview-5271527758)
are historical inputs, not results for this slice's new files.

The new PR's exact-head logs record its actual outcomes. Preserve incomplete and
failed attempts rather than rewriting them as passes. Distinguish local synthetic
checks, full-checkout tests, editorial self-review and independent review.
