# Vaeil MVP — approved specification

## Problem statement and solution

Vaeil offers values-based matching with AI-assisted safety. Students and young professionals aged 18-28 need deliberate introductions based on values, with identity private until a mutual Reveal. Vaeil delivers one invite-only loop: Invite → Vetting → admission → structured-form Onboarding → curated Match → both accept → anonymous Conversation → consensual Reveal. The enforced age minimum is 18; 28 describes the audience, not an additional admission gate. Conversational LLM Onboarding is approved stretch scope, not an MVP dependency.

Target viva: December 5, 2026, confirmed; five build sessions per week. Capacity and date are confirmed; effort estimates are reviewed against actual velocity. Hosting budget is $0 and inference runs on the owner's laptop with no paid provider. Updated October 24 with the user's superseding free-stack, scope, team and sequencing decisions. T1-T6 child publication is approved; later children wait for the first velocity review, and the amended T1 seam is approved, with implementation gated on red-test review; no provisioning or purchase is authorized by this spec.

## User stories

1. As an Applicant, I redeem an Invite only when old enough and receive Vetting without automatic rejection.
2. As a NeedsReview Applicant, I await an Admin's admission decision.
3. As a Member, I build a Values Profile and fixed Pseudonym without publishing my private identity.
4. As a Member, I receive a curated Match that opens a Conversation only when both accept.
5. As a Member, I exchange moderated Messages and control my own Reveal Consent.
6. As a Member, I can Block or Report, including after a Reveal.
7. As an Admin, I issue Invites, trigger matching, and review admission, Escalated Message, and Report queues.
8. As a teammate, I can run, demonstrate, test, and explain the deployed product using accurate evidence.

## Six rules: behavior, domain seam, and viva check

All domain tests use the existing public domain API. The seams below describe behavior; new signatures and types require their later seam approval. HTTP/UI checks supplement rather than replace domain tests.

| Rule | Observable behavior | Domain seam under test | End-to-end viva check |
| --- | --- | --- | --- |
| 1. Invite-only access | No account without redeeming a valid, unused Invite. Issuer is retained; reuse or invalid redemption leaves state unchanged. | Existing Invite redemption plus proposed admission operation. | Try absent/invalid/reused Invites; show refusal, then successful single redemption and the resulting account. |
| 2. Vetting never rejects | Verdict can represent Approved or NeedsReview only. Approved admits the Applicant; NeedsReview requires Admin approval. Every rejection is an auditable Admin decision. Errors, timeouts, budget failures, and malformed model output yield NeedsReview. | Existing Verdict and Vetting wrapper plus admission transitions. | Show Approved admission, demo-configured adapter failure entering NeedsReview, and an audited Admin approve/reject action. |
| 3. Moderated delivery | Delivery follows moderation. Provider failure, timeout, or budget cap produces Withheld with retry feedback. Escalated Messages are delivered, queued for Admin review, and audited. After Reveal only identifier escalation stops; safety moderation continues. Block ends sending. | Proposed Message moderation/delivery operation using the LLM port and scanner. | Exchange a normal Message; enable demo-only adapter failure and show no recipient delivery; send an identifier pre-Reveal and show delivery plus escalation/audit evidence. |
| 4. Consensual Reveal | Offer Reveal only at ≥20 delivered Messages, ≥5 delivered by each Member, and ≥72 hours after the first delivered Message. Escalated counts; Withheld does not. Both consents are required and withdrawable before completion. Completed Reveal is irreversible and frees the active slot while chat stays open until Block. | Proposed Conversation eligibility and consent transitions, with timestamp-capable injected Clock. | Seed the 19/20, 4/5, and just-before/at-72-hours boundaries; show ineligible → eligible, unilateral consent insufficient, withdrawal, then bilateral completion. |
| 5. Anonymity before Reveal | A Match receives exactly Pseudonym and Values Profile before Reveal. Legal name, email, optional phone, and DOB never enter that view or serialization; no photo representation. Reveal state belongs to the Conversation, never the Member. Profile saves reject detected identifiers/self-name content. | Proposed pure Member projection, profile-write validation, and Conversation-isolation behavior. | Scan every projected/serialized view for private-field canaries. In the viva, Reveal A-B first, then Match A-C and verify C still sees the anonymous view. The pure isolation test need not simulate this active-slot sequence. Show a flagged profile save refused. |
| 6. Age gate | Check 18+ before consuming the Invite. Underage attempts leave it unused; future DOB is refused. A leap-day birthday reaches 18 on February 28 in a non-leap year. | Existing redemption operation with injected Clock. | Attempt underage redemption, confirm Invite remains unused, then redeem for an eligible Applicant; demonstrate birthday boundary fixtures. |

## Implementation decisions and scope

**Identity and Values Profile.** Private Member fields are legal name, email, optional phone, and DOB. The post-Reveal identity payload is legal name, email, and optional phone alongside Pseudonym and Values Profile; DOB is excluded. Photos have no representation anywhere in the MVP. The pre-Reveal allow-list remains exactly Pseudonym and Values Profile.

No earlier concrete schema exists in DESIGN or the glossary. Use relationship intent (choice), life stage (choice), one to five distinct interests and one to five distinct values from fixed lists for complete profiles, communication style (choice), pace and lifestyle (choice), and one optional `about` field capped at 280 characters. Every free-text field, including LLM-generated text, passes the shared identifier scanner and self-name check before storage; flagged saves are refused.

For the self-name check, tokenize the legal name and email local part on whitespace, dots, underscores, hyphens, and plus signs; NFKC-normalize and casefold; ignore tokens shorter than three characters. Refuse a Pseudonym whose normalized form contains any remaining token. Profile About uses whole-word mode over the same tokens; Pseudonyms use substring mode. Mark/market is accepted; Will/will is a known false positive. Existing Pseudonym format/reserved-name, normalization, uniqueness, and fixed-once rules remain.

**Conversation lifecycle.** Active means not Revealed and not Blocked. A completed Reveal frees the Member's one-active-Conversation slot and permits new proposals. The Revealed Conversation remains open for reading and sending until Block; identifier escalation stops there, safety moderation and Reporting continue. Block ends it and permanently excludes the pair. The pure identity projection depends on that Conversation's Reveal state, not on active-slot eligibility.

**Matching.** Matching is curated only and Admin-triggered. Domain compatibility and ranking are deterministic, based on structured fields; LLM re-ranking is out of the MVP. Match explanation text is dropped in working Plan B; ranking remains deterministic and values-only. Vetting and moderation still fail closed. Exclude declined/Blocked pairs and Members with an active Conversation. Both Members must accept; declines exclude the pair permanently. Accurately describe this as values-based matching with AI-assisted safety, rather than claiming the LLM ranks or selects pairs.

**Safety, Admin, and audit.** Block is available at any time. Post-Reveal disclosure is irreversible; Reporting remains available after Block. The Admin console includes Invite issuance, NeedsReview decisions, Escalated Messages, and Report queues. The minimal append-only audit log records invite redeemed, verdict, escalation, reveal, block, report, and every Admin approve/reject decision on admission and queue items. No analytics. Scan results retain reasons rather than copied identifiers/spans; future span retention needs a separate decision.

**Architecture and storage.** FastAPI backend and React/Vite frontend; pure domain core, owned LLM boundary with one adapter wiring point, Repository and Clock secondary seams. Add timestamp-capable Clock behavior without breaking age-gate dates. The Repository port has one implementation over SQLAlchemy Core with two connection URLs: SQLite by default for local runs/tests with no database install, PostgreSQL for deployment. One shared repository contract suite runs against both, covering concurrent normalized-Pseudonym uniqueness, rollback and append-only audit. Deployed data and server-side sessions must not depend on Render's ephemeral disk. PostgreSQL CI tests use a disposable database; production-Neon smoke checks use synthetic data and its free quota sparingly.

**Auth, deployment, and demo.** Email/password authentication uses a vetted password-hashing library or stdlib scrypt, not home-made cryptography. Use a server-side session in an HTTP-only SameSite cookie; seed one Admin account from environment configuration. Protected Member operations require admission; auth cannot bypass Invite redemption or Vetting/Admin approval.

Start the local walking skeleton after T1: it needs the identity view, not Conversation implementation. Use an in-memory adapter initially. Proposed deployment is one Render Free FastAPI service serving built React assets at the same origin, with Neon Free PostgreSQL; no separate frontend service or CORS setup. Do not provision without approval. Render's own free PostgreSQL is excluded because it expires after 30 days. SQLite stays the default local run with ≤5 PowerShell commands and no database installation. Deployed skeleton includes a health endpoint, first-request loading feedback, a database readiness probe/smoke check where connected, and a checklist to wake both service/database before the viva. In-memory demo fixtures remain non-durable until the repository increment. Free quotas and external database/API traffic can cause outages; this is a course-demo deployment, not a production-availability promise.

**Demo-only fault injection.** Proposed configuration name: `VAEIL_DEMO_LLM_FAILURE=1`, accepted only when the process is configured as `VAEIL_ENV=demo`; reject that configuration outside demo mode. Wire failure at the fake or real LLM adapter boundary, not a web route/UI control. It forces failure to demonstrate NeedsReview/Withheld (and matching fallback), never bypasses safety, and must be unavailable in production. DESIGN documents the name, restriction, and viva purpose.



## Testing and evaluation deliverables

Tests first through approved public seams: show the red run, implement small green cycles, then run targeted mutations and the purity guards. Pin the pre-Reveal view's exact two-field set and scan every projected/serialized view for private-field canaries. Test cross-Conversation isolation, profile-write refusal for Member/LLM text, atomic storage uniqueness, and UI/API behavior. Rule 5 remains partial during the upcoming domain work; do not claim full coverage from view tests alone. Current baseline: 122 tests, 3 of 6 rules domain-level, 0 of 6 end-to-end.

Deliver a live URL; README with ≤5 local application-run commands; synchronized UBIQUITOUS_LANGUAGE and GLOSSARY; DESIGN with six rules, three decisions, the LLM boundary/wiring citations and factual AI/human contributions; TESTING with real rule-to-test citations, honest gaps and one weak test. Include a per-rule viva walkthrough and push `project-final` before the viva. All four teammates must explain the cited code. Windows CI remains the normal check gate; no new agent tooling is part of this MVP spec.

## Out of scope

Gender/orientation compatibility, mobile/React Native, browsing/search/swiping, a second mode, Member-issued Invites, scheduled Matching, notifications, photos, payments, multiple Admins, analytics, fine-tuning, automatic expiry, perfect/general identity detection, and LLM re-ranking. Structured-form Onboarding is required. Conversational Onboarding, Icebreakers, progress UI, Report UI, polish and a second provider are stretch, with the user's removal order Icebreakers → conversational Onboarding → progress UI → Report UI → polish. Admin console, Reveal, Report handling and all six rules stay above the cut line.

## Approved scope reduction and review gates

Structured-form Onboarding uses the settled schema and identical write-time checks. Conversational Onboarding is the first stretch item to restore ahead of Icebreakers. Teammates may own bounded UI/fixture/viva/docs tickets, with Parth as reviewer; they must not modify domain core or audit implementation. Put the real adapter in place by November 28 at the latest for the confirmed December 5 viva, so real Rule 2/3 paths are rehearsed for at least a week. After Reveal and Admin console merge, checkpoint all six rules on the deployed URL using the current adapter and minimal synthetic fixtures; fix a broken required path and cut optional work before proceeding. Final laptop/tunnel failure rehearsal remains required later.

## Known limitations

- Gender/orientation are omitted: values-only Matching does not promise compatibility on those dimensions. Private future preferences must not expand public view types.
- Whole-word self-name checks refuse ordinary uses of a name such as Will; the error offers rephrasing.
- Local safety inference depends on laptop/tunnel uptime; bounded failures go to Withheld/NeedsReview while the deployed app remains available.

- Identifier/self-name checks are heuristic: unrecognized name forms, spelled-out numbers, novel obfuscations, and identifiers split across Messages can be missed; false positives occur.
- Fixed fields and write-time scans reduce free-text identity leaks but cannot rule out indirect details such as a rare workplace. Canary tests prove projection boundaries, not semantic anonymity of arbitrary text.
- One active, unrevealed/unblocked Conversation per Member limits availability. Reveal releases the slot while chat remains open; unrevealed inactive Conversations do not auto-expire.
- Deployed SQLite on Render Free is excluded; local SQLite and deployed PostgreSQL need the same contract evidence. Render/Neon free sleep and quotas can interrupt the demo, and Render advises against production use of free instances.
- Domain tests alone do not prove auth, persistence, transport privacy, or the deployed loop.

## Open questions

- T1 choice lists/types are approved in the seam document. Deterministic compatibility weights/tie-breaking require the T10 seam. Local runtime/model, accuracy bar and measured limits await the post-T1 feasibility note.
- Render/Neon provisioning and app-specific eligibility remain gates. Local-model runtime/model/accuracy/timeout/queue settings await measured feasibility and review.

## Confirmed working scope and local-model decision

Vaeil is final. Capacity **5 build sessions/week**; viva **5 December 2026, confirmed**. Feature freeze **28 November**; **29 November-4 December rehearsal/fixes only**. Work to optimistic Plan B; report slippage immediately after T1 and T2. Teammates accepted H1-H6, still unassigned.

Drop conversational Onboarding, re-ranking, Icebreakers, explanation text, progress UI, Report submission UI, polish and a second adapter unless velocity proves room. Keep all six rules, Admin console, Reveal and Report handling. Product copy is “values-based matching with AI-assisted safety”, reflecting the dropped explanations.

Replace Gemini/AI Studio and the daily counter with a laptop-served model behind the owned LLM port. Ollama/llama.cpp choice and CPU/Vulkan support await the **0.5-session feasibility note immediately after T1**, alongside T2/T3. No model integration before Parth reads it. The [feasibility brief](local-model-feasibility-brief.md) fixes model/licence/structured-output/tunnel research, measured >=30-call/model p95/concurrency/ten-minute thermal runs, approved accuracy bar and fallback proposal. T12 is re-estimated from findings; grade 9 is the contract, grade 10 requires model feasibility, uptime and consent.

Use an authenticated laptop proxy/tunnel, environment-held secret on every deployed request, fixed-enum validation and measured per-call timeout/concurrency/bounded queue. Slow/offline/busy/malformed output yields Withheld/NeedsReview; Render stays usable. Fake tests include prompt injection and failures. Messages show checking/retry feedback. Synthetic-only restriction is lifted for the local model; demo notice remains until consent/deletion plan. Fictional seed personas remain. Demo checklist includes plugged-in/performance power/no sleep/warmed model/tunnel and mid-demo fail-closed fallback.

Gender/orientation are out of scope and a known limitation: Matching is values-only. Future private match preferences belong outside public profile/view types. Complete profiles require 1-5 distinct frozenset selections per list; T10 enforces complete-profile Matching eligibility. Stable enum codes, frontend labels, trimmed NFKC About <=280 code points, controls refused. Pseudonym self-name uses substring; About whole-word. Mark/market is accepted; Will/will is a documented false positive with rephrase feedback. Revealed views preserve the public fields; pre-Reveal keeps exactly two, with frozen/slotted/redacted records and no private references, per the approved T1 seam.

Render/Neon accounts are Parth-owned. T4 adds teammates where free collaboration allows, password-manager credential sharing outside the repo, and a one-page redeploy-from-scratch recovery note. Provisioning remains approval-gated.

## T1 opaque privacy supporting decision — 25 October

Private identity and authorized-view fields use immutable slotted opaque PrivateText/PrivateDate, not native scalar subtypes or dataclasses. No implicit native operations, hashing, plain-value equality or generic copy/serialization; display formats redact. Constructors accept plain inputs and wrap them. One noisy unwrap method is pinned by an AST test to the authorized encoder, self-name token extraction and age gate. T5 persistence/T6 login extend the allowed list only in their own tickets. Exact anonymous/revealed field names and authorized JSON values stay unchanged. Deliberate extraction by code with access remains possible: this is an accident-prevention and reviewable boundary, not a sandbox. The whole-record-only alternative was rejected because extracted scalars still leaked through JSON/format/logging. This is one private field-type refinement, not a new product rule. Rule 5 stays partial.
