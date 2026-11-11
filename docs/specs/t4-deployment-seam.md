# T4 implementation seam — prepared9November, approved10November

Canonical ticket #11: Early zero-cost deployed skeleton and cold-start checks. T3 merged f47d768; second velocity review exists. No resource created, purchase, account access, credential collection or provisioning performed. Dockerfile/render.yaml are reviewable proposals, not deployed evidence. Local Docker availability/build verification remains to be established before claiming image success.

## Proposed new test seam — confirm before tests

Keep `create_app()`, `/api/health`, `/api/demo/member` and local five-command path unchanged. Add **GET `/api/ready`**:200 `{"status":"ready"}` only after bounded PostgreSQL `SELECT 1`;503 `{"status":"unavailable"}` on absent configuration, connection error or timeout. Health stays200 when the database is off. Neither endpoint exposes DSN, credentials, exception messages or private values. No writes/schema/persistence claim.

Expose an adapter function `check_database_ready() -> bool` as a FastAPI dependency so HTTP tests substitute true/false at that external seam; the real adapter takes DATABASE_URL from environment and uses TLS and a fixed10-second worker budget (approved11November), with unchanged2-second driver connect and statement timeouts. The implementation must verify driver bounds and resource cleanup rather than assume a socket timeout bounds every operation. No DB install needed locally; readiness may be503 while the synthetic demo/health stays usable. Cache or restrict repeated readiness probes so public traffic cannot unnecessarily burn Neon quota; exact implementation follows the approved seam, without changing the response contract.

Red tests: ready/unavailable matrix, absent config, timeouts/malformed config/connection errors, no diagnostic secret leakage, health/demo unaffected by outage, cold-start UI still loading/retry. Real Neon wake probe is later live evidence after provisioning approval, not substituted by fake tests. No new unwrap site or domain dependency.

## Concrete deployment proposal

One Render Free Docker web service, building React with Node24 and running Python3.11 as non-root; bind Render PORT, default10000. Health path `/api/health`. Separate manual readiness smoke at `/api/ready`, so a sleeping/offline DB does not make Render restart an otherwise usable synthetic app. `DATABASE_URL` is a secret supplied in Render, never Git. No persistent Render disk, Render Postgres, paid plan, automatic upgrade or continuous keep-awake pings. Neon Free project in Parth's account, credentials in password manager.

Stages for human account work, after explicit free-only provisioning approval: (1) confirm Render/Neon free-plan eligibility and billing caps/no-card behavior, (2) create Neon project and obtain TLS connection string privately, (3) authorize repository and create Render Free service from reviewed deployment revision, set DATABASE_URL privately, (4) verify public origin/health/ready/fictional view then real sleep/wake and quota/RAM, (5) record service/project identifiers and continuity access without secrets. Named teammates/collaborator invites require actual identities; none invented. No tunnel/model needed in T4.

The deployment instruction names the implementation task, but #11 retains a separate explicit provisioning gate. New public readiness seam is not in T3's approved interfaces; TDD skill requires its confirmation before new tests. No product readiness code/stubs/tests added during preparation.

## Implementation status — 10 November

Parth explicitly approved this readiness seam and free-only provisioning. Readiness code/tests now exist; the earlier preparation/gate paragraphs are historical. The3-second worker deadline begins after OS process creation, with spawn/kill overhead separately acknowledged; no real-time HTTP SLA is promised. Database work remainsread-onlyandno data persistence is inferred. Both browser-controlroutes failkernelassetsinitialization; userwillrestoreaccess, so no cloudresources/livechecks yet. T4remainsincomplete pendingimageCIandliveevidence.

## 11 November diagnostic amendment
User approved a bounded10-second worker deadline after direct-URL redeployment still produced ready503 in3.411s. SQL/connecttimeouts remain2s, cache30s, one worker/no queue. Production timeout regression red3!=10 then green; real-child cleanup test injects3s and retains its original<6s bound/PID checks, so cleanup coverage is not loosened. Browser restored and fictional site deployed; prior access-blocked paragraphs are historical. Healthy database and cold-start evidence still pending.

