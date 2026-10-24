# Design

Vaeil — invite-only, anonymous matchmaking for 18–28 students and young professionals. This file is part of the IT643 evaluation: it must match the code at `file:line`, and a claim the code does not back is graded as absent.

**Status: working draft.** Citations are added as each slice lands; the file is complete before the pushed `project-final` tag.

## The six rules

The course asks for five rules; the product has six — the five plus a team-added age gate. All six are presented here; `TESTING.md` tracks which ones have tests today.

1. **Invite-only access.** Nobody gets an account without redeeming an Invite. Invites are Admin-issued in the MVP; each Invite records its issuer, so Member-issued Invites can be added later without a breaking change.
2. **Vetting never rejects.** The AI's Vetting returns Approved or NeedsReview only. An Approved Applicant becomes a Member at the verdict; a NeedsReview Applicant becomes a Member when an Admin approves. Every rejection is an Admin decision; the AI never rejects.
3. **Moderated delivery.** A Message reaches the other Member only after moderation passes. If the LLM fails or times out, the Message is Withheld and the sender is told to retry. An Escalated Message is still delivered, then reviewed afterwards by an Admin. Fail-closed: a cost-cap hit or provider failure yields Withheld (messages) or NeedsReview (vetting) — never unchecked delivery or auto-approval.
4. **Consensual Reveal.** A Reveal is offered only once the Engagement Threshold is met: ≥20 Messages in total, ≥5 from each Member, over ≥3 days. Both Members must give Reveal Consent; either can withdraw until the Reveal happens; a completed Reveal is irreversible.
5. **Anonymity before Reveal.** The system never shows or sends a Member's real name, photo, or contact details to their Match outside a Reveal. Identity is shown only as a Pseudonym plus the Values Profile; photos exist only after a Reveal. A Pseudonym is chosen by the Member during Onboarding, platform-unique (case-insensitive), must pass the same identifier check as Messages, and is fixed once set. Personal identifiers typed by Members are detected per Conversation — Escalated before that pair's Reveal, normal afterwards — and are delivered, reviewed by an Admin, and recorded in the audit log. Rule 5 constrains what the system shows and sends, not what Members type. Detection is heuristic: it routes suspicious text to Escalated but does not promise to catch every identifier — spelled-out numbers, novel obfuscation, or identifiers split across Messages can be missed, and a long numeric string can be a false positive. The system-side guarantee does not depend on detection.
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

- **Tools used**: OpenCode agents and the repository's engineering skills for the original design interview, vocabulary, first-slice tests and implementation. Codex continued from the recovered OpenCode session using terminal commands, file patches, and the gh CLI: it implemented identifier scanning and Pseudonym validation, added regression and mutation checks, ran independent Standards/Spec reviews, fixed scanner performance, maintained docs/logs, and added the approved Windows CI and agent-workflow checks. These are development tools; they are separate from the product's future real LLM adapter.
- **Human decisions and review**: Parth set the product scope and stack, made the safety/privacy policy decisions, approved public test seams, requested stronger boundary and failure tests and mutation evidence, reviewed the slice outputs, and authorized the merges. Agents prepared implementation, tests, documentation, and review reports; Parth remained the product decision-maker and human reviewer. All four team members must be able to explain the delivered code and its evidence at the viva.
- **In the product**: Vetting, Values Profiles via conversational Onboarding, compatibility scoring, Icebreakers, and Message moderation. The AI never rejects an Applicant, never forces a Reveal, and never exposes identity.
- **One rejected suggestion (primary)**: allowing contact details in chat and merely logging them. The AI recommended logging as a light-touch safety measure; rejected because logging enforces nothing — two Members could exchange numbers before a Reveal and bypass Reveal Consent, and Rule 5 would become untestable. Replaced with identifier detection that Escalates the Message: it is still delivered, but an Admin reviews it, it is audited, and Reveal remains the only route to identity.
- **Also rejected (secondary)**: a server-rendered HTML app. The stack was already decided (FastAPI + React/Vite), the team was comfortable with it, and the Reveal ceremony and chat UI benefit from client-side state. Server-rendered HTML would also have been defensible for a project this small — this was a fit choice, not a technical verdict.

## Values Profile write policy (approved, not implemented)

A Values Profile has structured fields from a fixed schema and at most one short free-text `about` field with a length cap. Every free-text field is checked with both the shared identifier scanner and the Member-specific self-name check at write time; a flagged save is refused. LLM-generated profile text passes the same checks before storage. The exact schema and numeric cap will be shown with the proposed Member/Values Profile types for approval; this document does not invent them.

These checks are heuristic: they can miss a name in an unrecognized form, novel obfuscation, or indirect identifying details such as a rare workplace. They do not establish general name detection. Private fields still need an explicit pre-Reveal allow-list projection and canary tests across projected/serialized views. This policy is pending implementation; Rule 5 remains partial.

The LLM provider and monthly cap remain `[provider]` and `[cap]`, deferred. Build against the fake adapter until the first approved ticket that needs a real LLM.

## Known limitations (MVP)

### Slice 2 detection and Pseudonym policy

**When in doubt, flag.** A false positive costs the Admin a queue item; a false negative can undermine Rule 5, so the cost asymmetry favours flagging. Detection is a safety net; the pre-Reveal display boundary must independently prevent system disclosure. This slice does not implement that boundary or decide delivery.

- `src/vaeil/domain/identifiers.py:32` normalizes input with NFKC and converts Unicode decimal digits before scanning. `MIN_PHONE_DIGITS = 10` is the threshold for a run after stripping whitespace, parentheses, dots, plus signs, and hyphens; 9 digits stay clean and 10 or more flag, with no upper limit. Numeric runs embedded in a Pseudonym also flag.
- Reason order is EMAIL, PHONE, HANDLE, OBFUSCATED_EMAIL, URL. Handles include `@name`, `insta: name`, `my ig is name`, and Instagram profile links. Web links, including bare domains, produce URL; Instagram profile links produce both HANDLE and URL. Email addresses alone do not additionally produce URL. Supported obfuscation includes plain, bracketed, and parenthesized `at`, plus `dot`/`d0t`, ignoring case.
- The immutable scan result stores only ordered reasons, never matched text or spans. Keeping another copy of identifiers in the audit log or Admin queue is deliberately avoided. Any later span-retention requirement belongs to the moderation slice.
- Pseudonyms are NFKC-normalized and trimmed for display, then casefolded for uniqueness. They contain 3-20 Unicode letters or decimal digits, underscore or hyphen, start with a letter, and cannot be reserved staff names (`admin`, `moderator`, `system`, `vaeil`, `support`, case-insensitively). Named constants live in `src/vaeil/domain/pseudonym.py:8`.
- The in-memory directory is only the domain seam. When the repository lands, uniqueness must be enforced atomically with a unique index on the normalized value; checking then inserting without that constraint races during concurrent signups. The current directory does not enforce platform-wide or cross-process uniqueness.
- Real names are not reliably detected; the format rule rejects `rahul.sharma` but a name such as `Rahul` can still pass. Spelled-out numbers, novel obfuscation, identifiers split across Messages, and numeric false positives remain known limits. Rule 5 is partially tested here and remains incomplete until the pre-Reveal display slice.

- No auto-expiry of inactive Conversations.
- Identifier detection is heuristic: spelled-out numbers, novel obfuscation, and identifiers split across Messages can be missed; long numeric strings can be false positives.

## Evidence

`file:line` citations land as slices land: the six rules in `TESTING.md`'s rule table, and the three decisions plus the boundary here. Merged slice 1 supports decisions 1 and 3 through the Vetting port and fail-closed wrapper. Merged slice 2 adds identifier scanning and Pseudonym claims, covering part of Rule 5. Conversation isolation (decision 2), the real-adapter wiring point, Rules 3 and 4, and the rest of Rule 5 remain pending. Current coverage stays 3 of 6 rules domain-level, 0 of 6 end-to-end; Rule 5 is partial.
