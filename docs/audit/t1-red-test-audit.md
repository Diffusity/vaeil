# T1 frozen red-test audit

Date: 24-25 October 2026. Historical snapshot: audit approved; stricter changes were committed in 607062b, opaque refinement in 34bb4e9, then implemented. Frozen line references/hash below describe the audited 98-case version, not the current file. The original proposal and observations are preserved as history.

## Scope, time box and integrity

Audit start: 24 October 14:55:38 UTC. Budget: half a 2-3 hour session, with a planned 60-minute ceiling. The tool clock then advanced to 25 October 08:13:47 UTC alongside an environment date update: an overnight elapsed window, not evidence of continuous active work. Active effort cannot be reconstructed reliably, so this report does not claim the time box was met. Close the audit now rather than invent a duration; keep the 0.5-session budget distinct from measured actual effort. No implementation, stubs, mutations, model work, ticket publication, commits or test edits are part of this audit. Temporary runners and the deliberately leaky positive control ran outside the repository. Only this report and a curated session log are deliverables.

Sources: `docs/specs/t1-seam-proposal.md` (S), `docs/specs/t1-seam-amendment-diff.md` (D), the frozen `tests/test_member_identity_red.py`, existing slice-1/2 tests and domain code. A1-A8 below mean the eight amendments in the user's consolidated approval, not assumption IDs.

The frozen T1 file SHA-256 is `82510f04eddad695c70e78f0cb272f8f58370c0d5fbb582d0ec731df04509dd9`. All 16 Python source files under `src/` and `tests/` were hashed before execution. Final verification must compare both contents and the file set; do not treat an empty tracked Git diff as protection for untracked tests.

## Findings that affect approval

1. **98 failures are not 98 demonstrated behavior defects.** There are 32 test functions, 15 parametrized functions, and 98 collected cases. All 32 function groups were run separately in fresh pytest subprocesses. There are 95 missing-attribute failures, two actual DOB-leak assertions and one actual missing-TypeError assertion. No collection or pytest setup-phase errors occurred, but many call-phase failures are in helper/data construction before the intended assertion. I cannot honestly confirm that those 95 messages establish the intended behavior: they establish absent APIs/prerequisites only.
2. **Direct old/new API contradiction:** the existing slice-2 tests require `claim(id, candidate)` to succeed, while F29 requires it to raise without identity. The approved seam explicitly calls for migrating old callers, but that migration now requires approval under the freeze. Keep every old policy assertion; add required identity at those call sites. Do not add a permissive default or special-case test Member IDs.
3. **The canary helper misses a DOB in raw pickle bytes.** The positive control caught 39/40 materialized surface/field combinations, missing raw DOB pickle bytes. Unpickling reveals it and the separate roundtrip check catches it. The slot helper itself is blocked by missing `d.Member`/`d.MemberIdentity`; no standalone traversal-positive-control success is claimed. See the proposed helper patch.
4. **Missing coverage:** overlapping viewer-error precedence, duplicate participant IDs/arity, combining-character and emoji About boundaries, true Unicode casefold (`ß`), separator-specific token targets, Will punctuation/apostrophe, Markus, required empty choices, embedded controls, long whole-word performance, and age-gate error redaction. Deterministic set serialization is asserted only with singleton sets. Existing repr assertions fail before their subsequent str assertions, so their current failures demonstrate repr leaks, not independently executed str checks.
5. No incompatible expected values were found **within the 98 cases**. Missing cases are not proof of consistency for all inputs. Exact code-point semantics and raw-control rejection are consistent with the current seam; UI/API auth, draft storage and Matching eligibility remain later-ticket obligations.

## Inventory: all 98 cases

All test IDs in the following single table are relative to `tests/test_member_identity_red.py`; the cited line is the frozen function's `def`, not its decorator. Each bracket lists all grouped parametrized suffixes, with a case count. F identifiers are stable audit references, not replacement test names.

Failure notation: `A(name)` is `AttributeError: module 'vaeil.domain' has no attribute 'name'`. `L` is an actual legacy DOB-leak assertion. `R` is an actual `Failed: DID NOT RAISE TypeError`. Missing helper/error/enum attributes are explicitly marked **blocked**; the intended behavioral assertion has not run. Every case failed when its function group ran independently; no import failure or setup-phase error is hidden in a category.

Quality flags: **V-part** = a vacuous sub-assertion, not the whole test; **D** = duplicate coverage; **OB** = exception-origin breadth or message-coupled wording; **P** = required structural/private-name reflection (`__dict__`, `__slots__`, `__mro__`), not a private domain method. A dash means none of the requested flags. No frozen case uses the real clock, randomness, network, filesystem I/O, process environment or mutable shared fixture state. `pickle` here is in-memory. Cases were executed on Windows. The audit runners do use temporary files and subprocesses; those are not dependencies of the frozen tests.

| Test ID, frozen file:line and cases | Requirement | Failure today | Minimal wrong implementation caught | Quality flags | Verdict / reason |
| --- | --- | --- | --- | --- | --- |
| F01 `test_pre_reveal_type_and_serialized_keys_are_exactly_the_allow_list` (1); `tests/test_member_identity_red.py:90`; cases: unparametrized | A1; S:39,70,89 | A(project_member_for_viewer) x1; assertion blocked | Return Member or add email to the anonymous view. | — | **keep** — Exact independent type/field/key pins. |
| F02 `test_private_canaries_are_absent_from_every_pre_reveal_route` (8); `tests/test_member_identity_red.py:102`; cases: repr; str; dict; slots; pickle; pickle-roundtrip; asdict; json | A4; S:71-72,90 | A(project_member_for_viewer) x8; assertion blocked | Retain an identity in a hidden slot or serialized payload. | V-part: dict branch scans an always-empty fallback; P: required graph reflection | **tighten** — Add positive controls, decouple graph inspection, decode pickle for DOB and retain no-dict assertion. |
| F03 `test_serialization_keeps_profile_codes_and_no_private_nested_payload` (1); `tests/test_member_identity_red.py:126`; cases: unparametrized | A5; S:70,74-83 | A(serialize_member_view) x1; assertion blocked | Serialize display labels, wrong nested fields or unstable set order. | D: top-level keys overlap F01; distinct transport oracle | **tighten** — Use a multi-selection literal payload to expose ordering, retaining code/key expectations. |
| F04 `test_reveal_adds_identity_without_removing_the_public_profile` (1); `tests/test_member_identity_red.py:139`; cases: unparametrized | A1/A4; S:39-44,90 | A(MemberIdentity) x1; assertion blocked | Reveal removes the profile or hides DOB inside the serialized profile. | — | **tighten** — Retain five-field pin; add DOB repr fingerprint, not ISO alone. |
| F05 `test_optional_phone_remains_absent_after_reveal_when_not_supplied` (1); `tests/test_member_identity_red.py:154`; cases: unparametrized | A1; S:24-25,40 | A(project_member_for_viewer) x1; assertion blocked | Replace an absent phone with a fabricated contact or omit its fixed field. | — | **keep** — None is a meaningful approved value, not a vacuous is-not-None check. |
| F06 `test_reveal_in_one_pair_does_not_reveal_the_subject_in_another` (1); `tests/test_member_identity_red.py:162`; cases: unparametrized | A2/A8; S:16,44,90 | A(MemberIdentity) x1; assertion blocked | Cache revealed status globally by Member and leak A to C. | — | **keep** — Same object, two pairs, third Member and anonymous reprojection. |
| F07 `test_viewer_errors_are_distinct_and_do_not_echo_identity` (6); `tests/test_member_identity_red.py:183`; cases: self-SelfViewerError-anonymous; self-SelfViewerError-revealed; outsider-ViewerNotParticipantError-anonymous; outsider-ViewerNotParticipantError-revealed; wrong-subject-SubjectNotParticipantError-anonymous; wrong-subject-SubjectNotParticipantError-revealed | A2/A4; S:69,71 | A(ConversationRevealState) x6; assertion blocked | Use one error type or echo an outsider identifier. | — | **tighten** — Keep all six cases; add overlapping-invalid-input precedence test. |
| F08 `test_owner_projection_is_a_separate_redacted_view` (1); `tests/test_member_identity_red.py:200`; cases: unparametrized | A2/A4; S:41-44,69 | A(project_own_profile) x1; assertion blocked | Reuse anonymous projection for the owner or print owner identity. | D: repr/str assertions overlap F09[own] | **keep** — Owner payload/own-function contract stays; merge the other duplicate instead. |
| F09 `test_private_records_never_print_identity_values` (4); `tests/test_member_identity_red.py:210`; cases: identity; member; revealed; own | A4; S:71 | A(MemberIdentity) x2; assertion blocked; A(project_member_for_viewer) x1; assertion blocked; A(project_own_profile) x1; assertion blocked | Redact identity alone but allow enclosing Member/revealed diagnostics to leak. | D: own case duplicates F08 | **merge** — Keep identity/member/revealed cases; own redaction remains in F08. |
| F10 `test_existing_date_of_birth_holders_also_redact_private_representations` (2); `tests/test_member_identity_red.py:224`; cases: applicant; redeemed-invite | A4; S:71 | L x1; repr leak reached; L x1; repr leak reached | Keep default Applicant repr, exposing DOB directly or nested in Invite. | — | **tighten** — Parametrize repr and str separately so repr failure does not conceal str. |
| F11 `test_approved_records_are_frozen_slotted_and_have_no_photo_field` (7); `tests/test_member_identity_red.py:234`; cases: identity; member; profile; pre; post; own; conversation | A4/A8; S:20,44,71 | A(MemberIdentity) x3; assertion blocked; A(project_member_for_viewer) x2; assertion blocked; A(project_own_profile) x1; assertion blocked; A(ConversationRevealState) x1; assertion blocked | Use unslotted or partly mutable records, or add a photo field. | P: required __dict__/field reflection | **tighten** — Attempt assignment to every field using its existing valid value, not only field zero. |
| F12 `test_member_cannot_supply_a_global_reveal_flag` (1); `tests/test_member_identity_red.py:257`; cases: unparametrized | A8; S:44,93 | A(MemberIdentity) x1; assertion blocked | Accept a discarded/global revealed constructor argument on Member. | — | **tighten** — Existing absence checks miss swallowed kwargs; add explicit constructor refusal. |
| F13 `test_stable_enum_codes_are_the_approved_vocabulary` (6); `tests/test_member_identity_red.py:272`; cases: intent; stage; communication; pace; interests; values | A5; S:74-83 | A(RelationshipIntent) x1; assertion blocked; A(LifeStage) x1; assertion blocked; A(CommunicationStyle) x1; assertion blocked; A(PaceAndLifestyle) x1; assertion blocked; A(Interest) x1; assertion blocked; A(CoreValue) x1; assertion blocked | Rename a code, add a display label as a code, or omit an approved choice. | — | **keep** — Literal code sets independent of implementation; six namespaces. |
| F14 `test_complete_profile_selection_boundaries` (8); `tests/test_member_identity_red.py:279`; cases: 0-False-interests; 0-False-values; 1-True-interests; 1-True-values; 5-True-interests; 5-True-values; 6-False-interests; 6-False-values | A6; S:31-32,59 | A(Interest) x4; assertion blocked; A(CoreValue) x4; assertion blocked | Allow zero/six selections or store a mutable collection. | — | **keep** — Both sides of each boundary; enum order only chooses valid inputs, not expected lengths. |
| F15 `test_duplicate_selections_are_refused_before_frozenset_conversion` (2); `tests/test_member_identity_red.py:292`; cases: interests; values | A6; S:59 | A(Interest) x1; assertion blocked; A(CoreValue) x1; assertion blocked | Silently deduplicate repeated choices instead of refusing the write. | — | **keep** — Repeated list input reaches validation before frozenset conversion. |
| F16 `test_unknown_choice_cannot_be_saved` (6); `tests/test_member_identity_red.py:301`; cases: relationship_intent; life_stage; interests; values; communication_style; pace_and_lifestyle | A5/A6; S:59,74-83 | A(InvalidValuesProfileError) x6; assertion blocked | Accept arbitrary unknown choices or echo the rejected private value. | — | **keep** — Six structured fields plus repr/str redaction; add missing-required cases separately. |
| F17 `test_about_is_optional_and_normalized_before_storage_and_counting` (1); `tests/test_member_identity_red.py:309`; cases: unparametrized | A7; S:61 | A(MemberIdentity) x1; assertion blocked | Count raw fullwidth/space input or store unnormalized About. | — | **keep** — Default, normalization, storage and 280/281 witnesses; complementary not contradictory. |
| F18 `test_about_within_the_limit_is_not_truncated_or_rejected` (4); `tests/test_member_identity_red.py:318`; cases: empty; blank; 279; 280 | A7; S:61 | A(MemberIdentity) x4; assertion blocked | Reject/truncate otherwise valid short or 280-character About. | —; oracle currently calls .strip() | **tighten** — Use explicit expected literals rather than the same trimming operator. |
| F19 `test_about_normalization_expansion_is_counted_not_raw_length` (1); `tests/test_member_identity_red.py:322`; cases: unparametrized | A7; S:61 | A(InvalidValuesProfileError) x1; assertion blocked | Count a compatibility ligature as one stored character. | — | **keep** — Independent 93x3/94x3 arithmetic. |
| F20 `test_about_control_characters_are_refused_even_at_trim_boundaries` (7); `tests/test_member_identity_red.py:330`; cases: nul; lf; cr; tab; esc; del; c1 | A7; S:61 | A(InvalidValuesProfileError) x7; assertion blocked | Strip edge controls and silently accept a profile. | — | **keep** — Seven Cc controls; add middle cases separately without dropping edges. |
| F21 `test_every_identifier_category_refuses_the_entire_profile_save` (5); `tests/test_member_identity_red.py:338`; cases: email; phone; handle; obfuscated; url | A3/A7; S:46,61 | A(MemberIdentity) x5; assertion blocked | Skip an identifier category at the profile write seam. | — | **keep** — Each category, refusal and safe retry; no persistence transaction is claimed. |
| F22 `test_generated_text_uses_the_same_validated_profile_write_seam` (1); `tests/test_member_identity_red.py:349`; cases: unparametrized | S:46; A7 | A(InvalidValuesProfileError) x1; assertion blocked | Same unchecked-email bug as F21; no distinct generated-source path is exercised. | D: duplicate email write; suspect as separate integration claim | **merge** — Move this exact input into F21; do not claim adapter/storage coverage. |
| F23 `test_profile_errors_never_print_private_rejected_text` (3); `tests/test_member_identity_red.py:356`; cases: legal-name; email; phone | A4/A7; S:71 | A(InvalidValuesProfileError) x3; assertion blocked | Echo rejected legal name/email/phone in diagnostics. | — | **keep** — One distinct canary per case; checks both repr and str. |
| F24 `test_about_whole_word_mode_accepts_market_for_mark` (1); `tests/test_member_identity_red.py:363`; cases: unparametrized | A3; S:65 | A(MemberIdentity) x1; assertion blocked | Apply substring mode to About at the factory boundary. | — | **keep** — Factory integration is distinct from F26 direct-predicate tests. |
| F25 `test_about_will_false_positive_gives_safe_rephrase_feedback` (1); `tests/test_member_identity_red.py:368`; cases: unparametrized | A3; S:65 | A(MemberIdentity) x1; assertion blocked | Miss the intentional Will false positive or print its private token. | OB: message-coupled keyword oracle | **tighten** — A valid “try different wording” message would fail; propose stable field/reason/rephrase attributes for approval, while keeping name redaction. |
| F26 `test_shared_predicate_has_distinct_pseudonym_and_about_modes` (6); `tests/test_member_identity_red.py:382`; cases: substring; whole-word; casefold; punctuation; embedded-about; embedded-name | A3/A8; S:65,92 | A(MemberIdentity) x6; assertion blocked | Use one matching mode or whitespace-only boundaries for both contexts. | — | **tighten** — Keep six cases; add apostrophe/period, true casefold and About NFKC witnesses. |
| F27 `test_self_name_normalization_tokens_and_length_boundary` (7); `tests/test_member_identity_red.py:396`; cases: nfkc-name; nfkc-local; email-separators; name-separators; short; three; not-domain | A3/A8; S:65,92 | A(MemberIdentity) x7; assertion blocked | Use the whole email local part or wrong normalized-token length. | — | **tighten** — Mixed separator examples do not prove every separator; add independent targets and normalized-length changes. |
| F28 `test_pseudonym_self_name_failure_does_not_consume_the_slot` (1); `tests/test_member_identity_red.py:401`; cases: unparametrized | A3/A4; S:46,65,71 | A(MemberIdentity) x1; assertion blocked | Consume a failed self-name claim or disclose its normalized token. | — | **tighten** — Keep retry; check repr and casefolded Mark in error, not original-case str only. |
| F29 `test_pseudonym_claim_requires_private_identity_without_a_bypass_default` (1); `tests/test_member_identity_red.py:410`; cases: unparametrized | S:46; A8 | R x1; intended behavior reached | Leave identity optional, allowing claims with no self-name context. | OB: any unrelated TypeError could satisfy current assertion; old/new API conflict | **tighten** — Pin required keyword-only public signature and migrate old callers; keep missing-argument refusal. |
| F30 `test_claim_rejects_a_mismatched_identity_without_leaking_private_values` (1); `tests/test_member_identity_red.py:415`; cases: unparametrized | S:46,71; A4 | A(IdentityOwnerMismatchError) x1; assertion blocked | Use another owner identity to evade checks or leak it in exception repr. | — | **tighten** — Keep owner-mismatch type/str; add repr and successful retry after refusal. |
| F31 `test_repeated_same_pseudonym_still_hits_the_fixed_once_guard` (1); `tests/test_member_identity_red.py:421`; cases: unparametrized | S:46,92; A8 | A(MemberIdentity) x1; assertion blocked | Treat claiming the same fixed name as idempotent success. | D: existing test_claiming_the_same_name_twice_is_still_a_change_attempt | **merge** — Delete duplicate only with approved identity migration of the existing test. |
| F32 `test_taken_claim_can_retry_and_preserves_normalized_uniqueness` (1); `tests/test_member_identity_red.py:429`; cases: unparametrized | S:46,92; A8 | A(MemberIdentity) x1; assertion blocked | Treat fullwidth normalized duplicate as free or consume loser slot. | D: existing normalized-name and failed-taken-retry cases | **merge** — Keep those old assertions after required-identity migration; then remove this duplicate composite. |

### Counts and every non-keep verdict

| Verdict | Functions | Cases |
| --- | ---: | ---: |
| keep | 14 | 44 |
| tighten | 14 | 47 |
| merge | 4 | 7 |
| remove | 0 | 0 |
| Total | 32 | 98 |

Failure categories: **95 missing attribute; 2 existing-leak assertions; 1 missing-required-argument assertion; 0 missing imports; 0 pytest setup/collection errors.** Quality-flag groups (overlapping): partial-vacuity 1 affected case in 1 group; duplicate assertions 6 affected cases in 6 groups (including both sides of the F08/F09 overlap); message/exception breadth 2 cases in 2 groups; required structural reflection 10 cases in 2 groups; suspect separate claim 1 group/1 case. Other requested risk flags: zero in the frozen T1 file.

Verdict counts are **cases reviewed under that group verdict**, not numbers to delete. In particular, F09's merge proposal removes only its `own` duplicate, retaining its other three cases. No deletion or tightening has been applied.

Non-keep list: **F02, F03, F04, F07, F09, F10, F11, F12, F18, F22, F25, F26, F27, F28, F29, F30, F31, F32**. The reasons are in their rows and the complete proposal below. F25 proposes structured `field="about"`, `reason="self_name"`, and `can_rephrase=True` error attributes rather than requiring the literal word “rephrase”; those attributes are an explicit public-contract proposal for approval, not a settled seam change. F22 is suspect as a separate test: a local variable named `generated` does not exercise an LLM or storage path distinct from F21. It still tests a valid rejected string; merge that exact input into F21 rather than claiming an extra integration path. No requirement-free domain behavior was found elsewhere. F09/F31/F32 are conditional deduplications, not weaker rules.

## Isolated execution and representative failures

Each F01-F32 was run with a fresh process:

```powershell
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --tb=short -rN tests/test_member_identity_red.py::<function>
```

JUnit output went to an OS temporary directory for exact case/error accounting. Different messages within a parametrized group were also counted, not inferred from its first case.

All **16 distinct message groups** below were observed in the isolated runs (the two date assertions differ by holder):

| Representative failure message | Cases |
| --- | ---: |
| `AttributeError: module 'vaeil.domain' has no attribute 'project_member_for_viewer'` | 13 |
| `AttributeError: module 'vaeil.domain' has no attribute 'serialize_member_view'` | 1 |
| `AttributeError: module 'vaeil.domain' has no attribute 'MemberIdentity'` | 36 |
| `AttributeError: module 'vaeil.domain' has no attribute 'ConversationRevealState'` | 7 |
| `AttributeError: module 'vaeil.domain' has no attribute 'project_own_profile'` | 3 |
| `assert '1998, 7, 23' not in "'Applicant(...98, 7, 23))'"` | 1 |
| `assert '1998, 7, 23' not in '"Invite(cod...8, 7, 23)))"'` | 1 |
| `AttributeError: module 'vaeil.domain' has no attribute 'RelationshipIntent'` | 1 |
| `AttributeError: module 'vaeil.domain' has no attribute 'LifeStage'` | 1 |
| `AttributeError: module 'vaeil.domain' has no attribute 'CommunicationStyle'` | 1 |
| `AttributeError: module 'vaeil.domain' has no attribute 'PaceAndLifestyle'` | 1 |
| `AttributeError: module 'vaeil.domain' has no attribute 'Interest'` | 6 |
| `AttributeError: module 'vaeil.domain' has no attribute 'CoreValue'` | 6 |
| `AttributeError: module 'vaeil.domain' has no attribute 'InvalidValuesProfileError'` | 18 |
| `Failed: DID NOT RAISE TypeError` | 1 |
| `AttributeError: module 'vaeil.domain' has no attribute 'IdentityOwnerMismatchError'` | 1 |

Examples retaining the relevant call site:

```text
F01 -> projected() -> d.project_member_for_viewer(...)
AttributeError: module 'vaeil.domain' has no attribute 'project_member_for_viewer'
# Intended public operation is absent; exact-shape assertion has not executed.

F04 -> member() -> identity() -> d.MemberIdentity(...)
AttributeError: module 'vaeil.domain' has no attribute 'MemberIdentity'
# Helper construction is blocked; this is NOT evidence of a wrong revealed payload.

F07 -> conversation() -> d.ConversationRevealState(...)
AttributeError: module 'vaeil.domain' has no attribute 'ConversationRevealState'
# Pair fixture is blocked; viewer error selection has not executed.

F29 -> with pytest.raises(TypeError): directory.claim('subject', 'Comet')
Failed: DID NOT RAISE TypeError
# This reaches the actual intended missing-identity behavior today.

F10[applicant] -> assert_no_canary(repr(value))
assert '1998, 7, 23' not in "'Applicant(date_of_birth=datetime.date(1998, 7, 23))'"

F10[redeemed-invite] -> assert_no_canary(repr(value))
assert '1998, 7, 23' not in '...redeemed_by=Applicant(date_of_birth=datetime.date(1998, 7, 23))...'
```

The last Invite line is an excerpt of the observed assertion, not an exact full-message oracle. New tests must not depend on pytest's formatting/truncation. Re-run targeted groups after their prerequisites exist before claiming behavior-sensitive red/green or mutation results.

## Traceability matrix

| Requirement and source | Current tests | Gap / boundary |
| --- | --- | --- |
| A1; S:39-44: exact two pre-Reveal fields; revealed preserves public fields plus permitted identity; no DOB/photos | F01-F05, F11 | F04 checks DOB ISO only in serialized payload; strengthen date-object/representation detection. |
| A2; S:16,69: subject/viewer are the actual pair, self view separate and distinct errors | F06-F08 | No overlapping-error precedence test or invalid participant-construction cases. No claim that these tests prove future HTTP authentication. |
| A3; S:63-65: shared normalized tokens, substring Pseudonym, whole-word About, Mark/market and Will false-positive feedback | F24-F28; F21/F23 integrate profile refusal | No `Will.`, `will's`, `Markus`, true casefold or separator-by-separator oracles; long predicate test absent. |
| A4; S:20,71-72: frozen/slotted, no private repr/str/errors, no Member/identity reference, canary surfaces | F02, F07-F11, F23, F28, F30 | Single-field freeze attempt; raw-pickle DOB false negative; independent scanner/traversal controls absent; age-gate errors untested for redaction. |
| A5; S:74-83: exact stable enum codes; frontend labels separate | F03, F13, F16 | Frontend does not exist: no label-layer test claimed. No multi-value deterministic serialization test. |
| A6; S:31-32,59: complete 1-5 unique frozenset selections | F14-F15, F11 | Alias mutation and required single-choice empties absent. Draft persistence belongs T6; T10 candidate selection must reject incomplete profiles. These are not silently declared tested by T1. |
| A7; S:61: optional About, trim/NFKC before 280 count, store normalized text, controls rejected, scanner plus whole-word check | F17-F25, F19 | Combining/emoji and embedded-control cases absent; F18 expected values call `.strip()` rather than use literal oracles. |
| A8; S:89-94: signature/types, vocabularies, separate red-green cycles, mutation checks, purity, Rule 5 partial | F01-F32 plus existing purity tests and docs | Execution/workflow obligations are gates, not all unit-testable. Signature constructor rejection and fixed-once precedence need stronger direct tests. Mutations not executed before implementation. |
| S:46: factory used for Member and generated text; no unchecked application save | F21-F23 | F22 covers the same factory with an email input; it does not prove a future LLM/storage adapter uses that factory. Application wiring tests belong T6 and local-model integration. |
| S:46: required private identity on claim, owner ID match, fixed-once first, retry semantics | F28-F32, existing `test_pseudonyms.py` | Mandatory old-caller migration; no competing-invalid-input test to prove fixed-once wins. |
| S:16/44: Reveal belongs Conversation, never Member; same Member in two pair contexts | F06/F12 | Explicit constructor rejection of Member Reveal input absent. |
| S:16: no active-slot/consent policy inside pure projection | F06 independent pair fixtures | T2 tests active-slot lifecycle; T4/T6 tests authoritative HTTP lookup. No artificial active-slot gate added to T1. |
| S:44/94: DOB absent in both Match views; no photos | F01/F04/F11 | Photo check only searches dataclass fields; graph tests/explicit view shape also matter. No image-upload implementation exists. |
| S:70: JSON-ready encoding and deterministic lists | F01/F03/F04/F05 | Singleton selections cannot establish ordering; owner serializer not exercised. |
| S:71: legacy Applicant/Invite DOB redaction | F10 | Add independently executed str and public age-gate error cases. |
| S:93: mutation list, purity; S:94 excludes consent/threshold/delivery/storage/UI | Purity suite; future mutations | Mutation preview below; TESTING remains 3/6 domain, 0/6 E2E, Rule 5 partial. No T1 test claims delivery or consent works. |

Requirements with **no current test** are enumerated in the gap column, the construction/boundary/self-name sections and the proposed additions. Deferred requirements are named, not counted as missing T1 implementations: T6 draft/account storage, T10 complete-profile eligibility, UI labels, transport auth, storage atomicity, generated-text adapter routing and actual consent. Tests with **no unique requirement**: F22 as a separate case; F09[own], F31/F32 duplicate already mapped requirements. No unexplained product requirement was invented by another frozen case. The owner projection's private payload is an explicit seam proposal, not a pre-Reveal payload.

## Contradiction and precedence check

Within the 98 cases, no identical valid input has incompatible expected outputs. About fullwidth expansion is checked after normalization; raw controls are rejected even if trimming would remove them, matching S:61. `market` is valid About for Mark but invalid as a Pseudonym under the **different explicitly selected mode**. Will's ordinary-word false positive is intentional, not a contradictory clean-text guard. `phone=None` is the optional-field representation while the revealed field set stays fixed.

**Across old/new suites, the claim-signature contradiction is real.** `tests/test_pseudonyms.py:16-21` expects `claim('member-1', 'Comet')` to return a Pseudonym; F29 expects an identity-free valid claim to raise. Neither expectation can be made conditional on test IDs. Proposed migration preserves the old assertions and supplies authoritative synthetic identity explicitly. All such callers are listed by the generated patch, not silently skipped.

Observable viewer precedence to pin: subject-outside-pair wins when the viewer is also invalid/self; otherwise own-view raises SelfViewerError and a nonparticipant raises ViewerNotParticipantError. With a valid subject, self and nonparticipant violations cannot overlap, so a black-box test cannot establish an internal ordering between mutually exclusive predicates. The proposed `test_viewer_error_precedence` below pins the externally meaningful selection. **It is not yet in the frozen suite and has not been run.**

`ConversationRevealState` currently has **no construction validation test**. Proposal: exactly two distinct participant IDs; reject duplicate, one-ID and three-ID tuples with a proposed `InvalidConversationParticipantsError` (name requires approval with this patch). Projection separately rejects an outside subject; self and outsider viewers have their distinct approved errors. A duplicate pair cannot be used as a projection fixture because its construction should already fail.

## Independent expected-value oracles

These derive from Unicode character decompositions and fixed literals, not a proposed domain implementation. Cross-check ran using the actual venv: **Python 3.11.2, Unicode database 14.0.0**. System Python is not substituted for the test interpreter.

| Input / rule | Independent derivation and expected result | Frozen coverage |
| --- | --- | --- |
| `Ａ` U+FF21 | Unicode compatibility decomposition `<wide> 0041`: one ASCII A. 280 copies -> 280 code points; 281 -> 281. Surrounding spaces are trimmed; stored text is ASCII A repeated. | F17 |
| `ﬃ` U+FB03 | `<compat> 0066 0066 0069`: each ligature becomes three code points `ffi`. 93 × 3 = 279 (accept), 94 × 3 = 282 (reject). Expected strings must remain literal `"ffi" * 93`, not calculated by calling the domain normalizer. | F19 |
| `e\u0301` | e plus combining acute is two input code points; canonical composition yields U+00E9 é, one stored code point. 280 pairs -> 280 stored characters (accept), 281 -> 281 (reject). | **Missing; proposed** |
| `🙂` | U+1F642 is one Python Unicode code point despite two UTF-16 code units on Windows. NFKC does not change it. 280 accept, 281 reject. | **Missing; proposed** |
| `👍🏽` | Base emoji plus skin-tone modifier is two code points, not one grapheme for this cap: 140 copies = 280 (accept); plus one ASCII x = 281 (reject). Neither is a Cc control. | **Missing; proposed** |
| `Straße` / `STRASSE` | NFKC leaves Straße unchanged; Unicode casefold maps ß -> ss, giving `strasse` for both. `.lower()` alone is insufficient. | **Missing; proposed** |
| `ßa` | Raw token has two code points; after casefold it is `ssa`, three. Under normalized-token length semantics it qualifies and must flag `StarSSA`. | **Missing; proposed** |
| `A\u030An` | Three raw code points compose to Ån, then casefold to ån: two normalized code points, so ignored. | **Missing; proposed** |
| `Li` vs `Ana` | Normalized `li` has two characters and is ignored; `ana` has three and flags `StarAna` in Pseudonym mode. No name-recognition claim. | F27[short,three] |
| Email `sara.lee_chen-park+jo@example.invalid` | Local part only; splitting produces sara, lee, chen, park, jo; lengths 4,3,4,4,2. Jo ignored. Current target StarChen proves chen, **not every separator**. | F27[email-separators], partial |
| `mint+surya@...`, `mint.surya@...` | Independently, local tokens mint/surya; each >=3, so StarSurya flags in substring mode. Target after plus/dot ensures the separator actually matters. Domain `example` must not become a token. | Plus/dot targets **missing**; F27[not-domain] protects exclusion. |
| Will punctuation | Token will is bounded by whitespace/punctuation in `Will.` and `will's`; both flag. It is embedded in `willow`, which must not flag About. `Markus` contains mark and flags Pseudonym; market has no whole-word mark. | Mark/market, Mark comma and bookmark covered; requested Will/Markus cases **missing**. |
| Controls | NUL/LF/CR/TAB/ESC/DEL/NEL are category Cc. NEL U+0085 and tab/newline can disappear under trimming, so controls must be rejected on raw input before such loss. NFKC leaves NEL unchanged. | F20 edges covered; middle missing. Cf/ZWJ policy is not decided by these tests. |

The new boundary examples use a fixed clock nowhere; a time-bounded subprocess in the performance proposal measures only a test hang, not domain time. “Characters” remains code points, not grapheme clusters or UTF-8 bytes. No normalization helper is used to compute the proposed assertions' expected values.

## Canary positive control and surfaces

Each field has a distinct value: legal name `CanaryNameZXQ`; email `canarylocalzxq@example.invalid`; phone `+919876543210`; DOB `date(1998, 7, 23)`. Date fingerprints include its ISO spelling and `1998, 7, 23` in Python repr. Values share no identical whole-canary string. Each positive-control run injected **one field only**, preventing one detected field from masking another missed field.

The following deliberately leaky fake was executed in a temporary audit script, not added to tests or source:

```python
@dataclass(frozen=True, slots=True)
class DeliberatelyLeakyView:
    pseudonym: str = "Comet"
    values_profile: str = "Reading"
    leaked: object = None  # intentionally violates the real allow-list

fake = DeliberatelyLeakyView(leaked=date(1998, 7, 23))
assert_no_canary(asdict(fake))  # raises AssertionError: date repr detected
assert_no_canary(pickle.dumps(fake))  # DOES NOT raise today: genuine gap
assert_no_canary(pickle.loads(pickle.dumps(fake)))  # raises: date detected
```

The audit caught the expected AssertionErrors rather than allowing them to abort the report. A clean fake with leaked=None passed. No product classes were monkeypatched or stubbed to run the control.

| Materialized surface sent to current scanner | Name | Email | Phone | DOB |
| --- | --- | --- | --- | --- |
| repr | caught | caught | caught | caught |
| str | caught | caught | caught | caught |
| dictionary payload | caught | caught | caught | caught |
| slot values materialized from fake dataclass fields | caught | caught | caught | caught |
| dataclasses.asdict | caught | caught | caught | caught |
| JSON (date explicitly encoded as ISO) | caught | caught | caught | caught |
| exception str | caught | caught | caught | caught |
| exception repr | caught | caught | caught | caught |
| pickle bytes | caught | caught | caught | **missed** |
| unpickled fake | caught | caught | caught | caught |
| current inspect_graph(fake) traversal | blocked: missing Member | blocked | blocked | blocked |

These are 39 caught / 1 missed across 40 materialized combinations, plus four blocked traversal calls. The materialized-slot row does **not** establish that the existing slot traversal works without domain types. The dictionary payload control also does not mean a real pre-Reveal view may have `__dict__`: absence is a separate structural requirement. Freeze remains intact. Proposed positive-control tests use ordinary test-only fakes, not replacements for domain APIs.

Surfaces required in the actual pre-Reveal suite: repr, str, absent `__dict__`, recursive slots/object graph, raw pickle bytes **and decoded state**, roundtrip equality, dataclasses.asdict, public JSON serialization and exception repr/str. Private identity/owner/revealed records must redact repr/str/errors; their authorized private fields, raw asdict/slots/pickle are intentionally not secrecy boundaries. No private record may be reachable from a pre-Reveal graph, even if its repr is redacted. Add cycle protection if traversal is extended to arbitrary graphs; approved value types should be acyclic.

## Pinned shapes and isolation evidence

Frozen F01 already asserts:

```python
{field.name for field in fields(view)} == {"pseudonym", "values_profile"}
set(serialize_member_view(view)) == {"pseudonym", "values_profile"}
```

Frozen F04 already asserts the revealed field set and JSON key set:

```python
{"pseudonym", "values_profile", "legal_name", "email", "phone"}
```

These are direct literal pins, not snapshots derived from implementation. DOB/photos are absent; optional phone remains a field with None when absent. Actual code uses `d.serialize_member_view`; the excerpts abbreviate the namespace only.

Frozen F06 constructs **one Member object** and supplies it to `(subject, viewer, revealed=True)` and `(subject, third, revealed=False)` with separate conversation IDs. It asserts RevealedMemberView for the first, PreRevealMemberView for the second, scans the second JSON and projects the anonymous pair again. F07 tests a viewer outside the pair and a subject outside `(viewer, third)`. No active-slot lifecycle is simulated, correctly: this pure projection test does not enforce the one-active rule. Constructor duplicate-ID/arity rejection is absent, not “implicitly covered” by F07; proposed below.

## Boundaries and self-name completeness

Already covered: About optional/empty/ASCII whitespace-only, 279/280 ASCII, 280/281 fullwidth after NFKC and trim, ligature expansion 279/282; interests and values 0/1/5/6, duplicate and unknown choices; seven Cc controls at both trim boundaries; 2/3 token threshold; mixed-case ASCII/fullwidth names and email-local forms; a multi-token name; shared two-mode behavior; Mark/market and Will/will; typed exceptions and retry after failed claims.

Not covered by those cases: 281 ASCII (only 281 fullwidth), combining sequences/emoji, internal controls, None/empty required single choices, Will period/apostrophe and Markus, ß casefold, independent plus/dot/whitespace token witnesses, normalized length changes at 2/3, empty/whitespace/very-long predicate input, one-owner direct token checks in About mode for every normalization variant, concurrent persistence uniqueness (later T5), and cross-Conversation lifecycle (later T2). Proposed additions below target the T1 gaps; do not call them current coverage.

Immutability today: F11 verifies dataclass status, absence of __dict__, no photo-named field and freezing **only the first field** per record. F14 proves the selected collections are frozensets. F02's graph probe forbids Member/MemberIdentity references but cannot independently run before those types exist. Add all-field assignment attempts and input-list alias checks; do not replace immutable collection requirements with tuple/list equivalence.

Legacy DOB: F10 contains repr and str assertions for Applicant and redeemed Invite, but current repr failures short-circuit str. There is no current age-gate-error redaction test. Existing age tests assert specific types and dates, not safe diagnostic text. Proposed extra cases retain those types, run repr and str separately and check FutureDateOfBirthError, UnderageError, InvalidInviteError and InviteAlreadyRedeemedError through the real redemption seam with a fixed FakeClock.

## Mutation preview — not executed

These are candidate killing tests, conditional on them reaching assertions after implementation. No mutation is claimed killed by a missing API. No source was rewritten during the audit.

| Mutation / plausible regression | Current expected killer | Gap or proposed killer |
| --- | --- | --- |
| Add/accept Member-level Reveal flag | F12 detects a declared field/property | Constructor swallowing a kwarg is not caught; add explicit Member(revealed=True) refusal. |
| Add private field to pre-Reveal dataclass/JSON | F01/F03; F02 canaries | DOB in raw pickle needs decoded-state check; hidden Member refs need traversal control. |
| Ignore Conversation Reveal state / always reveal | F01/F04/F06 | Different-pair isolation is necessary even if single-input tests pass. |
| Global cache keyed only by Member | F06 | Repeat order reversals would strengthen cache-safety; no active-slot mock needed. |
| Drop whole-word rule, use substring for About | F24; F26[whole-word,embedded-about] | These should fail immediately for market/bookmark. |
| Use whole-word for Pseudonyms | F26[substring,embedded-name], F28 | Add explicit Markus witness and punctuation-boundary cases. |
| Drop private repr redaction | F09/F10/F08 and date fingerprints | str-only leak needs independent str cases; age-error printing requires new tests. |
| Drop error redaction | F07/F23; partial F28/F30 | Tighten F28/F30 repr/normalized-name checks; add age errors. |
| Remove self-name NFKC | F27[nfkc-name,nfkc-local] | Both modes should have independent witnesses; proposed extra About rows. |
| Remove casefold | F26[casefold], F27 mixed-case | Replacing casefold with lower survives ASCII; proposed Straße/STRASSE. |
| Change token minimum to 2 or 4 | F27[short,three] | Add post-normalization length changes ßa/A-ring-n. |
| Do not split email plus or dot | F27 mixed token test does not prove each | Add target immediately after plus and dot, separately. |
| Include email domain as name token | F27[not-domain] | Current direct witness adequate. |
| Remove About scan / any scanner category | F21 category cases, F23 private text | Existing slice-2 detection tests additionally protect scanner internals. |
| Remove profile self-name call / use wrong mode | F23[legal-name], F24/F25 | Real LLM/storage routing is a future application test, not F22. |
| Remove identity check from claim | F28; F30 owner mismatch; F29 required argument | Migrate old callers, then use their unchanged policy assertions as regressions. |
| Remove fixed-once / let same-name repeat succeed | F31; existing same-name test | Conditional dedup relies on approved slice-2 migration. |
| Check candidate/owner error before fixed-once | No current competing-invalid-input witness | Proposed already-claimed owner + invalid candidate/mismatched identity -> PseudonymAlreadySetError. |
| Remove reserved names / unique check / scanner from claims | Existing `test_pseudonyms.py` reserved/unique/identifier cases | Preserve every assertion during required-identity migration. |
| Lower/raise selection max or permit empty | F14[0,1,5,6], F15 | None/empty scalar fields and external list aliases need additions. |
| Deduplicate instead of refusing input duplicates | F15 | A frozenset-only input cannot expose this bug; retain list-input cases. |
| Count length before NFKC / truncate | F17/F19 | Add combining/emoji/281 ASCII to protect code-point semantics. |
| Fail to trim / store raw text | F17/F18 | Replace F18's computed expected strip with literals. |
| Strip controls and accept the save | F20 | Add middle controls, not only edges. |
| Freeze only first field or retain mutable input aliases | F11/F14 partly | All-field assignments and caller-list mutation proposed. |
| Reject duplicate Conversation participants too late/not at all | No current constructor test | Proposed duplicate/arity cases. |
| Swap subject/self error precedence | No current overlapping case | Proposed single precedence test. |
| Iterate unsorted frozensets in JSON | F03 singleton cannot kill it | Multi-value literal payload helps; actual no-sort mutant must be run after green, not assumed killed for every hash seed. |
| Introduce quadratic whole-word scanning | No bounded predicate test | Proposed 350KB negative/late-positive subprocess check, not the About factory's 280 cap. |
| Leak a DOB only through binary pickle | F02 roundtrip may catch restored state; raw-byte scanner alone misses | Positive control plus combined raw/decoded checks required. |
| Import framework/SDK or read system clock in domain | Existing purity tests | Pure redaction/value objects should not require weakening those guards. |

## Size and viva recommendation

98 cases are **32 functions: 15 table-driven functions account for 81 cases; 17 single-case functions account for 17**. Most volume is legitimate boundary/route coverage, not 98 separate features. Several substantial requirements still have no witness. Do not delete boundaries merely to fit an estimate.

The useful deduplications are F09[own] (already in F08), F22's generated email input (fold into F21 without losing it), and F31/F32 (only after migrated old tests preserve fixed-once, normalized uniqueness and retry). F01/F03 share some shape assertions but protect dataclass structure versus transport values; keep those distinct. F24 versus F26 are **not** duplicates: factory integration can choose the wrong mode even if the direct predicate is correct.

For the viva, explain five groups matching the requested implementation cycles: legacy diagnostics; types/profile writes; predicate; projection; claims. Tables can stay parameterized. Trimming duplicate function bodies helps explanation, but missing boundary/privacy tests may increase the final case count. The 3-4-session estimate is not validated by an unimplemented red set. Reserve **0.5 session** for this audit in the planning ledger; actual active audit time is unverified across the clock/date gap, so report it separately rather than pretending the budget is a measurement. Report actual implementation sessions at completion and update the freeze forecast; do not treat tests-first red volume as earned velocity.

## Regression evidence and post-approval order

Observed baseline, excluding only the new T1 red file:

```text
pytest -q -p no:cacheprovider --ignore=tests/test_member_identity_red.py
122 passed in 3.91s

pytest -q -p no:cacheprovider tests/test_domain_purity.py
2 passed in 0.03s
```

The baseline includes the 107 slice-1/2/domain cases and 15 tooling cases; the purity guards are included, not an extra two when summing the suite. No current existing test depends on leaked Applicant repr, so correcting diagnostics should not conflict with age logic or purity. It is unsafe to claim all old tests will stay green with a required identity parameter until their approved migration is made. Source remains pure; standard-library dataclass repr suppression needs no framework or clock read.

After audit and proposed-test approval, follow the user's order, one focused red-green commit per cycle: (1) legacy Applicant/Invite/error redaction and its regression tests; (2) types/codes/profile write rules; (3) both self-name modes; (4) projection/viewer rules; (5) Pseudonym integration and explicit old-caller migration. A cycle's targeted tests may be green while later approved T1 cases remain red; do not claim the whole branch green early. No implementation stubs are authorized by this report. If an unapproved test change becomes necessary, stop and show it first. After final green run mutations, update actual DESIGN/TESTING citations, keep Rule 5 partial, create a feature-branch PR. No additional approval between these implementation steps after the user's audit approval. Then report T1 actual sessions including this audit and forecast against November 28, followed by the local-model feasibility note.

## Proposed changes for approval — NOT APPLIED

The following is a generated unified diff against the frozen files. It preserves expected outcomes; it strengthens missing oracles and conditionally removes only mapped duplicates. New boundary/positive-control/precedence tests are proposals, not executed tests. The separate slice-2 diff only supplies required identity and preserves every old assertion and candidate. Error-name/type additions and lexical edge cases are explicitly visible for approval; no implementation accompanies them.

```diff
--- a/tests/test_member_identity_red.py
+++ b/tests/test_member_identity_red.py
@@ -1,11 +1,14 @@
 """Approved T1 red set. Public seams only; implementation awaits red-test review."""
 
 from collections.abc import Mapping
-from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass
+from dataclasses import FrozenInstanceError, asdict, dataclass, fields, is_dataclass
 from datetime import date
 from enum import Enum
+import inspect
 import json
 import pickle
+import subprocess
+import sys
 
 import pytest
 
@@ -64,26 +67,26 @@
             assert canary.encode() not in value
 
 
-def inspect_graph(value):
+def inspect_graph(value, *, forbidden_types=()):
     """Probe public payload reachability, including hidden slots, per privacy contract."""
     if isinstance(value, Enum):
         return value.value
     if isinstance(value, (str, int, float, bool, bytes, type(None), date)):
         return value.isoformat() if isinstance(value, date) else value
-    assert not isinstance(value, (d.Member, d.MemberIdentity))
+    assert not isinstance(value, forbidden_types)
     if isinstance(value, Mapping):
-        return {key: inspect_graph(item) for key, item in value.items()}
+        return {key: inspect_graph(item, forbidden_types=forbidden_types) for key, item in value.items()}
     if isinstance(value, (tuple, list, frozenset, set)):
-        return [inspect_graph(item) for item in value]
+        return [inspect_graph(item, forbidden_types=forbidden_types) for item in value]
     found = {}
     if hasattr(value, "__dict__"):
-        found.update({key: inspect_graph(item) for key, item in vars(value).items()})
+        found.update({key: inspect_graph(item, forbidden_types=forbidden_types) for key, item in vars(value).items()})
     for cls in type(value).__mro__:
         slots = cls.__dict__.get("__slots__", ())
         slots = (slots,) if isinstance(slots, str) else slots
         for slot in slots:
             if slot not in {"__dict__", "__weakref__"} and hasattr(value, slot):
-                found[slot] = inspect_graph(getattr(value, slot))
+                found[slot] = inspect_graph(getattr(value, slot), forbidden_types=forbidden_types)
     return found
 
 
@@ -107,15 +110,17 @@
         output = str(view)
     elif route == "dict":
         assert not hasattr(view, "__dict__")
-        output = getattr(view, "__dict__", {})
+        return  # structural absence, not a vacuous scan of an empty fallback
     elif route == "slots":
-        output = inspect_graph(view)
+        output = inspect_graph(view, forbidden_types=(d.Member, d.MemberIdentity))
     elif route == "pickle":
-        output = pickle.dumps(view)
+        raw = pickle.dumps(view)
+        assert_no_canary(raw)  # supplementary byte fingerprints
+        output = inspect_graph(pickle.loads(raw), forbidden_types=(d.Member, d.MemberIdentity))
     elif route == "pickle-roundtrip":
         restored = pickle.loads(pickle.dumps(view))
         assert restored == view
-        output = inspect_graph(restored)
+        output = inspect_graph(restored, forbidden_types=(d.Member, d.MemberIdentity))
     elif route == "asdict":
         output = asdict(view)
     else:
@@ -124,12 +129,19 @@
 
 
 def test_serialization_keeps_profile_codes_and_no_private_nested_payload():
-    payload = d.serialize_member_view(projected())
+    subject = member()
+    subject = d.Member(identity=subject.identity, pseudonym=subject.pseudonym, values_profile=profile(
+        subject.identity, interests=[d.Interest.READING, d.Interest.ART],
+        values=[d.CoreValue.KINDNESS, d.CoreValue.HONESTY],
+    ))
+    payload = d.serialize_member_view(d.project_member_for_viewer(
+        subject, viewer_id="viewer", conversation=conversation(),
+    ))
     assert payload == {
         "pseudonym": "Comet",
         "values_profile": {
             "relationship_intent": "long_term", "life_stage": "undergraduate",
-            "interests": ["reading"], "values": ["honesty"],
+            "interests": ["art", "reading"], "values": ["honesty", "kindness"],
             "communication_style": "direct", "pace_and_lifestyle": "quiet_and_routine",
             "about": "",
         },
@@ -149,6 +161,7 @@
     payload = d.serialize_member_view(view)
     assert set(payload) == {"pseudonym", "values_profile", "legal_name", "email", "phone"}
     assert CANARIES[3] not in repr(payload)
+    assert "1998, 7, 23" not in repr(payload)
 
 
 def test_optional_phone_remains_absent_after_reveal_when_not_supplied():
@@ -206,28 +219,27 @@
     assert_no_canary(repr(view))
 
 
-@pytest.mark.parametrize("kind", ["identity", "member", "revealed", "own"])
+@pytest.mark.parametrize("kind", ["identity", "member", "revealed"])
 def test_private_records_never_print_identity_values(kind):
     if kind == "identity":
         value = identity()
     elif kind == "member":
         value = member()
-    elif kind == "revealed":
+    else:
         value = projected(revealed=True)
-    else:
-        value = d.project_own_profile(member())
     assert_no_canary(repr(value))
     assert_no_canary(str(value))
 
 
 @pytest.mark.parametrize("kind", ["applicant", "redeemed-invite"])
-def test_existing_date_of_birth_holders_also_redact_private_representations(kind):
+@pytest.mark.parametrize("surface", ["repr", "str"])
+def test_existing_date_of_birth_holders_also_redact_private_representations(kind, surface):
     applicant = d.Applicant(date_of_birth=date(1998, 7, 23))
     value = applicant if kind == "applicant" else d.Invite(
         code="demo-invite", issuer="admin", redeemed_by=applicant,
     )
-    assert_no_canary(repr(value))
-    assert_no_canary(str(value))
+    render = repr if surface == "repr" else str
+    assert_no_canary(render(value))
 
 
 @pytest.mark.parametrize("kind", ["identity", "member", "profile", "pre", "post", "own", "conversation"])
@@ -249,15 +261,18 @@
     assert is_dataclass(value)
     assert not hasattr(value, "__dict__")
     assert all("photo" not in field.name for field in fields(value))
-    first_field = fields(value)[0].name
-    with pytest.raises(FrozenInstanceError):
-        setattr(value, first_field, None)
+    for field in fields(value):
+        with pytest.raises(FrozenInstanceError):
+            setattr(value, field.name, getattr(value, field.name))
 
 
 def test_member_cannot_supply_a_global_reveal_flag():
     subject = member()
     assert "revealed" not in {field.name for field in fields(subject)}
     assert not hasattr(subject, "revealed")
+    with pytest.raises(TypeError):
+        d.Member(identity=subject.identity, pseudonym=subject.pseudonym,
+                 values_profile=subject.values_profile, revealed=True)
     assert type(d.project_member_for_viewer(subject, viewer_id="viewer", conversation=conversation())) is d.PreRevealMemberView
 
 
@@ -314,9 +329,9 @@
         profile(about="Ａ" * 281)
 
 
-@pytest.mark.parametrize("about", ["", "   ", "x" * 279, "x" * 280], ids=["empty", "blank", "279", "280"])
-def test_about_within_the_limit_is_not_truncated_or_rejected(about):
-    assert profile(about=about).about == about.strip()
+@pytest.mark.parametrize("about,expected", [("", ""), ("   ", ""), ("x" * 279, "x" * 279), ("x" * 280, "x" * 280)], ids=["empty", "blank", "279", "280"])
+def test_about_within_the_limit_is_not_truncated_or_rejected(about, expected):
+    assert profile(about=about).about == expected
 
 
 def test_about_normalization_expansion_is_counted_not_raw_length():
@@ -334,7 +349,8 @@
 
 @pytest.mark.parametrize("about", [
     "person@example.invalid", "98765 43210", "@someone", "person at example dot com", "https://example.invalid",
-], ids=["email", "phone", "handle", "obfuscated", "url"])
+    "Contact person@example.invalid",  # retained generated-text input
+], ids=["email", "phone", "handle", "obfuscated", "url", "generated-email"])
 def test_every_identifier_category_refuses_the_entire_profile_save(about):
     owner = identity()
     before = profile(owner, about="Music")
@@ -346,10 +362,6 @@
     assert profile(owner, about="Reading").about == "Reading"
 
 
-def test_generated_text_uses_the_same_validated_profile_write_seam():
-    generated = "Contact person@example.invalid"
-    with pytest.raises(d.InvalidValuesProfileError):
-        profile(about=generated)
 
 
 @pytest.mark.parametrize("private_text", CANARIES[:3], ids=["legal-name", "email", "phone"])
@@ -369,18 +381,26 @@
     owner = identity(name="Will", email="unrelated@example.invalid")
     with pytest.raises(d.InvalidValuesProfileError) as caught:
         profile(owner, about="I will bring snacks")
-    assert "rephrase" in str(caught.value).casefold()
+    assert caught.value.field == "about"
+    assert caught.value.reason == "self_name"
+    assert caught.value.can_rephrase is True
     assert "will" not in str(caught.value).casefold()
     assert_no_canary(str(caught.value))
 
 
-@pytest.mark.parametrize("mode_name,candidate,flagged", [
-    ("PSEUDONYM", "market", True), ("ABOUT", "market", False),
-    ("ABOUT", "MARK", True), ("ABOUT", "Mark, welcome", True),
-    ("ABOUT", "bookmark", False), ("PSEUDONYM", "bookmark", True),
-], ids=["substring", "whole-word", "casefold", "punctuation", "embedded-about", "embedded-name"])
-def test_shared_predicate_has_distinct_pseudonym_and_about_modes(mode_name, candidate, flagged):
-    owner = identity(name="Mark", email="unrelated@example.invalid")
+@pytest.mark.parametrize("mode_name,candidate,flagged,owner_name", [
+    ("PSEUDONYM", "market", True, "Mark"), ("ABOUT", "market", False, "Mark"),
+    ("ABOUT", "MARK", True, "Mark"), ("ABOUT", "Mark, welcome", True, "Mark"),
+    ("ABOUT", "bookmark", False, "Mark"), ("PSEUDONYM", "bookmark", True, "Mark"),
+    ("ABOUT", "Will.", True, "Will"), ("ABOUT", "will's", True, "Will"),
+    ("ABOUT", "willow", False, "Will"),
+    ("ABOUT", "STRASSE", True, "Straße"),
+    ("PSEUDONYM", "StarSTRASSE", True, "Straße"),
+    ("ABOUT", "mark", True, "Ｍａｒｋ"),
+], ids=["substring", "whole-word", "casefold", "punctuation", "embedded-about", "embedded-name",
+        "will-period", "will-apostrophe", "will-embedded", "about-sharp-s", "name-sharp-s", "about-nfkc"])
+def test_shared_predicate_has_distinct_pseudonym_and_about_modes(mode_name, candidate, flagged, owner_name):
+    owner = identity(name=owner_name, email="unrelated@example.invalid")
     assert d.contains_self_name(candidate, identity=owner, mode=getattr(d.SelfNameMode, mode_name)) is flagged
 
 
@@ -392,7 +412,16 @@
     ("A Li", "xy@example.invalid", "LiStar", False),
     ("Ana", "xy@example.invalid", "StarAna", True),
     ("Other", "local@example.invalid", "Example", False),
-], ids=["nfkc-name", "nfkc-local", "email-separators", "name-separators", "short", "three", "not-domain"])
+    ("Other", "mint+surya@example.invalid", "StarSurya", True),
+    ("Other", "mint.surya@example.invalid", "StarSurya", True),
+    ("Other", "mint_surya@example.invalid", "StarSurya", True),
+    ("Other", "mint-surya@example.invalid", "StarSurya", True),
+    ("Nora Arya", "other@example.invalid", "StarArya", True),
+    ("Mark", "other@example.invalid", "Markus", True),
+    ("ßa", "other@example.invalid", "StarSSA", True),
+    ("A\u030An", "other@example.invalid", "ÅnStar", False),
+], ids=["nfkc-name", "nfkc-local", "email-separators", "name-separators", "short", "three", "not-domain",
+        "plus", "dot", "underscore", "hyphen", "whitespace", "markus", "fold-length-three", "nfkc-length-two"])
 def test_self_name_normalization_tokens_and_length_boundary(name, email, candidate, flagged):
     owner = identity(name=name, email=email)
     assert d.contains_self_name(candidate, identity=owner, mode=d.SelfNameMode.PSEUDONYM) is flagged
@@ -403,34 +432,166 @@
     directory = d.PseudonymDirectory()
     with pytest.raises(d.InvalidPseudonymError) as caught:
         directory.claim("subject", "Market", identity=owner)
-    assert "Mark" not in str(caught.value)
+    for diagnostic in (str(caught.value), repr(caught.value)):
+        assert "mark" not in diagnostic.casefold()
     assert directory.claim("subject", "Comet", identity=owner).value == "Comet"
 
 
 def test_pseudonym_claim_requires_private_identity_without_a_bypass_default():
+    parameter = inspect.signature(d.PseudonymDirectory.claim).parameters["identity"]
+    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
+    assert parameter.default is inspect.Parameter.empty
     with pytest.raises(TypeError):
         d.PseudonymDirectory().claim("subject", "Comet")
 
 
 def test_claim_rejects_a_mismatched_identity_without_leaking_private_values():
+    directory = d.PseudonymDirectory()
     with pytest.raises(d.IdentityOwnerMismatchError) as caught:
-        d.PseudonymDirectory().claim("someone-else", "Comet", identity=identity())
+        directory.claim("someone-else", "Comet", identity=identity())
     assert_no_canary(str(caught.value))
-
-
-def test_repeated_same_pseudonym_still_hits_the_fixed_once_guard():
+    assert_no_canary(repr(caught.value))
+
+    assert directory.claim("subject", "Comet", identity=identity()).value == "Comet"
+
+@dataclass(frozen=True, slots=True)
+class LeakyCanaryView:
+    pseudonym: str = "Comet"
+    values_profile: str = "Reading"
+    leaked: object = None  # positive-control fake, never a domain implementation
+
+
+@pytest.mark.parametrize("value", [*CANARIES[:3], date(1998, 7, 23)], ids=["name", "email", "phone", "dob"])
+def test_canary_positive_controls_cover_each_private_field(value):
+    fake = LeakyCanaryView(leaked=value)
+    raw = pickle.dumps(fake)
+    payloads = [repr(fake), str(fake), asdict(fake), {"leaked": value},
+                inspect_graph(fake), json.dumps(asdict(fake), default=lambda x: x.isoformat()),
+                str(ValueError(str(value))), repr(ValueError(str(value))),
+                inspect_graph(pickle.loads(raw))]
+    for payload in payloads:
+        with pytest.raises(AssertionError):
+            assert_no_canary(payload)
+    # Byte fingerprints are supplementary: DOB is encoded as binary, not an ISO string.
+    if not isinstance(value, date):
+        with pytest.raises(AssertionError):
+            assert_no_canary(raw)
+
+
+def test_clean_canary_control_is_not_rejected():
+    assert_no_canary(inspect_graph(LeakyCanaryView()))
+
+
+@pytest.mark.parametrize("kind", ["member", "identity"])
+def test_graph_rejects_even_redacted_private_references(kind):
+    private = member() if kind == "member" else identity()
+    with pytest.raises(AssertionError):
+        inspect_graph(LeakyCanaryView(leaked=private), forbidden_types=(d.Member, d.MemberIdentity))
+
+
+def test_viewer_error_precedence():
+    subject = member()
+    other_pair = conversation(pair=("viewer", "third"))
+    for viewer in ("subject", "outsider"):
+        with pytest.raises(d.SubjectNotParticipantError) as caught:
+            d.project_member_for_viewer(subject, viewer_id=viewer, conversation=other_pair)
+        assert type(caught.value) is d.SubjectNotParticipantError
+    with pytest.raises(d.SelfViewerError) as caught:
+        d.project_member_for_viewer(subject, viewer_id="subject", conversation=conversation())
+    assert type(caught.value) is d.SelfViewerError
+    with pytest.raises(d.ViewerNotParticipantError) as caught:
+        d.project_member_for_viewer(subject, viewer_id="outsider", conversation=conversation())
+    assert type(caught.value) is d.ViewerNotParticipantError
+
+
+@pytest.mark.parametrize("pair", [("subject", "subject"), ("subject",), ("subject", "viewer", "third")], ids=["duplicate", "one", "three"])
+def test_conversation_state_requires_exactly_two_distinct_participants(pair):
+    with pytest.raises(d.InvalidConversationParticipantsError):
+        conversation(pair=pair)
+
+
+@pytest.mark.parametrize("about,expected,valid", [
+    ("x" * 281, None, False),
+    ("e\u0301" * 280, "é" * 280, True), ("e\u0301" * 281, None, False),
+    ("🙂" * 280, "🙂" * 280, True), ("🙂" * 281, None, False),
+    ("👍🏽" * 140, "👍🏽" * 140, True), ("👍🏽" * 140 + "x", None, False),
+], ids=["ascii281", "combining280", "combining281", "emoji280", "emoji281", "modifier280", "modifier281"])
+def test_about_code_point_oracles(about, expected, valid):
+    if valid:
+        assert profile(about=about).about == expected
+    else:
+        with pytest.raises(d.InvalidValuesProfileError):
+            profile(about=about)
+
+
+@pytest.mark.parametrize("field_name", ["relationship_intent", "life_stage", "communication_style", "pace_and_lifestyle"])
+def test_complete_profile_requires_each_single_choice(field_name):
+    for missing in (None, ""):
+        with pytest.raises(d.InvalidValuesProfileError):
+            profile(**{field_name: missing})
+
+
+@pytest.mark.parametrize("control", ["\x00", "\n", "\x85"], ids=["nul", "lf", "c1"])
+def test_about_rejects_embedded_controls(control):
+    with pytest.raises(d.InvalidValuesProfileError):
+        profile(about="Mu" + control + "sic")
+
+
+def test_profile_does_not_retain_mutable_selection_inputs():
+    interests = [d.Interest.READING]
+    values = [d.CoreValue.HONESTY]
+    saved = profile(interests=interests, values=values)
+    interests.append(d.Interest.MUSIC)
+    values.append(d.CoreValue.KINDNESS)
+    assert saved.interests == frozenset({d.Interest.READING})
+    assert saved.values == frozenset({d.CoreValue.HONESTY})
+
+
+@pytest.mark.parametrize("text", ["", "   "] , ids=["empty", "blank"])
+def test_whole_word_predicate_handles_empty_input(text):
+    assert d.contains_self_name(text, identity=identity(), mode=d.SelfNameMode.ABOUT) is False
+
+
+def test_whole_word_predicate_is_bounded_on_long_negative_and_late_positive_text():
+    code = (
+        "from datetime import date; from vaeil import domain as d; "
+        "owner=d.MemberIdentity(member_id='one',legal_name='Mark',email='unrelated@example.invalid',phone=None,date_of_birth=date(1998,7,23)); "
+        "text='market '*50000; "
+        "assert not d.contains_self_name(text,identity=owner,mode=d.SelfNameMode.ABOUT); "
+        "assert d.contains_self_name(text+' Mark',identity=owner,mode=d.SelfNameMode.ABOUT)"
+    )
+    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=3)
+    assert result.returncode == 0, result.stderr
+
+
+class FixedAuditTestClock:
+    def today(self):
+        return date(2026, 10, 24)
+
+
+@pytest.mark.parametrize("case,error_name,dob,fingerprints", [
+    ("future", "FutureDateOfBirthError", date(2030, 7, 23), ("2030-07-23", "2030, 7, 23")),
+    ("underage", "UnderageError", date(2010, 7, 23), ("2010-07-23", "2010, 7, 23")),
+    ("invalid", "InvalidInviteError", date(1998, 7, 23), ("1998-07-23", "1998, 7, 23")),
+    ("used", "InviteAlreadyRedeemedError", date(1998, 7, 23), ("1998-07-23", "1998, 7, 23")),
+], ids=["future", "underage", "invalid", "used"])
+def test_age_gate_errors_never_echo_dob(case, error_name, dob, fingerprints):
+    invite = None if case == "invalid" else d.Invite(code="demo", issuer="admin")
+    if case == "used":
+        invite.redeemed_by = d.Applicant(date_of_birth=dob)
+    error_type = getattr(d, error_name)
+    with pytest.raises(error_type) as caught:
+        d.redeem_invite(invite=invite, date_of_birth=dob, clock=FixedAuditTestClock())
+    assert type(caught.value) is error_type
+    for diagnostic in (str(caught.value), repr(caught.value)):
+        for fingerprint in fingerprints:
+            assert fingerprint not in diagnostic
+
+
+def test_fixed_once_precedes_other_claim_validation():
     owner = identity()
     directory = d.PseudonymDirectory()
     directory.claim("subject", "Comet", identity=owner)
     with pytest.raises(d.PseudonymAlreadySetError):
-        directory.claim("subject", "Comet", identity=owner)
-
-
-def test_taken_claim_can_retry_and_preserves_normalized_uniqueness():
-    directory = d.PseudonymDirectory()
-    first = identity("one")
-    second = identity("two")
-    directory.claim("one", "Comet", identity=first)
-    with pytest.raises(d.PseudonymTakenError):
-        directory.claim("two", " ＣＯＭＥＴ ", identity=second)
-    assert directory.claim("two", "Nova", identity=second).value == "Nova"
+        directory.claim("subject", "@bad", identity=identity("wrong-owner"))
+

--- a/tests/test_pseudonyms.py
+++ b/tests/test_pseudonyms.py
@@ -1,19 +1,29 @@
 """Rule 5: Pseudonym validation shares the identifier check and is fixed once set."""
+
+from datetime import date
 
 import pytest
 
 from vaeil.domain import (
     InvalidPseudonymError,
+    MemberIdentity,
     PseudonymAlreadySetError,
     PseudonymDirectory,
     PseudonymTakenError,
 )
 
 
+def claim(directory, member_id, candidate):
+    owner = MemberIdentity(member_id=member_id, legal_name="PrivateNameZXQ",
+                           email="privateownerzxq@example.invalid", phone=None,
+                           date_of_birth=date(1998, 7, 23))
+    return directory.claim(member_id, candidate, identity=owner)
+
+
 def test_a_valid_pseudonym_is_claimed() -> None:
     directory = PseudonymDirectory()
 
-    pseudonym = directory.claim("member-1", "Comet")
+    pseudonym = claim(directory, "member-1", "Comet")
 
     assert pseudonym.value == "Comet"
 
@@ -21,7 +31,7 @@
 @pytest.mark.parametrize("blank", ["", "   "])
 def test_blank_pseudonym_is_rejected(blank: str) -> None:
     with pytest.raises(InvalidPseudonymError):
-        PseudonymDirectory().claim("member-1", blank)
+        claim(PseudonymDirectory(), "member-1", blank)
 
 
 @pytest.mark.parametrize(
@@ -35,54 +45,54 @@
 )
 def test_identifier_like_pseudonym_is_rejected(candidate: str) -> None:
     with pytest.raises(InvalidPseudonymError):
-        PseudonymDirectory().claim("member-1", candidate)
+        claim(PseudonymDirectory(), "member-1", candidate)
 
 
 def test_pseudonyms_are_unique_case_insensitively() -> None:
     directory = PseudonymDirectory()
-    directory.claim("member-1", "Comet")
+    claim(directory, "member-1", "Comet")
 
     with pytest.raises(PseudonymTakenError):
-        directory.claim("member-2", "cOmEt")
+        claim(directory, "member-2", "cOmEt")
 
 
 def test_pseudonym_is_fixed_once_set() -> None:
     directory = PseudonymDirectory()
-    directory.claim("member-1", "Comet")
+    claim(directory, "member-1", "Comet")
 
     with pytest.raises(PseudonymAlreadySetError):
-        directory.claim("member-1", "Nova")
+        claim(directory, "member-1", "Nova")
 
 
 def test_a_failed_claim_does_not_set_the_pseudonym() -> None:
     directory = PseudonymDirectory()
 
     with pytest.raises(InvalidPseudonymError):
-        directory.claim("member-1", "")
+        claim(directory, "member-1", "")
 
-    assert directory.claim("member-1", "Comet").value == "Comet"
+    assert claim(directory, "member-1", "Comet").value == "Comet"
 
 
 def test_a_failed_taken_claim_does_not_set_the_member() -> None:
     directory = PseudonymDirectory()
-    directory.claim("member-1", "Comet")
+    claim(directory, "member-1", "Comet")
 
     with pytest.raises(PseudonymTakenError):
-        directory.claim("member-2", "comet")
+        claim(directory, "member-2", "comet")
 
-    assert directory.claim("member-2", "Nova").value == "Nova"
+    assert claim(directory, "member-2", "Nova").value == "Nova"
 
 
 @pytest.mark.parametrize("candidate", [" cOmEt ", "Ｃomet"])
 def test_normalized_names_share_one_claim(candidate: str) -> None:
     directory = PseudonymDirectory()
-    directory.claim("one", "Comet")
+    claim(directory, "one", "Comet")
     with pytest.raises(PseudonymTakenError):
-        directory.claim("two", candidate)
+        claim(directory, "two", candidate)
 
 
 def test_display_value_is_trimmed_and_nfkc_normalized() -> None:
-    assert PseudonymDirectory().claim("one", " Ｃomet ").value == "Comet"
+    assert claim(PseudonymDirectory(), "one", " Ｃomet ").value == "Comet"
 
 
 @pytest.mark.parametrize("candidate, valid", [
@@ -96,25 +106,25 @@
 
     assert (MIN_PSEUDONYM_LENGTH, MAX_PSEUDONYM_LENGTH) == (3, 20)
     if valid:
-        assert PseudonymDirectory().claim("one", candidate).value == candidate
+        assert claim(PseudonymDirectory(), "one", candidate).value == candidate
     else:
         with pytest.raises(InvalidPseudonymError):
-            PseudonymDirectory().claim("one", candidate)
+            claim(PseudonymDirectory(), "one", candidate)
 
 
 @pytest.mark.parametrize("candidate", ["admin", "MODERATOR", "System", "vaeil", "Support"])
 def test_reserved_names_are_refused(candidate: str) -> None:
     with pytest.raises(InvalidPseudonymError):
-        PseudonymDirectory().claim("one", candidate)
+        claim(PseudonymDirectory(), "one", candidate)
 
 
 def test_claiming_the_same_name_twice_is_still_a_change_attempt() -> None:
     directory = PseudonymDirectory()
-    directory.claim("one", "Comet")
+    claim(directory, "one", "Comet")
     with pytest.raises(PseudonymAlreadySetError):
-        directory.claim("one", "Comet")
+        claim(directory, "one", "Comet")
 
 
 def test_format_valid_phone_identifier_is_refused() -> None:
     with pytest.raises(InvalidPseudonymError):
-        PseudonymDirectory().claim("one", "Comet9876543210")
+        claim(PseudonymDirectory(), "one", "Comet9876543210")
```

The proposed patch parses as Python but has not been executed or applied. New tests include an explicit test-only fake, no domain stubs. The timeout case deliberately adds a local subprocess/outer timeout; it is Windows-compatible like slice 2 and does not read domain time. Re-run node-ID bounds and targeted red groups after approval. A frontend label test, T10 eligibility and adapter-routing test remain deferred to their actual seams.

## Final audit verification

- All 32 function groups ran separately: 98 failures total; failure category sum 95+2+1=98; no collection/setup-phase errors.
- Existing baseline 122 passed; purity 2 passed separately; no new mutation or implementation was executed.
- All 16 protected Python files have unchanged hashes and the exact same path set, including untracked T1 tests. Frozen T1 SHA-256 still matches the value above.
- Canary control results and Unicode oracles were measured against the current frozen helper/stdlib, not a hypothetical implementation. One raw-pickle DOB miss and four blocked graph controls are explicitly disclosed.
- Proposal syntax was parsed in memory, not applied, imported or run. Report contains 32 inventory rows covering all 98 IDs, every non-keep group, both review-only diffs and named gaps. New tests may increase case count; no size claim hides their scope.
- The active-time limit cannot be certified after the observed overnight clock/date gap; 0.5 session remains the budget, not an invented actual duration.
- Pending human approval: audit findings, all proposed test edits (including old callers and new error attributes) and implementation start. No test change, commit, PR, deployment action or next-ticket work was performed.

