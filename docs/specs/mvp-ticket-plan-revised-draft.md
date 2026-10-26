# Approved six-week MVP plan — staged publication

Parent: https://github.com/Diffusity/vaeil/issues/7. This replaces the earlier draft. T1 merged via PR #14 (`4f9ca80`); T1-T6 are published. T7-T13 and H1-H6 wait for the benchmark-informed velocity review. The label set/rubric needs review before any model run. Under the latest instruction, T2/T3 start after the benchmark report. No product code or new agent tooling is added by this plan.

Published: T1 [#8](https://github.com/Diffusity/vaeil/issues/8), T2 [#9](https://github.com/Diffusity/vaeil/issues/9), T3 [#10](https://github.com/Diffusity/vaeil/issues/10), T4 [#11](https://github.com/Diffusity/vaeil/issues/11), T5 [#12](https://github.com/Diffusity/vaeil/issues/12), T6 [#13](https://github.com/Diffusity/vaeil/issues/13). All are unassigned; implementation gates still apply.

## Estimate basis and safety gates

- A session is a provisional unit of 2-3 focused build/test/review hours. Viva target is **5 December 2026, confirmed**; capacity is five build sessions/week. Estimates include tests-first, targeted mutations, small review PRs, documentation, and Parth's integration review, not external approval delays.
- The Parth/agent table assumes the teammate UI/fixture/docs work below is delegated. It does not assume teammates implement domain or audit code. Their effort is counted separately, not subtracted twice.
- Provisioning Render/Neon still requires approval. Runtime/model/accuracy selection and integration wait for the post-T1 measured feasibility note. The local-model synthetic-only restriction is lifted; retain the demo notice until consent/deletion planning. No paid fallback.
- T1 choices/types are approved; red tests precede implementation and require review. Matching weights/tie-breaks need the later T10 seam proposal, including complete-profile eligibility.
- All core tickets retain red-run evidence, public-seam tests, mutations, purity checks, small PRs, and honest coverage. Rule 5 stays partial through the initial view work.

## Core ticket table

| ID | Deliverable and acceptance test focus | Genuine blockers | Parth/agent sessions |
| --- | --- | --- | --- |
| **T1 Member/profile/view + Pseudonym self-name** | Combine old T1/T3, keeping separate red-green commits for shared predicate/profile writes and Pseudonym claims. Approved fields, list/280-character limits, exact pre-Reveal allow-list, private-field canaries across all projections/serialization, no photo representation, Conversation-supplied Reveal state. Test normalization, separators, tokens <3 ignored, save refusal/retry for Member/LLM text and Pseudonyms. Consent/threshold out of scope. | Merged PR #14, 401 green, 74/74 mutations | **3-4 original; timed work in velocity report** |
| **T2 Conversation and isolation** | Active = unrevealed and unblocked; Reveal releases slot but chat remains open; Block ends chat; pair-specific projection/escalation; independent pure isolation tests and separate slot tests. Completed-Reveal fixtures do not implement consent early. Record actual sessions and update the remaining estimate when merged. | T1 | **1-2** |
| **T3 Local walking skeleton** | Needs only T1's identity view, not T2. FastAPI serves built React plus relative API routes on one origin; in-memory synthetic fixture crosses a real endpoint, not health-only. Verify canary-free rendering and ≤5 PowerShell app-run commands, no database installation or CORS setup. Keep real user data out before auth/admission. | T1; first velocity review | **1-2** |
| **T4 Early free deployed skeleton** | After explicit approval provision Render Free + Neon Free, no Render Free Postgres. Verify service/RAM fit, health endpoint, bounded DB readiness probe/connection, clear initial loading/retry state and same-origin assets. A Render cold start can occur before React loads: document its platform loading page and demonstrate retry/readiness after wake. Check both sleep/wake cycles and a demo-day app+DB warm-up checklist. Neon can be connection-tested here; app records remain in-memory until T5, so do not claim those fixtures survive restart. | T3; host/account/provisioning approval; security/Terms eligibility check | **2-3** |
| **T5 Shared repository, contract suite and audit** | One SQLAlchemy Core repository, SQLite/Postgres contract suite for concurrent uniqueness, rollback, append-only audit and equivalent behavior; durable sessions and deployed survival. Explicit opaque-value persistence mapper, exact new AST unwrap site, both-database wrapper round trips and diagnostic canaries. | T1, T2, T3; deployed survival also requires T4 | **2.5-4.5** |
| **T6 Auth/admission and profile APIs** | Vetted password hashing/scrypt, server-side HTTP-only SameSite session, env-seeded Admin, Invite/age/admission transitions and audited Admin decisions. Stable profile API for H1. Explicit login unwrap site, exact AST boundary and successful/failed-login diagnostic canaries. | T5 | **2.5-3.5** |
| **T7 Messages/moderation API** | Scanner first; safety moderation still required for identifier-flagged text. Fake-tested delivery/Escalated/Withheld, retry, no recipient delivery on failure, timestamps/Clock compatibility and Blocked-send denial. Use fake-tested timeout, concurrency cap, bounded queue, unreachable/busy/malformed output and injection paths; checking/retry feedback, no daily counter. Demo failure config is adapter-only and rejected outside demo. Stable chat API enables H3; no claim that local-model is live yet. | T2, T6 | **2-3** |
| **T8 Reveal ceremony** | Delivered/Escalated-only 20/5/72-hour boundaries, Withheld exclusion, bilateral/withdrawable consent, irreversibility, exact revealed identity payload excluding DOB/photos, pair isolation and slot release with continued chat. Minimal UI ceremony remains core; H3 can consume approved endpoint state, never decide eligibility client-side. | T7 | **2-3** |
| **T9 Admin console and deployed checkpoint** | Invite issuance, admission and all required queues; Admin-only actions and audit for every approve/reject. Minimal synthetic fixtures supply all six deployed rule paths. After T8+T9 merge, run the six-rule checkpoint with the current adapter and H1/H3 views; failures block optional work. Fix required paths, remove polish/options, then continue mandatory work. This checkpoint does not replace later live-local-model quota rehearsal. | T6, T7; checkpoint also T8, H1, H3, minimal H4 fixtures | **2-3** |
| **T10 Deterministic Matching** | Approve scoring/tie-break proposal, then test deterministic ranking/exclusions, bilateral acceptance/declines, slot races, and Admin-triggered batches. No LLM re-ranking. Explanation text is dropped in working Plan B. Publish stable Match APIs for H2. | T1, T2, T6, T9 | **2-3** |
| **T11 Block/Report paths** | API, Admin queue and audit are required; Report submission UI is optional. Test pre/post-Reveal Block, stopped sends, freed slot, permanent pair exclusion, irreversible disclosure and Reports after Block; deny unauthorized actors. | T2, T6, T7, T9 | **1-2** |
| **T12 Local-model adapter and rehearsal** | Authenticated laptop proxy/tunnel; fixed-enum validation, prompt-injection cases, measured timeout/concurrency/queue limits, offline/malformed/busy fail-closed paths, checking/retry UI and real synthetic evaluation. No explanation text or daily budget. | T7 and reviewed post-T1 feasibility note; runtime/model/accuracy approval. Safety integration immediately after T7 where capacity permits. | **Re-estimate after feasibility; prior 3-4 is not validated for local inference** |
| **T13 Full seed demo and evaluation** | Integrate H4 synthetic data through approved APIs/fixture builders, not raw audit writes. Verify every audit event/decision and six deployed rules, sequential A-B Reveal then A-C Match, persistence, HTTP privacy, five-command local run, laptop/tunnel/cold-start checklist, cited deliverables, truthful coverage/weak test, all four walkthroughs, and authorized final tag. | T4-T12 required paths; H1-H6 deliverables | **2-3** |

**Known lead work excluding T12: 23-36 sessions**, plus feasibility/benchmark work and the measured/re-estimated local-model adapter effort. T5 and T6 each include a provisional additional 0.5-session boundary allowance, not measured velocity. The original 0.5-session research note is distinct from the newly authorized one-session benchmark block; account for its actual time separately. The previous 25-39 total assumed a remote adapter and is superseded. Work to optimistic Plan B and report slippage immediately; a final total and T7/T12/T13 update require measurements. Preserving 4-6 contingency sessions is desirable but that capacity is not available in the optimistic plan.

## Ready-for-human draft tickets

These will carry `ready-for-human` after publication approval. Names are suggestions, not assignments or messages. Parth is reviewer on all; teammates must demonstrate and explain their work. Protected files/behaviors: domain core, repository/audit implementation, auth/LLM policies and secrets. If an API contract is wrong, report it for Parth's core change instead of modifying it in the UI task.

| Draft | Suggested owner and suitable scope | Acceptance tests | Ready after | Sessions |
| --- | --- | --- | --- | --- |
| **H1 Profile form page** | Nevil; React inputs and API error/loading/saved states using fixed approved schema | API-backed form submits valid values, surfaces rejected/over-cap/identifier saves without claiming a save, no private canary fields or extra free-text fields | T6 API merged | **1-2** |
| **H2 Match view** | Tej; display and accept/decline existing endpoints, no scoring code | Correct pair/pseudonyms, API-authorized acceptance/decline states, pending/error behavior, no client ranking/identity reveal | T10 API merged | **1** |
| **H3 Conversation view** | Vatsal; React read/send/Withheld/Escalated feedback, consume server-provided Reveal state | API-backed send/blocked/retry states; no optimistic delivered mark on Withheld; correct pre/post-Reveal fields, no canary leak; add Reveal endpoint UI cases after T8 API exists | T7 API merged; T8 for Reveal cases | **1-2** |
| **H4 Synthetic seed fixtures** | Nevil or Tej; JSON/example inputs only, no domain/audit edits | No real people/contact data; schema-valid profiles, message/timestamp/queue scenario manifest; fixtures validated through approved APIs by Parth, no invented audit entries. Minimal subset before checkpoint, full set before T13 | Schema-only fictional personas can start after T1 choice-list approval; executable scenarios wait for relevant API contracts | **1-2** |
| **H5 Per-rule viva scripts** | Vatsal; scripts and expected observations | Six runnable paths plus cold-start warm-up, laptop checklist and offline/timeout/busy/malformed failure rehearsal; each references deployed behavior and approved test evidence | Draft from approved spec this week; validate after T7/T8 and finalize after T12 | **1** |
| **H6 TESTING citation check** | Tej; docs/citation review only | Resolve each test/code citation, report stale claims, keep rule coverage honest; demonstrate owned evidence at viva. No editing domain/audit to make a claim true | Spec/evidence inventory this week; code citation checks per merged slice; final T13 | **0.5-1** |

**Teammate effort: 5.5-9 sessions**, overlapping core work. Teammates have accepted this work; names remain proposals, with no assignments. T1/T2/T5-T12 core/policy work is not suitable for these teammate tickets; UI-only portions and T13 documentation/fixture inputs are suitable under the boundaries above.

## Plan B and honest capacity

Capacity is **five build sessions/week**. Viva is **5 December 2026, confirmed**. Plan B is the working scope, using the optimistic estimate; feasibility risks are reported immediately. A session is 2-3 focused hours, not a calendar day.

**Feature freeze: 28 November. 29 November-4 December: rehearsal and fixes only, no new features.** There are approximately five build weeks, not six: **25 lead build slots**. T13 seed integration lands before freeze; reserve 1-2 later sessions for final rehearsal. Revised known work excluding T12 is 23-36 sessions including rehearsal. At its optimistic bound, subtract one rehearsal session and add the original 0.5-session research allowance: **22.5 build slots before T12**, leaving about **2.5 for the adapter**, before any extra benchmark time or delay. Holding the higher original T1 reservation reduces that residual to 1.5. These are planning constraints, not measured adapter estimates; cross-database concurrency/rollback/audit/CI and private mapping still require evidence. The upper range does not fit; disclose slippage immediately and update T7/T12/T13 after measurements.

| Lead capacity | Build slots before freeze | What ships / feasibility |
| --- | --- | --- |
| 1-3 sessions/week | 5-15 | Plan B core below is the required scope, but cannot honestly fit; extra core-building capacity or a changed deadline is required. |
| 4 sessions/week | 20 | Below even the optimistic 24-session core; not feasible with current ownership. |
| 5 sessions/week | 25 | Only the optimistic core fits, with effectively no contingency; high risk, not a credible commitment. Teammate delivery and measured T1/T2 velocity are necessary, not sufficient guarantees. |

**Exactly what Plan B ships:** structured form; Pseudonym/profile checks and private identity view; invite/age/admission/auth; deterministic values-only Matching and bilateral acceptance; moderated chat with fail-closed authenticated local-model calls; Conversation-isolated threshold/consent/Reveal; minimal Admin console for Invites/admission/Escalated/Report decisions; Block/Report API, required Admin Report handling and append-only audit; shared SQLite/Postgres repository and contracts; one deployed URL, health/loading/warm-up paths; fictional fixtures, six-rule evidence and rehearsal. Minimal member UI remains required. No auth, moderation, privacy, Reveal, Report-handling or audit tests are cut.

**Exactly what drops:** conversational Onboarding, LLM re-ranking, Icebreakers, LLM Match explanation text, threshold-progress UI, Member Report submission UI, cosmetic polish, and second-provider implementation. Registration's demo-only notice remains. Dropping explanation text saves at most about 0.5-1 session; it does not close the upper-estimate gap. In that mode public copy must identify explanations as unavailable/deterministic rather than imply AI-generated explanations. Plan B is now active; public copy omits the explanation claim.

At <=4 lead sessions/week these optional cuts do not rescue the date. At 5 the core is possible only at the low bound, not safely promised. Recommend additional accepted core-capable help or a deadline change if measured velocity misses the low bound; none is assumed or assigned. Admin console, Reveal, Report handling and all six rules remain protected.

## Provisional allocation and approved gates

| Week | Focus |
| --- | --- |
| Oct 24-Nov 1 | Approve T1 seam/lists, T1; first velocity review; overlap T2 and local T3 with serial review. H5 spec scripts/H6 evidence inventory can start now if owners accept. |
| Nov 2-8 | Second velocity review after T2, before T4; approval-gated free deployment; T5 shared repository/audit. H4 fictional schema fixtures after choices approved. |
| Nov 9-15 | T6 auth/profile APIs, T7 moderation/bounded failure handling; start T12 immediately after T7, alongside required Reveal work where review capacity permits. |
| Nov 16-22 | T8 Reveal and T9 Admin, real synthetic local-model Rule 2/3 rehearsal, required six-rule checkpoint; H1/H3 minimal pages. T12 safety integration target Nov 21, subject to actual velocity. |
| Nov 23-28 | T10 Matching, T11 Block/Report, H2, seed integration and remaining required paths; freeze Nov 28. If checkpoint fails, cut all optional work first. |
| Nov 29-Dec 4 | Rehearsal and fixes only, laptop/tunnel/cold-start drills, evaluation/citation checks; no new features. |

This is a capacity scenario, not a guarantee. At the first velocity review publish the revised T7-T13/H1-H6 estimates; after T2 show another update before T4. T3 does not wait for T2. Do not let early T12 displace required rule work. Its safety calls need T7, not Matching; leave explanations out unless velocity permits. Live Rule 2/3 rehearsal must begin at least a week before viva.

No teammate is assigned. H5/H6 drafts can start **this week** from the spec after owner acceptance; H1-H3 owners may review wireframes/error-state inventories this week without inventing APIs or implementing policy. H4 starts fictional persona inputs after choice-list approval. API-bound implementation still waits on its documented blocker. Parth reviews each deliverable; each owner must explain their own work.

## Cut line, claim and release gates

Above the line: the 13 core rows, structured form, minimal member views, Admin console, Reveal, Report handling, repository evidence, the six rules and the rehearsal requirement. Below: conversational Onboarding (first stretch), LLM re-ranking (second stretch), Icebreakers, threshold-progress UI, Report submission UI, polish, second free provider. If any extras entered scope, remove in the specified order: Icebreakers → conversational Onboarding → progress UI → Report UI → polish. Neither mandatory Report handling nor Admin queue UI is the optional Report-submit UI.

Cannot safely cut: auth/participant checks, profile write checks, cross-pair privacy, moderation failure paths, server-side consent/threshold checks, audit consistency, either repository's contract evidence, laptop/tunnel/cold-start rehearsals. Reducing the LLM budget must cause explicit safe failure, not unchecked delivery or automatic admission.



## Publication and implementation gates

Publish only T1-T6 now, unassigned, as children of #7 with native blocking edges. Publish T7-T13 and H1-H6 only after the first velocity review, with real estimates. The user's approval covers this revised plan, not provisioning or implementation. Present T1 seam/types/choice lists and wait for approval before implement/tests. No new agent tooling.


Historical 25-39 lead sessions included the previous 3-4-session provider adapter. The local-model T12 row is unvalidated; add the 0.5-session feasibility note and re-estimate at first velocity review. Do not present the previous bound as proof that local inference fits.

## Confirmed working scope and local-model decision

Vaeil is final. Capacity **5 build sessions/week**; viva **5 December 2026, confirmed**. Feature freeze **28 November**; **29 November-4 December rehearsal/fixes only**. Work to optimistic Plan B; report slippage immediately after T1 and T2. Teammates accepted H1-H6, still unassigned.

Drop conversational Onboarding, re-ranking, Icebreakers, explanation text, progress UI, Report submission UI, polish and a second adapter unless velocity proves room. Keep all six rules, Admin console, Reveal and Report handling. Product copy is “values-based matching with AI-assisted safety”, reflecting the dropped explanations.

Replace Gemini/AI Studio and the daily counter with a laptop-served model behind the owned LLM port. Ollama/llama.cpp choice and CPU/Vulkan support await the **0.5-session feasibility note immediately after T1**, alongside T2/T3. No model integration before Parth reads it. The [feasibility brief](local-model-feasibility-brief.md) fixes model/licence/structured-output/tunnel research, measured >=30-call/model p95/concurrency/ten-minute thermal runs, approved accuracy bar and fallback proposal. T12 is re-estimated from findings; grade 9 is the contract, grade 10 requires model feasibility, uptime and consent.

Use an authenticated laptop proxy/tunnel, environment-held secret on every deployed request, fixed-enum validation and measured per-call timeout/concurrency/bounded queue. Slow/offline/busy/malformed output yields Withheld/NeedsReview; Render stays usable. Fake tests include prompt injection and failures. Messages show checking/retry feedback. Synthetic-only restriction is lifted for the local model; demo notice remains until consent/deletion plan. Fictional seed personas remain. Demo checklist includes plugged-in/performance power/no sleep/warmed model/tunnel and mid-demo fail-closed fallback.

Gender/orientation are out of scope and a known limitation: Matching is values-only. Future private match preferences belong outside public profile/view types. Complete profiles require 1-5 distinct frozenset selections per list; T10 enforces complete-profile Matching eligibility. Stable enum codes, frontend labels, trimmed NFKC About <=280 code points, controls refused. Pseudonym self-name uses substring; About whole-word. Mark/market is accepted; Will/will is a documented false positive with rephrase feedback. Revealed views preserve the public fields; pre-Reveal keeps exactly two, with frozen/slotted/redacted records and no private references, per the approved T1 seam.

Render/Neon accounts are Parth-owned. T4 adds teammates where free collaboration allows, password-manager credential sharing outside the repo, and a one-page redeploy-from-scratch recovery note. Provisioning remains approval-gated.
