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

The course asks for three decisions with `file:line`; these are the three. Citations land with the code.

1. **The domain core owns the LLM interface.** The LLM is the dependency worth protecting the domain from — probabilistic, timeout-prone, and fail-closed. The core defines the port; a fake adapter runs the tests; the real adapter is wired in exactly one place.
2. **Anonymity is enforced per Conversation, not globally.** Identifier detection and Reveal state are scoped to the pair: a Reveal in one Conversation never relaxes detection in another.
3. **Time is a port.** An injectable Clock lets tests cross the ≥3-day Engagement Threshold without waiting and lets seeded Conversations carry backdated Messages.

Also ratified and binding:

- **Match acceptance is bilateral.** Both Members must accept a proposed Match before its Conversation opens; a declined Match opens no Conversation and the pair is never proposed again.
- **One active Conversation per Member.** A Member is not proposed in new Match batches while a Conversation is active; a Conversation ends by a Block or after a completed Reveal, after which the Member can be proposed again.
- **Block is available at any time.** It ends the Conversation and prevents any future Match between the pair; after a Reveal the Reveal stands and both Members can still Report.
- **The audit log is minimal and append-only**: invite redeemed, verdict, escalation, reveal, block, report. No analytics.
- **The MVP is Admin-issued Invites only.** The Invite model carries an issuer so Member-issued Invites remain a later, non-breaking extension.

## Boundary

**The LLM port is the one boundary** — where the domain core stops and the outside world begins, and the dependency it protects the domain from. The port's interface is owned by the domain; the real adapter is wired at exactly one place. At submission this section cites the port at `file:line` plus that single wiring point, so "where does your core stop?" has one precise answer.

Storage sits behind a repository port and time behind a Clock port — secondary seams, mentioned but not cited as the boundary.

## AI use

- **In the product**: Vetting, Values Profiles via conversational Onboarding, compatibility scoring, Icebreakers, and Message moderation. The AI never rejects an Applicant, never forces a Reveal, and never exposes identity.
- **In the build**: Parth is the sole human implementer; the agent implements through the repository and Parth reviews every slice. The repo's skills drive the domain docs, tests, and reviews.
- **One rejected suggestion**: an early recommendation of a server-rendered HTML app was rejected in favour of FastAPI + React (Vite) with a pure domain core — no server-rendered HTML.

## Known limitations (MVP)

- No auto-expiry of inactive Conversations.

## Evidence

`file:line` citations land as slices land: the six rules in `TESTING.md`'s rule table, and the three decisions plus the boundary here.
