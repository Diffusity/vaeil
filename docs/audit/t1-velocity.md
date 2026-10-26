# T1 velocity review — 25 October 2026

## Measured work and original estimate

Original estimate: **3-4 sessions**, using the plan's 2-3 focused hours/session. Timed T1 work blocks through PR publication at 11:38:31 UTC: **2h 43m 36s**, equivalent to **0.91-1.36 sessions**. The next feasibility note is recorded separately in block 15. These are agent-led timings, not a substitute for Parth's human review-session ledger.

Audit: budget **0.5 session**, actual active duration unverified because its clock observations span an overnight gap. Initial T1 test drafting/recovery before timestamp tracking is also unmeasured. Therefore **total actual T1 sessions cannot honestly be certified yet**. Measured portion is inside the 3-4 estimate; do not claim all unmeasured work took zero or release reserved slots as “savings”. Reconcile with Parth's own session notes.

## What cost more than the first seam implied

- 98-case audit and extra strict boundaries/precedence; preserving every merged legacy case.
- Whole-record redaction did not prevent native scalar JSON/format leaks. The approved scope refinement needed an extra test-only commit, two opaque-value cycles and exact AST extraction policy.
- Windows CRLF handling in the mutation runner required correction/restart. The completed evidence is 74/74 kills, restored bytes, then 401 green and AST 4 green; no test loosened after its approved commit.
- Review identified a real contract conflict; the user decision interval is excluded from timed work, rather than billed as active coding.

## Forecast against the confirmed freeze

Inputs remain fixed: **5 build sessions/week**, viva **5 December**, feature freeze **28 November**, **29 November-4 December rehearsal/fixes only**. Plan B remains the working scope, with no explanation text, conversational Onboarding, re-ranking, Icebreakers, progress UI, Report submission UI, polish or second adapter. Never cut six rules, Admin, Reveal or Report handling.

Remaining lead work after T1, excluding local-model T12: **19-31 sessions**, plus **0.5-session feasibility** and T12 measured estimate (still unknown). This is the previous 22-35 non-T12 range minus T1's original 3-4 reservation, not a fabricated model-adapter estimate. One to two T13 rehearsal sessions occur after feature freeze; optimistic build work is about **18.5 sessions plus T12** after T1.

With the original T1 reservation still held against the approximately 25-slot build window, only **2.5-3.5 slots** remain for T12 and unexpected work at the optimistic bound. The upper range does not fit. The measured portion of T1 is **not evidence that we are behind its estimate**, but the entire plan remains tight/high-risk; a low-effort local adapter and accepted teammate work are necessary. Do not extrapolate domain-test speed to SQL contracts, deployment or laptop availability.

Next: start the half-session local-model feasibility note; T2/local T3 can overlap after T1 lands and this review. Re-estimate again after T2, before T4. If T2 exceeds two sessions or local-model setup/adapter/rehearsal needs more than the remaining bound, flag the freeze forecast immediately and propose capacity/deadline adjustment; mandatory safety scope stays. Later tickets remain unpublished until the review and feasibility findings make their estimates real. No teammate assignment is made here.

PR #14 is open against master, not merged. Windows checks passed at head9a02f31. Local-model research has started in docs/research/local-model-feasibility-2026-10-25.md; actual runtime benchmarks and the accuracy-bar/model decision remain pending.

## Post-merge correction — 26 October

PR #14 merged at 2026-10-25 13:44:48 UTC with merge commit `4f9ca80`, after Windows CI passed on final head `6066868`; #8 is closed. Two pre-merge documentation findings were fixed; code and tests did not change. The quoted paragraph above is historical, not current status. Effort before tracking remains unverified; the overnight tool gap is excluded.

T5/T6 now explicitly budget the persistence/login extraction boundaries at +0.5 session each (planning allowance, not measured effort). Remaining non-T12 work is therefore 20-32 sessions. Holding the original T1 reservation leaves roughly 1.5-2.5 optimistic slots for T12/contingency before additional benchmark effort; the upper bound does not fit. This is increased schedule risk, not measured evidence that T1 exceeded its estimate. The authorized benchmark is capped at one session; labels require approval first. T7/T12/T13 cannot yet be honestly re-estimated from measurements. T2/T3 and later publication now follow the benchmark report and velocity update under the latest instruction.
