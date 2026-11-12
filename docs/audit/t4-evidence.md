# T4 code/deployment evidence — incomplete live acceptance

**Current update, 12 November:** owner confirms the Neon password was changed. Public readiness returned200 in8.034seconds and the complete healthy deployment smoke passed afterward. Earlier rotation-pending statements below are historical. Actual host spin-down/platform-loader evidence remains outstanding; live RAM graphs are unavailable on Free and no upgrade is planned. PR21 remains unmerged pending the acceptance/review gate. See docs/logs/sessions/2026-11-12-deployment-gates.md.

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

## Final local verification/access status

Final source (including-I-S) passed full478Python/4browser/strict TypeScript/build again; local real-server smoke verified HTML/staticassets,anonymousAPI,health andready503duringintentionalbadDBconfig, then stopped its exact owned process tree. No listeners8000/8765/8768 remained. This is not image/Neon/Render evidence. Standards/Spec final rechecks report no residual findings after graded-doc fixes.

Last successful remote branch push3ca3b69a146ddbca522b88dafc6e424f6d0d54c5 includes implementation fixes and imageCIdefinition. Local510076c5971bd6fbcbb6645e6b5f52eca536b53f adds final DESIGN wording/citation fixes; later handoff docs are also local. Push retry failedconnectionresetthenDNSresolution forgithub.com; connected GitHub create-PR fallbackreturned403Resource notaccessiblebyintegration. **No draftPRwascreated; no containerCIrun or imagebuild is claimed.** Restore GitHub access, pushremainingcommits, open refs-onlydraftPR and runfullWindows/containerCI, then approvedaccountsideprovisioning/livechecks. No repeat provisioningapprovalneeded.

10 November deployment resumption: PR #21 created at450f3bd. First Windows CI green; Linux image build succeeded but startup smoke failed with ConnectionResetError before the server accepted connections. New CLI regression reproduces that exact failure, then passes after adding ConnectionError to the existing bounded startup retry. Full local479Python green (55.84s); no frozen domain tests changed. Browser access restored; cloud setup underway, not yet a live deployment.

11November: approved10s worker budget red3!=10 then green479Python20.46s. Actual-child cleanup keeps injected3s/<6s/PIDassertions; no safety check removed. Finalcode4ce56bd Windows/container/securityCIgreen run43015627583, manuallydeployed. Publicready returned200 ready in5.504s; fullpublicsmoke thenPASSHTML/assets/anonymouspayload/health/readiness. This supports prior3sbudget being too short; no precise worker-phase timings claimed. No diagnostic logging needed. Live coldstart/outage/RAM/continuity acceptance stillpending, issue11open. No model/tunnel or persistence added.

11November follow-up: docs-only0408bf9 CI uncovered a smokeclient deadline mismatch: urlopen5s expired before10sworker returned. Regressiontest at externalHTTPboundary raisesTimeoutError for<=10s; redobserved, green with15sclientbound. Full480Python21.22s/Ruff/assumptionsgreen. No server/domainlimit changed; finalimageCI rerun follows.

## Live acceptance attempt — 11 November

| Check | Observed result | Limit |
| --- | --- | --- |
| Public healthy smoke | PASS on7fd4ad0 after restoration: HTML/assets, exact anonymous payload, health200, ready200 | Fictional endpoint only; no persistence claim |
| Idle interval | No agent public requests from17:26:59 until17:43; browser profile available after7.811s including tool overhead; subsequent ready2004.958s | Same host instance remained in logs; neither actual Render sleep nor platform loader captured. This is an idle-return check, not proof of spin-down/wake. |
| Live DB outage | Reversible loopback-only connection fixture; smoke with expected-unavailable passed: ready503 while health/demo/assets200 | Simulated connection failure, no database data changed |
| Recovery | First restore did not persist; corrected edit was verified saved, manually redeployed; healthy full smoke PASS | Require save completion before deployment, not just clicking Save |
| RAM/quota | Constrained CI512MiB/0.1CPU smoke passed; earlier memory sample34.16MiB. Live demo operates on Free | Free dashboard hides live RAM/CPU graphs behind paid upgrade; no paid plan added and no live peak claimed |
| Continuity | Owner-led configuration restore/redeploy succeeded; one-page recovery note exists | User explicitly deferred collaborators and password-manager storage; owner-account access required |

Browser accessibility unexpectedly returned a private URL even after visually masking it. No URL is recorded here or in Git. User was asked to rotate the database password and replace the Render secret; rotation confirmation pending. Secret fields will not be read again. This is a tool-output incident, not evidence of a public app response leak.

T4 remains open: actual host spin-down/platform-loading capture and credential-rotation confirmation remain gates. Do not close#11 or claim all acceptance is green. The final code review assesses these gaps separately from code correctness.
