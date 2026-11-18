# T8 — Engagement Threshold and consensual Reveal: seam draft

**Approved by Parth on 17 November 2026. Implementation authorized at these seams, tests first.**

Source: approved MVP spec #7 / docs/specs/mvp.md Rule4, identity payload and Conversation lifecycle; approved T7 delivery rules. T7 PR29 and H1 PR28 are merged. This is the previously missing T8 review document, not a new definition phase. Published as T8Issue30under#7 after approval.

## Settled behavior

- Eligibility requires all three: at least20 delivered Messages total, at least5 delivered by each participant, and at least72hours between the first delivered Message and the injected Clock's eligibility check. Escalated counts. Withheld never counts; a human-released Message counts once at its actual delivery time.
- Reveal needs both participants' consent. A participant may withdraw their own consent before completion. No Admin/model/outsider can consent for them. Completion is irreversible and scoped to this Conversation.
- Completion frees both active-Conversation slots. This Conversation remains open for chat until Block; safety moderation continues and pre-Reveal identifier escalation stops only here.
- Pre-Reveal partner payload has exactly pseudonym and values_profile. Revealed payload preserves those plus legal_name, email and optional phone. Never DOB/photos. Existing opaque wrappers and authorized serializer remain the identity-export mechanism.
- No public set-Reveal flag, client-controlled counts/time/participants, automatic expiry or progress UI. The minimal consent ceremony is core, not optional polish.

## Proposed pure domain seam

Proposed new module: src/vaeil/domain/reveal.py. Names/signatures below are interface proposals only.

```python
@dataclass(frozen=True, slots=True)
class DeliveredMessageEvidence:
    message_id: str
    conversation_id: str
    sender_id: str
    delivered_at: datetime

@dataclass(frozen=True, slots=True)
class RevealConsents:
    conversation_id: str
    consented_member_ids: frozenset[str]

@dataclass(frozen=True, slots=True)
class RevealTransition:
    conversation: Conversation
    consents: RevealConsents
    revealed_now: bool

def is_reveal_eligible(
    conversation: Conversation,
    *, delivered: tuple[DeliveredMessageEvidence, ...], now: datetime,
) -> bool: ...

def change_reveal_consent(
    conversation: Conversation,
    *, consents: RevealConsents,
    actor_id: str, consent: bool,
    delivered: tuple[DeliveredMessageEvidence, ...], now: datetime,
) -> RevealTransition: ...
```

Evidence is body-free and comes exclusively from the T7 delivered query, not HTTP input. Validate same Conversation, participant sender, distinct Message IDs and timezone-aware timestamps. Duplicated IDs must never inflate counts. The application supplies Clock.now(); the domain reads no real clock, filesystem, network or environment.

Proposed transition semantics for approval: adding consent requires eligibility now; the second consent completes Reveal in that same transition. Repeating an already-recorded consent is idempotent. Withdrawal before completion removes only the actor's consent, including when none was recorded; it never withdraws the other participant's consent. After completion, repeated consent is a no-op and withdrawal raises a distinct completed-Reveal error. Blocked changes and outsider actors raise distinct errors. Malformed evidence/consent state raises a separate validation error; all messages are fixed and input-free. These details are proposed interface behavior, not silently approved decisions.

## Application, storage and HTTP seam

Proposed RevealApplication with existing Repository, session principal, token source and Clock dependencies:

```python
read_reveal(*, actor, conversation_id) -> RevealStatusView
set_reveal_consent(*, actor, conversation_id, consent: bool) -> RevealStatusView
read_partner(*, actor, conversation_id) -> PreRevealMemberView | RevealedMemberView
```

Proposed frozen/slotted RevealStatusView fields: conversation_id, eligible, viewer_consented, revealed. No partner identity or optional threshold-progress counters. Public payloads are explicit dictionaries, never generic dataclass export.

Add UnitOfWork get_reveal_consents(conversation_id) and store_reveal_consents(consents), using the existing SQLAlchemy SQLite/Postgres layer and transaction serialization. Absent state means no consent. A consent row contains only Conversation/Member IDs, not identity or Message bodies. Reload current admitted Member role and participant pair for every operation. Read delivery evidence, check eligibility/Block, change consent, advance the stored Conversation and append the existing CONVERSATION_REVEALED audit event in one transaction. Use revealed_now to emit exactly one completion event. Roll back consent/state/audit together on failure. No moderation or password hashing inside this transaction.

read_partner derives the other participant server-side and calls existing project_member_for_viewer and serialize_member_view. No new private unwrap site. Projection never depends on whether the Member currently occupies another active slot.

Proposed same-origin cookie-authenticated routes:

- GET /api/conversations/{id}/reveal — viewer's current ceremony state.
- PUT /api/conversations/{id}/reveal/consent — record viewer's consent; empty body, no actor/count/time/Reveal fields.
- DELETE /api/conversations/{id}/reveal/consent — withdraw viewer's consent.
- GET /api/conversations/{id}/partner — explicit authorized pre/post-Reveal view.

Reuse T6/T7 authentication, Origin checks, no-store responses and safe errors. No public restore/force-Reveal route. Minimal Conversation UI loads status and partner view, offers consent only when eligible, offers withdrawal before completion, and refreshes state/identity after the operation. A failed or unconfirmed request never optimistically reveals identity. Repeated requests cannot duplicate audit or reverse completed disclosure.

## Tests and mutation gate, after approval

1. Pure boundary table:19/20 total,4/5 per side, immediately before/at72hours; all conditions combined, zero deliveries, only Withheld, Escalated and late human release. No real clock or sleeps.
2. Consent: unilateral insufficient, bilateral completion, own withdrawal, repeated request, completed irreversibility, stranger/blocked refusal, invalid pair/evidence and duplicate-ID refusal. Independent Conversations keep independent consent/state.
3. SQLite/Postgres contracts: durable consent, competing consents, consent-vs-withdrawal and consent-vs-Block serialize to a valid result; completion/audit once; rollback leaves no partial disclosure; active slots free only after completion. A committed Block before the consent transaction prevents Reveal.
4. Authenticated HTTP: cookie/role/Origin/pair guards; forged counts, time, actor and Reveal input refused. Canary tests pin exact pre/post field/key sets and scan wrappers, errors and serialized outputs; DOB remains excluded. No new unwrap allowlist entry.
5. Real-API browser: ineligible consent unavailable; unilateral consent leaves anonymous view; withdrawal works; bilateral completion shows authorized identity; refresh preserves completion. Synthetic fixtures supply Message/time boundaries without a public time/eligibility bypass. Sequential viva check: A-B Reveal, then A-C opens and C still sees anonymous A. Continued A-B chat still runs safety checks.
6. Show each red run before the minimal green change. Mutations drop each threshold, count Withheld, use creation time, remove bilateral/withdrawal/Block/pair checks, share consent across Conversations, double-audit completion, accept a client Reveal flag, leak DOB/private pre-Reveal fields or add an unapproved unwrap. Each must fail at an approved public seam. Purity and AST remain green; final two-axis review and CI before a merge request.

Rule5 stays partial. Rule4 evidence remains partial until its complete deployed viva path is exercised; do not increment completed-rule counts from pure tests alone.

## Handoff and estimate

The approval gate is satisfied; Issue30tracks implementation of these approved interfaces. Tests-first implementation proceeds on codex/t8-reveal; PR review/merge and deployment remain separate gates. Optimistic planning allowance remains2lead sessions, not measured velocity or a promise. Roughly7.5core sessions remain against about8available before28November, with little review/rework buffer. Protect Reveal, Admin, Report handling and all six rules. No new agent tooling or deployment in this proposal.

No new product questions identified; review the proposed technical interfaces and transition/error semantics above. H1Issue26 remains a separate human-understanding handoff; T4Issue11 and H7Issue16 still need their existing evidence/closure reconciled, not a renewed product interview.

Approval record: Parth says the T8 seams are good to move forward with. This approves the proposed interfaces and transition semantics above, publication under #7 and tests-first implementation. Earlier draft wording preserves the review source; its gate is satisfied. No merge/deployment authorization.
