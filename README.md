# ShieldLab

ShieldLab solves small, hand-written protocol games with an adversarial environment. Inspect the fixed-point rounds, controller moves, losing ranks and branching strategy graphs in Python or the browser. The Python package has no runtime dependencies; separate native checkers and independent JavaScript implementations replay the reports.

[Interactive inspector](https://midya8.github.io/shieldlab/) | [Exact method and sources](METHOD.md) | [Native solver](shieldlab/core.py) | [Independent checker](shieldlab/verify.py)

## Choose an objective

- **Safety:** keep every possible play away from unsafe states. Safe waiting can win.
- **Reach-avoid:** stay safe until the first goal visit. Safe waiting without arrival loses.
- **Safe recurrence:** stay safe and visit a target infinitely often. Reaching it once is not enough.

These are separate interfaces, not interchangeable checks. In particular,
reach-avoid stops at the first goal while recurrence follows its outgoing moves.
The controls below show where the answers differ.

## Safety example

`choose` can take `fast` to a currently safe `pending` state, or `review` to safe `approved`. At pending the environment can choose `fault` and reach unsafe leak. A one-step safe-target filter permits fast; the complete safety fixed point rejects it. Change only pending's owner to controller, and choosing ok now makes fast winning. Same graph, different quantifier.

Six editable controls include that owner flip, a five-step forced failure, a safe environment cycle, indefinite safe waiting without progress, and an already-unsafe root.

## Inspect

- Every synchronous safety round, previous/next set, removed state and final unchanged round.
- Every state's existential/universal obligation and every move's previous-round target membership.
- All winning controller moves, canonical choices and losing ranks.
- For every winning root, the complete reachable closed-invariant graph under a canonical controller policy and every environment choice.
- For every losing root, a rank-decreasing environment counterstrategy graph retaining every controller choice, stopping at unsafe terminals.
- Downloadable canonical JSON, strict bounded native CLI and a separate full-report checker with an exhaustive positional-policy oracle.

## Run

Python 3.10+; no runtime dependencies. Node 22+ and Chrome for optional browser checks.

```sh
python -m unittest discover -s tests -v
npm test
python -m shieldlab arena.json --output report.json
python -m shieldlab report.json --verify
bash tools/check_wheel.sh
python -m http.server 8000 --directory docs
```

Input is exactly `states`, an array of one to six `{name, owner, safe, moves}` records. Each state needs one to three `{action, to}` moves. Owners are controller/environment; safe is boolean. All targets declared; actions unique within each state. Dead ends are rejected, not silently converted into terminal self-loops. Both module and installed `shieldlab` CLI support stdin (`-`) and atomic `--output`.

The original eight native tests cover all 21,952 three-state total graphs across every ownership/safe-set assignment and 150 seeded larger graphs. The original three Node/actual-Chrome tests compare 643 complete certificates and every control record at 320/390/1280, including export and invalid-input clearing. Installed-wheel checks run both CLI entry points outside checkout. Full counts, exact conventions and seven inspected sources are in [METHOD.md](METHOD.md).

## Limits

Finite, total, deterministic moves and turn-based perfect information. Adversarial environment, not probabilities. Safety is never visiting unsafe, not progress or reward. This is a model inspector, not a deployed shield or guarantee about an LLM or real software. No model API, private dataset, new algorithm, formal proof, temporal-logic compiler or scalability claim. Original implementation/fixtures; established theory is attributed.

## Reach-avoid: first goal visit

[Reach-avoid inspector](https://midya8.github.io/shieldlab/reachavoid.html) | [Precise contract and eight-source ledger](REACHAVOID.md)

A separate finite first-goal objective distinguishes safe waiting from forced arrival. Inspect every synchronous attractor obligation, exact minimum worst-case move bound, rank-decreasing strategy graph and complete target-avoiding counterstrategy. A move to a winning successor can still stall forever. A slower detour can also be winning: every positional controller assignment is evaluated separately, including a worst-case goal path, unsafe path or non-goal lasso for each root.

```sh
python -m shieldlab.reachavoid docs/reachavoid-example.json --output reachavoid.json
python -m shieldlab.reachavoid reachavoid.json --verify
# After installation: shieldlab-reachavoid
```

Terminal goals must be safe and stop the play on first hit. Empty targets lose; an unsafe root loses immediately. Safety-until-goal treats success as absorbing and is not necessarily the original nonterminal infinite-safety objective. No fairness, probabilistic model, recurrent-goal guarantee, real deployment or new algorithm is implied.

The reach-avoid release checked 24 native test functions (8 original plus 16 reach-avoid) on Python 3.10-3.13. Independent deterministic strategy-pair simulation checks 324 two-state and 32,928 three-state cases; 120 seeded larger cases and the 729-policy boundary have full replay. That release also checked six Node/Chrome tests. Complete native/JavaScript agreement covers 457 reports, 1,329 policies and 6,291 root outcomes. Actual Chrome drills all 12 controls at 320/390/1280, including every policy/root and 12 actual exports verified by the native CLI. Fresh installed wheels on all four Python versions reproduce 6 original and 12 reach-avoid reports through both entrypoints, check 8 module origins and reject 20 forged CLI records. These counts describe bounded coverage, not a proof or scaling benchmark. The original safety engine, checker, controls, JavaScript and tests retain their original semantics.


## Safe recurrence (0.3): repeated target visits

A target is live, not terminal. The separate safety-and-Buchi inspector checks that every play stays safe **and visits a supplied target infinitely often**. One acknowledgement followed by permanent safe waiting passes first-hit reach-avoid but fails recurrence. Goal outgoing edges and environment ownership can change the answer.

[Safe recurrence inspector](https://midya8.github.io/shieldlab/recurrence.html) | [Exact recurrence contract and inspected sources](RECURRENCE.md)

Every nested greatest/least fixed-point round, every successor obligation, both players' complete positional-policy atlases, every root outcome and labeled failure lasso are retained. A separate checker enumerates full strategy pairs and simulates their unique plays; an independent JavaScript engine does the same. Complete branching proof graphs retain every opponent move and stop only at unsafe, never at a target.

```sh
python -m shieldlab.recurrence request.json --output report.json
python -m shieldlab.recurrence report.json --verify
node --test tests/test_recurrence_engine.mjs tests/test_recurrence_browser.cjs
bash tools/check_recurrence_wheel.sh
```

The recurrence release checks cover 39 Python tests, all 74,088 three-state graph/owner/safety-target configurations, a third matrix-cycle oracle, 498 complete cross-language/checker reports, 163 individual primitive-leaf forgeries, isolated installed reproduction and 12 trusted actual-Chrome downloads verified natively. Hosted release and deployment are separate checks, not inferred from these local results. Exact bounds remain six states and three moves per state, not a scalable solver or real-agent guarantee. Original safety and first-goal interfaces retain their meaning. No fairness, probabilities, private data or model API.
