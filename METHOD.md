# BisimLab method and attribution

## Fragment and meaning

A finite labelled transition system is a set of states, a set of visible actions and a set of source/action/target edges. BisimLab accepts one through six states, zero through three action names, and up to eighteen unique edges. It compares all ordered state pairs, without an initial-state or reachability restriction. Names carry no state propositions or termination meaning. Deadlock is just the absence of outgoing edges; every state admits the empty finite trace.

Strong bisimulation requires each transition from either state to have a same-label transition whose target states remain related. It is a greatest fixed point. Starting with all pairs and repeatedly applying this transfer test gives decreasing finite approximants. The report includes round zero, each strict refinement and a final empty-removal stability round. The stable equivalence classes induce quotient edges. No special tau semantics: that label is visible like any other.

## Witnesses and checking

For a newly removed ordered pair (p,q), choose the first failed attack in deterministic order: left edges then right edges, in input order. If p -a-> t has no matching q successor surviving the previous round, construct `<a> (and F(t,u) for every q -a-> u)`. With no matching successor, the conjunction is true. Every referenced successor pair was removed earlier. If the chosen attack is on the right, construct the analogous formula true on q and negate it so the final formula is true on p and false on q. The report uses DAG node IDs instead of recursive textual expansion; conjunctions need not be simplified or deduplicated.

Modal operators are true, negation, conjunction and diamond. A diamond holds when a matching successor satisfies its child. Modal depth counts nested diamonds; boolean operators do not add depth. Every formula carries its independently evaluable truth set over all original states. Earliest removal rank is the minimum separating modal depth in this finite Hennessy-Milner fragment: pairs surviving k rounds agree on depth-k observations, and the generated witness at the next removal has that depth. This does not minimize number of nodes, conjunctions or negations.

The generator uses pair sets and bitmask trace subsets. The separate verifier imports only shared input validation, never invokes analyze, and reconstructs relations through action-to-partition-block signatures. It checks the exact ordered rounds, every attack/match record and first-failed attack, all DAG references/semantics/truth sets/depths, all pair results, classes and quotient edges. A separate explicit-frozenset BFS replays finite-trace results. Full typed structural equality rejects extra/missing fields and boolean/integer substitution. Generator-disabled replay and report forgeries are tests, not a formal proof.

## Finite traces are a different question

Trace comparison starts from singleton reachable subsets for p and q. BFS explores pairs of subsets under each action in input order. A word distinguishes exactly when one reachable subset is empty and the other nonempty. If BFS exhausts all reachable subset pairs without such a mismatch, all finite words agree. Otherwise the first mismatch is a shortest finite distinguishing word, with input-order tie breaking. `explored` means the number of discovered subset pairs when the mismatch is dequeued, not necessarily the number already processed. This is exact finite-word language comparison, not infinite traces, completed traces, accepting-state NFA semantics or a depth-limited sample. It can be exponential: at most 2^(2n) subset pairs per state pair before considering transition cost.

The default original six-state control intentionally uses the standard late-choice versus early-choice structure. From p, action a retains both b and c; from q, action a commits to one. Both admit exactly the same finite words, but the branching possibilities differ. The control illustrates known semantics, not a new research example. Retry cycles, delayed mismatch, named deadlocks, visible tau and a single empty state test different boundaries.

## Source ledger

Sources were read on November 9, 2026. These establish theory and scope; none establishes our implementation's correctness or performance. Original implementation and controls, no copied source code. No claim to implement the advanced algorithms in these papers.

| Source | Type | Sections read and used | Boundary |
| --- | --- | --- | --- |
| [mCRL2, Labelled transition systems](https://www.mcrl2.org/mcrl2/web/user_manual/fundamentals/labelled_transition_systems.html) | Official tool documentation, version 202607.0 | LTS, traces, strong bisimilarity, internal actions and branching contrast | Our model has no designated initial state or silent abstraction |
| [Jurriaan Rot, Coalgebra lecture 7: Non-deterministic systems](https://cs.ru.nl/~jrot/coalg18/coalg-lect7.pdf) (October 18, 2018) | Academic teaching notes | Section 1, trace recursion, nondeterministic choice, transfer clauses and largest bisimulation | Hand-written control has the familiar structure, not new theory; no coalgebra framework implemented |
| [Herman Geuvers, Apartness and Distinguishing Formulas in Hennessy-Milner Logic](https://www.cs.ru.nl/~herman/PUBS/Apartness_Vaandrager.pdf) (2022) | Primary paper | Introduction, Definition 1, section 2.1 Definition 2 and Proposition 1, image-finiteness caveat | Finite HML witness construction; no weak/branching apartness implemented |
| [Remco van Os, Computing Minimal Distinguishing Formulas for Bisimulation](https://cs.ru.nl/~freek/courses/mfocs-2024/slides/remco.pdf) (January 21, 2025) | Academic presentation of Martens/Groote work | Strong definition, HML, observation depth, k-bisimilarity, witness recursion, minimal-size warning | Depth is not formula size; no optimization algorithm or claimed new bound |
| [Thorsten Wissmann, Stefan Milius, Lutz Schroder, Explaining Behavioural Inequivalence Generically in Quasilinear Time](https://drops.dagstuhl.de/storage/00lipics/lipics-vol203-concur2021/LIPIcs.CONCUR.2021.32/LIPIcs.CONCUR.2021.32.pdf) (CONCUR 2021) | Primary paper | Abstract/introduction and partition preliminaries, DAG versus expanded-tree warning | We do not implement the paper's quasilinear generic algorithm or claim its asymptotic bound |
| [Cambridge, Topics in Concurrency, Lecture 4](https://www.cl.cam.ac.uk/teaching/1920/TopConc/Lecture4.pdf) (2019/20 course) | Academic teaching notes | Language/ completed trace distinctions and strong transfer clauses | This project's trace comparison is finite traces only, not completed/infinite trace equivalence |
| [Wikipedia, Bisimulation](https://en.wikipedia.org/wiki/Bisimulation) | Community reference, terminology cross-check | Formal definition, union/greatest relation, fixed point and game definitions | Primary papers/notes carry the mathematical claims |

## Validation and exclusions

See README for concrete test counts. An exhaustive tiny reference enumerates symmetric diagonal-containing relations directly, independent of fixed-point/partition implementations. Native and browser engines agree on complete reports; this is cross-implementation evidence, not proof. The wheel check runs both installed entry points outside checkout and checks four site-packages module origins.

No probabilistic systems, transition weights, propositions, weak or branching bisimulation, fairness, rewards, source-code extraction, accepting states, causal attribution or real-agent safety claim. Trace equality alone cannot establish branching equivalence. A syntactically valid hand-written model can omit behavior of the real system it describes.
