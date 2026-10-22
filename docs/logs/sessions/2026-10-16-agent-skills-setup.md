# 2026-10-16 — Agent skills setup

_Session ran 2026-10-16 into 2026-10-17._

## Goal

Initialize the per-repo configuration the Matt Pocock engineering skills assume: issue tracker, triage labels, and domain docs (via `.agents/skills/setup-matt-pocock-skills`).

## What happened

- Explored the repo: greenfield — only `.agents/`, `LICENSE`, `skills-lock.json`. GitHub remote `Diffusity/vaeli`. `triage` skill installed. No monorepo signals → single-context.
- User decisions (asked explicitly):
  - Issue tracker → **GitHub** Issues via `gh` CLI.
  - Triage labels → **keep the five defaults**.
  - Instruction file → create **`AGENTS.md`** (no `CLAUDE.md`).
- Wrote from the skill's seed templates: `AGENTS.md`, `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, `docs/agents/domain.md`.
- User installed and authenticated `gh`: version 2.102.0, account `Diffusity`, HTTPS, token scopes `gist, read:org, repo, workflow`.
- Created issue labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`. `wontfix` already existed and was left as-is.
- User asked to keep an assumptions log and session logs → created `docs/logs/` (this file, `assumptions.md`, `README.md`) and added a `## Project logs` section to `AGENTS.md`.

## Open / follow-ups

- None blocking. Revisit the single-context assumption if monorepo signals (`packages/`, workspaces) appear.

## Environment notes

- The hosting app (OpenCode) cached the pre-install `PATH`, so `gh` wasn't visible to its shells. Fix (restart app, or PATH-refresh one-liner) recorded in `docs/logs/README.md`.

## Related artifacts

- `AGENTS.md`, `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, `docs/agents/domain.md`
- Issue tracker: https://github.com/Diffusity/vaeli

## 2026-10-18 addendum

- Committed the setup as `48f75f2` on `master` ("Add agent skills setup and project logs"): `AGENTS.md`, `docs/`, and `.gitignore` (which keeps the vendored `.agents/` skills directory and `skills-lock.json` out of the repo).

## 2026-10-19 addendum

- Surfaced a local `main` branch (GitHub's default branch) carrying three local-only commits imported from `vaeil.zip` — skeleton, backend slices (domain rules, `Clock` port/adapter), and a pytest suite. `origin/main` is still at "Initial commit" (`d4199cb`); nothing has been pushed.
- **User decision:** development continues on `master`; `main` is out of scope — left untouched, not to be merged, checked out, or cherry-picked from (see `../assumptions.md`).
- Push to GitHub deferred (user: "Not yet"). Everything stays local.

## 2026-10-19 — Course deliverables wired in

- Read the IT643 project page (https://it643.ankushchander.com/project/): evaluation requires four root files — `README.md`, `UBIQUITOUS_LANGUAGE.md`, `DESIGN.md`, `TESTING.md` — and docs are graded against the code (`file:line`); stale docs count as absent.
- Created `UBIQUITOUS_LANGUAGE.md` (course format: term table + flagged ambiguities) and `GLOSSARY.md` (skills format). Both are intentionally empty of terms: the course warns an unreviewed agent-authored glossary is worse than none — the team populates them.
- `docs/agents/domain.md`: vocabulary section added (read both files; keep in sync; code wins on disagreement).
- `AGENTS.md`: `## Project constraints` section added.
- Not yet created on `master`: `README.md`, `DESIGN.md`, `TESTING.md` — they land with the work.

## 2026-10-19 — grill-with-docs session, Round 1 decisions

- **Product shape (corrected)**: Vaeil — invite-only, anonymous matchmaking for college students and young professionals (18–28). One loop only: invite → vet → onboard → match → anonymous chat → reveal.
- **Invite flow**: an Applicant redeems an Invite; AI Vetting returns Approved or NeedsReview (never auto-reject); an Admin makes every rejection.
- **AI powers**: builds the Values Profile (conversational Onboarding); vets Applicants; scores compatibility and proposes Matches; writes Icebreakers; moderates Messages (LLM failure/timeout → Message is Withheld, sender retries; escalated Messages are delivered and reviewed afterwards); never forces a Reveal or exposes identity.
- **Reveal**: mutual Reveal Consent (withdrawable until it happens; irreversible after); offered once the Engagement Threshold is met (≥20 Messages total, ≥5 from each, ≥3 days). "Introduction runs out of time" was dropped — never decided.
- **Block/Report (post-Reveal)**: Block ends the Conversation, the pair is never rematched, the Reveal stays, both can still Report.
- **Six rules, not five** — the sixth is 18+ validation before Invite redemption (an under-18's Invite stays unused). The course page says "five rules"; plan (pending confirmation): present all six in DESIGN.md/TESTING.md rather than dropping one.
- **Delivery**: ceiling 9 (deployed MVP, live URL); chase 10 opportunistically. Deadline: start of December 2026; viva date TBD.
- **Team**: Parth builds (agent-driven implementation, Parth reviews each slice); Nevil, Tej, Vatsal get `ready-for-human` issues (test cases from the TESTING.md plan, rule-doc review, viva walkthrough notes) — to be created once those plans exist. All four must be able to explain any `file:line` → keep the MVP small, docs clean.
- **Stack**: FastAPI + React (Vite; no server-rendered HTML); pure domain core with ports/adapters as the one graded boundary; LLM behind a port with a fake adapter in tests; SQLite locally. Deployment: only hosts with persistent disk, else hosted Postgres behind a repository port. Local workflow must be PowerShell-native (no bash/WSL/Makefile).
- Vocabulary files populated: 18 terms across Access / Onboarding & vetting / Matching / Conversation & safety; six ambiguities flagged in `UBIQUITOUS_LANGUAGE.md` for Round 2.

## 2026-10-19 — grill-with-docs session, Round 2 decisions

- **Six rules final** (present all six everywhere; "6 of 6" in TESTING.md — the course's five plus the team-added age gate):
  1. **Invite-only access** — nobody gets an account without redeeming an Invite.
  2. **Vetting never rejects** — the AI outputs Approved or NeedsReview only; every rejection is an Admin decision.
  3. **Moderated delivery** — a Message reaches the other Member only after moderation passes; on failure/timeout it is Withheld and the sender retries; an Escalated message is delivered and reviewed afterwards by an Admin.
  4. **Consensual Reveal** — offered only once the Engagement Threshold is met; requires Reveal Consent from both; withdrawable until it happens; irreversible after.
  5. **Anonymity before Reveal** — the system never shows or sends a Member's real name, photo, or contact details to their Match outside a Reveal; identity is shown only as a Pseudonym plus the Values Profile.
  6. **Age gate** — 18+ validated before an Invite is redeemed; an under-18's Invite stays unused.
- Curated-only matching (no browsing/search) is a DESIGN.md constraint, not a numbered rule.
- **Ambiguities resolved** (winners in `UBIQUITOUS_LANGUAGE.md`): Match (not Introduction); Member at Approved Verdict (NeedsReview → Member on Admin approval); Block available any time; Admin-issued Invites (issuer modelled for later Member-issued); Admin reviews escalations; both Members must accept a Match (declines are permanent for that pair).
- **Anonymity contract**: pre-Reveal = Pseudonym + Values Profile; name/photos/contact hidden; photos exist only post-Reveal. Personal identifiers typed into Messages are detected by moderation → Escalated: delivered, Admin queue, audit log — never Withheld for this. Rule 5 governs what the system shows/sends, not what Members type.
- **MVP scope additions**: Report joins the Admin review queue; Admin invite issuance; seeded demo data; matching stays Admin-triggered. If time gets tight, trim in order: Engagement Threshold progress UI → Report UI → polish; never trim the Admin console or the Reveal.
- **Audit log**: minimal, append-only; events: invite redeemed, verdict, escalation, reveal, block, report. No analytics.
- **Fail-closed rule**: cost cap hit or LLM failure → Messages Withheld, vetting NeedsReview; never fail open.
- **Cold start**: seed the team + friends; hand Invites to classmates only once the MVP is stable.
- Still open: LLM provider + monthly cap (Parth to supply — left blank in Round 2); viva date; hours/week.

## 2026-10-19 — grill-with-docs Round 3 (Q11) decisions

- **LLM provider + cap**: still blank — deferred by agreement; build against the LLM port with the fake adapter, Parth swaps in the real adapter before the first LLM-backed slice. Due again at deployment.
- **Identifier detection is per Conversation, never global**: pre-Reveal, **Personal identifiers** in Messages are Escalated; after that pair's Reveal they stop being Escalated (normal safety moderation continues); a Reveal in one pair never relaxes detection in another.
- **The boundary (DESIGN.md)**: the LLM port is the cited boundary — the core owns the interface and the real adapter is wired at exactly one place. DESIGN.md must cite the port at its exact file:line plus that single wiring point, so "where does your core stop?" has one precise answer. Storage/repository is a secondary seam — mentioned, not cited.
- **Pseudonyms**: Member-chosen during Onboarding; platform-unique (case-insensitive); must pass the same identifier check as Messages (no real names, emails, phone numbers, handles) — a taken or identifier-like one is rejected and the Member picks another; fixed once set.
- New term: **Personal identifier**; Pseudonym definition tightened.
- Status: awaiting Parth's confirmation of the shared understanding (recap sent in chat); on confirmation, the definition phase closes and the build phase starts (spec → GitHub issues → first TDD slice).

## 2026-10-20 — Definition phase closed

Parth confirmed the shared-understanding recap. Ratified on top of Rounds 1–3:

- **Tag requirement corrected**: the viva needs **a pushed `project-final` tag** (the recap's "≥project-final tag" was wrong). Recorded in `../assumptions.md` and `DESIGN.md`.
- **Earlier decisions re-verified**: Pseudonym rules; Member timing (Approved at the verdict, NeedsReview on Admin approval); Match decline (never re-proposed); Block available any time (post-Reveal: Reveal stands, pair never rematched, both can still Report); under-18's Invite stays unused; Withheld + retry and Escalated delivered + reviewed by an Admin; Admin-issued Invites with an issuer for a later Member-issued extension; identifier detection per Conversation. All were already in the Round 2/3 entries and are now also in `UBIQUITOUS_LANGUAGE.md` and `GLOSSARY.md` definitions/relationships.
- **Conversation lifecycle**: a Member has at most one active Conversation at a time and is not proposed in new Match batches while it is active; a Conversation ends by a Block or after a completed Reveal, after which the Member can be proposed again.
- **Known limitation (MVP)**: no auto-expiry of inactive Conversations — recorded in `DESIGN.md`.
- **Demo pool**: because the Engagement Threshold needs ≥3 days, the seeded pool must be large enough that an Admin-triggered batch still produces Matches; seeded Conversations carry backdated Messages.
- **Clock port**: time comes from an injectable Clock port — a second secondary seam beside the repository port; Rule 4's 3-day threshold is testable without waiting, and seeds can backdate. The LLM port remains the cited boundary.
- **Rule docs**: `DESIGN.md` created with the six rules, the ratified decisions, the boundary, and the known limitation (citations land with the code); `TESTING.md` starts with the first slice.
- **Build phase starts**: spec → GitHub issues → first TDD slice (domain core).

## 2026-10-22 — Build phase approved; first-slice constraints

- **Graded decisions swapped**: headline #3 is now **the LLM port fails closed** — budget cap, timeout, or provider failure means Withheld for Messages and NeedsReview for Vetting, never fail open. Chosen because it is a product trade-off with real costs (delayed Messages, more Admin work) that Parth can defend in a minute. The **Clock port** is documented as a supporting decision under the LLM-boundary decision (testing aid, secondary seam), not a headline.
- **Rejected AI suggestion changed**: the primary entry is now the "contact details allowed in chat, only logged" recommendation (it would let Members bypass Reveal Consent and make Rule 5 untestable); the server-rendered HTML suggestion stays as a shorter secondary entry — stack already decided, client-side state suits the Reveal ceremony and chat UI, and server-rendered HTML would have been defensible at this scale.
- **First slice — Invite, age gate, Vetting verdict**:
  - Tests first: the failing tests are shown to Parth before any implementation.
  - The Vetting `Verdict` is an enum with only Approved and NeedsReview — Reject is unrepresentable in the type; the fake LLM adapter can only produce those two values.
  - Age gate runs before Invite redemption; a test proves an under-18's Invite stays unused.
  - The core imports nothing from FastAPI, the database, or any LLM SDK.
  - All commands run in PowerShell on Windows; no bash-only tooling.
  - Parth reviews and approves each slice before the next begins; tickets stay small enough to explain every file in one sitting.
