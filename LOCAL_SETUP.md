# Local fork setup

Upstream: https://github.com/antimemes/REPS
Base commit: f3735f82388815fb145f2a7fd329f7b2224439ac
Working branch: slick/ballet-boxing-bar
Upstream remote is named `upstream`; no publication `origin` is configured.

This local fork adds experiments/ballet-boxing-bar. It uses upstream's automatic
experiment registry, provider client, event vocabulary and Python environment
builder. Source identity includes the code and lock. No dependencies were
installed and no Nix store build or model requests were performed during setup.
`uv lock` resolved metadata and wrote the dependency lock using an already
installed interpreter; it did not sync/install an environment.

Private prompt-document/comment snapshots are outside this checkout. The prompt
implementation remains explicitly provisional. Ricky approved using his own GitHub account. An authenticated publication
route, contribution remote and final research conditions are still needed. No remote fork, push or PR
has been created. Packaged mock verification passed on c0a68db in Wick’s build environment:
14 pytest tests and 54 verified smoke events. Slick independently read the Nix
derivation logs. No real-provider smoke has run. Shared provider seeds may
correlate identical requests; sampling design remains unresolved for science runs.
