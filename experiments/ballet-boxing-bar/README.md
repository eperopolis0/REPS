# Ballet / Boxing / Bar

A new REPS experiment for independent one-shot pairs: coordination,
anti-coordination, or a stag-hunt payoff rule, with an optional outside option.
Both players use the same payoff rule from their own perspective. This is **not**
the asymmetric-preference Battle of the Sexes unless a future explicitly named
condition implements that different payoff matrix.

## Status

Local setup draft, prompt version `setup-v0-table`. This is a runnable adapter
implementation and Nix registration, not a completed experiment or an upstream
accepted package. At commit c0a68db, the packaged Nix checks passed: 14 pytest tests including
real event_capture, plus a completed mock smoke with 54 records passing
reps-runner verification (schemas, projection, producer audit, results and seeds).
Wick executed the build; Slick independently read the Nix derivation logs. The
original 625a249 smoke failed seed verification; c0a68db fixes that mismatch.
The secrets scan had zero known credential values, so it does not establish
coverage of actual runtime credentials. Real-provider calls remain untested.
The event receiver worked inside Wick's Nix sandbox; that does not establish
this seat's ability to launch the same build or access another machine.

The table prompts are a **new provisional variant**, not a verbatim transcription
of an approved prose prompt set. Do not treat the three short introduction
variants as the final three parallel prose conditions. Prompt review must finish
before scientific runs. No comprehension check is injected into a scored game.

## Design

- Each pair starts fresh. Nothing is learned from earlier pairs. `trials` counts
  independent pairs, not repeated interaction.
- Neutral A/B or Ballet/Boxing labels; Bar is optionally present.
- Positive integer rewards for A/B, nonnegative integer reward for Bar. Common
  scaling changes the framing and is recorded; it is not assumed behaviorally
  irrelevant. Bar is always paid to its chooser; the partner may earn zero.
- Stag hunt: A pays `reward_a` only against A, B always pays `reward_b`, and Bar
  (when enabled) always pays `bar_reward`.
- Anti-coordination: A/B pay only against the other letter; unequal A/B rewards
  are rejected in this first version.
- Shared fixed/random order or independently randomized order. Every condition
  states which one is in use. Separate model instances can truthfully receive the
  same initial prompt. This does not claim an internal-state fork or identical
  random draws. Same-model/same-prompt framing requires equal model IDs and shared
  order; all calls use the same run seed, as required by the upstream verifier, and
  that seed is recorded. Identical prompts with identical provider seeds may
  yield identical or correlated outputs. Fresh conversations do not establish
  independent random draws; this limitation matters for symmetry-breaking claims.
  Order randomization uses a separate recorded seed derived from run seed + trial.
- Optional one-message exchange: neither recipient receives the other's message
  before both have written. Final actions are not disclosed to either player.
  Requests may execute sequentially, but information remains simultaneous.
- Optional full probability forecasts before exchange and, if applicable, after
  exchange. Both target the eventual final choice. Forecasts stay in each
  player's conversation, so elicitation is an intervention, not a passive measure.
- Strict JSON parsing with no repair calls or default actions. Invalid choices
  yield missing pair payoffs, not losses. Invalid forecasts are separately counted.
- The REPS ChatClient records requests, responses, usage and errors. Adapter
  observations retain trial/order/seeds, messages, parsed choices and outcomes.
  Provider errors abort the run; no fake zero summary is emitted.

Mock replies exercise wiring only. Their choices are scripted, not model results.
The Brier sum pools phases; use the phase-tagged events for before/after analysis.
It is a prediction accuracy measure, not a direct measure of optimism or trust.
A nominal token cap does not bound spend across all retries: the common REPS
client controls transport retries. Review budget and provider support before a
real-model run.

## Build and run (packaged mock checks verified; real providers pending)

From the fork root, with the existing Nix infrastructure available:

```
nix build .#checks.x86_64-linux.ballet-boxing-bar -L
nix run .#ballet-boxing-bar -- --describe
nix run .#ballet-boxing-bar -- \
  --set game=coordination --set model_a=mock/model --set model_b=mock/model \
  --set trials=2 --set wording=1 --set labels=ballet_boxing \
  --set partner=same_model_same_prompt --set order=shared_random \
  --set include_bar=true --set reward_a=10 --set reward_b=10 --set bar_reward=5 \
  --set communication=true --set forecasts=true \
  --set temperature=0.0 --set max_tokens=256 \
  --seed 0 --json --non-interactive
```

The named app is the execution entry point. Do not manufacture REPS runs by
calling the runner with a hand-written manifest. The registered smoke check
executes the built app and verifies its saved run.

Unit checks without pytest, from this directory in a configured Python environment:

```
python -m unittest discover -s tests -p test_core.py -v
```

The separate `test_events.py` requires the REPS `event_capture` fixture and a
working socket environment. Unit mocks do not certify transport or run storage.

## Before tomorrow's main batch

Freeze prose wording and the exact payoff conditions; decide how many independent
pairs, which models, and whether forecasts/messages are enabled. Run the built
mock smoke, inspect and verify its store, then conduct a small authorized provider
smoke. A local branch is not a hosted fork, upstream merge, or a job on someone
else's machines. Set a publication remote only after choosing its owner; exclude
credentials and private review snapshots from the contribution.
