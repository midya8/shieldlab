# Finite safety games, with every obligation

## Model and exact semantics

The input contains exactly `states`: one to six records with exactly `name`, `owner`, `safe`, `moves`. Names and action labels are ASCII identifiers of at most 16 characters. Each state has one to three moves with exactly `action` and `to`; action labels are unique within a state and every target is declared. Owners are `controller` or `environment`; safe is a JSON boolean. Moves are deterministic, but the owner chooses which move to take. Distinct actions may share a target. Every state must have a move: dead ends are rejected, never silently completed. A terminal outcome can be modeled explicitly with a self-loop, but doing so is a modeling decision.

A play is an infinite path in this finite total graph. The controller wins exactly when every visited state, including the initial state, is marked safe, against every environment strategy. State ownership need not strictly alternate. There is no probability distribution, fairness assumption, liveness requirement or reward. A safe self-loop can win forever without accomplishing a task.

All states are analyzed as possible roots, including those unreachable from any particular chosen state. No starting state is inferred from array order or state names. Names such as leak are labels only; the safe flag defines the objective.

## Greatest fixed point and dual ranks

Let Safe be the set of safe states. Start W0 = Safe. The next set contains safe controller states with at least one successor in W, and safe environment states whose every successor lies in W. Both conditions use the same previous set; updates are synchronous. This monotone descending iteration stops at the greatest safety fixed point. The report includes each previous/next set, every state's operator and target-membership flags, removed states and the final unchanged round.

Unsafe states have losing rank zero. A state removed in the first update has rank one, and so on. Winning states have null rank. At a safe losing controller state every successor has lower rank; at a safe losing environment state some successor has lower rank. Picking a rank-decreasing environment move therefore forces unsafe in at most the root rank despite any controller choices. The canonical move is the first such move in input order, not necessarily a fastest move. Winning controller moves are exactly those with winning targets; every such move is shown. The first is the canonical witness. All environment successors of a winning environment state are winning.

For each winning root, its proof graph fixes canonical controller choices and retains all environment choices. Its reachable states form a closed safe invariant. For a losing root, its graph fixes canonical environment counterchoices, retains all controller choices and stops at unsafe states. Every retained edge before failure strictly decreases rank, so the graph cannot cycle before failure. These are branching strategy witnesses, not a single sampled trace. Proof graph nodes use BFS first-discovery order and edges use source discovery order and input move order. They are witnesses for the selected canonical policy, not every possible winning policy or smallest proof graph.

## Implementation and checks

The native generator uses bitmasks for winning sets. Separate native verification shares only input validation, computes the dual unsafe attractor with explicit sets, checks full typed canonical structure and independently enumerates every positional controller policy. Under a fixed controller policy, all environment edges remain; ordinary graph reachability decides whether any unsafe state can be visited. Unioning the safe starting states over these policies independently checks the winning region. Positional policies suffice for finite perfect-information safety games. The bounded oracle may enumerate up to 3^6 controller policies; it is intentionally not a scalable verification strategy. The JavaScript implementation uses explicit sets and ordered arrays, not the Python executor.

Eight native tests include all 21,952 three-state total directed graphs with distinct outgoing targets, all ownership assignments and all safe subsets; 150 seeded larger games; exact owner-flip and delayed-failure controls; full-structure and typed forgeries; checker replay with the solver disabled; ordering/immutability; strict bounded JSON and atomic CLI output. Distinct actions with duplicate targets occur in seeded tests. Independent JavaScript matches all fields of 643 reports: 1,066 rounds, 3,251 state obligations, 3,170 moves and 1,738 proof edges. Six actual-Chrome controls expose 12 rounds, 52 state obligations, 59 round-move records, 18 state verdicts, 23 state moves, 18 proof roots and 32 proof edges, each checked at 320/390/1280px, plus JSON/export/invalid-input clearing/overflow. Installed wheels replay all six controls through module and console CLI outside checkout, with four installed module origins checked. Tests are evidence, not a formal proof or independent authored review.

Report schema: `shieldlab-v1`. Native input is capped at 64 KiB and report verification at 8 MiB; duplicate keys/nonfinite constants are rejected, malformed input does not replace existing output, and output replacement is atomic. Browser JSON.parse uses its usual last-key-wins parsing before bounded value validation. There is no persistence or network request from user-entered inputs; the page loads its static local assets only.

## Source ledger

Inspected November 9, 2026. The implementation, UI and six control arenas are original. Standard mathematical ideas are attributed rather than claimed as new.

| Source | Type | Use and boundary |
| --- | --- | --- |
| [Dietmar Berwanger, Graph games with perfect information](https://lsv.ens-paris-saclay.fr/~dwb/gtc.pdf), MPRI 2009/10 | Academic notes | Total game arenas, safety/reachability duality, unsafe attractor ranks, uniform memoryless strategies and graph-size complexity. This inspector uses a simple synchronous scan, not the linear-time queue implementation. |
| [Synthesising Succinct Strategies in Safety Games](https://ar5iv.labs.arxiv.org/html/1404.6228), 2014 | Primary paper | Explicit turn-based safety semantics, positional policies, graph-reachability strategy definition and attractor. No antichains, alternating simulations, succinct minimum-support strategies or OTFUR. |
| [Chatterjee, de Alfaro and Henzinger, Strategy improvement for concurrent reachability and turn-based stochastic safety games](https://luca.dealfaro.com/papers/13/2013-JCSS.pdf), JCSS 2013 | Primary paper | Distinguishes deterministic turn-based games from stochastic and simultaneous/concurrent games. No stochastic values, randomization or strategy-improvement implementation. |
| [UPPAAL Tiga User-manual](https://docs.uppaal.org/extensions/tiga/manual.pdf) | Official tool documentation | Controller/environment synthesis context, and the important boundary to timed automata and temporal-logic specifications. No UPPAAL integration, clocks or TCTL compiler. |
| [Alshiekh et al., Safe Reinforcement Learning via Shielding](https://arxiv.org/html/1708.08611), 2017 preprint | Primary paper | Safe-action filtering context and the need for a conservative environment abstraction. No RL training, runtime shield, automata product, LTL translation, minimum-interference theorem or real-world guarantee. |
| [Mikolaj Bojanczyk, Safety Games](https://www.mimuw.edu.pl/~bojan/20142015-2/alg/5-piecewise-testable-languages/safety-games), 2014/15 course | Academic notes | A different dead-end convention, where a player unable to move loses. This inspector deliberately rejects dead ends and uses explicit bad-state safety instead. The conventions are not silently mixed. |
| [Wikipedia, Safety and liveness properties](https://en.wikipedia.org/wiki/Safety_property) | Community cross-check | Safety/liveness distinction and finite bad-prefix intuition. Safe forever does not establish task progress. |

## What this does not establish

No learned or extracted model, LLM/policy guarantee, source-code verification, execution enforcement, partial observation, timing, probability, reward optimization, fairness, liveness or temporal-logic synthesis. A hand-written protocol can omit real behaviors or mislabel safe states. Results about the supplied graph do not validate the graph as a real-system abstraction. No new algorithm, formal proof, deployment certificate or scalability claim.
