# PR #14 merge and benchmark review gate

## Working blocks (UTC)

| Start | End | Work |
| --- | --- | --- |
| 2026-10-25 13:40:07 | 2026-10-25 13:42:26 | Recovered PR/issue, independent Standards/Spec review, full check: 401 passed, Ruff/assumptions green. Also recorded in the T1 block log. |
| 2026-10-25 13:42:26 | 2026-10-25 13:44:48 | Fixed two stale-doc findings, committed/pushed 6066868, verified final-head Windows success, merged PR #14 with a merge commit. |
| 2026-10-26 04:09:37 | 2026-10-26 04:13:58 | Recovered after overnight tool gap, added T5/T6 explicit unwrap work/allowances and updated existing issues #12/#13; reconciled plan/status evidence. |
| 2026-10-26 04:13:58 | 2026-10-26 04:15:09 | Validated 40 unique labels and exact scanner flags without a model, corrected schedule arithmetic and wrote merge/benchmark-gate handoff. |

Merge: `4f9ca807f9ca5a6cc4fa31a32bf413cd9f865864`, two parents `75d4ced` and `6066868`. PR #14 MERGED; #8 CLOSED. Windows CI completed successfully at 2026-10-25 13:44:07 UTC on final head6066868. No squash/rebase or branch deletion; cited implementation/test commits survive. Review result: Standards two stale documentation findings fixed, Spec zero findings; no source/test changes. README/TESTING now record merged status, 401 tests and Rule 5 partial (3/6 domain, 0/6 E2E).

The tool clock crossed an overnight gap before returning the next timestamp. Do not treat 13:44:48–04:09:37 as active work. Label/rubric drafting around that interruption lacks a verified exact duration. All effort before time tracking started remains unverified; do not certify total T1 sessions or count the gap as zero-effort proof.

Latest benchmark authorization and acceptance bars are recorded in the feasibility note and proposed rubric. Forty synthetic cases are proposed, not approved/frozen. Labels, prompt and settings must be approved and hashed before any model run. No runtime/model installed, tunnel provisioned or benchmark measured. The next dedicated block is capped conservatively at two hours, with cleanup and partial reporting on overrun. No T2/T3 start or later ticket publication until benchmark report/velocity update under the latest instruction.

T5/T6 allowance: +0.5 session each for explicit mapping/login extraction, exact AST sites and canaries; existing three-site test is unchanged. Published existing tickets updated, no new tickets or assignments. Current remaining forecast is high-risk; T7/T12/T13 estimates await measurements. Proposed labels/rubric live in docs/research/local-model-labels.json and local-model-benchmark-rubric.md. The shared scanner confirms exactly M06 phone, M07 email, M08 handle, M20 phone; all other cases are clean. Ten safe and ten review-required cases per task, forty unique IDs.
