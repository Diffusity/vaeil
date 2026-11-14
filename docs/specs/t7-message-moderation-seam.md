# T7 Message/moderated-delivery seam — proposed

**Awaiting Parth's interface approval.** Behavior derives from #7's approved7November human-review amendment. T6 merged as ba9212b. Technical choices below are proposals, not silently adopted product decisions. No tests/stubs/implementation in this step.

## Public seams

```python
# Pure domain; no framework/storage/network/real time/identity extraction.
assess_message(text: str, *, sender_id: str, conversation: Conversation,
               moderation: Verdict | ModerationFailure) -> MessageAssessment

# Application; actors come from T6 server sessions.
send_message(*, actor: SessionPrincipal, conversation_id: str,
             request_id: str, text: str) -> SenderMessageView
submit_for_review(*, actor: SessionPrincipal, message_id: str) -> SenderMessageView
decide_message(*, actor: SessionPrincipal, message_id: str,
               decision: MessageReviewDecision) -> None
read_conversation(*, actor: SessionPrincipal,
                  conversation_id: str) -> ConversationMessagesView

# Optional external port, injection only until separately approved real adapter.
moderate(text: str) -> Verdict
```

Assessment tests catch outcome/scanner/pair/Block policy, not durable or HTTP authority. Application tests use real repositories with injected Clock/moderator/IDs and catch roles, stale-state races, audit, rollback and duplicates. HTTP/browser tests catch cookie/Origin, payloads and UI states, not model accuracy/deployment readiness. Pure sender/Conversation inputs are trusted application values, never transport authority. No public create-Conversation or set-Reveal route; fixtures use isolated fictional state.

## Proposed types

- `ModerationFailure`: timeout, unreachable, busy, queue_full, malformed, unavailable. Typed technical reasons, never Approved. Runtime baseline returns unavailable without live inference. Optional wrapper accepts exact Verdict only; exceptions/unexpected output fail closed. Model receives only untrusted text, no identity/session/Conversation record.
- `MessageAssessment`: outcome Delivered/Escalated/Withheld, ordered scanner reasons, optional typed Withheld reason. Reasons only, no copied matched text/spans. Review-required is distinct from technical failures.
- `MessageRecord`: ID, Conversation ID, sender ID, canonical text, request key/digest, scanner reasons, outcome/reason, review state, created_at and optional delivered_at. Frozen/slotted, text hidden from repr/str, generic export/copy refused using existing private-record pattern. Text is not an identity wrapper; explicit persistence/transport maps need no new unwrap. One canonical body, no queue/audit body copies; safe errors never echo it.
- `MessageReviewDecision`: release/discard, human-only. States not_submitted/pending/released/discarded. Technical failure starts not_submitted; explicit submission makes pending. NeedsReview goes directly pending. Both stay Withheld until release; discard is terminal/undelivered. Human release records human provenance, never model approval.
- `SenderMessageView`: IDs, outcome, reason, review state, scanner reasons, retry_allowed, can_submit_for_review and timestamps, no echoed body. Delivered view: ID, sender ID, text, delivered_at, for participants only. `ConversationMessagesView`: delivered views plus only requesting sender's attempt receipts. Admin pending DTO: Message/Conversation/sender IDs, canonical text and reasons, no private identity. Queue stores IDs and joins canonical body only when authorized.

## Authority/outcome/transactions

Scan before optional moderation; retain all ordered flags. Baseline send -> technical Withheld/unavailable, no delivery. Explicit sender submission enables review, not delivery. In injected Approved tests: pre-Reveal flags Escalate, otherwise Deliver. NeedsReview -> review-required/pending. Human release scans again against fresh Conversation state; clean -> Delivered, pre-Reveal flags -> Escalated with queue/audit. Escalated queue references the Message; review acknowledgement must not deliver again. T9 owns its acknowledgement UI/decision handling.

Reload session role/admission and participant pair for every operation, even idempotent reads. Final transaction rechecks Block, pair and Reveal after any slow external call; no model call holds write lock. Atomically commit Message, queue state and audit. Existing typed message release/discard/escalation audit uses IDs/reasons only. Concurrent finalization allows one transition/audit. Block prevents sends/releases including queued-before-Block; Admin can discard. T11 owns public Block API. Revealed chat stays open until Block. Delivery time is taken from injected Clock on actual delivery; Withheld never qualifies for T8.

No arbitrary timeout numbers adopted. Baseline performs no inference; T12 supplies measured bounded calls/queue. Fake tests cover all failures. Reject stays unrepresentable; prompt-injection text cannot supply authority or clear flags. Demo failure switch is environment-only and rejected outside demo mode; baseline already visibly Withholds on unavailability.

## Exact comparison/request proposals — approval required

1. **Text:** nonempty str, valid UTF-8; NFKC then outer trim; maximum2000 normalized Unicode code points, no truncation. Refuse whitespace-only and control categories Cc/Cf/Cs except permit newline/tab for chat. This length/control policy is a new technical proposal, not an earlier settled requirement. Safe distinct errors precede storage/model.
2. **Same text:** SHA-256 canonical UTF-8, case-sensitive, punctuation retained; scope `(conversation_id, sender_id)`. Model-flagged digest cannot be resent in that Conversation even after release/discard. This is exact comparison, not semantic/paraphrase detection. Proposed extension: explicit manual-review submission reserves that digest too to prevent duplicate queues. Unsubmitted technical failures remain retryable; repeated submission of the same Message returns its current receipt.
3. **Request idempotency:** caller supplies opaque UUID request_id; unique `(sender_id, conversation_id, request_id)`. Same key/text returns current receipt with no second moderation/delivery/audit; same key/different canonical text -> safe409. Deliberate technical retry uses new key. Reload authority before returning an existing receipt. Digests are internal, never logged/audited/public.
4. **Provenance:** retain model versus human origin. Blocked pending content stays undelivered and can be discarded. Reveal/Block never clears same-text protection for that Conversation.

## Repository/HTTP/UI proposal

Extend UnitOfWork: add/get Message, get by request key, check review digest, transition Message, list delivered, list sender attempts, list pending/Escalated IDs. One SQL implementation/shared SQLite+Postgres contracts, database uniqueness and atomic transitions. Explicit mapping only; no new identity extraction.

POST `/api/conversations/{id}/messages` (request_id,text); GET same path; POST `/api/messages/{id}/review` (no text/actor); GET `/api/admin/messages`; POST `/api/admin/messages/{id}/decision` (release/discard). T6 cookies/same-origin CSRF, server-owned authority.400 validation,401 session,403 authority,404 absent within authorized scope,409 state/key/same-text conflict,503 storage. A stored Withheld attempt is a successful command with typed reason, not HTTP transport failure. Do not leak pending content through errors.

Minimal UI: authenticated reader/composer, checking disables duplicates, technical Withheld offers retry/submit-for-review, pending shows under review without retry; recipient sees delivered text only. T9 full console, H3 later presentation. No Matching UI/pair-create bypass.

## Tests/mutations after approval

- Assessment: all identifier categories/reasons; all outcome/reason combinations; malformed verdict/no Reject;0/1/2000/2001 normalized code points, UTF-8/control/allowed whitespace, independent normalization oracles.
- Repository/application: technical retry/manual submission; model review/no-resend; authorized release/discard; idempotency; pair isolation; Block/Reveal races; terminal decisions; unique digest; rollback/audit; actual delivery timestamp/Withheld exclusion. Both databases, injected Clock.
- HTTP/browser: role/Origin, safe errors/canaries, recipient cannot see pending text, checking/retry/under-review, exactly one audited release/delivery. Rule5 partial; no full six-rule completion claim.
- Mutations: auto-approve clean scan; clear reasons; deliver Withheld; omit key/digest; duplicate release; bypass role/pair/Block/recheck; use Member Reveal; count Withheld; timestamp submission not delivery; early commit; body copied to audit/queue; recipient pending leak; unauthorized unwrap. Run writers alone, restore, full checks/two-axis review, small PRs.

Approve the interfaces/types and four exact comparison/request proposals before red tests. Identifier detection stays reason-only; the moderation domain decides delivery.

## Capacity checkpoint after T6 merge

| Remaining work | Optimistic lead sessions |
| --- | --- |
| T7 Messages/moderation |3|
| T8 Reveal |2|
| T9 Admin console |1.5|
| T10 Matching |1.5|
| T11 Block/Report |1|
| T13 seed/evaluation build |1|
| Integration allowance |0.5|
| **Total** |**10.5**|

Roughly10slots remain at5/week to28November freeze: minimum0.5session gap,1.5if T7 takes4sessions. Review/rework adds risk; this is not measured human velocity. T6 review/merge is complete, so it is no longer a pending prerequisite. H1 was already outside the lead baseline and cannot be counted as new savings. Keep optional model/explanations/progress/Report UI/polish out; protect all six rules/Admin/Reveal/Report handling. No new features29November–4December; viva5December. Re-estimate after T7 first vertical cycle, using recorded active blocks plus the owner human ledger.
