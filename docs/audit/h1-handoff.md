# H1 handoff — Nevil-Nandasana, Codex-assisted

Issue26; basea4036b6 (approved planning PR27 merged). Parth explicitly assigned H1 to Nevil-Nandasana and requested commit attribution using Nevil's supplied email. Codex wrote the implementation/tests on his behalf; commit bodies disclose assistance. No independent human coding or review claim. Parth reviews the PR; Nevil must read/run the form and be able to explain it at the viva.

## What changed

An admitted Member signs in or resumes a cookie session, loads a private profile draft, saves the whole form, completes choices/Pseudonym, and later updates without reclaiming the fixed name. Draft and complete response shapes differ; explicit parsing accepts approved stable codes and keeps only form fields, never identity, in form state. Frontend labels are separate from codes. Server owns normalized length, identifier/self-name refusal, uniqueness and admission; the browser does not duplicate those decisions. No client truncation, token storage, raw server-error rendering, new unwrap, domain/audit changes or deployment.

## Tests-first evidence

| Cycle | Observed red | Green/commit |
| --- | --- | --- |
| Draft/reload | Missing named form after real admitted sign-in |1browser, ed65997|
| Safe completion/errors | Generic About failure instead of safe rephrase |2browser,4628737|
| Malformed response |3invalid payloads accepted,1missing-shape control already safe |6browser,7d44ffb|
| Acceptance coverage | Taken-name setup initially raced login cookie; test helper tightened to await actual sign-in, not behavioral red evidence |Taken retry green;6e917fa|
| Fresh review | Delayed old Applicant session hid newly signed-in Member editor |Auth-generation regression green,f478bc2|

No assertions deleted/loosened. Heading ID collision and implicit label contents were fixed in implementation. Existing six browser cases stay intact. Real HTTP/browser fixtures use owned temporary SQLite, fictional Invites and audited Admin admission through the same APIs. Invalid response/storage failures are explicit HTTP-boundary injections; positive flows use the real API. No fake production approval toggle.

Full prior restored run:615Python passed86explicitlocalPostgreSQLskips31.49s;18browser43.0s before the new race test. Final restored browser/CI results are recorded in the PR/session log, not guessed here. Rule5partial;3/6domain,0/6complete-ruleE2E unchanged.

## Review

Standards0findings. Spec1P2: initial async session restoration could overwrite a newer explicit login. Deterministic delayed-snapshot regression red->green; the independent Spec reviewer confirmed closure. No outstanding source findings. Four targeted browser mutations are recorded in h1-mutations.json after exact source restoration; final CI remains a handoff gate.

## Nevil's viva walkthrough

1. Run the README five commands; for automated fictional cases run frontend typecheck/build/test. Browser fixtures are disposable test setup, not a public account/Invite shortcut. Use no real personal details.
2. Trace session -> admitted role -> GET own profile. Show pending/rejected Member restrictions, sign-out/revoked401 handling, and why old restore responses cannot replace a newer sign-in.
3. Explain the draft response's complete:false versus complete own-view shape. PUT replaces fields: submit the entire form; omit Pseudonym after completion. A taken name can be corrected without losing choices.
4. Show safe About refusal retaining edits; show280emoji accepted and281refused without truncation, plus NFKC normalized server output. Explain why JavaScript UTF-16 maxLength is not used.
5. Explain fixed stable codes/frontend labels and response validation. Errors shown to users are fixed local strings; identity payload values are not copied into React form state, browser storage or logs.
6. Run the browser cases and point to an assertion you can explain. Describe AI assistance honestly and confirm understanding before presenting this as your owned deliverable.

## Operational limits and next step

Not merged/deployed by this task. Registration/admission fixture accounts are synthetic; live site remains earlier runtime. No H1 ownership hours or human review time fabricated, and no double-counted gap savings: H1 was already excluded from lead core estimates. Next lead work is approved-seam T7 Messages/moderated delivery, after Parth reviews this H1 PR. Baseline remains explicit human review, not scanner-clean automatic delivery; no provider/tunnel/model setup.

## Small retrospective

Independent HTTP-boundary malformed-data tests and fresh async lifecycle review found faults beyond happy paths. Await real sign-in before fixture API actions; explicit label associations survive populated controls. Keep issue+API contract in the review packet, use existing checks rather than new agent tooling, and preserve clear human-versus-AI attribution and unverified-time limits.

Final restored local browser suite: **19/19 passed49.7seconds** after all four source mutations were restored. TypeScript/build pass; full Python regression remains615passed86explicitlocalPGskips31.49s. Product policy/source unchanged after that Python run. Final-head Windows/container/shared-Postgres CI will be checked before handoff.

Current16November forecast:10.5remaining lead sessions versus roughly8–9slots before freeze, at least1.5–2.5gap plus review/rework. H1 was outside that estimate already; no new savings inferred.
