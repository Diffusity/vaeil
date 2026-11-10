# T4 code/deployment evidence — incomplete live acceptance

Ticket #11, approved readiness interface and free-only provisioning10November. No repeat approval is needed. Dockerfile/Render blueprint and recovery note are prepared, not proof a service exists. Browser/session control fails to initialize with `failed to write kernel assets: The system cannot find the path specified (os error3)` on both supported routes. No configured Render/Neon API credentials were found (presence check only, no values printed). Parth is restoring browser access. Live URL, Neon connection, actual plan/billing eligibility, cold starts, memory and collaborator access remain **unverified**. Do not close #11 or raise milestone progress to4/12 from code-only work.

## Red/green and review

| Cycle | Red evidence | Green evidence |
| --- | --- | --- |
| HTTP readiness | Missing adapter, then404instead of200/503 |2casesgreen,1199bbd |
| Isolated probe/cache | Worker success still returnsFalse |7casesgreen,67dc2cc; other failure cases already safe underFalse stub, no artificial red claimed |
| TLS roots/CLI cleanup |3casesfail on missing explicit trust root |12casesgreen,79089fe |
| Cache/concurrency regression | Already supported by previous implementation |14green; no fabricated red,beb8ded |
| Container asset path + real Windows worker | Configured directory ignored; actual PID21108 differed from launcher28200 |15green,ac637d8 |
| Windows package isolation | `-S` missing from isolated bootstrap |15green,8c79546 |

Full local check before last bootstrap-only correction: **478 Python tests**, Ruff/assumptions green; frontend strict TypeScript/build and four browser cases green. Targeted15readiness cases green after final correction; final CI must repeat full check and container smoke. Existing T1/T2/T3 tests unchanged. Rule5partial,3/6domain0/6complete-ruleE2E. No new private unwrap or domain framework dependency.

Readiness is a cached diagnostic, not data persistence:3-second worker timeout **after process creation**, plus OS spawn/kill overhead; no false claim of a hard real-time HTTP SLA. Tests allow6seconds total for the synthetic stalled worker and verify actual interpreter PID equals the reaped child. Windows uses direct base interpreter `-I -S` and explicitly adds the pinned venv site, avoiding a surviving venv redirector and global package precedence. Linux executes the installed interpreter directly. Parent suppresses worker output/errors and keeps DSN in a minimal environment, not argv; worker uses certifi trust roots, verify-full,2s connect/statement limits, read-only SELECT1 and closes resources. Cache30seconds (including unavailable), one non-queued probe; no continuous warm-up job. Public abuse can still consume free service capacity; it is not a production availability guarantee.

## Selected mutations

Each final source mutation is run alone via `pytest -q tests/test_readiness.py`, then exact bytes restored before further verification. Five behavioral kills: force200on DB failure; accept nonzero worker exit; disable cache hits; downgrade TLS verification; accept wrong SELECT result. Final restoration hashes are recorded in the session log after the run. No collection/import error is counted as a kill. Production code mutations are never run concurrently with other tests/source writers.

## Live acceptance checklist (all pending)

- Verify Parth-owned Render Free/Neon Free and $0 controls, no payment-method overage fallback. No Render Postgres or disk/paid addon.
- Build reviewed image; bind PORT; health200, ready200withactualNeon, exactanonymousendpoint and browser assets. Use scripts/smoke_deployment.py once, no keep-alive loop.
- Disconnect/misconfigure DB intentionally through private config: ready503, health/demo usable; restore, wait cache30s and check recovery.
- Observe actual Render15-minute idle sleep/pre-React platform wake and Neon idle wake; record timings and platform errors, not inferred local behavior.
- Record actual free instance RAM/quota, memory and public URL. CI limits512MiB/0.1CPU are only a container model, not vendor-host measurements.
- Confirm collaborator limits and identities before invitations; credentials in password manager, never logs/repo/chat. Recovery note docs/deployment/recovery.md.

No Docker executable is installed locally. Container build/non-root/asset/outage smoke is delegated to the ordinary Linux CI job, not claimed before its run. T4 remains partial even if that job passes.
