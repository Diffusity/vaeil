# Testing

Vaeil's rules are tested where they live. This file maps each rule to the test that proves it, says how many rules are covered, and names one test I would not defend as strong.

**Status: in progress.** Slice 1 proves Rules 1, 2, and 6 at the domain seam. Rules 3 and 4 have no tests yet; Rule 5 has partial domain tests and is not counted as done. **Current coverage: 3 of 6 rules domain-level; 0 of 6 end-to-end.** Rule 5 remains partial until the pre-Reveal display slice proves the system-side guarantee.

## How to run

```powershell
.venv\Scripts\python.exe -m pytest -q
```

The 107 product tests cover 22 slice-1 and 85 slice-2 cases. Additional agent-tooling tests live under `tests/tooling/`; they do not increase product-rule coverage. The domain suite uses no network, database, or real clock; its fakes include a fixed `FakeClock`. Tooling tests exercise local CLIs and bounded pytest subprocesses.

Run all checks with `.venv\Scripts\python.exe scripts/check.py`; Windows CI uses the same command. It runs Ruff, validates assumption IDs/supersession links, and executes the whole pytest suite. `tests/tooling/test_agent_tools.py` covers invalid assumption histories, filtered/paginated session reads, malformed exports, and bounded test IDs. Mutations remain a separate manual check because they temporarily rewrite sources.

## Rules → tests

| # | Rule | Test(s) (`file:line`) | What is proven | What is still missing |
|---|------|-----------------------|----------------|----------------------|
| 1 | Invite-only access | `tests/test_invite_redemption.py:121`, `:131`, `:136` | An Invite is required, single-use, and unknown or malformed Invites are refused without changing the original redeemer | Account creation and the API/UI are not built; the app slice must redeem before creating an account |
| 2 | Vetting never rejects | `tests/test_vetting.py:42`, `:58`, `:64`, `:70`, `:76` | Reject is unrepresentable; port errors, timeouts, and non-Verdict results fail closed to NeedsReview | The Admin approval flow, persistence, and the real LLM adapter are not built |
| 3 | Moderated delivery | — | — | Messages and moderation are not built. Fail-closed is proven for vetting only, not yet for Messages |
| 4 | Consensual Reveal | — | — | Conversation and Reveal are not built |
| 5 | Anonymity before Reveal (partial) | `tests/test_identifier_detection.py:27`, `:61`, `:76`; `tests/test_pseudonyms.py:36`, `:41`, `:49`, `:57`, `:66` | Supported identifiers are reported; identifier-like Pseudonyms are rejected, claims are case-insensitively unique within one directory and fixed once set; failed claims do not reserve a name | Self-name and profile-write validation remain pending. Persistent uniqueness, identity projection, Conversation-scoped escalation, delivery, and audit integration are not built; this rule is not counted as fully covered |
| 6 | Age gate | `tests/test_invite_redemption.py:54`, `:68`, `:77`, `:86`, `:91`, `:104`, `:112`, `:150` | Under-18 is refused and leaves the Invite unused; both birthday boundaries; the Feb 29 rule; future DOB has its own error; the age check reads the injected Clock | The UI must surface the refusal; no HTTP layer yet |

**How many rules are tested?** 3 of 6 rules have domain-level tests (Rules 1, 2, 6); none is end-to-end. The count stays here until the other rules' tests actually exist.

## The leap-day rule

Someone born on 29 February is treated as having their birthday on 28 February in non-leap years. In 2026 (not a leap year) they turn 18 on 2026-02-28, not 2026-03-01. Both dates are tested at `tests/test_invite_redemption.py:91` and `:104`; the clamp is implemented at `src/vaeil/domain/invite.py:71`.

## Identifier detection is heuristic

Rule 5's guarantee is about what the system displays and sends: a Member's real name, photo, or contact details are never shown to a Match outside a Reveal. Detection is a safety net for text Members type. It returns a result — clean, or flagged with a reason — and does not decide delivery; a flagged Message is Escalated by the moderation slice, delivered, and reviewed by an Admin. A clean scan is not proof of anonymity. Known limits:

- numbers spelled out in words, e.g. "nine eight seven six five four three two one zero";
- obfuscations the patterns do not cover;
- identifiers split across multiple Messages;
- false positives: a long numeric string that is not a phone number is still flagged.

The scanner at `src/vaeil/domain/identifiers.py:32` handles email, phone, handle/social hints, supported obfuscated-email patterns, and URLs. It normalizes NFKC and Unicode decimal digits, returns all reasons in enum order, and stores no matched text. It does not detect real names. Pseudonym validation at `src/vaeil/domain/pseudonym.py:31` shares this scanner, so the documented real-name prohibition is not yet fully enforced. Claims are unique only within a shared in-memory directory; database-backed platform uniqueness remains pending.

The expanded detection cases begin at `tests/test_identifier_detection.py:85`: phone formats and threshold boundaries, handle/URL classification, obfuscation, ordinary-number guards, deterministic reasons, long input, and reason-only results. Pseudonym normalization, format boundaries, reserved names, repeat claims, and a format-valid identifier are covered from `tests/test_pseudonyms.py:77`.

## Mutation checks (slice 2)

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

The injected-clock test at `tests/test_invite_redemption.py:150` is no longer weak. The fake date is 2000-01-01 and the birth date is 1990-01-01: the fake clock says 10, while every real date after 2008 says adult. The fake and real outcomes can never converge, so a `date.today()` implementation always fails it.

## Punctuation-heavy input regression

`tests/test_identifier_detection.py:147` scans 100 KB of dot- or hyphen-separated clean text in a subprocess with a three-second deadline. Both cases timed out before the fix; after restricting obfuscated-email matching to token starts, direct scans took about 0.04 seconds each and both subprocess tests pass. The deadline includes process startup and is deliberately generous; it catches repeated suffix scanning, rather than enforcing a tight benchmark.
