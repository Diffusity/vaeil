# T6 red/green evidence — implementation pending review

Approved seam docs/specs/t6-auth-admission-seam.md; approved docs PR23mergedca2f475. Feature codex/t6-admission, baseca2f475. No T6 merge/deployment authorized or performed. Full timeline: docs/logs/sessions/2026-11-14-t6-implementation.md.

| Cycle | Observed red | Observed green |
| --- | --- | --- |
| Note-only port |1missingApplicantnote |16selected, seven legacy assertions retained |
| Note validation |24failed1passed; missingpolicy and actual invalid-note approval |40selected |
| Scrypt/exact fifth site |12failed7passed |21selected |
| Private admission storage |4failed4PGskips |14selected4skips; old/new contracts38pass34skips |
| Application/session workflow |9failed9PGskips |23selected13skips |
| Draft/completion/profile update |7failed7PGskips |220selected7skips incl frozenT1profile cases |
| Authenticated HTTP |11failed11PGskips |22selected11skips incl existing HTTP cases |
| Minimal registration/session UI |2missingbutton |6browser,TypeScript/build |
| Password capacity |1missingBusyError,13application regressions alreadygreen |37selected15PGskips |
| Remote storage TLS |disable!=verify-full |64selected49PGskips |
| Versioned independent hash vector |1validreference refused |23selected |
| Safe rephrase guidance |1missingcan_rephrase,1PGskip |12HTTP12skips |
| Invite before Vetting |1modelcalledonunknownInvite,1PGskip |21application/repository20skips |
| Local age date/UTC expiry |1date14!=15 atfixedboundary |3selected inclpurity |

Full restored check:600passed71explicitlocalPostgresskips,25.20seconds; Ruff/assumptions/TypeScript green. Browser6passed8.3seconds. One existing unsuppressedStarlette/httpxwarning remains. Initial localT6mutations34/34killed; originalT5local14/14killed. Final remote contracts/matrices and review remain gates. No six-ruleE2Ecompletion claim; Rule5partial.

Old test changes: tests/test_vetting.py changes only three fake argument annotations plus valid-note fixture used by six behavior tests; all seven assertions retained. tests/test_private_unwrap_boundary.py adds only the approved fifth function and two stricter login positive controls. Frozen T1Member/profile/scalar assertions unchanged. New malformed-hash fixture prefixes tightened to the new valid version to retain meaningful invalid-cost/hex cases; no case count reduced. No tests were deleted to reach green.

Known operational scope: current deployed runtime remains T4. Default local auth storesSQLite; runtime seeding reads owner env only on actual authentication use. Browserfixture overrides storage with an owned tempDB and removes inheritedAdminenv. RealModel/tunnel/provider work remains deferred. Admin console, Invite issuance UI, Messages, Reveal, Matching and Report/Block flows are not implemented by this slice. Admission queue API and minimal registration/sessionUI are included; profile-form teammateUI remains separate.

Additional restored run:606passed77explicitPostgreSQLskips26.95s; six browser tests9.0s, build/typecheck green. Availability regressions: KDF lock-scope failure -> pass; remote timeout arguments absent -> present; duplicate-email503 ->409 with Invite retry. Issue13 recipient-note canary additions are regression coverage already green after correcting a new test setup attribute typo, not behavioral red claims. Final totals below supersede earlier chronological snapshots.

Final restored check after all mutations and review coverage: **608passed79skipped24.52seconds**, Ruff/assumption validation green. Final localT6matrix43/43killed and T5matrix14/14killed, exact byte restoration; no live DB/model. Windows/shared-PostgreSQL/container CI remains required on the PR.
