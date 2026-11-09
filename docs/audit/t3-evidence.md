# T3 local walking skeleton — 9 November

Spec #10; approved interfaces in docs/specs/t2-t3-seams.md. Base master2794a56274b98fd0324b2469857bd20103ca6c1e. No existing domain/T1/T2 test was changed; no private unwrap site added.

| Cycle | Red evidence | Green evidence |
| --- | --- | --- |
| Anonymous endpoint | Missing module, then minimal real FastAPI app returns404 instead of200 | Exact anonymous payload passes through domain projection and authorized encoder; cc1cb4d |
| Health/build/query guard | 5failed6passed; missing build-path setting and4 query requests incorrectly return200 | 11 HTTP cases pass; e51e8f8 |
| Browser display/states | 3 browser tests fail: Comet, loading status and error alert absent on incomplete page | 3 pass against built React served by real FastAPI;447faef |
| Malformed success | 1failed3passed:200 response with invalid shape has no load-error state | 4 browser tests pass; runtime shape guard and strict TypeScript checks green;0b2e9c3 |

Full Python check: **463 passed**, Ruff and assumptions green; four browser tests separately green. Strict frontend TypeScript/build green. Python static typing is not configured. Windows CI repeats Python, frontend typecheck/build and Chromium tests; local browser is installed Edge. Starlette emits an unsuppressed httpx deprecation warning; assertions remain green. No live model/database is used. Rule5 partial,3/6 domain,0/6 complete-rule E2E unchanged.

## Five-command fresh-checkout verification

Verified a new local Git clone at `%TEMP%/vaeil-t3-fresh-20261109-verified`, commit0b2e9c3, using `--no-hardlinks` to copy between D: and C:. This is a fresh working tree/dependency directories, not an uncached internet-download claim. Python3.11.2, Node24.13.1, npm11.12.1. The README's five application-run commands passed: new venv, editable dev install, npm clean install, Vite build, Uvicorn factory on127.0.0.1:8000. Health JSON, built root HTML and exact anonymous Member response verified. The fresh checkout also passed all four browser cases. All owned server process trees stopped afterwards; no database/model/service provisioned. Clone command/cd are checkout prerequisites, not additional application-run commands.

The first verification attempt failed before creating a clone because Git tried cross-volume hardlinks; `py -3.11` also did not resolve an installed Python. Its shell did not stop immediately and reran installs/build in the original checkout; it is **not** counted as successful fresh verification. The corrected run used the verified `python` executable and explicit fail-fast checks after every stage. No unrelated directory was deleted. Temporary clones are retained for inspection, not running.

## Focused privacy mutations

Run alone, replacing one source anchor at a time in `src/vaeil/web.py`, running `pytest -q tests/test_web.py`, then restoring exact bytes:

| Change | Result |
| --- | --- |
| Fixed ConversationRevealState False -> True | Killed by anonymous shape/canary assertions |
| `if request.query_params:` -> `if False:` | Killed by four unsupported-parameter cases |
| Add `legal_name` field to authorized response | Killed by exact payload and private-field assertions |

**3/3 killed**, source restored SHA25627b1cc4daf6f990d4dd759f001fab9b0f3b3d0235d02f8f99b142236efa4c559. Source restoration precedes normal final checks/CI; do not run mutations alongside source readers/writers or tests. Existing domain mutation evidence remains unchanged.

## Review and scope

Independent Standards review requested final graded-doc refresh; no additional implementation finding. Independent Spec review found no actionable mismatch; malformed-success cycle was already in progress. Final review rechecks follow the doc refresh. This public route is fixed fictional data, not auth/registration or a Member-facing identity retrieval service. T4 deployment remains approval-gated; T5/T6 provide storage/auth, later tickets moderation/Reveal/Admin. The local model is optional and no new runtime GO is inferred.
