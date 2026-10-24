# Vaeil

Invite-only, anonymous matchmaking for students and young professionals (18–28). Vaeil runs one loop: invite → vetting → onboarding → curated match → anonymous chat → consensual Reveal.

This repository is the IT643 course project. The design and vocabulary live in [DESIGN.md](DESIGN.md), [UBIQUITOUS_LANGUAGE.md](UBIQUITOUS_LANGUAGE.md), and [TESTING.md](TESTING.md).

## Status

Slices 1 and 2 are merged into `master`: single-use Invite redemption behind an 18+ age gate, reject-free fail-closed Vetting, heuristic identifier scanning, and normalized in-memory Pseudonym claims. The retrospective tooling is also merged, including Windows CI. The verified suite has 122 tests (107 product and 15 tooling).

Rule 5 remains partial: the Member/Values Profile view, Conversation isolation, self-name check, and profile-write validation are not built. The self-name check will compare against the Member's own real name and email local part; it is not general name detection. API, UI, database, admission wiring, and real LLM integration remain pending. The product definition is closed; the MVP spec and remaining-ticket plan await approval.

## Remaining schedule (provisional)

Target: the start of December 2026, roughly five weeks from the October 24 audit. This is a proposed allocation from the confirmed scope, not an approved ticket plan or a delivery guarantee. Detailed session estimates and dependencies follow the MVP spec; each slice still needs tests and human review.

| Week | Proposed focus |
| --- | --- |
| Oct 26-Nov 1 | Member and structured Values Profile; pre-Reveal allow-list view; Conversation-scoped Reveal state and isolation; self-name validation |
| Nov 2-8 | FastAPI + React/Vite walking skeleton; persistent-disk deployment; PowerShell five-command local run; SQLite and auth/admission wiring |
| Nov 9-15 | Messages and fail-closed moderation; Reveal Consent and Engagement Threshold through the Clock port |
| Nov 16-22 | Minimal Admin console and queues; Matching and conversational Onboarding; Block/Report, append-only audit events, and real LLM integration when credentials are available |
| Nov 23-29 | Finish integration; seeded demo data; deployed rule walkthroughs, end-to-end verification, code/doc citation checks, and team viva rehearsal |
| Nov 30-start of December | Final fixes, live-demo verification, and submission readiness; push `project-final` before the viva |

Capacity is not yet established in sessions. This is tight for one human builder, especially the Admin/Matching/Onboarding integration; the last week must not become a second feature-build week. If estimates exceed capacity, the recommended cuts are Icebreakers first, then Engagement Threshold progress UI, then Report UI, then polish. Keep Report handling in the Admin queue, the Admin console, the Reveal, and all six rules. The spec-derived plan must expose any remaining overrun rather than silently cut those requirements.

## Run the tests (5 commands)

Requires Python 3.11+ and Git; PowerShell on Windows.

```powershell
git clone https://github.com/Diffusity/vaeil.git
cd vaeil
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest -q
```

The suite uses in-memory fakes: no network, no database, and no real clock.

After setup, run all development checks with `.venv\Scripts\python.exe scripts/check.py` (Ruff, assumption-history validation, and pytest). The Windows CI job runs the same command on PRs and pushes to master. The five-command setup above is unchanged.

## Repository layout

- `src/vaeil/domain/` — pure domain core: no frameworks, no database, no LLM SDK.
- `tests/` — the pytest suite.
- `docs/` — project logs and agent docs.

## Licence

See `LICENSE`.
