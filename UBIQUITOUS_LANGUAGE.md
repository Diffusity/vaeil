# Ubiquitous Language

The words the product is about. Same format as the IT643 labs; this file is part of the project evaluation, so its `Named in code at` citations must match reality — docs that don't match the code are graded as absent. Keep in sync with `GLOSSARY.md`; rules in `docs/agents/domain.md`. Human edits win — never silently rename a term that people actually use.

## Access

| Term | Definition | Aliases to avoid | Named in code at |
| ---- | ---------- | ---------------- | ---------------- |
| **Invite** | A code that grants its holder the right to apply for membership; Vaeil is invite-only. Admin-issued in the MVP; Member-issued Invites are a planned extension. | invitation, referral code, signup code | `src/vaeil/domain/invite.py:33` |
| **Applicant** | A person who has redeemed an Invite and is being vetted; not yet a Member. | user, candidate, signup | `src/vaeil/domain/applicant.py:9` |
| **Member** | A vetted person admitted to the platform — an Approved Applicant at the verdict, a NeedsReview Applicant when an Admin approves. | user, account, player | `src/vaeil/domain/member.py:9` — complete-profile projection input; admission wiring remains T6 |
| **Admin** | The human operator; every rejection of an Applicant is an Admin decision, and the Admin oversees safety reviews. | moderator, staff, superuser | _(absent)_ |
| **Pseudonym** | The name a Member chooses during Onboarding and is shown under before a Reveal; platform-unique after normalization, fixed once set, and must never be a Personal identifier. It is 3-20 letters, digits, underscores or hyphens, starts with a letter, and cannot impersonate staff through a reserved name and must pass the owner-specific self-name check. | alias, username, handle | `src/vaeil/domain/pseudonym.py:29`, `:33`; owner-specific checks at `src/vaeil/domain/self_name.py:11`; atomic storage uniqueness remains T5 |

## Onboarding & vetting

| Term | Definition | Aliases to avoid | Named in code at |
| ---- | ---------- | ---------------- | ---------------- |
| **Vetting** | The AI's assessment of an Applicant before admission. | screening, background check | `src/vaeil/domain/vetting.py:23` |
| **Verdict** | The outcome of Vetting: Approved or NeedsReview. The AI never rejects. | decision, score, result | `src/vaeil/domain/vetting.py:9` |
| **Values Profile** | A Member's structured self-description: relationship intent, life stage, one to five distinct interests and one to five distinct values from fixed lists for complete profiles, communication style, pace and lifestyle, and at most one about field of up to 280 characters, built through Onboarding. | bio, profile, personality test | `src/vaeil/domain/profile.py:95`, `:104` — validated complete profiles; form/API remains pending |
| **Onboarding** | The structured-form process in which a Member builds a Values Profile; the conversational LLM version is stretch scope. | setup, intake, signup flow | _(absent)_ |

## Matching

| Term | Definition | Aliases to avoid | Named in code at |
| ---- | ---------- | ---------------- | ---------------- |
| **Match** | A pairing of two Members proposed for anonymous Conversation; its Conversation opens when both Members accept, and a declined Match is never proposed again. | introduction, pairing, date | _(absent)_ |
| **Icebreaker** | A short, AI-written opening line offered to a Match to help start the Conversation. | prompt, opener, pickup line | _(absent)_ |
| **Engagement Threshold** | The condition that makes a pair eligible to be offered a Reveal: at least 20 delivered Messages, including Escalated, at least 5 delivered by each Member, and at least 72 hours since the first delivered Message; Withheld does not count. | milestone, quota | _(absent)_ |

## Conversation & safety

| Term | Definition | Aliases to avoid | Named in code at |
| ---- | ---------- | ---------------- | ---------------- |
| **Conversation** | The private exchange between the two Members of a Match, anonymous until Reveal and open for chat until Block; it occupies the active slot only while neither Revealed nor Blocked. | chat, DM, thread | _(absent)_ |
| **Message** | A single contribution to a Conversation, moderated before delivery. | text, line, post | _(absent)_ |
| **Withheld** | A Message not delivered, with a reason: technical failure permits retry; a model flag means under Admin review, no same-text resend, and an audited Admin release or discard. | blocked (see **Block**), filtered, rejected | _(absent)_ |
| **Personal identifier** | A real name, email address, phone number, or social handle that ties text to a Member's identity; pre-Reveal moderation checks for identifiers heuristically. | PII, personal data, doxxing | `src/vaeil/domain/identifiers.py:11` and `:32` — implemented reason types and scanner; general name detection is not provided; owner-specific self-name checks implemented; Message moderation integration remains pending |
| **Escalated** | A Message approved by safety moderation but identifier-flagged before Reveal; delivered, queued for Admin review and audited. | flagged, suspicious, quarantined | _(absent)_ |
| **Reveal** | The event that ends anonymity: both Members' identities become known to each other. | unmask, unlock | _(absent)_ |
| **Reveal Consent** | A Member's agreement to a Reveal. Both are required; either can be withdrawn until the Reveal happens; a completed Reveal is irreversible. | opt-in, approval | _(absent)_ |
| **Block** | An action available at any time; it ends the Conversation and prevents any future Match between the pair. After a Reveal the Reveal stands and both Members can still Report. | unmatch, ban | _(absent)_ |
| **Report** | A flag a Member can raise against the other Member. | complaint, flag | _(absent)_ |
| **Audit log** | An append-only record of invite redemption, Verdicts, escalation, Reveal, Block, Report, and Admin approve/reject decisions on admissions and queue items. No analytics. | event log, history, analytics | _(absent)_ |

## Relationships

- An **Invite** is issued by an **Admin** (Member-issued Invites are a planned extension) and is redeemed by a single **Applicant**; an under-18's **Invite** stays unused.
- An **Applicant** becomes a **Member** at the Approved **Verdict**; a NeedsReview **Applicant** becomes a **Member** when an **Admin** approves.
- A **Match** pairs exactly two **Members**; a declined **Match** opens no **Conversation** and the pair is never proposed again.
- A **Conversation** holds many **Messages**; each **Message** is sent by one of its two **Members**.
- A **Member** has at most one active **Conversation** (not Revealed and not Blocked); Reveal frees the slot for new **Matches** but that **Conversation** stays open for chat until **Block**. Identifier escalation stops there; safety moderation and Reporting continue.
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
> **Expert:** Only once they've met the Engagement Threshold — 20 delivered Messages, at least 5 delivered by each Member, and 72 hours since the first delivered Message — and only with both Reveal Consents. Escalated counts; Withheld does not. Either can withdraw consent until Reveal happens.
> **Developer:** Can one of them force it?
> **Expert:** Never. Neither the AI nor a Member can force a Reveal or expose an identity.
> **Developer:** What if someone types their phone number before the Reveal?
> **Expert:** Moderation detects personal identifiers and marks the Message Escalated. It is still delivered, but an Admin reviews it afterwards and it lands in the audit log. We don't withhold it — we just don't treat it as normal.
> **Developer:** What stops someone from just using their real name as a Pseudonym?
> **Expert:** The implemented scanner rejects supported email, phone, and handle patterns. The self-name check also rejects a Pseudonym containing a token of that Member's own real name or email local part. It is not general name detection, and unfamiliar forms can still be missed. Once set, a Pseudonym is fixed.
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

Slices 1-2 implement Invite, Applicant, Vetting, Verdict, identifier scanning, and Pseudonym claims. T1 adds Member, Values Profile, the self-name check, and pair-scoped identity views. Conversation lifecycle, transport, and persistent platform uniqueness remain planned; Rule 5 stays partial. The self-name check is implemented, but general real-name detection is not promised; see `DESIGN.md` for the heuristic limits.
