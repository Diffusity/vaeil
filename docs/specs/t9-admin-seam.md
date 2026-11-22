# T9 Admin console seam

Drafted 18 November 2026. Approved by Parth on 22 November 2026. Based on MVP issue #7, the approved human-review baseline, T6 admission, T7 delivery and merged T8 Reveal.

## First end-to-end slice

An Admin signs in, issues an Invite, and copies the code from the issuance response. A fictional Applicant uses it through ordinary registration. The Applicant enters NeedsReview. The Admin reviews the application note and approves or rejects it. The existing audit trail records the decision. The Invite can only be redeemed once.

## Application and HTTP interfaces

| Action | Proposed seam | Authorized response |
| --- | --- | --- |
| Issue Invite | `AdmissionApplication.issue_invite(*, actor) -> IssuedInvite` and `POST /api/admin/invites` with an empty body | 201 with `invite_code`, returned only on successful issuance |
| Review admission | Existing `GET /api/admin/applications` and `POST /api/admin/applications/{id}/decision` | Applicant ID and application note. Decision is `approve` or `reject`. |
| Read Message queues | Reuse `GET /api/admin/messages` | Separate the existing response into under-review messages and Escalated deliveries in the console. |
| Decide a withheld Message | Existing `POST /api/admin/messages/{id}/decision` | `release` or `discard`. T7 still decides delivery and writes the audit atomically. |
| Resolve an Escalated item | Proposed `MessageApplication.decide_escalation(*, actor, message_id, decision)` and `POST /api/admin/messages/{id}/escalation-decision` | `approve` or `reject` records the review disposition. Either action leaves delivery and qualifying Message counts intact. |

The Invite uses the existing secure token source and digest storage. Commit before exposing the code. Keep raw codes out of audit events, logs, URL parameters and browser storage. Render the issuance code only in the Admin's current page, with a copy action. Use a fixed conflict response on duplicate issuance and leave existing codes intact.

Each operation rechecks approved Admin authority from storage. Reuse same-origin cookie auth, Origin checks on mutations, explicit request/response fields and no-store. Review notes and Message bodies render as text. Keep queue access separate from Member views. No new private extraction site.

## Escalated and Report ownership

Proposed Escalated disposition is keyed by Message ID and stays separate from the delivery outcome. A transaction claims the open item, stores one terminal disposition and appends one typed queue audit event. A repeated identical decision is a no-op. A conflicting decision returns 409. Failed audit writes leave the item open. The console removes resolved items from the open queue. A rejection records the Admin's decision on the already delivered item. It does not retract the Message or reverse a Reveal.

T11 owns durable Reports, Report submission, terminal Admin Report decisions and their audit. T9 defines the console integration point and reserves the Report section. Until T11 connects the real queue, the section is explicitly unavailable. An empty-state message is reserved for a real empty queue. T10 owns the Matching action and policy. Both dependencies remain required for the MVP.

## Acceptance tests after approval

- Real API and browser flow issues an Invite, rejects an underage redemption without consuming it, accepts one eligible redemption and refuses reuse. Member, Applicant and expired sessions cannot issue or review. Wrong Origin and extra command fields are rejected. The raw Invite never appears in audit, logs or a list response.
- Show admission approve and reject, and withheld release and discard. Verify existing audit events, safe errors, current authority and that recipient history changes only on release.
- An Escalated Message is already delivered, appears in the Admin queue and records exactly one review decision. Test concurrent and conflicting decisions, audit rollback and unchanged eligibility counts with the same SQLite/PostgreSQL contract suite.
- Use one plain Admin console with distinct queues, clear loading and error states, disabled duplicate actions and truthful empty/unavailable states. Sign-out clears the views, and stale responses cannot overwrite a newer session. Check real API behavior in the browser using fictional data and canaries.
- Tests first at each seam, followed by purity, extraction boundary, targeted mutations and Windows/container/PostgreSQL CI before review.

## Deployed checkpoint and estimate

After T9 merges, run the checkpoint on an explicitly authorized deployed revision with synthetic data. Record pass, fail or blocked for each of the six rules. Exercise the available Invite, age gate, human admission, moderated delivery and Reveal/privacy paths. Track any missing Match display, Block/Report and fixture paths against T10, T11 and T13, then rerun the full six-rule checkpoint when those dependencies land. Report handling stays in scope throughout.

Working T9 allowance is 1.5 optimistic lead sessions for the plain console and its tests. Review and deployed checkpoint work draw on the remaining integration capacity. The approved Escalated disposition and Report integration split govern this slice.
