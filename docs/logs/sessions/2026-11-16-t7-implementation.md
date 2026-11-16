# T7 implementation

Block start verified2026-11-16T10:32:23UTC (16:02:23Asia/Calcutta). User explicitly invokes implement for T7#25: Messages and human-reviewed moderated delivery. Read issue/approved seam, assumptions/workflow/TDD and current storage/auth/privacy modules. Basea4036b6, branchcodex/t7-messages. H1PR28OPENunmerged; preserve pendingH1CIlog in path-scoped stash plus .git patch, unrelated untracked files untouched. NoH1merge/deploy/model/tunnel authorized. T7commitsusecurrentprojectauthor, notNevil attribution (H1only).

Pure assessment -> durable message transitions -> application/manual-review -> authenticated HTTP -> minimal ConversationUI, each red shown then green, onecommitpercycle. Final mutation/purity/AST/fullchecks/two-axisreview/PR required, no merge without later authorization. Rule5partial; current16Novembercalendar10.5corevs8–9slots remains risk, not verified human velocity.

Cycle1assessmentred33missingmodule ->green35selectedincludingpurity. Approved outcome/scanner/normalization/pair/Block policy only; no delivery persistence yet.

Cycle2repositoryred5local4PGskips ->green48selected4PGskips inclassessment/purity/AST. Singlecanonicalbody, immutable slotted non-dataclassrecords, request/reviewdigestuniqueconstraints, terminaltransitionguards, exactroundtrip/rollbacktested. PostgreSQLnotclaimedlocally; sharedCIwillrun.

Cycle3applicationred11local11PGskips ->green59selected15PGskips inclrepository/assessment/purity/AST. Durable in-flight requestreservation exposes only technicalBusy receipt on replay, so cross-instance samekeydoesnotcallmoderationtwice; modelcalloutsidewrite. Finaltransitionfreshpair/Block/revealcheck, manualsubmission/terminalhumanrelease/discard+atomic audit, timestamponactualdelivery. Unfinishedservercrash attempt stays technicalBusy; newrequestkeycanretry, never counted/delivered. This is infrastructure failure behavior, not auto-approval.

Cycle4HTTPred9local9PGskips unexpectedfactorykeyword ->green40passed40PGskips, including T6HTTP regressions. Routes use existing T6 session/Origin/exact/NoStore helpers; Messagebody DTOs explicit. NewHTTPfixture hash corrected toexistingfakecredentialencoding before behavioral checks; no policy assertion weakened. Body-only test mode remains trustedDI, no production approval switch.

Cycle5runtimeconfigred3failed2pass5PGskips (productionmisuse/malformedaccepted,demofailureignored) ->green8selected5PGskips inclruntimeclock/purity. VAEIL_DEMO_LLM_FAILURE=1onlywithVAEIL_ENV=demo forcesTimeoutError; otherproductionusesrefused beforemessageapp, noHTTPswitch/noinference.
