# Testing

**Current evidence:** 401 tests pass: 386 product/domain/boundary cases and 15 tooling cases. Verified locally before merging PR #14; Windows CI passed on final head `6066868`, preserved by merge commit `4f9ca80`. Windows checks run Ruff, assumption validation and pytest. T1 adds identity/profile/projection, opaque private values and the exact unwrap boundary; no API or UI exists yet. **Coverage stays 3 of 6 rules domain-level, 0 of 6 end-to-end. Rule 5 is partial.**

## How to run

```powershell
.venv\Scripts\python.exe scripts/check.py
```

Product/domain tests use no live provider/database or system clock. Logging tests capture diagnostics; bounded parser/predicate subprocesses enforce generous regression deadlines, not latency claims. The AST tests inspect source for purity and the private extraction boundary. Tooling tests do not increase rule coverage.

## Rules → tests

| # | Rule | Current evidence (`file:line`) | Proven / remaining |
| --- | --- | --- | --- |
| 1 | Invite-only | `tests/test_invite_redemption.py:123`, `:133`, `:138` | Single-use/unknown/invalid Invite refusal; account/API/admission wiring still T6. |
| 2 | Vetting never rejects | `tests/test_vetting.py:42`, `:58`, `:64`, `:70`, `:76` | Closed Verdict and safe wrapper; real model and Admin admission remain pending. |
| 3 | Moderated delivery | — | Message delivery/moderation not implemented; Vetting failure tests do not prove delivery. |
| 4 | Consensual Reveal | — | Eligibility, Clock timestamps and bilateral consent not implemented. T1 Reveal fixtures are projection inputs only. |
| 5 | Anonymity before Reveal — **partial** | `tests/test_member_identity_red.py:107`, `:119`, `:189`, `:508`; `tests/test_opaque_private_values.py:23`, `:39`, `:144`, `:165`, `:179`; `tests/test_private_unwrap_boundary.py:60` | Exact view shape, graph/serialization canaries, pair isolation, owner checks and opaque scalars/authorized payload. State authority, HTTP auth, deployed UI, persistence and moderated transport remain pending. |
| 6 | Age gate | `tests/test_invite_redemption.py:56`, `:61`, `:70`, `:79`, `:93`, `:106`, `:114`, `:152` | 18+ before consume, birthday/leap boundaries and injected Clock; UI/admission integration pending. |

**How many rules are tested?** Rules 1, 2 and 6 have existing domain-level evidence; 3/6 domain, 0/6 E2E. Domain privacy improvements do not mark Rule 5 done.

## T1 privacy/profile evidence

- Exact pre-Reveal `{pseudonym, values_profile}` and revealed `{pseudonym, values_profile, legal_name, email, phone}` field/key sets; DOB never enters a Match payload. No photos.
- Profile writes: seven distinct validation failures in order, stable code sets, 1-5 distinct frozenset selections, trimmed NFKC About at 280 code points, no controls/truncation, shared scanner then whole-word self-name checks. See `tests/test_member_identity_red.py:302`, `:309`, `:339`, `:535`, `:665`.
- Own-name tokens use normalized names/email-local parts of length >=3; Pseudonyms use substrings and About whole words. Mark/market accepted; Will/will remains a documented rephraseable false positive. Unicode/casefold/token and long-input evidence: `tests/test_member_identity_red.py:419`, `:442`, `:571`.
- Opaque scalar rendering/equality/native-operation/export tests: `tests/test_opaque_private_values.py:23`, `:39`, `:58`, `:79`, `:90`, `:110`, `:128`. Unhashable values; plain-field constructors wrap without caller hand-wrapping.
- Distinctive DOB canaries include ISO, DMY, MDY, English display, date repr and pickle state/decoded values; positive controls demonstrate actual detection (`tests/test_member_identity_red.py:482`, `:617`). Pre-Reveal tests inspect dict/slots, pickle/roundtrip, asdict, JSON and references. Private records/scalars instead refuse generic export (`:638`). Logs/tracebacks/errors are scanned (`tests/test_opaque_private_values.py:179`).
- Exact unwrap allowlist and deliberately violating fake modules: `tests/test_private_unwrap_boundary.py:60`, `:73`. The guard catches direct loads, aliases and literal getattr; deliberate reflective access/dynamic indirection is not prevented. Allowed code can intentionally extract data; review remains required.

## T1 red/green and mutation evidence

The test-only commit preceded the measured skeleton: 219 failed/106 passed, with 178 direct NotImplementedErrors and 41 assertions (one wrapped a child NotImplementedError). Every passing T1 control was classified in `docs/audit/t1-skeleton-red.md`. Five separate implementation cycles reached 325 green. The approved opaque refinement then showed 39 failed/35 passed against old scalars, including actual native JSON/format leaks, before separate text/date green commits reached **401 passed**. No tests were loosened; wrapper-comparison refinements and full legacy diffs are recorded in `docs/audit/`.

Run `.venv\Scripts\python.exe scripts/check_t1_mutations.py` separately: it temporarily rewrites one fault at a time, rejects collection/setup-error kills and restores exact bytes in finally. Do not run concurrent source-mutating checks. Results table: `docs/audit/t1-mutation-results.md`; raw results: `t1-mutation-results.json`. This does not prove unlisted faults impossible. The existing slice-1/2 mutation tables below are historical baseline evidence, not current counts.

## The leap-day rule

Someone born on 29 February is treated as having their birthday on 28 February in non-leap years. In 2026 (not a leap year) they turn 18 on 2026-02-28, not 2026-03-01. Both dates are tested at `tests/test_invite_redemption.py:93` and `:106`; the clamp is implemented at `src/vaeil/domain/invite.py:73`.

## Identifier detection is heuristic

Rule 5's guarantee is about what the system displays and sends: a Member's real name, photo, or contact details are never shown to a Match outside a Reveal. Detection is a safety net for text Members type. It returns a result — clean, or flagged with a reason — and does not decide delivery; a flagged Message is Escalated by the moderation slice, delivered, and reviewed by an Admin. A clean scan is not proof of anonymity. Known limits:

- numbers spelled out in words, e.g. "nine eight seven six five four three two one zero";
- obfuscations the patterns do not cover;
- identifiers split across multiple Messages;
- false positives: a long numeric string that is not a phone number is still flagged.

The scanner at `src/vaeil/domain/identifiers.py:32` handles email, phone, handle/social hints, supported obfuscated-email patterns, and URLs. It normalizes NFKC and Unicode decimal digits, returns all reasons in enum order, and stores no matched text. It does not detect real names. Pseudonym validation at `src/vaeil/domain/pseudonym.py:33` shares this scanner and the owner-specific predicate at `src/vaeil/domain/self_name.py:11`. T1 also checks owner-specific tokens in Pseudonym claims and About; it is not general name recognition. Claims remain in-memory; atomic database uniqueness is T5.

The expanded detection cases begin at `tests/test_identifier_detection.py:85`: phone formats and threshold boundaries, handle/URL classification, obfuscation, ordinary-number guards, deterministic reasons, long input, and reason-only results. Pseudonym normalization, format boundaries, reserved names, repeat claims, and a format-valid identifier are covered from `tests/test_pseudonyms.py:77`.

## Historical mutation checks (slice 2 baseline)

Run `.venv\Scripts\python.exe scripts/check_slice2_mutations.py`. Each mutation is applied alone and restored in a `finally` block; pytest exit code 1 is required. Results on the 85 slice-2 cases (rerun after the scanner performance fix):

| Mutation | Result |
|---|---|
| Remove phone | 16 failed, 69 passed |
| Remove email | 3 failed, 82 passed |
| Remove handle | 6 failed, 79 passed |
| Remove obfuscated email | 8 failed, 77 passed |
| Remove URL | 5 failed, 80 passed |
| Threshold 10 to 9 | 2 failed, 83 passed |
| Threshold 10 to 11 | 13 failed, 72 passed |
| Remove casefold | 6 failed, 79 passed |
| Remove Pseudonym NFKC | 2 failed, 83 passed |
| Remove identifier check | 1 failed, 84 passed |
| Remove fixed-once guard | 2 failed, 83 passed |
| Remove reserved-name check | 5 failed, 80 passed |

All mutations were restored; the full suite returned to **107 passed**, including the purity guards.

## Mutation checks (slice 1)

After the suite was green, I broke three guards one at a time; each made at least one test fail:

| Mutation | Failing test(s) |
|----------|-----------------|
| Age boundary `>=` → `>` in `src/vaeil/domain/invite.py` | `test_turning_eighteen_today_is_allowed`, `test_leap_day_birthday_turns_eighteen_on_feb_28_in_non_leap_years` |
| Removed the single-use guard in `src/vaeil/domain/invite.py` | `test_redeeming_an_already_redeemed_invite_is_refused` |
| Propagated the LLM error instead of returning NeedsReview in `src/vaeil/domain/vetting.py` | `test_port_error_fails_closed_to_needs_review`, `test_port_timeout_fails_closed_to_needs_review` |

Each mutation was reverted and the full suite returned to green.

## The weak test

`tests/test_domain_purity.py:106` (`test_domain_does_not_read_the_system_clock`) is the weakest test in the suite. It is a static AST check: it catches direct calls (and common import aliases) to `datetime.now()`, `date.today()`, and `time.time()`, but it does not follow indirection such as `today = date.today; today()` or `getattr(datetime, "today")()`. It is a guardrail, not a sandbox. The Clock port and review remain the real protection; the test only makes the obvious bypass visible.

The injected-clock test at `tests/test_invite_redemption.py:152` is no longer weak. The fake date is 2000-01-01 and the birth date is 1990-01-01: the fake clock says 10, while every real date after 2008 says adult. The fake and real outcomes can never converge, so a `date.today()` implementation always fails it.

## Punctuation-heavy input regression

`tests/test_identifier_detection.py:147` scans 100 KB of dot- or hyphen-separated clean text in a subprocess with a three-second deadline. Both cases timed out before the fix; after restricting obfuscated-email matching to token starts, direct scans took about 0.04 seconds each and both subprocess tests pass. The deadline includes process startup and is deliberately generous; it catches repeated suffix scanning, rather than enforcing a tight benchmark.
