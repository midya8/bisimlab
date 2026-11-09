# Exact finite trace-product audit

## What changed

The base inspector compares each original state pair's finite trace languages and reports an early-stop BFS count/word. The separate trace-product inspector expands one selected pair's entire reachable determinised product, including successors after mismatch. Different counts are intentional: a full product can contain more discovered nodes than an early-stop comparison. It does not change base bisimulation or trace-summary behavior.

Input is exactly `system` and `pair`. The system uses the existing one-to-six-state, zero-to-three-visible-label, eighteen-unique-edge schema. Pair entries are declared state names, possibly equal. No explicit accepting states, epsilon moves, initial-state inference or state propositions. Every label, including tau, is visible. Every original state admits the empty finite word.

## Product semantics

For state set S and action a, next(S,a) is the union of targets of all a-labelled outgoing edges from states in S. The empty subset maps to itself under every action. Start from the two singleton subsets named by the pair. Each reachable pair of subsets (S,T) is a deterministic product node; its output is a mismatch exactly when one subset is empty and the other is nonempty.

Breadth-first traversal assigns node IDs in first-discovery order, processing each node and actions in input order. Each node stores ordered left/right state lists, parent ID, discovery action, depth, mismatch flag and one successor ID per declared action. Root parent and discovery action are null; depth is zero. Parent links strictly precede their children. Equal subset pairs are never duplicated. All reachable action successors are included, even after mismatch and through the both-empty sink.

Layers list nodes by first-discovery depth. They are not lists of words or bounded trace samples. `mismatches` lists every reachable possibility-mismatch node; the UI's “mismatch frontier” is not an antichain, minimum cut or enumeration of every distinguishing word. A mismatch can lead to other mismatches or the both-empty sink.

If no reachable node mismatches, every finite word has the same possibility from both states. Otherwise, the first mismatch in canonical BFS order has minimum depth. Replaying its parent chain gives a shortest distinguishing word. Multiple shortest words may exist; ties follow input action order. No minimum formula size, modal depth or branching-equivalence conclusion is inferred from this word.

Complete reachable-subset equality is the familiar product-language equivalence test applied to an LTS in which all original states are implicitly accepting. That is why output nonemptiness, rather than membership in an arbitrary final-state set, decides word possibility. Equal finite traces still do not imply strong bisimulation of original nondeterministic states.

## Checker and representation

The generator uses integer subset masks. The separate native verifier shares input validation only, precomputes explicit-frozenset next transitions for every original subset and action, and independently constructs canonical reachable provenance. It checks exact typed full structure: node IDs/lists, every successor, parent/action/depth, layers, complete mismatch list, verdict, first mismatch, path and word. It separately replays the final word over its explicit-subset transition table and compares minimum mismatch depth. It never imports/calls audit_traces as an executor. Independent JavaScript uses ordered state arrays/sets.

Report schema is `bisimlab-traces-v1`. Paths are stored once for the counterexample and as parent links for each node, not repeated word arrays. Node count is at most 2^(2n); at n=6 this loose cap is 4096 before reachability restrictions. Runtime and output are exponential in the state cap; this is intentionally tiny, not a scalable implementation. No HKC, congruence closure, minimized DFA, new algorithm, cryptographic signature or formal proof is implemented. Native JSON limits and atomic-output rules are inherited from the CLI; browser uses JSON.parse then bounded value validation.

## Validation

The original nine native and three Node/Chrome tests remain intact. Eight added native tests cover every one of 512 unary three-state graphs at all nine starting pairs, direct original-graph path enumeration to each discovery node and the finite product bound for shortest unary counterexamples, 120 seeded multi-action systems, equality with the base summary verdict/word, mismatch continuation, graph/provenance/layer/frontier/word forgeries, checker replay with generator disabled, immutability/permutation, schema/empty actions and strict atomic CLI modes.

Independent Python/JavaScript match 4,715 complete trace reports: 13,001 reachable nodes, 13,926 action edges and 1,156 mismatch nodes. The seven browser controls expose 18 nodes, 32 action successors, 15 discovery layers, three mismatch nodes and eight shortest-path prefixes. Actual Chrome checks every record at 320/390/1280, full JSON/export/invalid-input clearing and page overflow. Installed wheels reproduce six base and seven trace reports through both entry points outside checkout, with six site-packages module origins checked. Tests are evidence, not a proof or independent authored review.

## Source ledger and scope

The seven inspected sources in [METHOD.md](METHOD.md) remain the basis for finite visible LTS, trace-versus-bisimulation and modal-witness boundaries. This increment directly inspected further sections of Rot and two additional sources below, giving nine unique sources across official tool documentation, primary papers/academic notes and community cross-checks. Read November 9, 2026.

| Source | Type | Exact use | Not implemented |
| --- | --- | --- | --- |
| [Jurriaan Rot, Coalgebra lecture 7](https://cs.ru.nl/~jrot/coalg18/coalg-lect7.pdf), October 18, 2018 | Academic notes | Section 2.1.2 union-based determinisation, singleton language preservation Theorem 2.5; section 2.2 deterministic subset equivalence | No HK/HKC or up-to-congruence algorithm from section 3 |
| [Regular Language Equivalence and DFA Minimization, hosted by Michael Goodrich at UCI](https://ics.uci.edu/~goodrich/teach/cs162/notes/rm.pdf) | Academic teaching notes | Product DFA synchronized transitions, XOR final output and emptiness iff equivalence | No arbitrary accepting-state input or DFA minimization; hosting is not an unverified author attribution |
| [Wikipedia, Powerset construction](https://en.wikipedia.org/wiki/Powerset_construction) | Community cross-check | Reachable-only construction, union transitions and exponential subset caveat | No epsilon closure, copied diagram/code or attributed novelty |

The original base sources distinguish completed/infinite traces and silent/branching semantics. This mode does none of those. Hand-written finite models need not cover real software behavior; no LLM/policy safety or external execution guarantee. All UI/code/controls are original; standard mathematical ideas are attributed, not claimed as new.
