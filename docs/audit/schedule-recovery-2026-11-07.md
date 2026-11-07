# Freeze recovery — approved 7 November

Five sessions/week; feature freeze 28 November, viva 5 December; 29 November–4 December rehearsal/fixes only. As of 7 November there are **21 days / 7 × 5 = 15 build slots** through 27 November. Do not assume a sixteenth session on freeze day or unused October slots carried forward. Sessions are 2–3 focused hours. No T2/T3 implementation starts from this proposal.

## Ledger reconciliation

Verified T1 timed portion: 2h43m36s = 0.91–1.36 sessions; pretracking drafting/audit effort is unverified, not zero. Accepted CPU/Vulkan measurement windows total about 66 minutes; 27 October setup through final stop was 1h44m20s elapsed, not certified active effort. The earlier failed runtime attempt and post-measurement reporting/review are separate recorded blocks; gaps/waiting must not be counted as active work. Human review/build-session ledger has not been supplied. Thus total actual sessions cannot be certified or used to claim a measured product velocity. T2 has not landed; there is no honest measured-velocity estimate for persistence, deployment or moderation yet.

The previous 27.5–29.5 versus 25 forecast included past reservations. It must not be compared directly with today's remaining capacity. Remaining non-T12 estimate was 21–33 sessions; remove one post-freeze rehearsal slot: **20–32 build sessions versus 15**, gap **5–17**, before new application-note validation or recovery planning. Optional T12 (2–3) is excluded here, not subtracted twice. Plan B options were already excluded and save zero again.

## Proposed optimistic re-scope (not measured promises)

| Ticket | Previous remaining sessions | Proposed build sessions | Constraint preserved |
| --- | --- | --- | --- |
| T2 Conversation/isolation | 1–2 | 1 | Full lifecycle, slot and pair isolation |
| T3 local skeleton | 1–2 | 1 | Health plus real identity endpoint, five-command setup |
| T4 deployed skeleton | 2–3 | 1.5 | Same minimal endpoints, cold start, continuity/recovery |
| T5 storage/audit | 2.5–4.5 | 2.5 | Both SQL backends, concurrency, rollback, append-only audit, unwrap boundary |
| T6 auth/admission | 2.5–3.5 | 3 | Includes new note validation, model-input exclusion and privacy tests |
| T7 moderation | 3–4 | 3 | Under-review/no-resend, explicit human release, technical failures |
| T8 Reveal | 2–3 | 2 | Every threshold/consent/isolation rule, minimal ceremony |
| T9 Admin | 2–3 | 1.5 | Plain shared queue table/actions; all queues/authorization/audit remain |
| T10 Matching | 2–3 | 1.5 | Deterministic score, exclusions, bilateral acceptance/races |
| T11 Block/Report | 1–2 | 1 | API, queue, audit; no submission UI |
| T12 local model | 2–3 conditional | 0 core | Optional; no accuracy result means no safety claim |
| T13 seed/evaluation | 2–3 incl rehearsal | 1 build | Plus 1 rehearsal session after freeze; six-rule deployed evidence |
| Recovery/approval integration allowance | not separately estimated | 0.5 | Docs, new contract and revised plan integration |
| **Total before freeze** | | **19.5** | **19.5 − 15 = 4.5 sessions short** |

Cuts ordered by lowest cost: leave already-dropped options out (zero new saving); defer T12 (2–3 against a plan that still includes it, zero against the non-T12 baseline above); cap T4 to health + one real endpoint (0.5 optimistic); reuse a plain Admin queue UI (0.5); narrow Matching presentation/batch controls while keeping all matching policy (0.5). These three proposed reductions save 1.5 against the 20-session optimistic baseline, but the new note adds 0.5 and recovery adds 0.5: 20 − 1.5 + 0.5 + 0.5 = 19.5.

Move H1–H3 React implementation to teammates with fixed API contracts and Parth review; this prevents lead work expanding beyond the table. Their 4–5 estimated sessions are already outside the lead baseline, so do not claim them as new savings. H4 fixtures/H5 scripts/H6 citations can reduce workload, but acceptance/integration review remains; no unconfirmed hours are credited.

**Core does not honestly fit five sessions/week from today on present evidence.** Recommend these re-scopes plus **at least 4.5 additional lead-equivalent build sessions (9–13.5 hours)** over the three weeks, before contingency. If that capacity is unavailable, required behavior cannot be promised by 28 November. Do not silently cut a rule, Admin, Reveal, Report handling or audit. Need Parth's completed-session ledger and teammate available hours/week (including who can implement H1–H3); use those to replace reservations, not invented velocity. No assignments made. Re-estimate after T2 before T4.

## Rules-first baseline triggered by 1 November deadline

Accuracy was not complete/reported by 1 November. The baseline therefore uses deterministic validation and **human safety decisions**. A deterministic clean result alone cannot automatically deliver/admit under the existing fail-closed contract. This proposal does not invent an automatic rules-only safety classifier or silently relax Rule 3.

| Rule | Baseline observable path |
| --- | --- |
| 1 | Invite-only admission; invalid/reused codes refused atomically |
| 2 | Valid application note goes to NeedsReview without a validated model; Admin approves/rejects, audited; no automatic rejection |
| 3 | Messages enter model-unavailable technical Withheld with retry; an explicit submit-for-Admin-review path is proposed so the Admin can release/discard with audit. Human-reviewed release is not labelled model-approved automatic Delivered; pre-Reveal identifier flags still require escalation/queue/audit. Never deliver unchecked text. Model-flagged text, if optional inference is used, stays under review/no same-text resend. |
| 4 | Delivered human-released/Escalated messages count toward unchanged 20/5/72-hour mutual Reveal; Withheld does not |
| 5 | Same projection, note/About scanner/self-name checks, private-value boundary and pair-specific Reveal |
| 6 | Same 18+ check before Invite consumption |

The explicit manual-review submission route is a **proposal needing approval**, not existing behavior: an unavailable model currently creates technical Withheld, not a model-review queue item. A live fake Approved adapter would demonstrate plumbing, not satisfy a real safety decision. Optional local inference can only tighten a deterministic/human baseline; approve its exact policy separately after evidence. Product AI claims and evaluation must disclose when the demo is human-reviewed. No model run before GO, no tunnel provisioning.

## Approval recorded

Parth: “i approve of the reduced schedule and the human - review baseline”. The proposal, including manual message submission/release, is approved; prospective language above describes the proposal as presented. T2/T3 may start through the TDD seam gate. Capacity gap is a retained risk, not an extra-hours commitment or proof it fits. No model run before exact GO.
