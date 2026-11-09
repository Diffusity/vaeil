# Vaeil

Values-based matching with AI-assisted safety for students and young professionals (18–28). Vaeil runs one loop: invite → vetting → onboarding → curated match → anonymous chat → consensual Reveal.

This repository is the IT643 course project. The design and vocabulary live in [DESIGN.md](DESIGN.md), [UBIQUITOUS_LANGUAGE.md](UBIQUITOUS_LANGUAGE.md), and [TESTING.md](TESTING.md).

**Demo only — do not enter real personal details.** Future registration carries the same notice. Keep this notice until a consent and deletion plan exists; Render and Neon store app data. Seed personas are fictional. Local-model outside-user stretch requires uptime and consent planning.

## Status

Slices 1 and 2 are merged into `master`: single-use Invite redemption behind an 18+ age gate, reject-free fail-closed Vetting, heuristic identifier scanning, and normalized in-memory Pseudonym claims. The retrospective tooling is also merged, including Windows CI. The current suite has 463 passing Python tests (443 product/domain/boundary and 20 tooling), plus four browser tests; T1 merged with 401, and the earlier baseline was 122. The five benchmark cases guard the client; T2 adds 46 Conversation-domain cases without marking another rule done.

T1 merged in [PR #14](https://github.com/Diffusity/vaeil/pull/14), merge commit `4f9ca80`, with **401 passing tests**. It implements the Member/Values Profile pure view, shared self-name checks, ordered profile validation, opaque private scalars and pair-projection isolation. **Rule 5 remains partial**: T2 adds in-memory Conversation lifecycle/state authority; HTTP auth/display, persistence and moderated delivery remain future work. The real local-model adapter is not built. T1 tests cover constructor-friendly wrappers, safe diagnostics/export and an exact three-function unwrap allowlist; explicit authorized JSON remains unchanged. Spec: [#7](https://github.com/Diffusity/vaeil/issues/7). T1-T6 are published; later ticket estimates wait for the benchmark-informed velocity review.

## Remaining schedule (confirmed dates/capacity; estimates under review)

Confirmed viva: December 5, 2026, with five build sessions/week. Effort allocations depend on measured velocity. Hosting budget is $0; proposed deployment is Render Free plus Neon Free PostgreSQL, with SQLite the default local run. Provisioning remains approval-gated.

| Week | Proposed focus |
| --- | --- |
| Oct 26-Nov 1 | Combined identity/profile/Pseudonym self-name work, Conversation isolation and local skeleton; review velocity after T1, overlap Conversation/local skeleton, review again after T2 before deployment |
| Nov 2-8 | Early free deployment; one shared SQLite/Postgres repository, shared contract suite, persistence and audit foundation |
| Nov 9-15 | Auth/profile APIs; Messages/fake moderation and timeout/busy paths; teammate profile/chat pages after APIs merge |
| Nov 16-22 | Reveal and Admin console; deployed six-rule checkpoint with synthetic fixtures/current adapter |
| Nov 23-29 | Matching, Block/Report and seed integration; feature freeze Nov 28. Local-model safety integration starts immediately after Messages, targeting Nov 21 |
| Nov 30-Dec 4 | Rehearsal and fixes only (Nov 29-Dec 4); no new features |

Working scope is Plan B: drop conversational Onboarding, re-ranking, Icebreakers, explanation text, progress UI, Report submission UI, polish and a second adapter unless velocity permits. Protect all six rules, Admin console, Reveal and Report handling. Feature freeze **28 November**; **29 November-4 December: rehearsal/fixes only**. Five sessions/week is a tight optimistic plan; reviews after T1/T2 immediately report slippage. Teammates accepted H1-H6 but remain unassigned.

The real LLM will run on the owner's Windows laptop, behind the same LLM port. [Native Ollama CPU/Vulkan timings](docs/research/local-model-runtime-results-2026-10-27.md) are now measured for the three approved candidates; all met the short-call latency bars. Labels are reviewed/frozen and application-note vetting input is approved; accuracy and final model selection remain unmeasured. The approved baseline uses human safety review; the model adapter is optional and is not built. Authenticated tunnel/proxy, bounded timeout/concurrency/queue and fail-closed behavior remain required. Grade 9 is the contract; grade 10 is conditional stretch. See the [feasibility brief](docs/specs/local-model-feasibility-brief.md) and [working plan](docs/specs/mvp-ticket-plan-revised-draft.md). Conditional estimates and the increased freeze risk are in the measured report, not a claim that the whole plan fits.

## Local demo (five commands)

From the repository root of a fresh checkout, with Python3.11+ available as `python`, Node22.12+ (Node24 verified) and npm installed, run in PowerShell. No database or model installation is needed. The Windows Python launcher `py` is not required.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd ci --prefix frontend
npm.cmd run build --prefix frontend
.venv\Scripts\python.exe -m uvicorn vaeil.web:create_app --factory --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 and stop with Ctrl+C. **Demo only — don't enter real personal details.** The fixture is fictional and always anonymous; no registration, auth, admission or durable storage is exposed. FastAPI serves the built React assets and relative API routes on the same origin. A missing build returns a setup message; unknown API paths stay404. Rebuild and restart after frontend edits.

After setup, Python checks use `.venv\Scripts\python.exe scripts/check.py`. Frontend checks use `npm.cmd run typecheck --prefix frontend` and `npm.cmd test --prefix frontend`; local browser tests use installed Microsoft Edge, while CI installs Chromium. Browser tests launch/stop their own local server. The suite includes loopback HTTP/browser tests; it uses no live LLM or database. Windows CI runs the Python checks, typecheck, frontend build and browser tests.

## Repository layout

- `src/vaeil/domain/` — pure domain core: no frameworks, no database, no LLM SDK.
- `tests/` — the pytest suite.
- `docs/` — project logs and agent docs.

## Licence

See `LICENSE`.

T2 implements pair-scoped lifecycle, active-slot exclusion, monotonic trusted restoration and permanent Block exclusion. The current reduced schedule/human-review baseline is approved; the 7 November recovery proposal still has a 4.5-session capacity gap. See `docs/audit/t2-velocity.md` before T4. Model accuracy has not been measured; no live model is required by the approved human-review baseline.

T3 adds the local same-origin synthetic demo: health and anonymous Member endpoints, a real React rendering path, loading/error/retry states and HTTP/browser privacy checks. It is not the authenticated pre-Reveal product flow; Rule5 stays partial.
