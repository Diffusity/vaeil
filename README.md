# Vaeil

Values-based matching with AI-assisted safety for students and young professionals (18–28). Vaeil runs one loop: invite → vetting → onboarding → curated match → anonymous chat → consensual Reveal.

This repository is the IT643 course project. The design and vocabulary live in [DESIGN.md](DESIGN.md), [UBIQUITOUS_LANGUAGE.md](UBIQUITOUS_LANGUAGE.md), and [TESTING.md](TESTING.md).

**Demo only — do not enter real personal details.** The T6 registration form carries the same notice. Keep this notice until a consent and deletion plan exists; Render and Neon store app data. Seed personas are fictional. Local-model outside-user stretch requires uptime and consent planning.

**Live fictional demo:** [vaeil-demo.onrender.com](https://vaeil-demo.onrender.com). Healthy/outage/recovery smoke passed on 11 November. The owner confirmed password rotation on 12 November, and healthy public smoke passed again. Actual host spin-down/platform-loader capture remains pending; live RAM graphs are unavailable on Free.

## Status

Slices 1 and 2 are merged into `master`: single-use Invite redemption behind an 18+ age gate, reject-free fail-closed Vetting, heuristic identifier scanning, and normalized in-memory Pseudonym claims. The retrospective tooling is also merged, including Windows CI. The current suite has 608 passing Python tests (586 product/domain/application/transport/storage/boundary and 22 tooling); 79 PostgreSQL variants are explicitly skipped locally and run in disposable-database CI, plus six browser tests; T1 merged with 401, and the earlier baseline was 122. The five benchmark cases guard the client; T2 adds 46 Conversation-domain cases without marking another rule done.

T1 merged in [PR #14](https://github.com/Diffusity/vaeil/pull/14), merge commit `4f9ca80`, with **401 passing tests**. It implements the Member/Values Profile pure view, shared self-name checks, ordered profile validation, opaque private scalars and pair-projection isolation. **Rule 5 remains partial**: T2 adds in-memory Conversation lifecycle/state authority; T6 implements admission/session and own-profile HTTP access; Match/Conversation display and moderated delivery remain future work. T5 implements the storage seam. The real local-model adapter is not built. T1 tests cover constructor-friendly wrappers, safe diagnostics/export and an exact approved unwrap allowlist (T5 adds the explicit persistence mapper); explicit authorized JSON remains unchanged. Spec: [#7](https://github.com/Diffusity/vaeil/issues/7). T1-T6 are published; later ticket estimates wait for the benchmark-informed velocity review.

## Remaining schedule (confirmed dates/capacity; estimates under review)

As of14November,14calendar build days remain through27November: about10lead sessions at5/week. The approved T6 planning allowance makes the pre-T6 remaining plan14sessions including integration, about4sessions over these10slots. T6 implementation is now awaiting review; after it merges the conditional remaining T7–T11/T13 estimate is10sessions plus0.5integration, about0.5sessions over available slots before outstanding T6 review/rework. These are planning scenarios, not verified human velocity. Extra teammate capacity is pledged, not yet assigned or verified; do not count already-excluded UI work twice. The T6 seam/implementation hold was lifted on14November; final feature PR review is pending. The28November freeze and29November–4December rehearsal-only period remain unchanged.

Confirmed viva: December 5, 2026, with five build sessions/week. Effort allocations depend on measured velocity. Hosting budget is $0; deployment is Render Free plus Neon Free PostgreSQL, with SQLite the default local run. Free-only provisioning was approved and the fictional demo is live.

The table below is the historical October allocation, superseded for current estimates by the [14 November velocity forecast](docs/audit/t5-velocity-2026-11-14.md). It is not a commitment or a claim that past planned work has landed. T3 and T4 are merged; T4 has accepted operational limits. T5 storage and isolated Neon restart survival are verified. Current forecast is below.

| Week | Historical proposed focus |
| --- | --- |
| Oct 26-Nov 1 | Combined identity/profile/Pseudonym self-name work, Conversation isolation and local skeleton; review velocity after T1, overlap Conversation/local skeleton, review again after T2 before deployment |
| Nov 2-8 | Early free deployment; one shared SQLite/Postgres repository, shared contract suite, persistence and audit foundation |
| Nov 9-15 | Auth/profile APIs; Messages/fake moderation and timeout/busy paths; teammate profile/chat pages after APIs merge |
| Nov 16-22 | Reveal and Admin console; deployed six-rule checkpoint with synthetic fixtures/current adapter |
| Nov 23-29 | Matching, Block/Report and seed integration; feature freeze Nov 28. Local-model integration is optional/deferred under the approved human-review baseline, not a required November milestone |
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

Open http://127.0.0.1:8000 and stop with Ctrl+C. **Demo only — don't enter real personal details.** The fixed demo profile remains fictional and anonymous. T6 adds registration/session and own-profile APIs using default local SQLite; normal runtime never seeds the browser-test Invite. Admission remains human-review-first. Admin seeding requires VAEIL_ADMIN_EMAIL and VAEIL_ADMIN_PASSWORD together in the process environment (no defaults); Invite issuance UI remains T9. Use fictional details only. FastAPI serves the built React assets and relative API routes on the same origin. A missing build returns a setup message; unknown API paths stay404. Rebuild and restart after frontend edits.

After setup, Python checks use `.venv\Scripts\python.exe scripts/check.py`. Frontend checks use `npm.cmd run typecheck --prefix frontend` and `npm.cmd test --prefix frontend`; local browser tests use installed Microsoft Edge, while CI installs Chromium. Browser tests launch/stop their own local server. The suite includes loopback HTTP/browser tests; it uses no live LLM or production database; browser tests own a temporary SQLite fixture. Windows CI runs the Python checks, typecheck, frontend build and browser tests.

## Repository layout

- `src/vaeil/domain/` — pure domain core: no frameworks, no database, no LLM SDK.
- `tests/` — the pytest suite.
- `docs/` — project logs and agent docs.

## Licence

See `LICENSE`.

T2 implements pair-scoped lifecycle, active-slot exclusion, monotonic trusted restoration and permanent Block exclusion. The current reduced schedule/human-review baseline is approved; the 7 November recovery proposal still has a 4.5-session capacity gap. See `docs/audit/t2-velocity.md` before T4. Model accuracy has not been measured; no live model is required by the approved human-review baseline.

T3 adds the local same-origin synthetic demo: health and anonymous Member endpoints, a real React rendering path, loading/error/retry states and HTTP/browser privacy checks. It is not the authenticated pre-Reveal product flow; Rule5 stays partial.

## T5 repository status

[PR #22](https://github.com/Diffusity/vaeil/pull/22) adds one SQLAlchemy Core implementation for SQLite/PostgreSQL, atomic normalized-Pseudonym ownership, Conversation state storage, rollback/append-only audit and opaque server-session records. T6 implements auth/admission and their audit emission; Message/Reveal/Report business-event wiring remains future work. Local repository callers default to `sqlite:///vaeil.sqlite`; the existing five-command run needs no database install. The fixed anonymous endpoint remains independent of product storage; T6 auth/profile operations use repositories. Contract CI uses disposable PostgreSQL, never the deployment database. An isolated fictional Neon fixture survived a Render restart on14November; T6 product API persistence is locally/CI tested, not yet deployed. Rule 5 remains partial.
T4 merged in PR #21 (d16c32f), with disclosed operational limitations accepted on 14 November: `/api/ready` reports200/503 independently of health and caches the bounded read-only DB probe for30seconds. With no DATABASE_URL locally it returns503 while the demo works. The five local commands are unchanged. The fictional Render/Neon deployment and live healthy/outage/recovery smoke are verified; recovery is in `docs/deployment/recovery.md`. Password rotation is owner-confirmed and public readiness passed afterward. Actual host spin-down/platform loader remains unverified; live RAM graphs require paid compute, which is outside scope. #11 stays open for the outstanding operational evidence and future registration notice.






## T6 review status

The approved implementation includes note-only Vetting, human admission review,24-hour server sessions, scrypt passwords, strict same-origin mutation checks, private drafts/complete-profile APIs and minimal registration/sign-in UI. Passwords are12–128Unicode code points without silent normalization. Never put passwords, session tokens or connection URLs in commands/URLs/logs. Configure Secure cookies for HTTPS (`VAEIL_SECURE_COOKIES=1` in the deployment environment); same-origin responses need no CORS exception. No real-model selector or automatic clean-text admission exists. Matching, chat, Reveal ceremony, Admin console and Block/Report are later slices. Rule5 remains partial. The live deployment still runs the earlier reviewed T4 runtime; no T6 deployment is claimed.
