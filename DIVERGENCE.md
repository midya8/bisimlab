# The loop must stay inside

Version0.4 exact contract. This is a separate finite unrooted divergence-preserving branching-equivalence inspector. Earlier strong/modal, complete finite trace products and divergence-insensitive weak/branching workflows remain unchanged.

## What changes when silence can continue forever?

The first control reconstructs Bas Luttik2020 Example3/Figure1. It is credited, not a new mathematical counterexample. Six states have edges `s -i-> s`, `s -i-> s1`, `s -a-> s2`, `s1 -i-> s1`, `t -i-> t1`, `t -a-> t2`, `t1 -i-> t1`; only i is hidden. The s/t pair is divergence-insensitive branching equivalent and both states can reach infinite internal activity. Yet only s can loop internally while remaining in the class in which a is available. The pair is not divergence-preserving branching equivalent. Adding a global possible-divergence bit to the old relation is too weak.

An isolated silent loop and deadlock are also branching equivalent but not divergence-preserving equivalent. A one-way silent step between deadlocks is not a cycle. A two-state silent cycle is a cycle without needing a self-loop. These controls are distinct from the technical term divergence-sensitive branching equivalence, which can identify deadlock and livelock; no such name is substituted for this implementation.

## Input and finite search

Input is exactly `{"system":{"states":[...],"actions":[...],"edges":[...]},"silent":[...]}`. Existing structural bounds apply:1..6 states,0..3 distinct ASCII action names,18 unique edge triples, short unique state/action identifiers. Silent labels must be distinct declared labels and are normalized to action order. All hidden labels become one internal action. Even the literal label tau is visible unless listed. Names are not observations. Every state is included, reachable or not.

The implementation enumerates every set partition in lexicographic restricted-growth order. Bell numbers for1..6 states are1,2,5,15,52,203. Candidates are not successive fixed-point rounds. Each candidate assigns every state one block; blocks are numbered by first appearance. No random partition, depth cutoff or heuristic search is used.

For a candidate partition, an inert edge is a hidden step whose endpoints stay in the same block. For every state, the report retains every inert-reachable endpoint and one canonical shortest path to it. Ties use lexicographic original edge IDs.

An exit signature is a pair `(action,target_block)`: a visible edge to any block, including its own, or a hidden edge to a different block. It is reachable after an inert prefix inside the source block. Multiple hidden labels use null in the report, not a reserved action name. For each signature, one shortest whole prefix-plus-exit path is retained, with original edge ID. The signature table is complete; it does not enumerate infinitely many paths or all matching paths.

A candidate is branching-valid in this internal-path/stuttering form exactly when every pair in each block has equal exit-signature sets. Each direct inert attack can stutter. Every other attack is matched after an internal path that stays related to its source, followed by a step to the attack target's block. Conversely, unequal exit signatures expose a failure of this form's matching obligation. This stable-colouring/internal-path characterization gives the established coarsest branching equivalence by the stuttering results in the cited foundations; it is not an assertion that every arbitrary symmetric endpoint-form relation already has that property.

## The explicit-divergence obligation

For an equivalence partition, a state has internal divergence when it can reach a nonempty silent cycle without leaving its block. In a finite graph, an infinite path inside the block exists iff such a lasso exists: an infinite path repeats a state, and a finite prefix plus nonempty cycle can be repeated forever.

For every state, all reachable cycle roots are considered. Each root gets its shortest nonempty returning cycle. The selected lasso minimizes total prefix-plus-cycle length, then prefix edge IDs, then cycle edge IDs. This is canonical over these root/shortest-path choices, not a new optimal witness theorem or minimum modal formula. A zero-edge path never counts as a cycle.

A branching-valid partition is preserving-valid when all states in each block agree on this internal-divergence property. For the partition relation, this is exactly the explicit-divergence condition(D): an infinite silent path that remains related to the other state must have a matching infinite silent path whose states stay in the same class. Both directions are checked. It is not enough to match unrestricted divergence after leaving the class.

Every same-block ordered pair is related. Reports retain every candidate, every state obligation, every unequal exit-set record and every divergence mismatch. No first-failure truncation is used. Each semantics records all accepted candidate indices and the unique coarsest accepted partition. The implementation explicitly checks that its relation contains every pair from every accepted partition. The independent checker instead constructs their union and requires exactly one accepted candidate equal to it. The preserving relation is checked to be included in the ordinary branching relation.

## Replay, interfaces and lexical boundaries

```sh
python -m bisimlab.divergence examples/divergence.json -o /tmp/divergence.json
python -m bisimlab.divergence /tmp/divergence.json --verify
# after installation:
bisimlab-divergence examples/divergence.json
```

API: `from bisimlab.divergence import analyze_divergence`; checker: `from bisimlab.divergence_verify import verify_divergence`. Neither is silently added to the old package-root API. New module/console entrypoints are separate. Existing commands and three prior workflows remain intact.

The native checker imports only structural validation, never the generator or its path/partition helpers. It enumerates set partitions by block insertion, simple internal paths/cycles rather than BFS, reconstructs every field and compares exact types, keys, array ordering and values. Python bool is not accepted in place of integer evidence. Object key insertion order is not semantic. Complete reports are checked, not only final classes.

CLI generation input cap65,536 UTF-8 bytes, verification input cap8MiB, duplicate/nonfinite JSON rejection, strict error exit2 and atomic output replacement. Browser uses JSON.parse and therefore last duplicate-key wins, with no lexical distinction between1 and1.0; accepted normalized requests match, not every lexical input. Browser edits immediately clear stale results and disable export. Validating a report does not authenticate its author or prove the supplied protocol matches a program.

## Checked coverage

32 Python tests retain all23 previous tests and add nine. All512 unary three-state graphs with visible and hidden cases and all256 two-state/two-label graphs with all four hidden-label subsets are checked. For every candidate partition, a separate direct attack/response oracle and matrix nonempty-path closure check defining obligations without using the generator's exit signatures or cycle BFS. Seeded larger systems and13 controls are checked as well. Six-state/eighteen-edge/three-label capacity, canonical nonempty cycles, normalization, invalid shapes, immutability, strict CLI/atomic behavior, type/key/order forgeries and generator-disabled checker replay are covered. All220 non-input primitive leaves in the declared three-state prefix-control report are individually changed and rejected. This count does not claim every leaf of every report was mutated.

Three new Node/Chrome tests supplement the nine unchanged prior tests. Across1,157 requests (1,024 two-state hidden-subset cases,120 seeded larger systems and13 controls), complete independent JavaScript reports equal Python and pass the independent simple-path checker. Those atlases contain8,720 partitions,37,743 state records and19,346 failure records. Shared theory/schema/canonicalization remain common assumptions; this is not a formal proof.

Actual Chrome exercises39 control/width reports at1280/390/320; every843 candidate selection,4,467 state record and2,955 failure record is checked against native output, including the selected raw JSON. Thirteen trusted completed JSON downloads are read from disk and pass the native CLI checker. Forty-seven complete unmasked PNG states cover39 control/width pairs, three preserving choices, two rightmost narrow-scroll states, two expanded rejected candidates and invalid input. Counts are bounded coverage, not benchmarks or general correctness proofs.

A fresh isolated0.4 wheel checks both new entrypoints for all13 controls,26 forged-report rejections and three new installed module origins, while retaining the previous6 base/7 trace/10 silent control checks through their four entrypoints, eight prior origins and20 prior forgery checks. All checks run outside checkout with PYTHONPATH removed. Wheel installation itself runs outside checkout too, so source-tree package metadata cannot be mistaken for an already-installed wheel.

## Actual external reference

Unmodified mCRL2 `ltscompare`202507.0 agrees on353 frameworks and3,672 unordered-pair/semantics comparisons across `branching-bisim` and `dpbranching-bisim`. Corpus: all260 one/two-state two-label graphs with the first label hidden,80 seeded3..6-state systems and13 controls. Original labels are remapped to safe action names so a literal tau is not accidentally hidden. Explicit `--tau` lists exactly the requested mapped labels. This checks final equivalence relations, not report paths, candidate rejection details or UI rendering.

The optional reference is downloaded only for testing, not a runtime dependency or vendored implementation. Official Ubuntu Jammy package:
https://ppa.launchpadcontent.net/mcrl2/release-ppa/ubuntu/pool/main/m/mcrl2/mcrl2_202507.0.1-1ubuntu1ppa1~jammy_amd64.deb

SHA256 `70711c755b1520df061c3a1d25a77da971a920b963da9b9f3182861a2b9ad1f4`; version prints `ltscompare mCRL2 toolset202507.0 (Release)` with the tool's usual spacing. No binary, source or reference result is represented as this project's original algorithm.

```sh
python -m unittest discover -s tests -v
npm test
npm run test:divergence
PYTHONPATH=. python tools/check_divergence_installed.py
PYTHONPATH=. python tools/check_divergence_mcrl2.py --ltscompare /path/to/ltscompare
```

## Inspected foundations and attribution

1. Van Glabbeek, Luttik and Trcka, *Branching Bisimilarity with Explicit Divergence*: https://cgi.cse.unsw.edu.au/~rvg/pub/bbed.pdf . Relational(T)/(D), variants(D0..D4), the equivalence/stuttering argument and colouring discussion inspected. Primary source for why endpoint approximations, equivalence partitions and divergence obligations must not be conflated.
2. Bas Luttik, *Divergence-Preserving Branching Bisimilarity*, EXPRESS/SOS2020: https://arxiv.org/pdf/2008.13355 . Definition1, Proposition2, Example3/Figure1, modal discussion and divergence-sensitive/deadlock distinction inspected. The actual rendered Figure1 was inspected when reconstructing the credited first control. No new-counterexample claim.
3. Van Glabbeek and Weijland, *Branching Time and Abstraction in Bisimulation Semantics*, section1: https://theory.stanford.edu/~rvg/abstraction/node2.html . Branching definitions, internal-path and endpoint formulations and stuttering result inspected. This earlier page explicitly sets divergence aside; divergence claims rely on sources1/2 instead.
4. mCRL2 operator reference, `ltscompare`: https://www.mcrl2.org/web/user_manual/tools/release/ltscompare.html . AUT, explicit hiding and separate branching/divergence-preserving options inspected and exercised. Live page identifies202607.0; actual pinned executable is202507.0, not silently upgraded.
5. mCRL2 developer notes: https://www.mcrl2.org/web/developer_manual/libraries/lts/bisimulation_partitioner.html . Internal SCC preprocessing, added tau loops for divergence preservation and block signatures inspected. Our exhaustive203-partition atlas does not implement or claim its efficient partitioner or complexity.
6. Ubuntu operator manual: https://manpages.ubuntu.com/manpages/xenial/man1/ltscompare.1.html . Historical `dpbranching-bisim` and explicit equivalence distinctions inspected; current executable/options were checked directly, not inferred from this old manual.
7. *The mCRL2 Toolset for Analysing Concurrent Systems*, TACAS2019: https://evink.win.tue.nl/research/Postscript/tacas19.pdf . Section4.1 and established independent algorithm/tool context inspected. No toolkit performance is attributed to this bounded enumerator.

Failed arXiv HTML/abstract and DOI fetches were not used as evidence; the actual author PDF was read. The public sources contain established definitions, not authority to modify accounts or disclose private data. No external code is copied.

## Limits

This solves a supplied finite labelled transition system only. No source-code extraction, learned model, probabilistic transitions, rootedness, stability-respecting refinement, fairness, temporal-logic synthesis, agent safety/liveness guarantee or scalable implementation is claimed. Hidden divergence is possible behavior, not a prediction that every execution loops. Bell-number bounds are candidate counts, not wall-time, memory or serialized-byte guarantees. Finite bounded cross-checks and an external reference are evidence, not a general proof or cryptographic signature. Original code and UI are MIT licensed.
