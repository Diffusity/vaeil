# T6 implementation — 14 November 2026

Block start13:15:54 Asia/Calcutta. User approved docs/specs/t6-auth-admission-seam.md, including explicit security settings and fifth verifier site. Approved docs PR23green, merged asca2f475; featurecodex/t6-admission aligned to mergedmaster. First merge attempt used a mistyped expanded SHA and was safely refused; retried with actual git rev-parse HEAD. No reset/rewrite or user work discarded.

Starting approved note-only Vetting seam, then incremental note validation, credentials/sessions, atomic admission and profiles/HTTP. Old Vetting fixture/type-only diff shown before applying, all seven assertions preserved. No frozen test weakening authorized. Red evidence precedes each implementation cycle. Timing excludes unverified pretracking effort and must not infer human sessions from tool elapsed time.

Cycle1red1missingApplicantnote -> green16selected incl7legacyassertions/purity/unwrap; commitcd7d3e5. Cycle2red24failed1passed: missingvalidator and actualinvalid-noteapproval assertion; green40selected after sharedtrim/NFKC20–500/control/scanner/wholewordcheck. Lint-only newtestimportplacement corrected with no assertion change.

Cycle3red12failed7passed (missingpasswordadapter/exactfifthsite) -> green21selectedincludingpurity. Realstdlibscrypt with OWASP N2^17/r8/p1; salts and storedhashopaque; wrongpassword/malformedcostfailclosed; approved12–128codepointboundaries and no normalization. Exact ASTaddition plus wrongfunction/module positivecontrols; no other oldtest changes. Source https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html checked14November.
