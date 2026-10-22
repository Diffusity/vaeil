# Testing

Vaeil's rules are tested where they live. This file maps each rule to the test that proves it, says how many rules are covered, and names one test I would not defend as strong.

**Status: in progress.** Slice 1 proves Rules 1, 2, and 6 at the domain seam. Rules 3–5 have no tests yet. **Current coverage: 3 of 6 rules domain-level; 0 of 6 end-to-end.** This count changes only when a rule's tests are green; no future coverage is claimed here.

## How to run

```powershell
.venv\Scripts\python.exe -m pytest -q
```

The 22 slice-1 tests are green; the slice-2 red tests are waiting for implementation. No network, no database, and no real clock: the domain tests use in-memory fakes, including a fixed `FakeClock`.

## Rules → tests

| # | Rule | Test(s) (`file:line`) | What is proven | What is still missing |
|---|------|-----------------------|----------------|----------------------|
| 1 | Invite-only access | `tests/test_invite_redemption.py:121`, `:131`, `:136` | An Invite is required, single-use, and unknown or malformed Invites are refused without changing the original redeemer | Account creation and the API/UI are not built; the app slice must redeem before creating an account |
| 2 | Vetting never rejects | `tests/test_vetting.py:42`, `:58`, `:64`, `:70`, `:76` | Reject is unrepresentable; port errors, timeouts, and non-Verdict results fail closed to NeedsReview | The Admin approval flow, persistence, and the real LLM adapter are not built |
| 3 | Moderated delivery | — | — | Messages and moderation are not built. Fail-closed is proven for vetting only, not yet for Messages |
| 4 | Consensual Reveal | — | — | Conversation and Reveal are not built |
| 5 | Anonymity before Reveal | — | — | Conversation and per-Conversation identifier detection are not built |
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
