## Parent

Part of #7. Ready-for-human, **unassigned**; Parth confirms ownership and reviews the PR. Every owner must explain their work at the viva.

## What to build

React form over the merged T6 own-profile API: load/save a private draft, complete/update Values Profile and claim fixed Pseudonym. No domain/auth-policy/database/audit changes. Live deployment remains earlier runtime; develop locally with isolated fictional fixture setup, no production credentials or real people.

## Acceptance criteria

- [ ] Follow T6 HTTP contract, stable codes and frontend labels. All structured choices,1–5 distinct interests/values for completion, optional About and fixed Pseudonym; drafts may omit choices, no invented defaults/Matching eligibility.
- [ ] Handle incomplete and complete response shapes. PUT sends the complete form per replacement/omission semantics. Omit Pseudonym after completion, display without rename option.
- [ ] Server owns validation/scanner/self-name/length/uniqueness. Show safe field/rephrase errors, preserve failed input, permit taken-name retry. No silent truncation or browser-only normalized-length policy.
- [ ] Relative same-origin routes/HttpOnly cookies; no token/localStorage/response logging. Pending/rejected/expired sessions cannot edit; clear sign-in/admission feedback.
- [ ] Demo-only warning; untrusted content rendered as text. Own identity never copied into recipient views, analytics, console or localStorage.
- [ ] Real-API browser fixtures: restricted/expired refusal; draft/reload; complete; later update without name; unsafe About refusal retaining input; taken-name retry; malformed response/storage-error recovery. Existing choice/privacy tests unchanged. Frontend typecheck/build/browser pass, no domain/audit edits.
- [ ] Handoff run/test evidence and viva explanation: shapes, draft/completion, errors/fixed name and why privacy policy stays server-side. Parth reviews before merge.

## Dependency and estimate

T6 #13 closed; can start locally now. Contract: docs/specs/t6-profile-http-contract.md. Choice codes pinned by existing tests. Fictional setup stays test-only; no public account/Invite bypass. Report API gaps rather than editing core/audit.

**1–1.5 teammate sessions plus lead review**, estimate only. Already excluded from lead baseline, not new gap savings. No assignee or outbound teammate messages.
