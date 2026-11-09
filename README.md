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
