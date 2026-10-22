# Vaeil

Invite-only, anonymous matchmaking for students and young professionals (18–28). Vaeil runs one loop: invite → vetting → onboarding → curated match → anonymous chat → consensual Reveal.

This repository is the IT643 course project. The design and vocabulary live in [DESIGN.md](DESIGN.md), [UBIQUITOUS_LANGUAGE.md](UBIQUITOUS_LANGUAGE.md), and [TESTING.md](TESTING.md).

## Status

Slice 1 is complete: the pure domain core handles single-use Invite redemption behind an 18+ age gate, and reject-free vetting that fails closed. The API, UI, database, and real LLM adapter are not built yet.

## Run the tests (5 commands)

Requires Python 3.11+ and Git; PowerShell on Windows.

```powershell
git clone https://github.com/Diffusity/vaeil.git
cd vaeil
python -m venv .venv
.venv\Scripts\python.exe -m pip install pytest
.venv\Scripts\python.exe -m pytest -q
```

The suite uses in-memory fakes: no network, no database, and no real clock.

## Repository layout

- `src/vaeil/domain/` — pure domain core: no frameworks, no database, no LLM SDK.
- `tests/` — the pytest suite.
- `docs/` — project logs and agent docs.

## Licence

See `LICENSE`.
