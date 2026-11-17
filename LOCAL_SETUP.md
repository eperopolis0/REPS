# Local fork setup

Upstream: https://github.com/antimemes/REPS
Base commit: 4abd8ccb9364c2fad7b41feb7da403bc983fbb27
Working branch: slick/ballet-boxing-bar
Upstream remote is named `upstream`; `origin` is the public fork at
https://github.com/eperopolis0/REPS.git (HTTPS fetch and push URLs).

This local fork adds experiments/ballet-boxing-bar. It uses upstream's automatic
experiment registry, provider client, event vocabulary and Python environment
builder. Source identity includes the code and lock. No dependencies were
installed and no Nix store build or model requests were performed during setup.
`uv lock` resolved metadata and wrote the dependency lock using an already
installed interpreter; it did not sync/install an environment.

Private prompt-document/comment snapshots are outside this checkout. The prompt
implementation remains explicitly provisional. The public fork exists; no feature-branch
push or PR has been performed by Slick. Credential setup has been reported by Wick,
but Slick has not independently verified authentication. Final research conditions
remain unresolved. Packaged mock verification passed on 51727d8 in Wick’s build environment:
16 pytest tests and two 54-record verified smokes, covering run_seed and
provider_random. Slick independently read all three Nix derivation logs.
No real-provider smoke has run. provider_random omits the provider seed; it does
not establish independent draws. Sampling design still needs a scientific choice.

## TMPDIR integration, 2026-11-17

Rebased the seven local commits onto upstream 4abd8cc without conflicts. No changes
to GovSim were introduced. Affected source tests passed: 31 tests covering
lib/reps-events/tests/test_event_socket.py and experiments/ballet-boxing-bar/tests,
including upstream TMPDIR placement/cleanup and long-path diagnostics.

Used the existing environment
/nix/store/7yqsnrm4h65s64h1lh4v0v11vifk4m5b-ballet-boxing-bar-env/bin/python
with PYTHONPATH pointing to this checkout's reps-events, reps-experiment,
reps-testing and ballet-boxing-bar directories. Temporary files were under
/home/slick-admin/.slick-check/reps-tmp; bytecode and pytest cache writes disabled.
This was a source test run, not a rebuilt Nix package or new packaged smoke.
No dependencies were installed, model calls made or branch pushed.
