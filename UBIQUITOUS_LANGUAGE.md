# Ubiquitous Language

The words the product is about. Same format as the IT643 labs; this file is part of the project evaluation, so its `Named in code at` citations must match reality — docs that don't match the code are graded as absent. Keep in sync with `GLOSSARY.md`; rules in `docs/agents/domain.md`. Human edits win — never silently rename a term that people actually use.

## Access

| Term | Definition | Aliases to avoid | Named in code at |
| ---- | ---------- | ---------------- | ---------------- |
| **Invite** | A code that grants its holder the right to apply for membership; Vaeil is invite-only. Admin-issued in the MVP; Member-issued Invites are a planned extension. | invitation, referral code, signup code | _(absent)_ |
| **Applicant** | A person who has redeemed an Invite and is being vetted; not yet a Member. | user, candidate, signup | _(absent)_ |
| **Member** | A vetted person admitted to the platform — an Approved Applicant at the verdict, a NeedsReview Applicant when an Admin approves. | user, account, player | _(absent)_ |
| **Admin** | The human operator; every rejection of an Applicant is an Admin decision, and the Admin oversees safety reviews. | moderator, staff, superuser | _(absent)_ |
| **Pseudonym** | The name a Member chooses during Onboarding and is shown under before a Reveal; platform-unique (case-insensitive), fixed once set, and must never be a Personal identifier. | alias, username, handle | _(absent)_ |

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
| **Match** | A pairing of two Members proposed for anonymous Conversation; its Conversation opens when both Members accept, and a declined Match is never proposed again. | introduction, pairing, date | _(absent)_ |
| **Icebreaker** | A short, AI-written opening line offered to a Match to help start the Conversation. | prompt, opener, pickup line | _(absent)_ |
| **Engagement Threshold** | The condition that makes a pair eligible to be offered a Reveal: at least 20 Messages in total, at least 5 from each Member, over at least 3 days. | milestone, quota | _(absent)_ |

## Conversation & safety

| Term | Definition | Aliases to avoid | Named in code at |
| ---- | ---------- | ---------------- | ---------------- |
| **Conversation** | The private, anonymous exchange between the two Members of a Match. | chat, DM, thread | _(absent)_ |
| **Message** | A single contribution to a Conversation, moderated before delivery. | text, line, post | _(absent)_ |
| **Withheld** | A Message not delivered because moderation failed or timed out; the sender is told to retry. | blocked (see **Block**), filtered, rejected | _(absent)_ |
| **Personal identifier** | A real name, email address, phone number, or social handle that ties text to a Member's identity; moderation detects them in Messages before a Reveal. | PII, personal data, doxxing | _(absent)_ |
| **Escalated** | A Message that moderation flagged for Admin review; it is still delivered and reviewed afterwards. | flagged, suspicious, quarantined | _(absent)_ |
| **Reveal** | The event that ends anonymity: both Members' identities become known to each other. | unmask, unlock | _(absent)_ |
| **Reveal Consent** | A Member's agreement to a Reveal. Both are required; either can be withdrawn until the Reveal happens; a completed Reveal is irreversible. | opt-in, approval | _(absent)_ |
| **Block** | An action available at any time; it ends the Conversation and prevents any future Match between the pair. After a Reveal the Reveal stands and both Members can still Report. | unmatch, ban | _(absent)_ |
| **Report** | A flag a Member can raise against the other Member. | complaint, flag | _(absent)_ |

## Relationships

- An **Invite** is issued by an **Admin** (Member-issued Invites are a planned extension) and is redeemed by a single **Applicant**; an under-18's **Invite** stays unused.
- An **Applicant** becomes a **Member** at the Approved **Verdict**; a NeedsReview **Applicant** becomes a **Member** when an **Admin** approves.
- A **Match** pairs exactly two **Members**; a declined **Match** opens no **Conversation** and the pair is never proposed again.
- A **Conversation** holds many **Messages**; each **Message** is sent by one of its two **Members**.
- A **Member** has at most one active **Conversation** at a time and is not proposed in new **Match** batches while it is active; a **Conversation** ends by a **Block** or after a completed **Reveal**, after which the **Member** can be proposed again.
- An **Escalated** **Message** is delivered, enters the Admin review queue, and is recorded in the audit log.
- Identifier detection is per **Conversation**: **Personal identifiers** in a **Message** are **Escalated** only before that **Conversation**'s **Reveal**; afterwards they stop being **Escalated**, though safety moderation continues.
- A **Report** enters the Admin review queue.
- A **Reveal** is offered only once the **Engagement Threshold** is met, and requires **Reveal Consent** from both **Members**.
- A **Block** ends a **Conversation** and prevents any future **Match** between the pair; after a **Reveal** the **Reveal** stands and both **Members** can still **Report**.
- Before a **Reveal**, a **Member** appears only as a **Pseudonym**; a **Pseudonym** must never be a **Personal identifier** — a taken or identifier-like one is rejected and the **Member** picks another.

## Example dialogue

> **Developer:** An Applicant redeems an Invite — does the AI decide whether they get in?
> **Expert:** It gives a Verdict — Approved or NeedsReview. It can never reject. Every rejection is an Admin decision.
> **Developer:** When can a pair Reveal?
> **Expert:** Only once they've met the Engagement Threshold — 20 messages, at least 5 from each, over at least 3 days — and only with Reveal Consent from both. Either can withdraw consent until the Reveal happens.
> **Developer:** Can one of them force it?
> **Expert:** Never. Neither the AI nor a Member can force a Reveal or expose an identity.
> **Developer:** What if someone types their phone number before the Reveal?
> **Expert:** Moderation detects personal identifiers and marks the Message Escalated. It is still delivered, but an Admin reviews it afterwards and it lands in the audit log. We don't withhold it — we just don't treat it as normal.
> **Developer:** What stops someone from just using their real name as a Pseudonym?
> **Expert:** The same identifier check as Messages — a Pseudonym that looks like a real name, email, phone number, or handle is rejected, and they pick another. Once set, a Pseudonym is fixed.
> **Developer:** And if someone blocks after a Reveal?
> **Expert:** The Conversation ends, the pair is never rematched, and the Reveal stands. Both can still Report.

## Flagged ambiguities

Resolved — winners recorded (kept here as findings):
1. **Match vs Introduction** — two words for one concept. Winner: **Match**; "Introduction" is an alias to avoid.
2. **Applicant → Member timing** — Winner: at the Approved Verdict; a NeedsReview Applicant becomes a Member when an Admin approves.
3. **Block timing** — the spec said "after a Reveal". Winner: Block is available any time; post-Reveal the Reveal stands and Reporting remains possible.
4. **Invite issuer** — Winner: Admin-issued in the MVP; the model carries an issuer so Member-issued Invites are a later, non-breaking extension.
5. **Escalation reviewer** — Winner: an Admin, via the review queue.
6. **Match acceptance** — Winner: both Members must accept; a declined Match is never proposed again.

## Code drift

| Canonical term | Called in code | Location | Note |
| -------------- | -------------- | -------- | ---- |

_None yet — no code on `master`. All `Named in code at` citations are marked `_(absent)_` until the first slices land._
