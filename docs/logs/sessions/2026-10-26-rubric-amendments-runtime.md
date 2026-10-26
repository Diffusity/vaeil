# Rubric amendments, label review, runtime prerequisites

Working blocks (UTC):

| Start | End | Work |
| --- | --- | --- |
| 2026-10-26 04:33:00 | 2026-10-26 04:44:47 | Recovered rubric/spec; official runtime-control research; power preflight; amended 40 labels/category overlaps and hard negatives; exported synthetic review sheets; recorded Rule 3 clarification/vetting open question and drafted H7/T7. |
| 2026-10-26 05:50:59 | 2026-10-26 05:59:54 | Recovered download failure/power state, one bounded resume attempt, completed doc clarifications/development review exports and normal check (401 passed, Ruff/assumptions green). No model measurements or concurrent tests/inference. |

Runtime installer download began at 2026-10-26 04:45:52 UTC. The initial transfer reset after curl reported 17m09s elapsed, around 661 MiB received; not installed or verified. The next tool clock was 05:50:59: do not treat the gap as active effort. Runtime work has a conservative wall-clock deadline 06:45:52 UTC for its one-session/two-hour cap, including download/pulls; stop/report if incomplete. Resume transfer is bounded to ten minutes and must pass exact official SHA256 and Authenticode before installation. No other software/model/tunnel authorized.

Power is a real measurement blocker: Win32 GetSystemPowerStatus ACLineStatus=0, battery81% initially then73%, active Balanced, only Balanced listed; AC/DC sleep timers already zero. User was asked asynchronously to plug in/confirm High performance. Do not claim the user-stated power conditions were verified. Native Windows11 Home Single Language build26300, HP15s-eq2xxx, 33635885056 bytes RAM. No model metrics/digests/GPU support are inferred from hardware.

H7 is #16 under #7, ready-for-human and unassigned. Proposed two-reader allocation only; English/disputes Parth. Human review window is24 hours from actual distribution, not a claim that teammates were contacted or sheets returned. All forty candidate labels remain unfrozen. Every task has10 safe/10 review, seven hard negatives; review-category occurrences: threats2, sexual2, hate2, scams2, identity-fishing4, non-threat pressure2, injection2. Main CSVs16 English/24 non-English; separate development CSVs2 English/6 non-English; no real data. No accuracy or prompt tuning before approved review/commit-hash freeze. Later label objections use included/excluded metrics on the same outputs, without reruns.

Spec #7 updated with typed Withheld semantics and vetting open question. Applicant currently contains only wrapped DOB; no applicant ID/text field. Automated Delivered/Escalated requires approval; Admin release is the explicitly authorized human moderation transition. Technical Withheld permits retry; model-Withheld is under review/no same-text resend, with audited release/discard. T7 remains an unpublished acceptance-test draft, not implementation. Existing vocabulary synchronized; TESTING401/Rule5partial unchanged, statistical warning added. No other tickets published or people assigned.

Named Cloudflare is out (no domain). ngrok credit/hourly price still unconfirmed; T12 must budget rehearsal/viva-only hours plus margin and propose Quick Tunnel or local-demo fallback if needed. No tunnel/account provisioned. T7/T12/T13 measured estimates and model recommendation remain gated on actual evidence, not guessed numbers.
