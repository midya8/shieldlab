# ShieldLab

**A safe next step can still lose.** An exact tiny safety-game inspector for hand-written agent protocols. Every fixed-point obligation, winning controller move, unsafe-attractor rank and branching strategy proof is visible. Dependency-free Python, separate native verification and independent JavaScript.

[Interactive inspector](https://midya8.github.io/shieldlab/) | [Exact method and sources](METHOD.md) | [Native solver](shieldlab/core.py) | [Independent checker](shieldlab/verify.py)

## The control

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

Eight native tests cover all 21,952 three-state total graphs across every ownership/safe-set assignment and 150 seeded larger graphs. Three Node/actual-Chrome tests compare 643 complete certificates and every control record at 320/390/1280, including export and invalid-input clearing. Installed-wheel checks run both CLI entry points outside checkout. Full counts, exact conventions and seven inspected sources are in [METHOD.md](METHOD.md).

## Limits

Finite, total, deterministic moves and turn-based perfect information. Adversarial environment, not probabilities. Safety is never visiting unsafe, not progress or reward. This is a model inspector, not a deployed shield or guarantee about an LLM or real software. No model API, private dataset, new algorithm, formal proof, temporal-logic compiler or scalability claim. Original implementation/fixtures; established theory is attributed.
