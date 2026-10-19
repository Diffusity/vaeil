# Ubiquitous Language

The words the product is about. Same format as the IT643 labs; this file is part of the project evaluation, so its `Named in code at` citations must match reality — docs that don't match the code are graded as absent. Keep in sync with `GLOSSARY.md`; rules in `docs/agents/domain.md`. Human edits win — never silently rename a term that people actually use.

## Access

| Term | Definition | Aliases to avoid | Named in code at |
| ---- | ---------- | ---------------- | ---------------- |
| **Invite** | A code that grants its holder the right to apply for membership; Vaeil is invite-only. | invitation, referral code, signup code | _(absent)_ |
| **Applicant** | A person who has redeemed an Invite and is being vetted; not yet a Member. | user, candidate, signup | _(absent)_ |
| **Member** | A vetted person admitted to the platform. | user, account, player | _(absent)_ |
| **Admin** | The human operator; every rejection of an Applicant is an Admin decision, and the Admin oversees safety reviews. | moderator, staff | _(absent)_ |

## Onboarding & vetting

| Term | Definition | Aliases to avoid | Named in code at |
| ---- | ---------- | ---------------- | ---------------- |
| **Vetting** | The AI's assessment of an Applicant before admission. | screening, background check | _(absent)_ |
| **Verdict** | The outcome of Vetting: Approved or NeedsReview. The AI never rejects. | decision, score, result | _(absent)_ |
| **Values Profile** | A Member's written self-description — who they are, their values and interests — built through conversational Onboarding. | bio, profile, personality test | _(absent)_ |
| **Onboarding** | The conversation in which the AI builds a Member's Values Profile. | setup, intake, signup flow | _(absent)_ |

## Matching

| Term | Definition | Aliases to avoid | Named in code at |
| ---- | ---------- | ---------------- | ---------------- |
| **Match** | A pairing of two Members proposed for anonymous Conversation. | introduction, pairing, date | _(absent)_ |
| **Icebreaker** | A short, AI-written opening line offered to a Match to help start the Conversation. | prompt, opener, pickup line | _(absent)_ |
| **Engagement Threshold** | The condition that makes a pair eligible to be offered a Reveal: at least 20 Messages in total, at least 5 from each Member, over at least 3 days. | milestone, quota | _(absent)_ |

## Conversation & safety

| Term | Definition | Aliases to avoid | Named in code at |
| ---- | ---------- | ---------------- | ---------------- |
| **Conversation** | The private, anonymous exchange between the two Members of a Match. | chat, DM, thread | _(absent)_ |
| **Message** | A single contribution to a Conversation, moderated before delivery. | text, line, post | _(absent)_ |
| **Withheld** | A Message not delivered because moderation failed or timed out; the sender retries. | blocked (see **Block**), filtered, rejected | _(absent)_ |
| **Reveal** | The event that ends anonymity: both Members' identities become known to each other. | unmask, unlock | _(absent)_ |
| **Reveal Consent** | A Member's agreement to a Reveal. Both are required; either can be withdrawn until the Reveal happens; a completed Reveal is irreversible. | opt-in, approval | _(absent)_ |
| **Block** | A post-Reveal action that ends the Conversation, prevents any future Match between the pair, and leaves the Reveal standing. | unmatch, ban | _(absent)_ |
| **Report** | A flag a Member can raise against the other Member. | complaint, flag | _(absent)_ |

## Relationships

- An **Invite** is redeemed by a single **Applicant**; an under-18's **Invite** stays unused.
- An **Applicant** with an Approved **Verdict** becomes a **Member**. _(pending: before or after Onboarding)_
- A **Match** pairs exactly two **Members** and opens one **Conversation**.
- A **Conversation** holds many **Messages**; each **Message** is sent by one of its two **Members**.
- A **Reveal** is offered only once the **Engagement Threshold** is met, and requires **Reveal Consent** from both **Members**.
- A **Block** ends a **Conversation** and prevents any future **Match** between the pair; the **Reveal** stands.

## Example dialogue

> **Developer:** An Applicant redeems an Invite — does the AI decide whether they get in?
> **Expert:** It gives a Verdict — Approved or NeedsReview. It can never reject. Every rejection is an Admin decision.
> **Developer:** When can a pair Reveal?
> **Expert:** Only once they've met the Engagement Threshold — 20 messages, at least 5 from each, over at least 3 days — and only with Reveal Consent from both. Either can withdraw consent until the Reveal happens.
> **Developer:** Can one of them force it?
> **Expert:** Never. Neither the AI nor a Member can force a Reveal or expose an identity.
> **Developer:** And if someone blocks after a Reveal?
> **Expert:** The Conversation ends, the pair is never rematched, and the Reveal stands. Both can still Report.

## Flagged ambiguities

Pending decisions (winner to be confirmed):
1. **Match vs Introduction** — early drafts said "Introduction"; the product spec says "Match". Winner: **Match** (pending confirmation).
2. **When is an Applicant a Member?** — at the Approved Verdict, or only after Onboarding?
3. **Block before a Reveal?** — the spec states Block "after a Reveal"; the pre-Reveal exit path is undecided.
4. **Who issues Invites?** — undecided (Admin-issued proposed for the MVP).
5. **Who reviews escalated Messages?** — "reviewed afterwards" names no reviewer (Admin proposed).
6. **Match acceptance** — must both Members accept a proposed Match before its Conversation opens?

## Code drift

| Canonical term | Called in code | Location | Note |
| -------------- | -------------- | -------- | ---- |

_None yet — no code on `master`. All `Named in code at` citations are marked `_(absent)_` until the first slices land._
