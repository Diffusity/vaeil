# T11 Block and Report — approved seam

24 November 2026. Based on MVP #7 and the approved Plan B. T10 must land first. Parth approved this seam on 24 November 2026.

## First end-to-end slice

Two fictional Members already have a Conversation. Either Member Blocks it. Both see that chat is closed and cannot send, retry, or submit an attempt for review. A Block releases any active slot and the unordered pair remains excluded from future proposals. A completed Reveal is not reset. Either participant can still Report the Conversation via the API, and the Admin sees and resolves the Report in the existing console.

| Public seam | Proposed interface |
| --- | --- |
| Block | `SafetyApplication.block_conversation(*, actor, conversation_id)` and `POST /api/conversations/{id}/block` with an empty body. Recheck approved Member and pair authority. Reuse the existing pair transition and ordered repository transaction; commit Block and exactly one `conversation_blocked` event together. Either participant's repeat is idempotent. |
| Closed Conversation | Participants retain a closed-state shell so they can navigate back or Report. Proposal for review: stop returning chat bodies or attempts after Block, and show a clear closed state instead. Preserve Reveal and already-disclosed identity history in storage; do not add an identity disclosure to the closed shell. Outsiders get the same 404 as a missing Conversation. |
| Report | `SafetyApplication.submit_report(*, actor, conversation_id, reason)` and `POST /api/conversations/{id}/reports`. Proposed typed reason codes: `harassment`, `identity_pressure`, `scam`, `other`. No free text, attachments, or raw Message copy. Only a participant may Report; the server establishes the reporter and pair. Available before/after Reveal and after Block. One Report per reporter per Conversation; an identical retry returns the existing opaque receipt, a conflicting retry returns safe 409, and the other participant can Report independently. Report creation and `report_submitted` audit commit together. |
| Admin queue | `GET /api/admin/reports` for pending Reports and `POST /api/admin/reports/{id}/decision` for `approve` or `reject`. Only current Admin. Show opaque Report and Conversation references, typed reason, time and status; no private identity or copied chat bodies. Decision is terminal, hides the item from the open queue and appends the matching typed Admin event atomically. An identical retry is a no-op; conflicting repeat is safe 409. Decision records the disposition only; it does not implicitly Block or reverse any Reveal. |

Use the existing cookie, Origin, exact body and no-store helpers. Add a single confirmed **Block Conversation** action and closed state to the Conversation UI, plus the real Report queue to the Admin console. Report submission via API is the working scope; the Member submission UI stays optional.

## Acceptance to pin after approval

- Approved participant CRUD boundaries: unauthorized, outsider, forged identifiers and wrong Origin fail without disclosure. Matching refuses the Blocked pair even after slot release; a different eligible pair can still match.
- Block races Message delivery/release and Reveal completion under the same serialized transaction. Once Block has committed, there is no later delivery, release, or Reveal; when Reveal committed first, it remains recorded. Block and audit roll back together. Repeat actions never duplicate audit.
- Report still works after Block and after Reveal, with one per reporter, exact safe payload, and no private values/chat bodies in the queue or audit. Concurrent submissions and Admin decisions have one durable outcome; failed audit writes leave prior state intact. Real browser verifies closed state and Admin queue decisions, with stale-session guards.
- Run the same SQLite and PostgreSQL contract selection before and after mutations. Local/browser evidence is separate from the final deployed rehearsal. Rule 5 stays partial until the deployed pair checks are demonstrated.

Approval requested for the closed history behavior, Report reasons and one-per-reporter rule, and the no-automatic-action meaning of the Admin disposition. Previous allowance: **1 optimistic build session, 1–2 ordinary**. Protect the 28 November freeze and do not add the optional Report submission UI.
