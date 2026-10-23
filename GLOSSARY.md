# Vaeil

Invite-only, anonymous matchmaking: AI curates Matches and identity is revealed only by mutual consent. Single context — this is the implementation-free view; the evaluated artifact with code citations is `UBIQUITOUS_LANGUAGE.md`. Keep both in sync — see `docs/agents/domain.md`.

Term decisions (including resolved ambiguities) are recorded in `UBIQUITOUS_LANGUAGE.md`.

## Language

### Access

**Invite**:
A code that grants its holder the right to apply for membership; Vaeil is invite-only. Admin-issued in the MVP; Member-issued Invites are a planned extension.
_Avoid_: invitation, referral code, signup code

**Applicant**:
A person who has redeemed an Invite and is being vetted; not yet a Member.
_Avoid_: user, candidate, signup

**Member**:
A vetted person admitted to the platform — an Approved Applicant at the verdict, a NeedsReview Applicant when an Admin approves.
_Avoid_: user, account, player

**Admin**:
The human operator. Every rejection of an Applicant is an Admin decision, and the Admin oversees safety reviews.
_Avoid_: moderator, staff, superuser

**Pseudonym**:
The name a Member chooses during Onboarding and is shown under before a Reveal; platform-unique after normalization, fixed once set, and must never be a Personal identifier. It is 3-20 letters, digits, underscores or hyphens, starts with a letter, and cannot impersonate staff through a reserved name.
_Avoid_: alias, username, handle

### Onboarding & vetting

**Vetting**:
The AI's assessment of an Applicant before admission.
_Avoid_: screening, background check

**Verdict**:
The outcome of Vetting: Approved or NeedsReview. The AI never rejects.
_Avoid_: decision, score, result

**Values Profile**:
A Member's written self-description — who they are, their values and interests — built through conversational Onboarding.
_Avoid_: bio, profile, personality test

**Onboarding**:
The conversation in which the AI builds a Member's Values Profile.
_Avoid_: setup, intake, signup flow

### Matching

**Match**:
A pairing of two Members proposed for anonymous Conversation; its Conversation opens when both Members accept, and a declined Match is never proposed again.
_Avoid_: introduction, pairing, date

**Icebreaker**:
A short, AI-written opening line offered to a Match to help start the Conversation.
_Avoid_: prompt, opener, pickup line

**Engagement Threshold**:
The condition that makes a pair eligible to be offered a Reveal: at least 20 Messages in total, at least 5 from each Member, over at least 3 days.
_Avoid_: milestone, quota

### Conversation & safety

**Conversation**:
The private, anonymous exchange between the two Members of a Match.
_Avoid_: chat, DM, thread

**Message**:
A single contribution to a Conversation, moderated before delivery.
_Avoid_: text, line, post

**Withheld**:
A Message not delivered because moderation failed or timed out; the sender is told to retry.
_Avoid_: blocked (see Block), filtered, rejected

**Personal identifier**:
A real name, email address, phone number, or social handle that ties text to a Member's identity; moderation detects them in Messages before a Reveal.
_Avoid_: PII, personal data, doxxing

**Escalated**:
A Message that moderation flagged for Admin review; it is still delivered and reviewed afterwards.
_Avoid_: flagged, suspicious, quarantined

**Reveal**:
The event that ends anonymity: both Members' identities become known to each other.
_Avoid_: unmask, unlock

**Reveal Consent**:
A Member's agreement to a Reveal. Both are required; either can be withdrawn until the Reveal happens; a completed Reveal is irreversible.
_Avoid_: opt-in, approval

**Block**:
An action available at any time; it ends the Conversation and prevents any future Match between the pair. After a Reveal the Reveal stands and both Members can still Report.
_Avoid_: unmatch, ban

**Report**:
A flag a Member can raise against the other Member.
_Avoid_: complaint, flag

**Audit log**:
An append-only record of the events an Admin may review: invite redeemed, verdict, escalation, reveal, block, report. No analytics.
_Avoid_: event log, history, analytics
