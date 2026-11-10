# Safe waiting is not arrival

Version 0.2 implementation contract. Release and deployment checks are separate gates. The code implements established finite reachability theory, not a new game-solving method.

## Objective and stopping convention

The request contains exactly `arena` and `goals`. The arena keeps the original ShieldLab schema: one to six named states; each has a controller/environment owner, boolean safe flag and one to three uniquely named deterministic moves. All targets are declared. Even goal and unsafe states must have moves in the supplied total arena; missing moves are rejected rather than assigned an implicit meaning.

Goals are unique declared names, normalized into arena order, and must be safe. A play wins on its **first goal visit**, provided no unsafe state has occurred before it. A goal root succeeds in zero moves. An unsafe root loses immediately, even if it has an edge to a goal. Empty goals make every root lose reach-avoid. Goal actions are not taken after success. This implements the classical `(V minus B)* F` reach-before-unsafe condition with disjoint target F and unsafe B, as stated in the LABRI source below.

No fairness assumption is imposed. An environment that can wait forever may do so. One favorable path to a goal is not a guarantee against every environment choice. This is finite arrival, not the repeated-goal objective of a Buchi game.

## Least fixed point and exact bounds

Seed the synchronous attractor with all goals. At each step retain goals and add safe controller states with at least one successor already admitted, and safe environment states with every successor admitted. Every round records the complete previous/next sets, added states, existential/universal test, each target's previous membership and the goal override. The final unchanged round is included. Goal states can have a false outgoing-target test while still being admitted because the play has stopped.

A state's rank is its first admission index: zero for goals, one for states admitted in the first transition, and null for losing states. It equals the minimum worst-case number of moves to a first goal. At an active winning controller state it is one plus the minimum successor rank; at an active winning environment state, one plus the maximum successor rank. Finite ranks are at most five in this six-state fragment. A strictly decreasing controller move is therefore rank-optimal. Environment moves in a winning proof all decrease rank, though not necessarily by exactly one.

Every original move reports its target's winning status and rank. Only active winning controller moves satisfying `1 + target_rank == state_rank` are called optimal. A move to a winning successor is **not** by itself a uniformly permissive progress shield: repeated choices can stall in a non-goal cycle. Conversely, a slower detour can still be winning under a fixed policy. The interface and controls show both cases.

## Complete strategy evidence

For each winning root, select the first optimal controller action in input order and retain every environment choice. The complete reachable proof graph terminates at goals; every nonterminal edge strictly decreases rank. The root rank is an attained worst-case first-hit bound.

For each losing root, select the first environment move whose target remains outside the attractor and retain every controller choice. Stop only at unsafe terminals. This graph is closed outside the goal attractor. An adversary can cause unsafe or prevent every goal forever. A single displayed lasso is only one failure witness; the full branching counterstrategy is the universal evidence against all controller choices.

The request's safety flags are also analyzed with goals treated as absorbing success. This `safe_until_goal` region can include states that cannot force arrival. It is not necessarily the original infinite-safety region: a terminal goal may have an unsafe outgoing edge that is irrelevant after the first hit but would matter to the original nonterminal safety game. The old inspector and API retain their original objective unchanged.

## Every positional controller assignment

The atlas enumerates every deterministic action assignment on **safe non-goal controller states**, in state/move input order. Goal and unsafe actions are irrelevant after stopping and do not multiply policy counts. Decisions at unreachable active controller states do multiply counts. Empty products give one empty assignment. At most `3^6 = 729` assignments are admitted; this bound can be attained with no goals.

For every assignment and every root, explore every environment branch until the first goal, unsafe state or repeated non-goal state. A policy wins from a root exactly when no unsafe path or goal-avoiding cycle is reachable. Winning outcomes retain an exact worst-case length and a canonical longest goal path. Losing outcomes retain the first depth-first original-move-order unsafe path or lasso. The lasso path includes the closing edge; `cycle_start` is the zero-based index of the repeated node in the path's source-node sequence. It separates a finite prefix from a nonempty cycle. No shortest-counterexample claim is made.

Each root lists every winning and every rank-optimal policy ID. A separate list contains policies optimal simultaneously from every reach-avoid-winning root. If no root is winning this condition is vacuous, not a new winning guarantee. Policy counts are action assignments, not distinct behavior classes, randomized strategies or all history-dependent strategies.

## Independent implementation and checks

Native generation uses synchronous attractor/rank calculation and recursive original-edge policy traversal. The separate checker imports no reach-avoid solver. It enumerates complete positional assignments, uses an iterative stack of vertex-simple play prefixes to detect terminal paths/cycles, derives ranks from the minimum worst-case lengths and reconstructs every field. Safety-until-goal is separately checked by fixed-policy reachable-state searches. Type-sensitive complete replay rejects altered records, missing/extra keys, incorrect witnesses and forged counts.

A third test reference enumerates every pair of deterministic controller/environment policies and simulates each unique play until terminal/repetition. This uses neither an attractor nor branching graph search. The JavaScript engine independently derives ranks and round obligations from its policy atlas. It is not served a native report.

Checked local coverage, not a general proof. There are 24 native test functions (8 original plus 16 reach-avoid) and six Node/Chrome tests:

- All 324 two-state total target-set graphs across every owner and safe/non-goal/goal configuration, with full independent report replay.
- All 32,928 three-state total target-set graphs with exactly one goal, every other-state safety assignment and every ownership assignment. Separate deterministic strategy-pair simulation checks each root and every controller policy's worst-case value.
- 120 seeded four-to-six-state arenas with full replay, 12 prescribed original controls, the full 729-policy boundary, state/move permutations, schema/isolation errors, native checker isolation, full-record forgeries and atomic CLI rejection.
- 457 complete native/JavaScript reports, 1,329 policy records, 6,291 root outcomes and 559 rounds agree exactly.
- Actual Chrome at 320/390/1280 checks 36 control reports, 75 rounds, 273 obligations, 105 state selections, 105 proof graphs/93 proof edges, 141 policy/root selections and 108 path edges. All 12 actual exported files are compared exactly and independently verified through the native CLI. The 729-policy custom editor and invalid-input clearing are also exercised.
- Fresh installed wheels outside the checkout reproduce six original safety controls and 12 reach-avoid controls through module and console entrypoints. All eight installed module origins are checked; 20 forged reach-avoid CLI records are rejected. These checks pass on Python 3.10, 3.11, 3.12 and 3.13.

Browser and source test counts are finite coverage, not a proof, timing benchmark or scaling claim. Large full-policy reports still cost time and memory even within the input cap. Browser resources run locally; no model API or private data is used.

## Reproduce

```sh
python -m unittest discover -s tests -v
npm test
bash tools/check_wheel.sh
python -m shieldlab.reachavoid request.json --output report.json
python -m shieldlab.reachavoid report.json --verify
# After installation:
shieldlab-reachavoid request.json --output report.json
shieldlab-reachavoid report.json --verify
python -m http.server 8000 --directory docs
# Open reachavoid.html; the original index.html is unchanged in meaning.
```

Both native entrypoints accept stdin `-`, reject duplicate keys/nonfinite JSON, bound request bytes to 65,536 and verification input/report bytes to 16 MiB, and write outputs atomically. Invalid input exits 2 with a prefixed stderr error, no partial stdout and no traceback. Browser JSON parsing also rejects duplicate keys, nonfinite numbers and oversized requests. Editing clears results and disables old downloads before any new solve, and custom input is labeled separately from the selected fixed control. Export object URLs are kept alive briefly to avoid a download/revocation race.

## Inspected sources and distinctions

- Dietmar Berwanger, university-hosted MPRI2009/10 notes, basic definitions and section 2, Theorem 1/rank construction/Corollary 2: https://lsv.ens-paris-saclay.fr/~dwb/gtc.pdf
- University reachability/Buchi lecture, attractors and separate recurrence condition: http://nts.imag.fr/images/3/3b/ReachabilityBuchiGames.pdf
- LABRI Games and controller synthesis, September 28, 2021, attractor layers as at-most-k bounds and Exercise 4's reach-before-unsafe condition: https://www.labri.fr/perso/anca/Games/TD1-en.pdf
- Karin Quaas, university lecture 3, Winter2026/27, decreasing levels and positional determinacy: http://www.informatik.uni-leipzig.de/~quaas/games/lecture03.pdf
- Independent course notes on total finite reachability and decreasing indices: https://younesse.net/Game-theory-CS/Lecture1/
- University LTL-synthesis slides, separate safety/reachability/Buchi objectives and target-avoiding cycles: https://xiangyin.sjtu.edu.cn/Paper/FM-5.pdf . The slide's parenthetical use of "Reach Avoid Game" for safety alone is not this project's semantic definition; the explicit LABRI condition above is used.
- Research-paper introduction only, continuous-time differential/PDE reach-avoid distinction: https://arxiv.org/html/1410.6445v2
- Research-paper introduction/Definition 1/Problem 1, continuous/stochastic first-target-hitting convention: https://lcs.ios.ac.cn/~xuebai/Reach_avoid_Controllers_Synthesis_for_Safety_Critical_Systems.pdf . No continuous/stochastic controller synthesis, empirical result or optimization method from that paper is implemented here.

Original bounded code, fixed controls and interface. No source implementation, source text, empirical data or published figure is copied. No fairness, partial observation, probabilities, continuous dynamics, reward optimization, real deployment, scalable solver or new theorem is claimed. Missing modeled behavior invalidates any conclusion about real software.
