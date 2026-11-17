# Bisimulation

I built Bisimulation to answer a small, stubborn question: when are two states of a labelled transition system actually the same? It compares small labelled transition systems and shows you why two states are — or aren't — equivalent: strong-bisimulation rounds, the step matches that failed, distinguishing modal formulas, and finite trace products. There are separate modes for explicitly hidden actions and for divergence-preserving branching.

Everything runs on the Python standard library, and the browser version is a separate JavaScript implementation. There's no model, no API, no dataset download, no hosted inference — the whole thing runs locally.

[Interactive demo](https://midya8.github.io/bisimulation/) · [Method and sources](METHOD.md) · [Native engine](bisimlab/core.py) · [Independent checker](bisimlab/verify.py)

## The same traces can hide different choices

An agent can preserve every possible action sequence and still lose the ability to choose what happens next. The default control is built around exactly that: a choice retained after action `a` versus a choice fixed during `a`. The two states have equal finite trace languages — checked exactly through reachable subset pairs — but they fail strong bisimulation at refinement round two. You can inspect every failed same-action response and the distinguishing Hennessy-Milner formula that comes out of it.

One thing this is not: a statement about LLMs, policies, real software, or deployed agents. It's a hand-written finite protocol model. No source-code extraction or state labeling is inferred.

## What the strong-bisimulation report shows

- Every ordered state pair, including unreachable states, every synchronous relation round, and the final unchanged round.
- Every left/right attack for each removed pair — every same-label candidate response, its target pair, and its previous-round status.
- A deterministic first-failed-attack witness for each removed pair, as a topologically ordered modal formula DAG with truth sets and depth.
- Greatest-fixed-point equivalence classes and quotient edges.
- Exact finite trace-language equality, or a shortest distinguishing word via paired reachable-subset BFS — not bounded trace sampling.
- A complete downloadable canonical report, independently replayable without calling the analyzer.

## Picking a semantics

- The original inspector compares visible-action strong bisimulation and finite traces.
- `traces.html` keeps the complete reachable paired-subset graph for one state pair.
- `silent.html` compares strong, divergence-insensitive branching, and weak semantics after explicitly hiding labels.
- `divergence.html` checks branching equivalence with an explicit within-class divergence obligation.

The suite right now is 32 Python tests and 12 Node/actual-Chrome tests, spread across the original and the separate divergence workflows. The historical checks below name the mode they cover; no one mode inherits another mode's guarantees.

## Running it

Python 3.10+, no runtime dependencies. Node 22+ and Chrome if you want the optional browser tests.

```bash
python -m unittest discover -s tests -v
npm run test:all
python -m bisimlab input.json --output report.json
python -m bisimlab report.json --verify
bash tools/check_wheel.sh
python -m http.server 8000 --directory docs
```

`npm run test:all` runs the nine original Node/Chrome tests plus the three explicit-divergence tests. `npm test` keeps the original three-mode suite; `npm run test:divergence` runs only the separate divergence suite. The Python tests still run with the command above.

Or `pip install .` and then `bisimlab input.json`. Input looks like this:

```json
{"states":["idle","done"],"actions":["send"],"edges":[["idle","send","done"]]}
```

Exactly `states`, `actions`, `edges` — one to six states, zero to three actions, at most eighteen unique edge triples. Identifiers are unique ASCII names up to sixteen characters. State and action order define deterministic output order; edge IDs are input positions. Native JSON rejects duplicate keys and nonfinite constants, caps analysis at 65,536 bytes and verification at 8 MiB, and only replaces output atomically after success. The browser uses JSON.parse (last duplicate key wins), then the same value-schema bounds; editing input immediately clears stale results and exports.

## What the original strong-mode checks cover

The original nine native tests are still in the suite. They include all 512 directed three-state/one-action graphs checked against enumeration of every symmetric relation containing the diagonal, 100 seeded graphs, semantic quotient checks, input immutability and permutation, canonical report forgeries, generator-disabled checker replay, and strict CLI/atomic-output behavior. The native checker shares input validation only — relation semantics use independent partition signatures, formulas use direct state evaluation, and trace comparison uses explicit frozensets instead of generator bitmasks.

The original three Node/actual-Chrome tests cover 593 complete Python/JavaScript reports (5,684 pairs, 1,492 rounds, 2,644 modal nodes), validation and immutability, and every control's round, removal, attack, match, pair, and formula at 320/390/1280. Six controls total 17 rounds, 50 removed ordered pairs, 96 attack records, 79 pair results, and 74 modal DAG nodes. Export and invalid-input clearing are checked. These counts describe the fixtures, not performance or general correctness proofs.

## Limits of the original strong mode

In the original strong mode every label is visible, including `tau`. The hidden-action and explicit-divergence modes below have their own separate contracts. This mode adds no weak or branching abstraction, no probabilistic bisimulation, no acceptance states, propositions, rewards, fairness, or temporal-logic model checking. State names are not observations. Deadlocks with different names are bisimilar. Loops need not be isomorphic to be equivalent. Every state has the empty finite trace.

First-removal rank equals minimum modal distinguishing depth in this finite visible-action logic. Formula size, negation depth, and displayed syntax are not minimized. Formula DAG references share subexpressions; there's no claim of quasilinear construction. Trace comparison is exponential in the state cap. No new algorithm, benchmark superiority, formal proof, or cryptographic authenticity claim.

The established theory is attributed in [METHOD.md](METHOD.md). The code, UI, and fixtures were written for this project. MIT licensed.

## Exact trace-product replay (v0.2)

[Trace-product inspector](https://midya8.github.io/bisimulation/traces.html) · [Trace method](TRACES.md)

For a single state pair, inspect every reachable paired subset, all action successors, canonical BFS discovery parents and depths, the complete mismatch-node list, and a shortest counterexample path. Unlike the base summary, this mode keeps exploring after finding a mismatch and retains the entire closed reachable graph. It stores provenance links instead of repeating full path strings at every node. No depth cutoff, and no claim that the listed mismatch nodes enumerate all distinguishing words.

```bash
python -m bisimlab pair.json --traces --output product.json
python -m bisimlab product.json --traces --verify
```

Input is exactly `{"system":{"states":["p","q"],"actions":[],"edges":[]},"pair":["p","q"]}`. Same bounded LTS schema; the pair can repeat a state. Finite-word possibility means a nonempty reachable subset, not arbitrary accepting-state NFA semantics. A native explicit-subset transition-table checker replays the complete report without invoking the bitmask generator.

Seventeen native tests retain all nine base tests and add all 512 unary three-state graphs with all nine ordered starting pairs, direct path-enumeration checks, 120 seeded products, forged graph/provenance/frontier/witness rejection, generator-disabled replay, input and empty-action boundaries, and strict atomic CLI modes. Six Node/actual-Chrome tests retain all three base tests; 4,715 complete independent trace reports match (13,001 nodes, 13,926 successor edges, 1,156 mismatch nodes). Seven UI controls expose 18 nodes, 32 successors, 15 BFS layers, three mismatch nodes, and eight witness-path prefixes, each record checked at 320/390/1280 along with export and stale-result clearing. Installed checks now cover six base and seven trace reports through both entry points and six module origins outside the checkout. These are fixture counts, not general proofs or benchmark claims. Base core, verifier, original five demo assets, and original tests are unchanged.

## Silent-action abstraction (v0.3)

[Separate weak/branching inspector](https://midya8.github.io/bisimulation/silent.html) · [Exact contract and inspected foundations](SILENT.md)

Hide supplied labels explicitly, then inspect three separate fixed points: strong on the original labels, divergence-insensitive branching, and divergence-insensitive weak bisimilarity. Every removed ordered pair keeps all attacks, canonical finite response-path skeletons, and previous-round relation requirements. Branching preserves the option at the matched step; weak matching may discard it. The default standard contrast is credited to Bisping Example 6.3 — not claimed as a new counterexample.

Canonical silent reachability, nonempty cycle witnesses, and per-state possible divergence remain separate. A silent loop and a deadlock may be equivalent under these semantics; no termination, fairness, liveness, or divergence-preserving guarantee follows. State names are not observations, and a label named `tau` is visible unless explicitly hidden.

```sh
python -m bisimlab.silent examples/silent.json -o /tmp/silent.json
python -m bisimlab.silent --verify /tmp/silent.json
```

Independent path/set reconstruction replays every field without calling the generator. Small-case test oracles enumerate candidate relations instead of refining them. Native/JS complete reports agree on 1,154 requests; the optional unmodified mCRL2 ltscompare 202507.0 agrees on 350 systems / 5,652 pair-semantics comparisons. All 23 native tests pass on 3.10–3.13, all 9 Node/Chrome tests pass, and an installed wheel reproduces 6 base, 7 trace, and 10 silent controls through four entrypoints outside the checkout, with eight checked module origins and 20 forged-report rejections. Actual local Chrome checks 30 reports at 320/390/1280, 294 rounds, 498 removed-pair selections, 960 attacks, 414 response records, and 10 independently verified downloads. These are bounded coverage counts, not a proof or performance benchmark.

## The loop must stay inside (v0.4)

[Separate explicit-divergence inspector](https://midya8.github.io/bisimulation/divergence.html) · [Exact contract and inspected sources](DIVERGENCE.md)

Both states can admit infinite silent activity and still fail divergence-preserving branching equivalence. The credited Luttik 2020 Example 3 control makes the missing obligation visible: divergence must stay inside the related class, not merely reach any silent cycle. Every set partition is enumerated (at most 203), with complete per-state internal reachability, exit signatures, canonical nonempty-cycle lassos, and all failed equal-block obligations. Ordinary branching and explicit-divergence coarsest classes are kept separate. These are exhaustive candidates, not fixed-point rounds.

```sh
python -m bisimlab.divergence examples/divergence.json -o /tmp/divergence.json
python -m bisimlab.divergence /tmp/divergence.json --verify
```

32 native tests retain all 23 prior checks. A separate direct relational/matrix oracle checks every candidate across the two small exhaustive graph corpora; an independent simple-path/partition checker reconstructs full evidence without generator imports. All 220 declared non-input primitive-leaf mutations are rejected. Complete Python/JavaScript reports agree on 1,157 requests (8,720 partitions, 37,743 state records, 19,346 failures). Actual unmodified pinned mCRL2 agrees on 353 frameworks / 3,672 unordered-pair/semantics comparisons, not every witness field. Three new Node/Chrome tests supplement the unchanged nine; the fresh wheel preserves all previous installed checks and adds 13 controls through two entrypoints with 26 forgery rejections.

Real Chrome checks 39 reports at 1280/390/320, every 843 candidate selection / 4,467 state record / 2,955 failure record, 13 completed native-verified JSON downloads, and 47 full pixel states. Six-state/eighteen-edge limits are explicit. No new algorithm, production program verification, fairness, formal proof, or real-world agent guarantee. Technical divergence-sensitive branching, rooted, and stability-respecting notions are not substituted for this mode. All earlier APIs, tests, and demo assets remain unchanged.
