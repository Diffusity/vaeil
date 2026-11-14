# T5 seam proposal — approval required before tests

Issue #12: Shared SQL repository, contracts and append-only audit foundation. This is a proposal derived from the approved ticket, not implementation. T1/T2/T3 are merged. T4's live survival acceptance remains gated; local contract work does not need to wait for that check. No new product decisions, authentication flow or moderation delivery path is introduced.

## Public test seams

```python
class Repository(Protocol):
    def transaction(self) -> ContextManager[UnitOfWork]: ...

class UnitOfWork(Protocol):
    def add_member(self, member: Member) -> None: ...
    def get_member(self, member_id: str) -> Member: ...
    def store_conversation(self, conversation: Conversation) -> None: ...
    def get_conversation(self, conversation_id: str) -> Conversation: ...
    def put_session(self, session: StoredSession) -> None: ...
    def get_session(self, token_digest: str) -> StoredSession | None: ...
    def delete_session(self, token_digest: str) -> None: ...
    def append_audit(self, event: AuditEvent) -> None: ...
    def list_audit(self, *, subject_id: str) -> tuple[AuditEvent, ...]: ...
    def commit(self) -> None: ...
```

Domain-owned Protocols/types contain no SQLAlchemy, FastAPI or driver imports. Existing Member/MemberIdentity/Pseudonym/ValuesProfile and Conversation remain the returned domain types, with opaque private fields intact. Missing Member/Conversation raises a distinct safe not-found error; an absent session returns None. No row/dict/SQL exception escapes this seam.

One SQLAlchemy Core implementation accepts either a SQLite or PostgreSQL connection URL. Default local SQLite requires no database install. Context entry starts one transaction; explicit commit persists it; exceptions or exit without commit roll back. A failed transaction cannot leave domain writes without their associated audit writes, or vice versa. Callers in later tickets own which business events must be emitted; T5 proves atomic storage, not admission/moderation completeness.

`add_member` reuses the existing Pseudonym/profile policy and atomically inserts the Member. The database has unique constraints on Member ID and normalized Pseudonym (trim/NFKC/casefold). This is the durable claiming boundary: two equivalent names racing on separate connections produce exactly one committed owner and a safe PseudonymTakenError for the other. A repeat Member cannot replace a fixed Pseudonym. No check-then-insert uniqueness or duplicate handwritten domain policy. SQL constraint errors are translated without input/SQL parameters in exception chains or logs.

Conversation storage preserves T2's participant identity, monotonic Revealed/Blocked flags, permanent pair Block and one-active-Conversation exclusion. A transaction serializes or rejects conflicting updates rather than accepting stale overwrites. The tests cover same-Member concurrent opens and Reveal/Block restoration races. Consent eligibility/threshold decisions remain T8; repository restoration is not an HTTP Reveal command.

## New records and private mapping

- `StoredSession`: frozen/slotted, redacted token digest, opaque principal ID and explicit UTC expiry. Store only the digest of a session token, never a raw cookie. T6 owns token generation, password hashing, cookie attributes, expiry/auth enforcement and Admin wiring; T5 only persists/loads/deletes session records.
- `AuditEvent`: frozen/slotted, event ID, UTC occurrence time supplied by caller, actor ID (optional for system events), subject ID, a fixed event-kind enum and enum reason codes. No free-form message/profile/identifier payload, private identity, raw Invite/session token or arbitrary details dict. Event kinds reflect the approved spec, including every Admin admission and queue approve/reject/release/discard decision. Future workflows append these events; T5 does not implement those decisions.
- Internal row mapping is explicit. The only proposed new unwrap site is `vaeil.adapters.persistence.encode_private_value`, accepting PrivateText/PrivateDate and returning the corresponding storage scalar. It is used only by the persistence mapper. Existing three sites remain unchanged; T6's login site is not added here. No asdict, pickle, generic export or wrapper weakening. SQLAlchemy echo is off and bound parameters are hidden. Plain internal row mappings never leave the adapter; reconstructed values are wrapped immediately.

## Contract suite and red-green order

One parametrized suite runs unchanged against SQLite (file-backed temporary DB, real separate connections) and a disposable PostgreSQL CI service. Tests never point at production Neon. Domain/purity/privacy tests remain green throughout.

1. Explicit Member/private-value round trip and safe diagnostics; exact mapper AST allowlist plus an unauthorized fake mapper that fails the guard.
2. Normalized-Pseudonym unique index and fixed-once behavior, including real concurrent transactions and a loser that can retry another name. Preserve every slice2 policy test.
3. Conversation round trips and atomic T2 invariants, including cross-Conversation isolation and concurrent active-slot/monotonic-transition conflicts.
4. Explicit commit/rollback across Member/Conversation and audit; mid-transaction failures leave neither partial data nor events. Duplicate event IDs refuse replacement.
5. Append-only audit at repository and database boundary. No update/delete repository methods; database guards reject direct audit UPDATE/DELETE on both dialects. Raw SQL is a separate approved storage-boundary test, not inspection of repository internals. No claim against a privileged owner deliberately dropping guards.
6. Session durability across new repository/connection instances, exact expiry-field round trips, deletion, redacted digest diagnostics. No login behavior.
7. After T4 acceptance: one isolated fictional Neon fixture survives a Render restart/redeploy. Record evidence without credentials; no automatic production test loop or deletion of existing records.

Each cycle shows its red run before implementation and gets one red-green commit. Mutations: remove normalized uniqueness; remove normalization; allow second Pseudonym overwrite; swallow rollback/commit one side early; allow audit update/delete; omit atomic Conversation exclusion or monotonic guard; skip wrapper reconstruction; unwrap from an unauthorized function; leak SQL parameters. Each must have a named killing contract/privacy test on the relevant database. Full checks plus both-database CI before review.

## Estimate and gate

Keep the ticket estimate at **2.5–4.5 lead sessions**, targeting the optimistic end but re-estimating after the first real SQLite/PostgreSQL cycle. Concurrency and dialect audit guards are mandatory; do not cut them to claim the lower estimate. The deployed survival check waits for T4 acceptance. No optional model work or new agent tooling.

Approval requested for this interface, atomic transaction semantics, exact mapper site, audit/session record shape and contract boundaries. No T5 tests, stubs, implementation or ticket edits have been made. Draft choices here are reviewable proposals, not silent settled decisions.
