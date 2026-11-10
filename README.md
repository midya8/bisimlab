# BisimLab

**Same traces. Different choices.** A finite agent-protocol inspector with every strong-bisimulation refinement, failed step match and executable modal witness. Original dependency-free Python and independent JavaScript implementation. No model, API, dataset download or hosted inference.

[Interactive demo](https://midya8.github.io/bisimlab/) · [Method and sources](METHOD.md) · [Native engine](bisimlab/core.py) · [Independent checker](bisimlab/verify.py)

## Why this exists

An agent can preserve every possible action sequence while losing the ability to choose what happens next. The default control contrasts a choice retained after action `a` with a choice fixed during `a`. The states have equal **finite trace languages**, checked exactly through reachable subset pairs, but fail strong bisimulation at refinement round two. Every failed same-action response and the resulting distinguishing Hennessy-Milner formula is inspectable.

This is about a hand-written finite protocol model, not a guarantee about an LLM, a policy, real software or a deployed agent. No source-code extraction or state labeling is inferred.

## What is inspectable

- Every ordered state pair, including unreachable states, every synchronous relation round and the final unchanged round.
- Every left/right attack for each removed pair; every same-label candidate response, its target pair and its previous-round status.
- A deterministic first-failed-attack witness for each removed pair, represented as a topologically ordered modal formula DAG with truth sets and depth.
- Greatest-fixed-point equivalence classes and quotient edges.
- Exact finite trace-language equality or a shortest distinguishing word via paired reachable-subset BFS, not bounded trace sampling.
- Complete downloadable canonical report, independently replayable without calling the analyzer.

## Run

Python 3.10+; no runtime dependencies. Node 22+ and Chrome for the optional browser tests.

```bash
python -m unittest discover -s tests -v
npm test
python -m bisimlab input.json --output report.json
python -m bisimlab report.json --verify
bash tools/check_wheel.sh
python -m http.server 8000 --directory docs
```

Or `pip install .` then `bisimlab input.json`. Input:

```json
{"states":["idle","done"],"actions":["send"],"edges":[["idle","send","done"]]}
```

Exactly `states`, `actions`, `edges`; one to six states, zero to three actions, at most eighteen unique edge triples. Identifiers are unique ASCII names up to sixteen characters. State and action order define deterministic output order; edge IDs are input positions. Native JSON rejects duplicate keys/nonfinite constants, caps analysis at 65,536 bytes and verification at 8 MiB, and replaces output atomically only after success. Browser uses JSON.parse (last duplicate key wins), then the same value-schema bounds; editing input immediately clears stale results/export.

## Validation

Nine native tests include all 512 directed three-state/one-action graphs against enumeration of every symmetric relation containing the diagonal, 100 seeded graphs, semantic quotient checks, input immutability/permutation, canonical report forgeries, generator-disabled checker replay and strict CLI/atomic-output behavior. The native checker shares input validation only; relation semantics use independent partition signatures, formulas use direct state evaluation, and trace comparison uses explicit frozensets instead of generator bitmasks.

Three Node/actual-Chrome tests: 593 complete Python/JavaScript reports (5,684 pairs, 1,492 rounds, 2,644 modal nodes), validation/immutability, and every control's round/removal/attack/match/pair/formula at 320/390/1280. Six controls total 17 rounds, 50 removed ordered pairs, 96 attack records, 79 pair results and 74 modal DAG nodes. Export and invalid-input clearing are checked. Counts describe these fixtures, not performance or general correctness proofs.

## Boundaries

All labels are visible, including `tau`. No weak/branching-bisimulation abstraction, probabilistic bisimulation, acceptance states, propositions, rewards, fairness or temporal-logic model checking. State names are not observations. Deadlocks with different names are bisimilar. Loops need not be isomorphic to be equivalent. Every state has the empty finite trace.

First-removal rank equals minimum modal distinguishing depth in this finite visible-action logic. Formula size, negation depth and displayed syntax are not minimized. Formula DAG references share subexpressions; no claim of quasilinear construction. Trace comparison is exponential in the state cap. No new algorithm, benchmark superiority, formal proof or cryptographic authenticity claim.

Established theory is attributed in [METHOD.md](METHOD.md). Code, UI and fixtures were written for this project. MIT licensed.


## Exact trace-product replay (v0.2)

[Trace-product inspector](https://midya8.github.io/bisimlab/traces.html) · [Trace method](TRACES.md)

For a single state pair, inspect every reachable paired subset, all action successors, canonical BFS discovery parents/depths, complete mismatch-node list and a shortest counterexample path. Unlike the base summary, this mode keeps exploring after finding a mismatch and retains the entire closed reachable graph. It stores provenance links instead of repeating full path strings at every node. No depth cutoff and no claim that the listed mismatch nodes enumerate all distinguishing words.

```bash
python -m bisimlab pair.json --traces --output product.json
python -m bisimlab product.json --traces --verify
```

Input is exactly `{"system":{"states":["p","q"],"actions":[],"edges":[]},"pair":["p","q"]}`. Same bounded LTS schema; the pair can repeat a state. Finite-word possibility means a nonempty reachable subset, not arbitrary accepting-state NFA semantics. A native explicit-subset transition-table checker replays the complete report without invoking the bitmask generator.

Seventeen native tests retain all nine base tests and add all 512 unary three-state graphs with all nine ordered starting pairs, direct path-enumeration checks, 120 seeded products, forged graph/provenance/frontier/witness rejection, generator-disabled replay, input/empty-action boundaries and strict atomic CLI modes. Six Node/actual-Chrome tests retain all three base tests; 4,715 complete independent trace reports match (13,001 nodes, 13,926 successor edges, 1,156 mismatch nodes). Seven UI controls expose 18 nodes, 32 successors, 15 BFS layers, three mismatch nodes and eight witness-path prefixes, each record checked at 320/390/1280 along with export and stale-result clearing. Installed checks now cover six base and seven trace reports through both entry points and six module origins outside checkout. These are fixture counts, not general proofs or benchmark claims. Base core, verifier, original five demo assets and original tests are unchanged.

## Silent-action abstraction (v0.3)

[Separate weak/branching inspector](https://midya8.github.io/bisimlab/silent.html) · [Exact contract and inspected foundations](SILENT.md)

Explicitly hide supplied labels, then inspect three separate fixed points: strong on original labels, divergence-insensitive branching and divergence-insensitive weak bisimilarity. Every removed ordered pair retains all attacks, canonical finite response-path skeletons and previous-round relation requirements. Branching preserves the option at the matched step; weak matching may discard it. The default standard contrast is credited to Bisping Example6.3, not claimed as a new counterexample.

Canonical silent reachability, nonempty cycle witnesses and per-state possible divergence remain separate. A silent loop and deadlock may be equivalent under these semantics; no termination, fairness, liveness or divergence-preserving guarantee follows. State names are not observations, and a label namedtau is visible unless explicitly hidden.

```sh
python -m bisimlab.silent examples/silent.json -o /tmp/silent.json
python -m bisimlab.silent --verify /tmp/silent.json
```

Independent path/set reconstruction replays every field without calling the generator. Small-case test oracles enumerate candidate relations instead of refining them. Native/JS complete reports agree on1,154 requests; the optional unmodified mCRL2 ltscompare202507.0 agrees on350 systems/5,652 pair-semantics comparisons. All23 native tests pass on3.10-3.13, all9 Node/Chrome tests pass, and an installed wheel reproduces6 base,7 trace and10 silent controls through four entrypoints outside the checkout, with eight checked module origins and20 forged-report rejections. Actual local Chrome checks30 reports at320/390/1280,294 rounds,498 removed-pair selections,960 attacks,414 response records and10 independently verified downloads. These are bounded coverage counts, not a proof or performance benchmark.
