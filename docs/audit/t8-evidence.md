# T8 tests-first, review and handoff evidence

Issue30 under#7; approved seam docs/specs/t8-reveal-seam.md; base78dd997; branchcodex/t8-reveal. No merge/deployment/provider authorization. All old frozen assertions retained.

| Cycle | Observed red | Green / commit |
| --- | --- | --- |
| Pure eligibility/consent | Missing domain module |33selected incl purity/AST; cdd0f40|
| Consent storage |2missing methods,2PGskips |35selected,2skips;683f83a|
| Atomic application |7missing module,7PGskips |42selected,9skips;b0b36ae|
| HTTP |3factory keyword failures,3PGskips |33HTTP incl T6/T7,33skips;2465b62|
| Browser ceremony |2missing RevealUI |2real-API browser10.8s;TypeScript/build;a837bf7|
| Review: DST elapsed time |1behavioral early-eligibility failure at71elapsedhours |34selected incl guards;200bb69|

The app-factory edit initially missed its annotated signature; corrected before green. The new partner browser helper initially did not await successful sign-in; explicit response200/signout readiness was added, retaining all ceremony expectations. No setup/invalid-script run counts as behavioral evidence or a mutation kill. Final canaries were tightened to legal_name, email, nonempty optional phone and the actual distinctive DOB; previous expectations retained.

## Two-axis review

Standards:0hard breaches/0actionable smells. Spec:1P2, direct subtraction of the same DST-aware timezone could count72wallhours as71elapsedhours. Both endpoints now normalize toUTC; literal regression needs no OS tzdata. Independent Spec recheck confirmed closure. No remaining source findings. Final doc/citation sanity is part of PR preparation.

## Mutation and normal checks

Local backend24/24:10domain,13SQLite,1AST. Browser2/2: ignored withdrawal and ineligible action. Exact source bytes restored and normal frontend build regenerated. Raw artifacts and the complete table are in docs/audit/t8-mutations.json, t8-browser-mutations.json and t8-mutation-results.md. Initial partial-run survivors/anchors and stricter committed withdrawal coverage are disclosed there. Final CI repeats13database faults on SQLite/Postgres plus10domain/1AST (expected37checks), and old T5/T6/T7 matrices.

Restored full Python724passed137explicitlocalPGskips39.14s; Ruff/assumptions/purity/AST green. Frontend typecheck/build green;30browserpassed1.2minutes. Subsequent stricter T8canary fixtures:11passed11skips2.68s, no production change or case reduction. Final Windows/container/sharedPostgres CI is required on the published head.

## Limits, effort and next step

No production database tests, deployment, real model or safety certification. Rule4/Rule5partial,3/6domain0/6complete-ruleE2E unchanged. Status/partner reads may straddle completion; the UI rejects inconsistent shapes and refreshes instead of guessing. Read states can become stale; no polling/expiry/progress feature added. The admitted/synthetic fixture is isolated from production. Indirect identity leakage remains heuristic, and deliberate extraction by authorized code remains possible.

Optimistic T8 allowance2lead sessions; human actual focused sessions and pretracking effort remain unverified. Verified working-block timestamps are in docs/logs/sessions/2026-11-17-t8-implementation.md, not converted into invented human velocity. Conditional on T8acceptance, remaining T9Admin1.5+T10Matching1.5+T11Block/Report1+T13seed/evaluation1+integration0.5=5.5optimistic sessions. T8review/merge and rework still consume capacity; no claim of a solved schedule gap. Freeze28November,29November–4December rehearsal/fixes only,viva5December. Next is T9Admin and the required deployed six-rule checkpoint, not optional UI/model work.

Small retrospective: measure elapsed time inUTC even with aware timestamps; use literal timezone-edge oracles. Await real authenticated readiness in multi-context browser tests. Test both rollback and committed withdrawal. Preserve exact source restoration, independent review axes, existing toolchain and truthful human/agent timing.
