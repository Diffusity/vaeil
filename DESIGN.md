# Design

Vaeil — invite-only, anonymous matchmaking for 18–28 students and young professionals. This file is part of the IT643 evaluation: it must match the code at `file:line`, and a claim the code does not back is graded as absent.

**Status: working draft.** Citations are added as each slice lands; the file is complete before the pushed `project-final` tag.

## The six rules

The course asks for five rules; the product has six — the five plus a team-added age gate. All six are demonstrated and tested ("6 of 6" in `TESTING.md`).

1. **Invite-only access.** Nobody gets an account without redeeming an Invite. Invites are Admin-issued in the MVP; each Invite records its issuer, so Member-issued Invites can be added later without a breaking change.
2. **Vetting never rejects.** The AI's Vetting returns Approved or NeedsReview only. An Approved Applicant becomes a Member at the verdict; a NeedsReview Applicant becomes a Member when an Admin approves. Every rejection is an Admin decision; the AI never rejects.
3. **Moderated delivery.** A Message reaches the other Member only after moderation passes. If the LLM fails or times out, the Message is Withheld and the sender is told to retry. An Escalated Message is still delivered, then reviewed afterwards by an Admin. Fail-closed: a cost-cap hit or provider failure yields Withheld (messages) or NeedsReview (vetting) — never unchecked delivery or auto-approval.
4. **Consensual Reveal.** A Reveal is offered only once the Engagement Threshold is met: ≥20 Messages in total, ≥5 from each Member, over ≥3 days. Both Members must give Reveal Consent; either can withdraw until the Reveal happens; a completed Reveal is irreversible.
5. **Anonymity before Reveal.** The system never shows or sends a Member's real name, photo, or contact details to their Match outside a Reveal. Identity is shown only as a Pseudonym plus the Values Profile; photos exist only after a Reveal. A Pseudonym is chosen by the Member during Onboarding, platform-unique (case-insensitive), must pass the same identifier check as Messages, and is fixed once set. Personal identifiers typed by Members are detected per Conversation — Escalated before that pair's Reveal, normal afterwards — and are delivered, reviewed by an Admin, and recorded in the audit log. Rule 5 constrains what the system shows and sends, not what Members type.
6. **Age gate.** 18+ is validated before an Invite is redeemed; an under-18's Invite stays unused.

**Not a numbered rule, but binding:** matching is curated only — no browsing or search. An Admin triggers a matching batch; the AI proposes pairs scored from Values Profiles.

## Decisions

The course asks for three design decisions. Each names the principle it applies, the `file:line` where it lives, and what it looked like before and why it changed. Citations are completed as the slices land; a later refactor is recorded here with the commit that shows the "before".

### 1. The domain core owns the LLM interface

- **Principle**: Dependency Inversion (SOLID) at the boundary (Lecture 23) — the core depends on an interface it owns, not on a provider SDK.
- **Where**: `src/vaeil/domain/vetting.py:16` (the port) + `_pending_` (the single place the real adapter is wired, in the adapter slice).
- **Before / why**: the straightforward version calls the provider client directly from the vetting and moderation flows. Rejected in the design interview — the core would depend on an SDK, tests would need the network, and failures could not fail closed. The port keeps the core testable with a fake adapter and turns every failure into Withheld (messages) or NeedsReview (vetting).
- **Supporting decision — time is a port**: the core asks a Clock port (`src/vaeil/domain/clock.py:7`) for "now" instead of reading the system clock. That makes the Engagement Threshold's ≥3 days testable without waiting and lets demo seeds backdate Messages. It is a testing aid, not a product trade-off, and stays a secondary seam.

### 2. Anonymity is enforced per Conversation, not globally

- **Principle**: information hiding — Reveal state and identifier detection are scoped to the pair, never to a global Member flag, so one Reveal cannot relax any other Conversation.
- **Where**: `_pending_`.
- **Before / why**: the first recommendation was to log contact details typed before a Reveal. Rejected because logging lets two Members bypass Reveal Consent and makes Rule 5 untestable. Changed to identifier detection that Escalates the Message (still delivered, Admin-reviewed, audited), then scoped per Conversation so a Reveal only relaxes its own pair.

### 3. The LLM port fails closed

- **Principle**: boundary (Lecture 23) — the port's contract defines the failure mode; the domain never sees an unchecked or partial LLM result.
- **Where**: `src/vaeil/domain/vetting.py:23` — the `vet` wrapper's `except Exception` fallback at `:27` and its `isinstance` guard at `:30` are the actual fail-closed checks.
- **Before / why**: the default failure behaviour is to fall back — deliver the Message anyway, or approve the Applicant. Rejected: unchecked delivery breaks Rule 3 and auto-approval breaks Rule 2. Changed to explicit domain states — a timeout, provider error, or budget-cap hit means Withheld for Messages and NeedsReview for Vetting, never fail open. The cost is real (legitimate Messages are delayed, and more work lands on the Admin), and that is the point: a human reviews instead of an unchecked model deciding.

Also ratified and binding:

- **Match acceptance is bilateral.** Both Members must accept a proposed Match before its Conversation opens; a declined Match opens no Conversation and the pair is never proposed again.
- **One active Conversation per Member.** A Member is not proposed in new Match batches while a Conversation is active; a Conversation ends by a Block or after a completed Reveal, after which the Member can be proposed again.
- **Block is available at any time.** It ends the Conversation and prevents any future Match between the pair; after a Reveal the Reveal stands and both Members can still Report.
- **The audit log is minimal and append-only**: invite redeemed, verdict, escalation, reveal, block, report. No analytics.
- **The MVP is Admin-issued Invites only.** The Invite model carries an issuer so Member-issued Invites remain a later, non-breaking extension.

## Boundary

**The LLM port is the one boundary** — where the domain core stops and the outside world begins, and the dependency it protects the domain from. The port's interface is owned by the domain at `src/vaeil/domain/vetting.py:16`; the real adapter will be wired at exactly one place when the adapter slice lands. At submission this section cites that single wiring point too, so "where does your core stop?" has one precise answer.

Storage sits behind a repository port and time behind a Clock port — secondary seams, mentioned but not cited as the boundary.

## AI use

- **Tools used**: OpenCode agents with the repository's engineering skills — for the design interview, domain vocabulary, specs, tests, docs, and implementation.
- **For what**: Parth is the sole human implementer; the agent implements through the repository and Parth reviews every slice. Every claim in this repo's docs is checked against the code at the viva.
- **In the product**: Vetting, Values Profiles via conversational Onboarding, compatibility scoring, Icebreakers, and Message moderation. The AI never rejects an Applicant, never forces a Reveal, and never exposes identity.
- **One rejected suggestion (primary)**: allowing contact details in chat and merely logging them. The AI recommended logging as a light-touch safety measure; rejected because logging enforces nothing — two Members could exchange numbers before a Reveal and bypass Reveal Consent, and Rule 5 would become untestable. Replaced with identifier detection that Escalates the Message: it is still delivered, but an Admin reviews it, it is audited, and Reveal remains the only route to identity.
- **Also rejected (secondary)**: a server-rendered HTML app. The stack was already decided (FastAPI + React/Vite), the team was comfortable with it, and the Reveal ceremony and chat UI benefit from client-side state. Server-rendered HTML would also have been defensible for a project this small — this was a fit choice, not a technical verdict.

## Known limitations (MVP)

- No auto-expiry of inactive Conversations.

## Evidence

`file:line` citations land as slices land: the six rules in `TESTING.md`'s rule table, and the three decisions plus the boundary here. Slice 1 cites decision 1 (the port) and decision 3 (fail-closed vetting); decision 2, the adapter wiring point, and Rules 3–5 land with their slices.
