# T2/T3 public test seams — proposed 7 November

Schedule and human-review baseline approved by Parth. This document proposes only implementation interfaces for settled behavior; no model, hosting or product scope decision is reopened.

## T2: Conversation lifecycle and pair isolation (#9)

Use a pure in-memory `ConversationDirectory` as the domain seam, analogous to the existing PseudonymDirectory. Its state holds Member IDs, never Member identities. T5 supplies atomic durable storage later; this seam does not claim concurrent persistence safety.

```python
@dataclass(frozen=True, slots=True)
class Conversation:
    conversation_id: str
    participant_ids: tuple[str, str]
    revealed: bool = False
    blocked: bool = False

    @property
    def active(self) -> bool: ...             # not revealed and not blocked
    @property
    def open_for_chat(self) -> bool: ...      # not blocked
    @property
    def identifier_escalation_required(self) -> bool: ...  # not revealed
    def reveal_state(self) -> ConversationRevealState: ...

class ConversationDirectory:
    def open(self, conversation_id: str, *, participant_ids: tuple[str, str]) -> Conversation: ...
    def get(self, conversation_id: str) -> Conversation: ...
    def block(self, conversation_id: str, *, actor_id: str) -> Conversation: ...
    def restore(self, conversation: Conversation) -> None: ...
```

`open` is an internal application/domain operation after bilateral Match acceptance, not a public route bypassing Matching. Require nonempty Conversation ID, exactly two distinct nonempty Member IDs, fresh Conversation ID, neither Member active elsewhere, and no previously Blocked pair in either order. Errors are distinct: `InvalidConversationError`, `ConversationAlreadyExistsError`, `MemberAlreadyActiveError`, `PairBlockedError`; never echo supplied inputs. Read/block missing ID uses `ConversationNotFoundError`; an actor outside the pair uses `ConversationActorError`. Refusal leaves state unchanged. Repeated Block by a participant is idempotent, preserving permanent exclusion.

`restore` accepts validated fixtures/persisted state, not a Member-facing Reveal command. It permits advancing the same Conversation to a completed-Reveal fixture for T2 tests, never changes participants or reverses Reveal/Block, and checks active-slot/permanent-Block invariants before replacement. Distinct `InvalidConversationTransitionError` for regression or pair mutation. T8 replaces application use of fixture advancement with consent/threshold-authorized transitions; no unconditional Reveal endpoint is introduced. No time source or auto-expiry is needed in T2.

Tests cross these methods plus the existing `project_member_for_viewer` / `serialize_member_view`. They cover active-slot conflicts on either participant, Reveal releasing both slots while chat remains open, Block before/after Reveal, reversed-pair exclusion, failed-operation rollback, immutable snapshots, outsider denial, and independent A-B/A-C projections/escalation. Pure projection isolation uses two contexts without active-slot sequencing; directory tests Reveal A-B before opening A-C. Continued safety moderation and Reporting are downstream requirements, not implemented message operations in T2. Mutations target active/open confusion, global Reveal, lost Block history, skipped slot/actor checks and reversed transitions. Existing T1 field shapes and unwrap sites stay fixed.

## T3: local same-origin skeleton (#10)

```python
def create_app() -> FastAPI: ...
# GET /api/health -> 200 {"status": "ok"}
# GET /api/demo/member -> 200 PreRevealMemberView authorized JSON
```

One fixed fictional pair, always unrevealed. `/api/demo/member` has no arbitrary viewer, subject or Reveal query parameter and cannot retrieve private/revealed records. Use the existing projection/encoder; no new unwrap site. This public synthetic fixture is explicitly demo-only, not authentication. No registration or real-data input. All other `/api/*` paths return HTTP errors, never the SPA shell. Serve built React/Vite assets at the same origin with relative API calls. Missing build assets produce a clear local setup error, not a claimed working UI.

HTTP tests pin the exact top-level two-field payload, health, absence of identity canaries and refusal to expand the payload through parameters. UI verifies actual endpoint rendering, loading/error feedback and demo-only/no-real-details notice. Domain purity tests stay unchanged. T3 does not wait for T2 and does not use ConversationDirectory fixtures; it only needs T1's fixed ConversationRevealState. New dependency versions will be checked against official package sources when implementing. Five-command PowerShell setup and a fresh-clone check remain acceptance gates.

## First red cycles after seam confirmation

T2: opening A-B prevents opening A-C, with a distinct error and unchanged state. Then implement just that behavior and expand through lifecycle/isolation cycles. T3: endpoint returns the exact anonymous payload from the real app, red shown before implementation. No product stubs or new tests are written merely by this proposal.
