# Testing

Vaeil's rules are tested where they live. This file maps each rule to the test that proves it, says how many rules are covered, and names one test I would not defend as strong.

**Status: in progress.** Slice 1 proves Rules 1, 2, and 6 at the domain seam. Rules 3–5 have no tests yet. The final answer before the pushed `project-final` tag is **6 of 6**; the table below is the checklist.

## How to run

```powershell
.venv\Scripts\python.exe -m pytest -q
```

22 tests, all green at slice 1. No network, no database, and no real clock: the domain tests use in-memory fakes, including a fixed `FakeClock`.

## Rules → tests

| # | Rule | Test(s) (`file:line`) | What is proven | What is still missing |
|---|------|-----------------------|----------------|----------------------|
| 1 | Invite-only access | `tests/test_invite_redemption.py:121`, `:131`, `:136` | An Invite is required, single-use, and unknown or malformed Invites are refused without changing the original redeemer | Account creation and the API/UI are not built; the app slice must redeem before creating an account |
| 2 | Vetting never rejects | `tests/test_vetting.py:42`, `:58`, `:64`, `:70`, `:76` | Reject is unrepresentable; port errors, timeouts, and non-Verdict results fail closed to NeedsReview | The Admin approval flow, persistence, and the real LLM adapter are not built |
| 3 | Moderated delivery | — | — | Messages and moderation are not built. Fail-closed is proven for vetting only, not yet for Messages |
| 4 | Consensual Reveal | — | — | Conversation and Reveal are not built |
| 5 | Anonymity before Reveal | — | — | Conversation and per-Conversation identifier detection are not built |
| 6 | Age gate | `tests/test_invite_redemption.py:54`, `:68`, `:77`, `:86`, `:91`, `:104`, `:112`, `:150` | Under-18 is refused and leaves the Invite unused; both birthday boundaries; the Feb 29 rule; future DOB has its own error; the age check reads the injected Clock | The UI must surface the refusal; no HTTP layer yet |

**How many rules are tested?** At slice 1, 3 of 6 rules have domain-level tests (Rules 1, 2, 6); none is end-to-end. At submission every rule has an automated test and the answer is **6 of 6**.

## The leap-day rule

Someone born on 29 February is treated as having their birthday on 28 February in non-leap years. In 2026 (not a leap year) they turn 18 on 2026-02-28, not 2026-03-01. Both dates are tested at `tests/test_invite_redemption.py:91` and `:104`; the clamp is implemented at `src/vaeil/domain/invite.py:71`.

## Mutation checks (slice 1)

After the suite was green, I broke three guards one at a time; each made at least one test fail:

| Mutation | Failing test(s) |
|----------|-----------------|
| Age boundary `>=` → `>` in `src/vaeil/domain/invite.py` | `test_turning_eighteen_today_is_allowed`, `test_leap_day_birthday_turns_eighteen_on_feb_28_in_non_leap_years` |
| Removed the single-use guard in `src/vaeil/domain/invite.py` | `test_redeeming_an_already_redeemed_invite_is_refused` |
| Propagated the LLM error instead of returning NeedsReview in `src/vaeil/domain/vetting.py` | `test_port_error_fails_closed_to_needs_review`, `test_port_timeout_fails_closed_to_needs_review` |

Each mutation was reverted and the full suite returned to green.

## The weak test

`tests/test_invite_redemption.py:150` (`test_age_check_uses_the_injected_clock_not_the_real_clock`) is the weakest test in this slice. It proves the Clock is used by picking a fake date (2030-01-01) on which a 2010-01-01 birth date is 20, while on the real 2026 date it is 16. If the implementation used `date.today()`, the test would fail today — but after 2028 the real date also makes that applicant an adult, so the test would pass for the wrong reason. The durable backstop is the purity guard at `tests/test_domain_purity.py:106`, which forbids `date.today()`, `datetime.now()`, and `time.time()` in the domain at all.
