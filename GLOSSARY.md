# Vaeil

Invite-only, anonymous matchmaking: AI curates Matches and identity is revealed only by mutual consent. Single context — this is the implementation-free view; the evaluated artifact with code citations is `UBIQUITOUS_LANGUAGE.md`. Keep both in sync — see `docs/agents/domain.md`.

Open term questions are flagged in `UBIQUITOUS_LANGUAGE.md` (Flagged ambiguities) until resolved.

## Language

### Access

**Invite**:
A code that grants its holder the right to apply for membership; Vaeil is invite-only.
_Avoid_: invitation, referral code, signup code

**Applicant**:
A person who has redeemed an Invite and is being vetted; not yet a Member.
_Avoid_: user, candidate, signup

**Member**:
A vetted person admitted to the platform.
_Avoid_: user, account, player

**Admin**:
The human operator. Every rejection of an Applicant is an Admin decision, and the Admin oversees safety reviews.
_Avoid_: moderator, staff, superuser

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
A pairing of two Members proposed for anonymous Conversation.
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
A Message not delivered because moderation failed or timed out; the sender retries.
_Avoid_: blocked (see Block), filtered, rejected

**Reveal**:
The event that ends anonymity: both Members' identities become known to each other.
_Avoid_: unmask, unlock

**Reveal Consent**:
A Member's agreement to a Reveal. Both are required; either can be withdrawn until the Reveal happens; a completed Reveal is irreversible.
_Avoid_: opt-in, approval

**Block**:
A post-Reveal action that ends the Conversation, prevents any future Match between the pair, and leaves the Reveal standing.
_Avoid_: unmatch, ban

**Report**:
A flag a Member can raise against the other Member.
_Avoid_: complaint, flag
