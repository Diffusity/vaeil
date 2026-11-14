# T6 application/API seam — proposal for approval

Issue13: Authentication, admission and structured profile APIs. T5 is merged (8a7a434). The14November instruction lifts the T6 hold to carry out the recommended flow; this proposal must be approved before tests. No product decisions are reopened. No tests, stubs, product implementation or unwrap allowlist changes accompany this document.

## Application interface

One application module coordinates existing pure policies, repository transactions and injected adapters. HTTP handlers authenticate, validate transport shape, call this interface and encode explicit responses. IDs/roles come from the server session, never request-body authority.

```python
class AdmissionApplication:
    def apply(self, command: ApplicationSubmission) -> ApplicationReceipt: ...
    def login(self, email: str, password: str) -> SessionGrant: ...
    def logout(self, raw_token: str) -> None: ...
    def session(self, raw_token: str) -> SessionPrincipal: ...
    def decide_admission(self, *, actor: SessionPrincipal,
                         applicant_id: str, decision: AdmissionDecision) -> None: ...
    def save_own_profile(self, *, actor: SessionPrincipal,
                         draft: ProfileDraftInput) -> OwnProfileView | DraftReceipt: ...
    def own_profile(self, *, actor: SessionPrincipal) -> OwnProfileView | DraftReceipt: ...
```

Constructor dependencies: repository, PasswordHasher, session-token source, an injected date/timestamp clock, and note-only VettingModel. No FastAPI/SQLAlchemy imports in domain policies. Concrete runtime randomness/time are adapters; tests inject fixed values. Existing Clock.today and the age gate remain; propose adding aware-UTC now() for session expiry, without changing existing callers or T1/T2 assertions. Public seam errors have fixed reason codes and no offending/private input.

ApplicationSubmission is a frozen/slotted private record: MemberIdentity (opaque legal_name/email/optional phone/DOB), Invite code, validated application note and an encoded password digest. Identity ID is generated server-side. HTTP accepts plain form values ergonomically, constructs wrappers immediately, and hashes the transient password through the password adapter; no plaintext password is persisted, logged or returned. Passwords/Invite codes and all private command fields are excluded from diagnostics; commands refuse generic export. The application note remains Applicant-private, even though it is plain normalized text for the note-only port.

SessionPrincipal contains opaque principal ID, server-owned role and admission status, never credentials. SessionGrant is a non-printing internal response holding the raw token solely for Set-Cookie; public response contains no token. Credentials and session digests use private records/wrappers; generic serialization/copy protections remain. AdmissionDecision is the human Admin approve/reject command, distinct from the unchanged Approved/NeedsReview Verdict enum; models can never create a Reject verdict.

## Two existing gaps and proposed resolution

1. VettingModel.vet currently receives the DOB-bearing Applicant. Change that port to `vet(application_note: str) -> Verdict`, with the fail-closed wrapper passing ONLY the already-validated normalized note. A capturing fake pins exact text and absence of identity/DOB/Invite canaries. The deployed human-review adapter always yields NeedsReview; scanner-clean text never auto-admits. A test-only approved fake exercises existing Approved semantics, but cannot be selected by web input or production config. No local-model integration is included.
2. Current Member and SQL members rows require a complete ValuesProfile. Preserve those invariants. Store the admitted principal/identity and partial Onboarding draft separately; admission still makes the person a Member in the existing vocabulary. Materialize the existing complete Member record when Pseudonym and complete profile are first saved. Drafts cannot become Matching-eligible; T10 enforces complete-profile eligibility when selecting candidates. This is a storage representation, not a delayed admission decision or a new product state. First completion uses T5 add_member and its normalized unique constraint; later writes use a narrow profile-update method preserving Member identity/Pseudonym. No fake choices, weakening of complete-profile tests or moving Onboarding before admission.

Draft fields use the approved enum codes and frozensets, with missing structured choices allowed. Existing per-field checks apply to every supplied field; About uses the same normalized/scanned/whole-word-self-name path even in drafts. First Pseudonym claim must pass the existing substring check and atomic normalized ownership. A failed/taken candidate leaves the Member able to retry; an already-set Pseudonym cannot be changed. Partial drafts never leave the own-profile API or appear in Match views.

## Transaction/storage additions

Extend the existing single SQLAlchemy implementation and owned transaction protocol for principal credentials, Invite redemption, Applicant/note/draft storage, atomic admission decision and profile update. Proposed operations: get_principal_by_email/get_principal, add_application, get_application/list_pending_applications, consume_invite, set_admission_decision, save_onboarding_draft/get_onboarding_draft and update_values_profile. Existing session/audit/add_member operations remain. Each added operation gets the same SQLite/PostgreSQL contract, not a second adapter or raw production test fixture. Tables/constraints enforce unique normalized login email, single Invite consumption, one application/principal ownership and terminal Admin decisions. No check-then-insert race.

Vetting runs outside an open write transaction; final transaction rechecks Invite/current state and commits Applicant, Invite consumption, admission status and audit together. Underage/future DOB fails before consumption (reuse redeem_invite on a detached Invite and injected Clock). Shape/note/scanner/self-name failures cause no save or model call. Later DB failure rolls everything back. Concurrent redemption has exactly one winner; conflicting/repeated Admin decisions cannot duplicate events. Human approve/reject and Invite/vetting outcomes use existing typed AuditKinds, with IDs/reason enums only, no note/identifier spans or identity copies.

## Password/session implementation proposal

Use stdlib scrypt, versioned salt/parameter/hash encoding and constant-time verification. Salt and session-token randomness come from secrets in the runtime adapter. Only hashed passwords and SHA-256 token digests persist; never raw cookies. Proposed exact fifth production unwrap site:

`vaeil.adapters.authentication.verify_password`

It unwraps only the stored encoded password hash for verification; raw submitted password is transient input. Hash creation takes that transient input directly and needs no wrapper extraction. Identity comparisons/mapping continue through existing authorized sites; no new email/name unwrap helper. Preserve all four existing sites and add successful/failed-login canaries plus wrong-function/wrong-module positive controls. No AST change until seam approval and red tests.

Cookie: server-side session, HttpOnly, SameSite=Lax, Secure on deployed HTTPS, Path=/, no token in JSON/localStorage/URLs. Logout deletes the stored session and expires the cookie; expired/absent/revoked tokens never authorize. Reject cross-origin state-changing requests; enforce same-origin/CSRF checks for cookie-authenticated mutations, not CORS permission as authorization. Session roles/admission are reloaded from storage. No public route can create an Admin; seed one from environment through the same hash path, never defaults/hard-coded passwords.

## HTTP interface proposed for contract tests

| Method/path | Authority | Observable response |
| --- | --- | --- |
| POST /api/applications | Valid Invite and18+; not Member access |202 applicant ID/status, no identity/note/Invite echo; baseline NeedsReview |
| POST /api/sessions | Valid credentials, returns appropriate restricted principal | Set-Cookie plus ID/role/admission status only; no unchecked admission |
| GET /api/session | Live session | ID/role/admission status only |
| DELETE /api/session | Live same-origin session |204 and cookie expiry |
| GET /api/me/profile | Admitted Member, own ID only | Existing explicit OwnProfileView, or private DraftReceipt before completion |
| PUT /api/me/profile | Admitted Member, own ID only | Validated own draft/complete profile; identity/Pseudonym fixed once set |
| GET /api/admin/applications | Admin only | Explicit queue DTO, note as untrusted text, no DOB/contact dump |
| POST /api/admin/applications/{id}/decision | Admin only |204; approve/reject atomic with audit |

Admin API actions are the minimal admission seam; the Admin console remains T9. No Match/Conversation recipient endpoint is invented here. Preserve existing projection isolation; later endpoint owners must enforce participant access through the existing policy. Registration shows the demo-only notice; minimal registration/session UI is core, teammate structured-profile UI consumes these contracts after merge. Error handlers strip FastAPI validation input and exception details; no submitted credentials/private values in HTTP errors, logs or tracebacks. Proposed statuses:400 safe invalid field reason,401 invalid session/credentials (same response for unknown email/wrong password),403 role/admission/CSRF refusal,409 Invite/email/Pseudonym/state conflict. No stack traces or private query parameters.

## Red-green sequence after approval

1. Note-only port/application-note rules:19/20/500/501 after trim/NFKC, controls/whitespace/combining/fullwidth; scanner and whole-word own-name; capturing fake only note, failures NeedsReview. Show red before code.
2. Scrypt verifier/session records and exact fifth unwrap site; fixed-clock expiry, wrong credentials, cookie/CSRF/logout/Admin-seed boundaries. Hash adapter tested with a real verify round trip, no live model/network.
3. Atomic Invite/age/application and Admin decisions across both databases, concurrency/rollback/audit; no admission bypass through login.
4. Private draft/complete profile flow, scanner/self-name and fixed-once Pseudonym; first completion and later profile updates retain T5 uniqueness and transaction invariants.
5. Minimal registration/session HTTP/UI path, role/own-profile canaries, untrusted Admin note rendering and demo notice; full Windows/container/two-database checks plus mutations, two-axis review and small PRs.

Each cycle gets red shown then minimal green, one commit per cycle. No frozen test loosening. Port change may require updating ONLY the existing an_applicant fixture and fake argument types in tests/test_vetting.py, adding a valid synthetic note; existing expectations retained. Affected behavior tests: test_approved_verdict_is_returned, test_needs_review_verdict_is_returned, test_port_error_fails_closed_to_needs_review, test_port_timeout_fails_closed_to_needs_review, test_non_verdict_result_fails_closed_to_needs_review, test_none_result_fails_closed_to_needs_review. Rejection-unrepresentable test unchanged. Show any actual old-test diff before applying; an incompatible expectation stops for approval.

Mutation targets: bypass Invite/age/admission/role/session expiry/CSRF; consume Invite before age/validation; clean scanner auto-admission; leak Applicant into port; permit model Reject; skip note controls/length/scanner/whole-word checks; omit audit or commit partial state; allow Pseudonym overwrite/concurrent duplicate; unauthorized login unwrap; leak hash/token/identity in HTTP/logs. Keep purity green and Rule5partial; no full-rule E2E completion claim until the integrated product path exists.

## Approval choices and estimate risk

Approve the application/HTTP seams, note-only port change, separate principal/draft representation and exact verify_password unwrap site before tests. Security defaults needing confirmation as part of this proposal:24-hour absolute session lifetime (no sliding renewal); new passwords12–128 Unicode code points with no composition rule or silent normalization; login email strip/NFKC/casefold uniqueness. These are proposed settings, not closed-definition decisions silently adopted. No email verification/reset flow or provider/tunnel added.

Ticket estimate2.5–3.5lead sessions is tight: T5 did not persist Invites/Applicants/credentials/drafts or support profile updates. The added contracts and restricted Member state are required T6 work, not free wiring. Using3.5sessions for T6 instead of the previous optimistic3 raises the remaining13.5session forecast to14sessions against about10available: at least4sessions short, excluding additional review/acceptance effort. This is a revised estimate, not approved capacity or a reason to cut required rules. Re-estimate after the first vertical cycle. Retain the28November freeze, protected six rules/Admin/Reveal/Report handling and optional-model deferral.
