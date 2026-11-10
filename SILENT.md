# Silence can hide a choice

Version0.3 implementation contract. Test counts below describe bounded checked coverage, not a general correctness proof.

## Definition and scope

This separate BisimLab inspector compares strong, unrooted divergence-insensitive branching and unrooted divergence-insensitive weak bisimilarity on the same supplied finite LTS. Existing strong/modal and trace-product inspectors remain separate.

Input is exactly `{"system": {"states": [...], "actions": [...], "edges": [...]}, "silent": [...]}`. The existing LTS validator permits1..6 states,0..3 action names and at most18 unique edge triples. Names are short ASCII identifiers; state names are not observations. The silent list contains distinct declared labels, normalized to action order. All listed labels become the same internal action. A name `tau` is not hidden automatically. Strong mode compares the original labels, before hiding.

Let `=>` be reflexive-transitive silent reachability. For an attacking step `p -a-> p'`, weak response is `q => q0 -a-> q1 => q'` with `p' R q'` when a is visible, or `q => q'` with `p' R q'` when a is hidden. Empty silent paths are allowed. Branching response is either a hidden step stuttering with `p' R q`, or `q => q0 -a-> q'` with both `p R q0` and `p' R q'`. Hidden central steps may use any listed hidden label. Both attack directions must hold.

The branching definition uses the published endpoint formulation. It does not require every intermediate path state to be related in each finite approximating round. The greatest branching bisimulation has the published stuttering property. No rooted, stability-respecting or divergence-preserving extension is implemented.

## Complete finite evidence

All ordered state pairs, including unreachable states, start related. Each synchronous refinement removes pairs whose one-step attacks have no successful response under the previous relation. Reports retain all rounds including the final unchanged round; all removed pairs retain every attack, every response skeleton, all required target/before-step pairs and previous-round booleans. The first failed attack is a deterministic witness, not a shortest modal formula. Retained pairs and classes are recorded separately for all three semantics; strict set differences are not a universal ranking.

Every reachable silent endpoint has one shortest path, tied lexicographically by input edge IDs. A weak visible response retains each possible prefix endpoint, central input edge and suffix endpoint with its canonical paths. Branching retains the analogous prefix/central-edge skeleton without suffix, plus the hidden stutter option. These are all finite endpoint/central-edge combinations, not all paths. Cycles can generate infinitely many concrete paths, and the report does not enumerate those paths.

Per-state possible divergence is a separate property: a canonical silent path leads to a nonempty silent cycle. It does not affect divergence-insensitive equivalence. A deadlock and an isolated silent loop are branching and weak equivalent even though only the latter diverges. This must not be presented as a termination, liveness, fairness or divergence-preserving result.

## Checked evidence

The native generator uses BFS path witnesses and set relation refinement. The independent verifier imports structural validation only, enumerates simple paths to determine reachability/canonical paths and reconstructs all records with separate code. It never imports/calls the generator. Test oracles additionally enumerate every symmetric reflexive relation for small cases and take the union of those satisfying the defining obligations, rather than using refinement. The diagonal can be included without loss because it is itself a bisimulation and these relations are closed under unions.

Native tests cover all256 two-state/two-label graphs with all four hidden-label subsets (1,024 requests), all512 three-state/unary graphs with hidden/visible cases (1,024 requests),120 seeded3..6state systems, strict contrasts, schema rejection, no mutation, checker isolation and altered output leaves. Input leaves are not generically forgery targets: changing an otherwise unused state name can define a different valid report. Strict atomic CLI, duplicate/nonfinite/oversize JSON, key/record forgery and installed-wheel checks also pass locally.

Native/JavaScript complete reports agree on1,154 requests: all1,024 two-state hidden-subset cases,120 seeded larger systems and10 controls. These reports contain8,461 rounds,4,014 removed-pair records and8,166 response records. These are coverage counts, not benchmark results.

Actual local Chrome checks30 reports at320/390/1280,294 rounds,498 removed-pair selections,960 attacks and414 response records. It checks all JSON/cards/tables/retained pairs, bounded horizontal scrolling, graph edge paths, exact source/target/hidden mappings, disjoint loop-label positions, export, invalid/stale clearing and recovery. Ten actual browser downloads passed the independent native CLI. Current local screenshots were visually inspected, including weak-versus-branching, deadlock/livelock and multiple hidden labels. All23 Python functions pass on3.10/3.11/3.12/3.13; all9 Node/Chrome tests pass. The installed wheel reproduces6 base,7 trace and10 silent controls outside the checkout, validates eight module origins, exercises four entrypoints and rejects20 forged reports.

Optional unmodified mCRL2 `ltscompare`202507.0 agrees on350 frameworks and5,652 unordered-pair/semantics comparisons. Inputs include all260 one/two-state/two-label graphs with one hidden label,80 seeded3..6state systems with0..2 hidden labels and10 controls. Action names are mapped to safe distinct labels in AUT files so a literal original `tau` does not accidentally become reserved; `--tau` is supplied only for weak/branching modes. This reference checks final relations, not every report witness or UI state.

## Reproduce local work

```sh
python -m bisimlab.silent examples/silent.json -o /tmp/silent.json
python -m bisimlab.silent --verify /tmp/silent.json
python -m unittest discover -s tests -v
node --test tests/test_silent_engine.mjs tests/test_silent_browser.cjs
PYTHONPATH=. python tools/check_silent_mcrl2.py --ltscompare /path/to/ltscompare
```

The reference executable is an optional external test dependency, not a runtime dependency. An official current nightly package required newer GLIBC/GLIBCXX than the local environment. The official Ubuntu Jammy PPA package ran without alteration: https://ppa.launchpadcontent.net/mcrl2/release-ppa/ubuntu/pool/main/m/mcrl2/mcrl2_202507.0.1-1ubuntu1ppa1~jammy_amd64.deb . SHA256 `70711c755b1520df061c3a1d25a77da971a920b963da9b9f3182861a2b9ad1f4`. The tool's version reports `ltscompare mCRL2 toolset 202507.0 (Release)`. No reference implementation code is copied or vendored into BisimLab.

Native generation bounds UTF-8 input at65,536 bytes and verification at4MiB, rejects duplicate JSON keys/nonfinite constants and replaces output atomically. Browser input also bounds UTF-8 bytes, but JSON.parse uses last duplicate key and has no lexical distinction between1 and1.0. Equality is checked on accepted normalized requests, not claimed for all lexical inputs.

## Inspected foundations and attribution

1. Rob J. van Glabbeek and W. Peter Weijland, *Branching Time and Abstraction in Bisimulation Semantics*, JACM1996. Author-hosted full section1, definitions1.1-1.6, stuttering lemma1.1 and equivalence discussion inspected: https://theory.stanford.edu/~rvg/abstraction/node2.html . Source of the explicit distinction between weak endpoint matching and branching before/after obligations. No proof or algorithm novelty claimed.
2. Bas Luttik, *Divergence-Preserving Branching Bisimilarity*, EXPRESS/SOS2020, EPTCS322,3-11, DOI10.4204/EPTCS.322.2. Introduction, relational condition(T), additional divergence condition(D), Proposition2 and counterexample3 inspected: https://arxiv.org/pdf/2008.13355 . The separate divergence warning is informed by this source; implementing only a cycle flag does not implement condition(D).
3. mCRL2, operator documentation, *Labelled transition systems*: https://www.mcrl2.org/mcrl2/web/user_manual/fundamentals/labelled_transition_systems.html . Definitions of visible/hidden actions, strong and branching bisimilarity and the difference from trace equality inspected. No toolkit algorithm copied.
4. mCRL2, operator documentation, `ltscompare`: https://www.mcrl2.org/web/user_manual/tools/release/ltscompare.html . AUT input, `bisim`, `branching-bisim`, `weak-bisim`, `--tau` and separate divergence-preserving options inspected and exercised. External results are attributed to this tool, not to our code.
5. Stephan Mennicke, *Concurrency Theory, Lecture7: Abstraction from Internal Activities*, TU Dresden, June6,2023: https://iccl.inf.tu-dresden.de/w/images/2/22/CONCUR23-07-Internals.pdf . Weak transitions/reflexive silent closure, classic one-step attack formulation, saturated formulation and rootedness distinction inspected. No CCS parser, composition or congruence claim implemented.
6. Benjamin Bisping, *Generalized Equivalence Checking of Concurrent Programs*, chapter6, *Recharting the Weak Silent-Step Spectrum*: https://generalized-equivalence-checking.equiv.io/06_weak-spectrum.html . Definitions6.1,6.3,6.7 and Example6.3 inspected. The default four-state contrast reconstructs the standard Example6.3 weak-but-not-branching witness; it is explicitly not a new counterexample. No stability-respecting logic or Isabelle proof copied or claimed.
7. *The mCRL2 Toolset for Analysing Concurrent Systems*, TACAS2019, section4.1 inspected: https://evink.win.tue.nl/research/Postscript/tacas19.pdf . Established independent algorithm/tool context, not a performance claim for this exhaustive inspector.

The original bounded code and UI are written for this repository. Established semantics, the adapted default contrast and optional external tool are credited above. Remaining tiny controls illustrate generic boundaries; no novelty of their mathematical patterns is claimed. No production-agent guarantee, inferred program model, probabilistic semantics, new algorithm or scalable solver claim.
