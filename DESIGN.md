# Design

Vaeil — values-based matching with AI-assisted safety for 18–28 students and young professionals. This file is part of the IT643 evaluation: it must match the code at `file:line`, and a claim the code does not back is graded as absent.

**Status: working draft.** Citations are added as each slice lands; the file is complete before the pushed `project-final` tag.

## The six rules

The course asks for five rules; the product has six — the five plus a team-added age gate. All six are presented here; `TESTING.md` tracks which ones have tests today.

1. **Invite-only access.** Nobody gets an account without redeeming an Invite. Invites are Admin-issued in the MVP; each Invite records its issuer, so Member-issued Invites can be added later without a breaking change.
2. **Vetting never rejects.** The AI's Vetting returns Approved or NeedsReview only. An Approved Applicant becomes a Member at the verdict; a NeedsReview Applicant becomes a Member when an Admin approves. Every rejection is an Admin decision; the AI never rejects.
3. **Moderated delivery.** Automated Delivered requires model approval and, before Reveal, no identifier flag. Before Reveal, model approval plus an identifier flag is Escalated: delivered, queued and audited. Withheld is not delivered and has a typed reason: technical failure, timeout, concurrency/queue exhaustion, unreachable runtime or malformed output allows retry; model NeedsReview instead queues Admin review, prevents same-text resend and shows under review. Admin release/discard are audited. After Reveal identifier escalation stops but safety moderation continues. No unchecked delivery.
4. **Consensual Reveal.** A Reveal is offered only once the Engagement Threshold is met: at least 20 delivered Messages, at least 5 delivered by each Member, and at least 72 hours since the first delivered Message, measured with the injected Clock. Escalated Messages count; Withheld Messages do not. Both Members must give Reveal Consent; either can withdraw until the Reveal happens; completed Reveal is irreversible. Reveal releases the active slot but chat stays open until Block.
5. **Anonymity before Reveal.** The system never shows or sends a Member's real name, photo, or contact details to their Match outside a Reveal. Identity is shown only as a Pseudonym plus the Values Profile; photos have no representation in the MVP. A Pseudonym is chosen by the Member during Onboarding, platform-unique (case-insensitive), must pass the same identifier check as Messages, and is fixed once set. Personal identifiers typed by Members are detected per Conversation — Escalated before that pair's Reveal, normal afterwards — and are delivered, reviewed by an Admin, and recorded in the audit log. Rule 5 constrains what the system shows and sends, not what Members type. Detection is heuristic: it routes suspicious text to Escalated but does not promise to catch every identifier — spelled-out numbers, novel obfuscation, or identifiers split across Messages can be missed, and a long numeric string can be a false positive. The system-side guarantee does not depend on detection.
6. **Age gate.** 18+ is validated before an Invite is redeemed; an under-18's Invite stays unused.

**Not a numbered rule, but binding:** matching is curated only — no browsing or search. An Admin triggers a batch; the domain computes deterministic compatibility and ranking from structured fields. LLM re-ranking and explanation text are dropped in working Plan B. Exclude declined/Blocked pairs and Members with an active Conversation. This is AI-assisted matchmaking, not LLM-selected or LLM-ranked Matches; an unqualified "AI-curated" claim would overstate that role.

## Decisions

The course asks for three design decisions. Each names the principle it applies, the `file:line` where it lives, and what it looked like before and why it changed. Citations are completed as the slices land; a later refactor is recorded here with the commit that shows the "before".

### 1. The domain core owns the LLM interface

- **Principle**: Dependency Inversion (SOLID) at the boundary (Lecture 23) — the core depends on an interface it owns, not on a provider SDK.
- **Where**: `src/vaeil/domain/vetting.py:17` (the port) + `_pending_` (the single place the real adapter is wired, in the adapter slice).
- **Before / why**: the straightforward version calls the provider client directly from the vetting and moderation flows. Rejected in the design interview — the core would depend on an SDK, tests would need the network, and failures could not fail closed. The port keeps the core testable with a fake adapter and turns every failure into Withheld (messages) or NeedsReview (vetting).
- **Supporting decision — time is a port**: the existing Clock (`src/vaeil/domain/clock.py:7`) supplies a date for the age gate. The approved 72-hour threshold needs a planned timestamp-capable contract; it is not implemented yet. Injected timestamps will permit exact boundary tests and backdated demo Messages. Clock remains a secondary seam, not the graded boundary.

### 2. Anonymity is enforced per Conversation, not globally

- **Principle**: information hiding — Reveal state and identifier detection are scoped to the pair, never to a global Member flag, so one Reveal cannot relax any other Conversation.
- **Where**: `src/vaeil/domain/member.py:28` and `src/vaeil/domain/member.py:89` supply the pair-context projection seam; `src/vaeil/domain/conversation.py:36` and `:69` supply T2 lifecycle/state authority in memory.
- **Before / why**: the first recommendation was to log contact details typed before a Reveal. Rejected because logging lets two Members bypass Reveal Consent and makes Rule 5 untestable. Changed to identifier detection that Escalates the Message (still delivered, Admin-reviewed, audited), then scoped per Conversation so a Reveal only relaxes its own pair.

#### Supporting decision: opaque private values and the extraction boundary

- **Alternative considered:** ban whole-record serialization only. Rejected after read-only probes and red tests showed extracted string scalars still leak through `json.dumps`, native formatting, f-strings and logging. A record-only ban did not cover the accidental scalar path.
- **Chosen boundary:** private text/date fields use immutable, slotted, non-native, non-dataclass `PrivateText`/`PrivateDate` (`src/vaeil/domain/privacy.py:35`, `:75`, `:80`). Rendering always redacts; equality is same-private-type only; values are unhashable because no private-value key API is needed. Pickle/reduction, copying, asdict and generic JSON refuse export. T5 supplies explicit persistence mapping; T6 adds only its approved password verifier.
- **Cost:** one field-type refinement on MemberIdentity and authorized views; constructors still accept plain inputs and wrap them. Exact anonymous/revealed field names and the explicit authorized JSON payload do not change. The age gate receives a raw date only through the noisy method.

**Rule 5 system-side boundary:** `UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE` may be loaded/called only in these production functions:

| First actual call (`file:line`) | Function | Purpose |
| --- | --- | --- |
| `src/vaeil/domain/invite.py:54` | `redeem_invite` | Birth-date age comparison before Invite consumption. |
| `src/vaeil/domain/member.py:125` | `serialize_member_view` | Explicit Reveal/owner payload only. |
| `src/vaeil/domain/self_name.py:14` | `contains_self_name` | Own legal-name and email-local tokens only. |
| `src/vaeil/adapters/persistence.py:89` | `encode_private_value` | Explicit private identity/date/session-digest storage mapping only. |
| `src/vaeil/adapters/authentication.py:48` | `verify_password` | Stored encoded-password verification only. |

The exact five-function set is pinned by `tests/test_private_unwrap_boundary.py:62`; direct/alias/getattr violations are rejected by `:76`, unauthorized mapper sites by `:89`, login sites by `:100`. T5 adds its approved mapper; T6 adds only the approved verifier. All other code keeps opaque fields. PreRevealMemberView contains only Pseudonym/Values Profile, never wrappers, Member or identity references; its shape and graph tests pin that boundary. Authorized JSON encoding is explicit, never recursive dataclass serialization.

**Residual limit:** deliberate extraction by code already holding a value is not prevented. Opaque values prevent accidental native conversion; the AST test makes extraction sites greppable/reviewable, not a runtime sandbox or taint analysis. Allowed functions necessarily handle plain values and must not log them. Review still matters.

### 3. Safety-related LLM calls fail closed

- **Principle**: boundary (Lecture 23) — Vetting and moderation define safe failure modes; model failure cannot approve an Applicant or deliver an unchecked Message. Matching has the separate non-safety fallback below.
- **Where**: `src/vaeil/domain/vetting.py:23` — the `vet` wrapper's `except Exception` fallback at `:27` and its `isinstance` guard at `:30` are the actual fail-closed checks.
- **Before / why**: the default failure behaviour is to fall back — deliver the Message anyway, or approve the Applicant. Rejected: unchecked delivery breaks Rule 3 and auto-approval breaks Rule 2. Changed to explicit domain states — timeout, concurrency or queue exhaustion, unreachable runtime, or malformed output means Withheld for Messages and NeedsReview for Vetting, never fail open. The cost is real (legitimate Messages are delayed, and more work lands on the Admin), and that is the point: a human reviews instead of an unchecked model deciding.

Also ratified and binding:

- **Match acceptance is bilateral.** Both Members must accept a proposed Match before its Conversation opens; a declined Match opens no Conversation and the pair is never proposed again.
- **One active Conversation per Member.** Active means not Revealed and not Blocked. Reveal frees the slot for new Matches; the Revealed Conversation remains open for reading/sending until Block. Identifier escalation stops only for that pair, while safety moderation and Reporting continue. The Rule 5 viva scenario runs A-B Reveal first, then A-C Match; pure projection-isolation tests need no active-slot sequence.
- **Block is available at any time.** It ends the Conversation and prevents any future Match between the pair; after a Reveal the Reveal stands and both Members can still Report.
- **The audit log is minimal and append-only**: invite redeemed, verdict, escalation, reveal, block, report, and Admin approve/reject decisions on admissions and queue items. No analytics. Every human rejection must be auditable.
- **The MVP is Admin-issued Invites only.** The Invite model carries an issuer so Member-issued Invites remain a later, non-breaking extension.

## Boundary

**The LLM port is the one boundary** — where the domain core stops and the outside world begins, and the dependency it protects the domain from. The port's interface is owned by the domain at `src/vaeil/domain/vetting.py:17`; the real adapter will be wired at exactly one place when the adapter slice lands. At submission this section cites that single wiring point too, so "where does your core stop?" has one precise answer.

Storage sits behind a repository port and time behind a Clock port — secondary seams, mentioned but not cited as the boundary.

## Free-stack persistence and deployment

Hosting budget is $0. PostgreSQL is the deployed database; SQLite stays the default local/test connection URL so the five-command PowerShell run needs no database install. One SQLAlchemy Core repository implementation and one contract suite must work against both databases, including concurrent normalized-Pseudonym uniqueness, rollback and append-only audit. Use an isolated PostgreSQL service for CI contracts rather than spending the production free quota on every run. Render's ephemeral filesystem cannot hold deployed SQLite or durable sessions.

Free-only stack approved10November and the fictional skeleton is deployed: Render Free FastAPI serves built React assets and relative API routes from one origin; Neon Free stores PostgreSQL data. No separate frontend deployment or CORS configuration. Exclude Render's expiring free Postgres. The deployed skeleton needs health/readiness checks, first-request loading feedback, and a checklist to wake the app and database before the viva. Cold starts, quota exhaustion, and external-traffic suspension can cause downtime; Render discourages production use of its free instances. This is a course-demo candidate, not an availability guarantee. Current official-source limits and unresolved app-specific Terms/AUP eligibility are in `docs/research/free-hosting-verification-2026-10-24.md`.

## AI use

- **T5 Codex work:** implemented the approved repository/transaction seam, shared SQLAlchemy Core mapping, database constraints/guards, contract and mutation tests, disposable PostgreSQL CI, and documentation. Independent Standards/Spec agents reviewed the diff; their findings were fixed. Parth approved the seam and exact mapper site; Parth authorized the integration/merge task; no separate human line-by-line code review is claimed. No real product LLM or teammate implementation is implied.

- **Tools used**: OpenCode agents and the repository's engineering skills for the original design interview, vocabulary, first-slice tests and implementation. Codex continued from the recovered OpenCode session using terminal commands, file patches, and the gh CLI: it implemented identifier scanning and Pseudonym validation, added regression and mutation checks, ran independent Standards/Spec reviews, fixed scanner performance, maintained docs/logs, and added the approved Windows CI and agent-workflow checks. These are development tools; they are separate from the product's future real LLM adapter.
- **Human decisions and review**: Parth set the product scope and stack, made the safety/privacy policy decisions, approved public test seams, requested stronger boundary and failure tests and mutation evidence, reviewed the slice outputs, and authorized the merges. Agents prepared implementation, tests, documentation, and review reports; Parth remained the product decision-maker and human reviewer. All four team members must be able to explain the delivered code and its evidence at the viva.
- **In the product**: MVP LLM uses are Vetting and safety moderation through a laptop-served model. Explanation text is dropped in working Plan B. Ranking and identifier scans are deterministic. Structured-form Onboarding is the MVP; conversational Onboarding, Icebreakers and a second provider are stretch. The LLM never rejects an Applicant, forces Reveal, or bypasses privacy boundaries.
- **One rejected suggestion (primary)**: allowing contact details in chat and merely logging them. The AI recommended logging as a light-touch safety measure; rejected because logging enforces nothing — two Members could exchange numbers before a Reveal and bypass Reveal Consent, and Rule 5 would become untestable. Replaced with identifier detection that Escalates the Message: it is still delivered, but an Admin reviews it, it is audited, and Reveal remains the only route to identity.
- **Also rejected (secondary)**: a server-rendered HTML app. The stack was already decided (FastAPI + React/Vite), the team was comfortable with it, and the Reveal ceremony and chat UI benefit from client-side state. Server-rendered HTML would also have been defensible for a project this small — this was a fit choice, not a technical verdict.

## Values Profile write policy (implemented at the pure domain seam)

No earlier concrete schema was defined. The approved Values Profile fields are relationship intent (choice), life stage (choice), 1-5 distinct interests and 1-5 distinct values from fixed lists for complete profiles, communication style (choice), pace and lifestyle (choice), and at most one `about` field capped at 280 characters. Choice/list vocabularies and the amended T1 seam are approved; red-test review precedes implementation. Every free-text field, including LLM-generated text, passes the shared scanner and self-name check before storage; flagged saves are refused.

Private Member fields are legal name, email, optional phone, and DOB; none belongs in a pre-Reveal view. The post-Reveal identity payload is legal name, email, optional phone, not DOB. No photos exist in the MVP. The self-name check splits legal name and email local part on whitespace, dots, underscores, hyphens, and plus signs, applies NFKC and casefold, ignores tokens shorter than 3 characters, and refuses a normalized Pseudonym containing any remaining token. About uses whole-word mode over the same tokens; Mark/market is accepted, Will/will is a known false positive with safe rephrase feedback. This is not general name detection. Auth will use vetted password hashing or stdlib scrypt and server-side sessions in an HTTP-only SameSite cookie; one Admin is seeded from environment configuration.

These checks are heuristic: they can miss a name in an unrecognized form, novel obfuscation, or indirect identifying details such as a rare workplace. They do not establish general name detection. Explicit pre-Reveal projection and canary tests cover the current pure view/serialization seams. The pure factory and projection are implemented; transport/admission/moderation integration is pending, so Rule 5 remains partial.



## Matching fallback and demo faults (approved, not implemented)

Deterministic values-only domain ranking is authoritative; LLM re-ranking and explanation text are dropped in working Plan B. Model availability cannot change ranking or admit an ineligible pair. Matching is not a safety path: this does not relax Vetting's NeedsReview or moderation's Withheld behavior. Score weights and stable tie-breaking remain to be specified before implementation.

Planned demo-only configuration: `VAEIL_DEMO_LLM_FAILURE=1` is accepted only with `VAEIL_ENV=demo`; configuration outside demo mode must be refused. It injects failure at fake/real adapter wiring for reproducible Rule 2/3 viva checks. Matching ranking stays deterministic; explanation text is out of working scope. There is no web UI or API toggle and no production activation path; this is not a bypass or a production backdoor. No product implementation is claimed here.

Parth approved structured-form Onboarding as MVP scope using the same schema and save checks. Conversational Onboarding is the first stretch item to restore; LLM re-ranking is next, ahead of Icebreakers. The removal order remains Icebreakers, conversational Onboarding, threshold-progress UI, Report UI, polish. Admin console, Reveal, Report handling, and all six rules stay required.

## Known limitations (MVP)

- Deliberate private extraction by code with access is not prevented: opaque values reduce accidents and an exact AST allowlist makes unwrap sites reviewable. This is not a sandbox or full taint analysis.

- Gender and orientation are omitted; Matching is values-only, without a compatibility claim for those dimensions.
- About whole-word self-name checks reject ordinary words such as “will” for Will; safe errors invite rephrasing.
- Laptop/tunnel availability constrains safety-model responsiveness; offline/busy/slow calls fail closed while the app stays usable.

## Out of scope

Gender/orientation compatibility and all Plan B cuts below. Future private preferences remain outside public profile/view types.

## Known detection limitations


### Slice 2 detection and Pseudonym policy

**When in doubt, flag.** A false positive costs the Admin a queue item; a false negative can undermine Rule 5, so the cost asymmetry favours flagging. Detection is a safety net; the pre-Reveal display boundary must independently prevent system disclosure. T1 implements the pure allow-list boundary; delivery is still owned by the later moderation slice.

- `src/vaeil/domain/identifiers.py:32` normalizes input with NFKC and converts Unicode decimal digits before scanning. `MIN_PHONE_DIGITS = 10` is the threshold for a run after stripping whitespace, parentheses, dots, plus signs, and hyphens; 9 digits stay clean and 10 or more flag, with no upper limit. Numeric runs embedded in a Pseudonym also flag.
- Reason order is EMAIL, PHONE, HANDLE, OBFUSCATED_EMAIL, URL. Handles include `@name`, `insta: name`, `my ig is name`, and Instagram profile links. Web links, including bare domains, produce URL; Instagram profile links produce both HANDLE and URL. Email addresses alone do not additionally produce URL. Supported obfuscation includes plain, bracketed, and parenthesized `at`, plus `dot`/`d0t`, ignoring case.
- The immutable scan result stores only ordered reasons, never matched text or spans. Keeping another copy of identifiers in the audit log or Admin queue is deliberately avoided. Any later span-retention requirement belongs to the moderation slice.
- Pseudonyms are NFKC-normalized and trimmed for display, then casefolded for uniqueness. They contain 3-20 Unicode letters or decimal digits, underscore or hyphen, start with a letter, and cannot be reserved staff names (`admin`, `moderator`, `system`, `vaeil`, `support`, case-insensitively). Named constants live in `src/vaeil/domain/pseudonym.py:10`.
- The in-memory directory is only the domain seam. When the repository lands, uniqueness must be enforced atomically with a unique index on the normalized value; checking then inserting without that constraint races during concurrent signups. The current directory does not enforce platform-wide or cross-process uniqueness.
- General names are not detected. The owner-specific check refuses known name/email tokens; another person's name, ignored short tokens and unfamiliar forms can still pass. Spelled-out numbers, novel obfuscation, identifiers split across Messages, and numeric false positives remain known limits. Rule 5 stays partial until API/UI display, durable Conversation-state authority and moderation integration are proven.

- No auto-expiry of inactive Conversations.
- Identifier detection is heuristic: spelled-out numbers, novel obfuscation, and identifiers split across Messages can be missed; long numeric strings can be false positives.

## Evidence

`file:line` citations land as slices land: the six rules in `TESTING.md`'s rule table, and the three decisions plus the boundary here. Merged slice 1 supports decisions 1 and 3 through the Vetting port and fail-closed wrapper. Merged slice 2 adds identifier scanning and Pseudonym claims, covering part of Rule 5. Pair-projection isolation is tested in T1. T2 now supplies in-memory Conversation lifecycle/state authority; the real adapter, Rules 3 and 4, and API/UI privacy remain pending. Current coverage stays 3 of 6 rules domain-level, 0 of 6 end-to-end; Rule 5 is partial.

## Confirmed working scope and local-model decision

Vaeil is final. Capacity **5 build sessions/week**; viva **5 December 2026, confirmed**. Feature freeze **28 November**; **29 November-4 December rehearsal/fixes only**. Work to optimistic Plan B; report slippage immediately after T1 and T2. Teammates accepted H1-H6, still unassigned.

Drop conversational Onboarding, re-ranking, Icebreakers, explanation text, progress UI, Report submission UI, polish and a second adapter unless velocity proves room. Keep all six rules, Admin console, Reveal and Report handling. Product copy is “values-based matching with AI-assisted safety”, reflecting the dropped explanations.

Replace Gemini/AI Studio and the daily counter with a laptop-served model behind the owned LLM port. The original post-T1 feasibility gate is complete for native Ollama CPU/Vulkan timings (27 October report); accuracy/final model selection remain unmeasured. Under the approved7November human-review baseline, T12 is optional, not a T3 blocker. No model integration before Parth reads it. The [feasibility brief](docs/specs/local-model-feasibility-brief.md) fixes model/licence/structured-output/tunnel research, measured >=30-call/model p95/concurrency/ten-minute thermal runs, approved accuracy bar and fallback proposal. T12 is re-estimated from findings; grade 9 is the contract, grade 10 requires model feasibility, uptime and consent.

Use an authenticated laptop proxy/tunnel, environment-held secret on every deployed request, fixed-enum validation and measured per-call timeout/concurrency/bounded queue. Slow/offline/busy/malformed output yields Withheld/NeedsReview; Render stays usable. Fake tests include prompt injection and failures. Messages show checking/retry feedback. Synthetic-only restriction is lifted for the local model; demo notice remains until consent/deletion plan. Fictional seed personas remain. Demo checklist includes plugged-in/performance power/no sleep/warmed model/tunnel and mid-demo fail-closed fallback.

Gender/orientation are out of scope and a known limitation: Matching is values-only. Future private match preferences belong outside public profile/view types. Complete profiles require 1-5 distinct frozenset selections per list; T10 enforces complete-profile Matching eligibility. Stable enum codes, frontend labels, trimmed NFKC About <=280 code points, controls refused. Pseudonym self-name uses substring; About whole-word. Mark/market is accepted; Will/will is a documented false positive with rephrase feedback. Revealed views preserve the public fields; pre-Reveal keeps exactly two, with frozen/slotted/redacted records and no private references, per the approved T1 seam.

Render/Neon accounts are owner-operated. On11November Parth deferred collaborator invitations and password-manager storage. T4 supplies a one-page redeploy-from-scratch recovery note; the owner-led configuration restoration/redeploy was exercised. Do not imply teammate access or independent recovery. Healthy/outage/recovery smoke passed; actual Render spin-down/platform loader and live RAM measurement remain unproven. Owner confirmed password rotation on12November, and public readiness passed afterward; no private URL belongs in docs.

## 26 October approved moderation outcomes and tunnel constraints

Model-flagged Withheld is not an Escalated delivery or a technical retry: it stays under review, cannot be resent as the same text, and requires an audited Admin release/discard. Technical failures remain retry-friendly. T7 pins the outcome/reason matrix and T9 includes this Admin queue. The application-note decision below resolves the former vetting-input question; T6 implements the note-only admission path; the deployed service still runs the earlier T4 runtime.

No owned Cloudflare domain: named Tunnel is excluded. Candidate is ngrok Free assigned dev domain, only during rehearsals/viva. Dashboard shows $0 of $5 and 7 March 2027 expiry; whether this means unused credit and the endpoint hourly cost await the Free credit breakdown, not an assumption of $5 available. T12 must budget active rehearsal/viva hours plus margin against confirmed credit. If unaffordable, propose the all-local demo or Quick Tunnel (changing URL requires updating Render environment config and rechecking authentication during rehearsal). Nothing provisioned.

## 27 October measured runtime evidence

Native Windows Ollama0.40.11 completed the authorized CPU and Vulkan timing protocols on the actual laptop; the integrated Radeon device was discovered and offload verified with process-local OLLAMA_IGPU_ENABLE=1. All three candidates met the short-call latency/failure bars on both paths. The [report](docs/research/local-model-runtime-results-2026-10-27.md) separates client/load/first-token timings, concurrent calls, ten-minute load and unmeasured safety accuracy. CPU is a sufficient runtime recommendation; final model choice still depends on the frozen accuracy gate, not speed alone. No production LLM adapter or LLM-related unwrap site exists. T6 separately adds the approved password-verifier unwrap.

Codex prepared the reproducible client, installed/pulled only the authorized runtime/models, measured and preserved synthetic evidence, and stopped the owned servers. Parth selected candidates and acceptance bars, authorized the work, changed the power setting and approved labels. Required independent label-review coverage has not been recorded; no completed teammate review is claimed. Proposed8-second end-to-end deadline/cap1/queue2 remain T12 review items, not adopted settings. Short fixed inputs/native API measurements do not establish arbitrary-length or OpenAI-compatible transport behavior. No tunnel/account/paid service was provisioned.

## Application note and fallback decision — 7 November

T6 validates a required 20–500-code-point application note after trim and NFKC, without control characters or truncation. Age precedes Invite consumption; scanner and whole-word self-name checks precede save/model. Vetting receives only that note, no identity, DOB, Invite code or wrapped fields. Refused contact content uses a remove-contact-details message without echoing input. The stored note is untrusted, Admin-visible for NeedsReview, excluded from all Match views and included in canary tests. Model output remains the fixed Approved/NeedsReview enum; every failure or approved unsupported-language policy hit is NeedsReview, all Admin decisions audited. Policy lives in `src/vaeil/domain/admission.py:19`/:32; the only T6 extraction addition is the approved password verifier above.

The accuracy deadline passed on 1 November. A rules-first human-review baseline is proposed in docs/audit/schedule-recovery-2026-11-07.md. A scanner-clean note/message is not by itself a safety approval. Manual message review needs an explicit submission route and audited release; this proposal must not quietly turn technical Withheld into model-approved delivery. Local inference is optional and may only tighten decisions. No real-model accuracy or unsupported-language policy is claimed.

### Human-review baseline approval — 7 November

Parth approved the reduced schedule and manual-review baseline: model-unavailable Applicants enter NeedsReview; technical-Withheld senders may explicitly submit for Admin review. No Message is delivered before an audited human release; pre-Reveal identifier flags retain escalation. Model-flagged content remains under review/no same-text resend; any optional model can only tighten decisions. This is a planned T7/T9 path, not an automatic rules-only safety claim or an implemented feature. The spec records the controlling behavior.

## T2 lifecycle/state authority

`src/vaeil/domain/conversation.py:36` is a frozen/slotted pair-state snapshot. `:54` defines active as unrevealed and unblocked; `:58` keeps Revealed chat open until Block; `:62` disables identifier escalation only for a Revealed pair. `:65` creates T1's existing projection context, without copying identity or changing its allow-list. `ConversationDirectory` at :69 owns in-memory active-slot/permanent-pair checks; `open` :73 follows bilateral Match acceptance in later wiring. `restore` :87 is trusted fixture/persistence input, checks monotonic history, and must not become an unconditional Member-facing Reveal route. T8 still owns consent/threshold enforcement. Shared placement checks :101 run before either write; `block` :92 requires a participant and preserves Reveal. No new clock read, framework dependency, LLM call or private unwrap site. T5 applies the same policy inside a database transaction; the original in-memory directory itself is not cross-process safe. No auto-expiry or message-delivery implementation is implied.

T2 tests were written/run red before their corresponding green cycles; projection regressions then verified the existing T1 behavior using directory contexts. The agent implemented/tested the approved seam, ran mutations and independent Standards/Spec reviews; Parth chose the behavior/interfaces and reviews the PR before merge. Those are distinct contributions. Rule 5 remains partial.

## T3 synthetic HTTP/display increment

`src/vaeil/web.py:38` creates the app outside the pure domain. The fixed fictional fixture at:25 passes through existing `project_member_for_viewer` and explicit `serialize_member_view` in the handler at:58; it never sends Member/identity records to framework serialization. The HTTP route rejects all query parameters and exposes no arbitrary subject/viewer/Reveal input. Health at:65, root build/setup response at:76, and mounted build assets share one origin. There is no broad SPA fallback swallowing unknown API paths. The synthetic public route is not authorization and must not later accept real records without T6's access checks. No new unwrap site.

`frontend/src/main.tsx` fetches the relative endpoint, validates its anonymous shape, renders approved fields only as React text, and reports loading/HTTP/malformed-data failure with retry. Display labels live in the frontend, stable codes stay in the domain. The demo-only notice and missing-build message make its limitations visible. A fictional transport canary check is now proven; T6 auth/admission is implemented but undeployed; pair-authorized display and moderation remain pending; T5 implements storage separately. Rule5 partial. The agent wrote red endpoint/browser tests and implementation, configured build/typecheck/Windows browser checks; Parth approved the seam, scope and human-review baseline and reviews the resulting PR.

## T5 persistence boundary and tradeoffs

`src/vaeil/domain/repository.py:78` owns UnitOfWork; :104 owns Repository. `src/vaeil/adapters/persistence.py:325` opens one SQLAlchemy Core implementation over either URL (SQLite default). Explicit commit is terminal; errors make the unit rollback-only (:272/:292), and context exit rolls back uncommitted work (:308). Unique normalized Pseudonyms use a database index rather than an existence pre-check. Candidate policy is shared at `pseudonym.py:33`; Conversation policy at `conversation.py:101`. No database/framework dependency enters the domain.

SQLite BEGIN IMMEDIATE and a PostgreSQL transaction-scoped advisory lock serialize repository transactions across connections/processes. This trades throughput for simple atomic active-slot/monotonic-state guarantees in the small demo. The unique index protects ownership independently. Audit UPDATE/DELETE guards are database DDL; a SQLite duplicate-ID insert guard also refuses INSERT OR REPLACE, and PostgreSQL rejects TRUNCATE. Guard removal by a privileged owner is outside this protection. 

Private identity values and session digests leave wrappers only through the approved mapper. Explicit fields become internal bound parameters, and reconstructed records restore wrappers. SQL echo is off, parameters hidden even at INFO logging, port errors suppress driver/configuration details. Rows never leave the adapter; no pickle/asdict fallback. StoredSession persists caller-supplied expiry; T6 owns tokens/login/cookies/expiry enforcement. AuditEvent holds typed metadata/reason codes rather than spans or arbitrary text; later workflows must actually emit required events. Storage does not implement those decisions.

An isolated fictional Neon record survived a Render restart on14November (docs/audit/t5-deployed-survival-2026-11-14.md). This is infrastructure evidence; the fictional endpoint still does not use product repositories, and no six-rule E2E completion is claimed. SQLite must not become the deployed database on Render ephemeral storage.
## T4 readiness — implemented diagnostic, deployment incomplete

`src/vaeil/adapters/readiness.py:30` is an infrastructure-only dependency: minimal-env worker with DSN off argv,10-second postspawn timeout (approved11November),30-second hashed-key cache and nonqueued lock. `database_probe.py:13` uses verify-full with certifi roots, read-only SELECT1 and closed resources; failures produce generic unavailable without copied exceptions. Windows direct base interpreter-I-Splusvenvsite avoids venv-launcher orphaning and global dependency precedence; synthetic PID regression verifies actual worker reaped. No domain/unwrap change. `/api/health` and synthetic demo remain independent. Docker supplies explicit VAEIL_FRONTEND_DIR so wheel installation does not mislocate assets. Container CI and live cold-start/free-plan/Neon proof are separate; do not claim persistence from readiness. The fictional demo is deployed; real database readiness, outage isolation and owner-led recovery smoke passed. Owner rotation is confirmed. Actual host spin-down/platform-loader capture remains unverified, and live RAM graphs are unavailable on Free; these limitations were accepted for the T4 merge.




## T6 application, authentication and privacy

`src/vaeil/application/admission.py:69` coordinates existing policies and transactions. A private application command (:19) contains wrapped identity, note and encoded credentials, never a model-ready identity dump. Apply (:79) checks age and real Invite availability before note-only Vetting; the final transaction consumes the Invite, creates the principal/application and appends typed audit events together. The model call holds no write transaction. Admin decisions (:150) re-read authority and use terminal compare-and-set plus an audit in one transaction. HumanReviewModel (`src/vaeil/runtime.py:28`) always yields NeedsReview; there is no HTTP/environment auto-approval switch. Model Verdict still cannot represent Reject; human AdmissionDecision/AdmissionStatus are separate types.

Admitted principals and normalized private Onboarding drafts are separate from existing complete Member records. This preserves admission-before-Onboarding and complete-profile invariants. `src/vaeil/domain/profile.py:150` retains the complete factory, sharing ordered validation with partial drafts (:176). A draft candidate name is not reserved; first completion uses T5's unique index, so a taken name refuses atomically and can be retried. Later profile updates retain identity/Pseudonym. Drafts never become Match views; T10 still owns complete-profile Matching eligibility.

`src/vaeil/adapters/authentication.py:34` uses stdlib scrypt with fresh16-byte salts, versioned encoding,N131072/r8/p1/dklen32 and constant-time verification (:42). [OWASP's current scrypt guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) supplies the parameter basis. One process-local worker and no queue bound128MiB-class KDF allocations; busy requests fail closed and are retryable. Passwords are12–128Unicode code points with no composition rule or normalization. Transient request passwords/raw Set-Cookie tokens are never persisted or JSON-encoded; stored hashes/token digests are opaque. Hash/token/identity diagnostics are redacted. The exact fifth extractor is scoped above; deliberate access by trusted code remains outside the accident boundary.

Sessions (:101/:119/:129 in the application module) use a cryptographic token source, SHA-256 stored digests and absolute24-hour expiry through Clock.now. HTTP (`src/vaeil/http_admission.py:48`) rejects missing/cross-site Origin on mutations; cookies are HttpOnly/SameSite=Lax,Secure on HTTPS,host-only andPath=/. Actor IDs/roles come from sessions and current storage, not body fields; unknown fields are refused. Explicit own encoding and note-only Admin DTOs avoid generic private serialization; fixed errors carry safe rephrase guidance. Minimal registration/session React UI never stores a token in localStorage and only renders fixed status/error strings. Admin console/profile form are later UI tasks.

Runtime composition is lazy (`src/vaeil/runtime.py:33`): failed authentication storage does not stop health/anonymous demo. One Admin can be seeded only from both environment credentials, through the same hasher; no default login or public seed/model switch. SQLite remains the local default; remote PostgreSQL now forces verify-full and certifi roots, including when a URL asks to disable TLS. Disposable loopback contract databases remain local. T6 is not yet deployed. Hosting/secret handling and demo-only notices remain as above.

**Factual AI contribution:** Codex wrote the approved T6 types/ports, transactions, API/UI and red/green/mutation checks. Independent review follows implementation. Parth approved the seam/security settings and five-function extraction boundary; final feature review remains his decision. Teammates are open to H4/H5/H6 ownership proposals; no implementation/hours/assignments are claimed. No real model was run, and no new agent tooling was added. Request/profile free text remains heuristic: names in unrecognized forms or indirect details can leak if typed; the note-only port prevents structural identity copies, not all personal content inside the note. Registration retains the demo-only warning pending consent/deletion planning.

Password verification releases the repository transaction before the bounded scrypt operation, then rechecks the stored credential hash before creating a session. Remote PostgreSQL forces certificate/hostname verification and bounds connect, individual statements and lock waits to two seconds; these are per-operation limits, not an end-to-end request SLA. Normalized-email conflicts return a safe409 and roll back Invite consumption.
