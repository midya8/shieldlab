# Again is a different promise

ShieldLab0.3 implementation contract. Source checks, hosted checks and deployment verification are separate release gates. This implements classical finite safety-and-Buchi game theory, not a new solving algorithm.

## Live targets, not terminal success

The request contains exactly `arena` and `goals`. Arena retains the original schema: one to six uniquely named states, each with controller/environment owner, exact boolean safe flag and one to three uniquely named deterministic moves. Targets are declared and every state must have outgoing moves. Goal names must be unique declared safe states and normalize into arena order. No dead-end semantics are invented.

Controller wins from a root iff every play remains safe forever and visits a goal infinitely often. Unsafe fails immediately and permanently, even if it has a path into a safe goal loop. Goals are **not terminal** and their outgoing choices remain live. A safe goal self-loop wins recurrence: distinct target states or travel are not required. Empty goals lose everywhere. All supplied states are analyzed, including unreachable components. There is no fairness: an environment may keep waiting forever despite an available exit.

This differs from both original nonterminal safety and0.2first-goal reach-avoid, which stops successfully on the first safe target visit and ignores its outgoing edges afterward. Those old APIs and pages retain their original meanings. The0.3entrypoint is separate: `shieldlab.recurrence.analyze_recurrence`; it is not a root-package export.

## All nested fixed-point obligations

For a set X, `CPre(X)` contains controller states with some successor in X and environment states with every successor in X. The total arena avoids vacuous dead-end cases. Compute:

```text
nu Z . mu Y . Safe intersect ((Goal intersect CPre(Z)) union CPre(Y))
```

Outer Z starts at all safe states. Each new inner Y starts empty and synchronously grows until unchanged. That inner fixed point becomes the next outer set, which shrinks until unchanged. Starting the greatest iteration at Safe instead of all states is equivalent because the operator always yields a subset of Safe.

Every outer before/after/removed set, every inner before/after/added set and each state's owner quantifier, safe/goal flags, every original successor's membership in both current sets, target-reset test, progress test and admission are retained. Final unchanged inner and outer rounds are included. Inner admission does not imply final winning membership: an outer restart can later remove it. A goal does not override its outgoing test.

## Complete policy atlases and independent replay

Each player's atlas enumerates every deterministic action assignment on **its safe owned states**, including goals and unreachable states, in input state/move order. Unsafe actions are irrelevant because failure stops there and do not multiply counts. Empty products give one empty assignment. Each atlas has at most729assignments. Their product is also at most729, not729squared, because each state has exactly one owner and at most three moves. These are complete assignments, not distinct behaviors or all history-dependent strategies.

For a fixed controller assignment, retain all environment edges. It wins at a root exactly when neither unsafe nor a target-free cycle is reachable. A target-containing SCC is insufficient: it can include a target-free non-bottom cycle on which the adversary may remain. For a fixed environment assignment, retain all controller edges. It wins the complementary objective iff there is no reachable safe cycle containing a target; unsafe terminates as adversarial success. Transient target visits are allowed by the complement.

Native generation searches every vertex-simple play prefix. A failed controller/root retains the first original-move-order unsafe path or nonempty target-free lasso. A failed environment/root retains the first safe lasso whose cycle includes a target. A lasso includes its closing edge; `cycle_start` is the source-node index of its repeated node, also the finite-prefix edge count. This is a deterministic first-DFS witness, not a shortest-path claim. A winning policy/root has null failure, which is not a claim that one successful path proves it. All policy/root outcomes and all winning policy IDs are retained.

A separate full-report checker imports no recurrence generator. It enumerates every complete controller/environment policy pair and simulates its unique play to unsafe or repetition. A safe repeated cycle wins controller exactly when its cycle includes a goal; a goal occurring only in the prefix does not count. For each fixed policy every opponent assignment is checked. The lexicographically first original-move-index sequence among failures reconstructs the DFS witness independently. Integer bit-vector evaluation reconstructs every nested obligation; policy-pair and fixed-point winning regions must agree. Exact recursive type/key/list/primitive equality rejects every missing/extra field, ordering change and bool/int/float substitution. This is deterministic verification, not cryptographic authentication or a proof of implementation correctness.

Memoryless determinacy establishes that positional enumeration suffices to determine winning regions for these perfect-information games. Safety is represented by terminal failure here; equivalently make every unsafe state an absorbing nontarget sink in a total Buchi game. Both players have a uniform positional policy winning simultaneously on their winning region. The report retains every such uniform policy ID. Uniformity is vacuous if that player's winning region is empty and must not be read as a global win.

## Branching strategy and counterstrategy graphs

For each root fix the first uniform policy of the player winning that root and retain **every** opponent move. Explore the complete reachable graph in breadth-first input order. Stop only at unsafe, never at a goal. Every edge references an original labeled move; every reachable safe node has at least one retained edge. The native checker independently reconstructs every node and edge. A third test oracle uses matrix reachability and positive-cycle closure to check every policy's objective and each selected graph. One displayed failure lasso is an existential witness for a policy that fails, not the universal evidence against all opposing choices in a selected winning proof graph.

No claim that every move with a winning successor is a permissive recurrence shield. Repeatedly choosing individually within-region detours can create a target-free cycle. The complete fixed policy must enforce recurrence. No optimal inter-target delay, shortest strategy, optimal-policy count, ranking-function certificate or bounded response-time claim is made.

## Checked local evidence

Finite coverage, not formal proof or speed/scaling evidence:

-39Python tests:24prior tests plus15recurrence tests.
- All324two-state total target-set graphs across every owner and unsafe/safe-nongoal/safe-goal configuration, with independent unique strategy-pair comparison and full report replay.
- All74,088three-state total target-set graph/owner/status configurations independently check every policy/root verdict by strategy-pair simulation.
-160seeded4..6state games,100separately seeded larger complete-checker replays,12original controls, all729policy boundaries for each owner, state/move/target permutations, immutable input/output, strict schema and generator-disabled checker.
-163non-input primitive leaves in a prescribed report individually mutated and rejected; extra/missing fields, tuples, reordered records and bool/int/float substitutions rejected. These tests do not claim every possible mutation.
- A third matrix-cycle oracle checks every policy/root and selected proof on456arenas:12controls+324two-state cases+120separately seeded larger games.
-498complete native/JavaScript/checker reports agree across881outer rounds,1386inner rounds,4720state obligations,3566policies,17,065root outcomes and2116proof edges. Includes two729policy boundaries.
- Actual Chrome at1280/390/320 checks36complete control reports,66outer/132inner rounds,393obligations,264policy/root selections,333failure-path edges,90proofs and234proof edges. All12trusted completed download files are read from disk, compared to native reports and independently verified by the native CLI. Both729policy editors, edited-input clearing, duplicate/nonfinite/oversize rejection and stale-download disabling pass.
- A fresh isolated0.3wheel outside checkout reproduces12new controls through both module and console entrypoints, checks all four new installed origins and rejects24forged CLI reports. It also reproduces all6old safety and12old reach-avoid controls through all four old entrypoints, checks eight old installed origins and rejects20old forged reach-avoid reports. Python3.10..3.13hosted runs are a separate release gate.

Counts describe tested records, not original empirical results. Controls are original supplied graphs, not measured agent traces or copied published examples. The first control is a three-state send/acknowledge/permanent-idle graph: all states safe, first arrival winning from start/ack, recurrence losing everywhere. Owner flip, non-bottom cycle, unsafe-after-goal, one-goal loop, empty/all targets, unsafe root, mixed stalling, six-state ring and disconnected goal controls expose different obligations.

## Strict reproduction

```sh
python -m unittest discover -s tests -v
node --test tests/test_recurrence_engine.mjs tests/test_recurrence_browser.cjs
bash tools/check_recurrence_wheel.sh
python -m shieldlab.recurrence request.json --output report.json
python -m shieldlab.recurrence report.json --verify
# After installation:
shieldlab-recurrence request.json --output report.json
shieldlab-recurrence report.json --verify
python -m http.server 8000 --directory docs
# Open recurrence.html. Old index.html and reachavoid.html remain available.
```

Standard-library Python3.10+ runtime, schema `shieldlab-recurrence-v1`. Node22+ and actual Chrome for optional cross-language/browser tests. No inference API or private data. CLI accepts file paths and stdin `-`; generation input is at most65,536bytes and verification input/report at most16MiB. Duplicate JSON keys, nonfinite constants, invalid UTF-8, extra/missing schema keys and invalid targets are rejected. Output is atomically replaced only after complete generation/verification and size checks. Errors exit2 with a prefixed stderr message, no partial stdout and no traceback. Exact bounded input does not promise every serialized report will fit16MiB. These lexical limits do not constitute runtime/memory guarantees. Shared original validation is not an independent assumption check.

Browser uses an explicit duplicate-key/nonfinite/oversize-rejecting JSON parser and shares only original schema validation/parser code with the previous browser engine; the recurrence engine computes its own policy-pair reports. JSON lexical forms1and1.0are both numbers in browser parsing, but the recurrence schema contains no numeric user fields. Editing clears old results and disables old exports immediately. Export URLs remain alive briefly so trusted downloads complete. Wide tables scroll with an explicit cue; full records remain in every download.

## Inspected sources

The source formula and assumptions, not a published source implementation, are used:

- University LaBRI, *Languages, logics and automata*, attractors, positional strategies and repeated nonempty return: https://www.labri.fr/perso/anca/Games/graphgames.pdf
- Chatterjee/Henzinger/Piterman, *Algorithms for Buchi Games*,2008, definitions and Theorem2.1 positional determinacy for both players, classical repeated reachability/removal algorithm: https://arxiv.org/html/0805.2620 . No improved-complexity claim adopted.
- Gradel/Lucking/Naaf, *Semiring Provenance for Buchi Games*, LMCS20(1):21,2024, Section2 and nested greatest/least winning-region discussion: https://lmcs.episciences.org/13205/pdf . No semiring provenance or absorption-dominant-strategy feature claimed.
- Zimmermann/Klein/Weinert, *Infinite Games*, university lecture notes, total perfect-information games and recurrence/attractor context: https://people.cs.aau.dk/~mzi/teaching/lecture-notes%20infinite%20games.pdf
- Hausmann/Schroder, *Computing Nested Fixpoints in Quasipolynomial Time*, university talk Oct22,2019, nested fixed-point definitions/background only: https://www.csc.liv.ac.uk/~hausmann/nested.pdf
- *Universal Algorithms for Parity Games and Nested Fixpoints*, arxiv revision2022, nested-equation/parity-game background only: https://arxiv.org/html/2001.04333v2 . No general parity or quasipolynomial solver is implemented.

No fairness constraints, partial observation, stochastic transitions, continuous control, source-model extraction, game repair, generalized recurrence, new theorem or deployed safety/liveness guarantee. A missing modeled move invalidates any real-world conclusion.
