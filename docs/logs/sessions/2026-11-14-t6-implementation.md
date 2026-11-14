# T6 implementation — 14 November 2026

Block start13:15:54 Asia/Calcutta. User approved docs/specs/t6-auth-admission-seam.md, including explicit security settings and fifth verifier site. Approved docs PR23green, merged asca2f475; featurecodex/t6-admission aligned to mergedmaster. First merge attempt used a mistyped expanded SHA and was safely refused; retried with actual git rev-parse HEAD. No reset/rewrite or user work discarded.

Starting approved note-only Vetting seam, then incremental note validation, credentials/sessions, atomic admission and profiles/HTTP. Old Vetting fixture/type-only diff shown before applying, all seven assertions preserved. No frozen test weakening authorized. Red evidence precedes each implementation cycle. Timing excludes unverified pretracking effort and must not infer human sessions from tool elapsed time.

Cycle1red1missingApplicantnote -> green16selected incl7legacyassertions/purity/unwrap; commitcd7d3e5. Cycle2red24failed1passed: missingvalidator and actualinvalid-noteapproval assertion; green40selected after sharedtrim/NFKC20–500/control/scanner/wholewordcheck. Lint-only newtestimportplacement corrected with no assertion change.

Cycle3red12failed7passed (missingpasswordadapter/exactfifthsite) -> green21selectedincludingpurity. Realstdlibscrypt with OWASP N2^17/r8/p1; salts and storedhashopaque; wrongpassword/malformedcostfailclosed; approved12–128codepointboundaries and no normalization. Exact ASTaddition plus wrongfunction/module positivecontrols; no other oldtest changes. Source https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html checked14November.

Cycle4red4failed4PGskips -> green14selected4skips; combinedold/newstorage38passed34PGskips. Addedprivateprincipal/applicationrecords, uniqueemail, hashedInvitecodes/atomicconsume, terminalAdminCAS/rollback, singleSQLimplementation. Existingcontractfixture reused via pytest plugin; CI includes newcontractfile on bothdatabases. Lint-onlyfixture-registration change, no assertion weakening.

Cycle5applicationred9failed9PGskips -> green23selected13PGskips with restrictedpending sessions/live roles,24hexpiry/logout,unknown/wrongcredentialssafefailure,underagebeforemodel/Inviteconsumption,humanterminalauditeddecisions. Applicationorchestration outsidepuredomain; newClock.now injected. No HTTP path or profile complete flow claimed yet.

Cycle6profile red7failed7PGskips -> green220selected7skips including all existingT1member/profile tests unchanged. Shared profile validation now supports explicit partialdrafts without fakechoices; completefactoryvalidationorder preserved. DraftcandidateisnotclaimeduntilfirstcompleteMemberinsert. Fixed-oncecompletePseudonym, takenretry, own/admittedaccess and laterprofileupdates tested. No Member reference or identity in draftreceipt.

Cycle7HTTPred11failed11PGskips missingfactoryinjection -> green22selected11skips includingexistingHTTPassertions. Addedexplicitpayloads, same-originCSRF,securecookie,restrictedpending login,Adminnoteonlyqueue/decision,ownencoding. Authstorage/compositionlazy so health/demo donotneedDBstartup. InitialsandboxHTTPteststalled; stoppedidentifiedPID2880tree and reranunchanged outside sandbox (1.93s). No expectation weakened.

Cycle8browserred2missingApplybutton -> green6browser(including4existing), TypeScript/build/Ruffgreen. RealAPIregister/login/pending403/logout testedthroughownedtempSQLitefixturewithfictionalInvite; separatevalidationfailureUIrephrase/retrytest. FixtureoverridesDATABASE_URLtoownedtempstorageandremovesAdminenv; neverNeon. No note/profileinputtruncation or browserpasswordnormalization. Required minimalUIonly; teammateform/Adminconsole stilllater.

Hardening: passwordcapacityred1missingBusyError ->37selectedpass15PGskips; actualInvite/AdminCASraces,humanbaselineclean/injectionNeedsReview,forgedroleandfailed-auditrollback alreadygreen(nofabricatedred). Sourcecapacitycommitdc775eb. SeparateTLSredasserteddisable!=verify-full ->64selectedpass49PGskips; aa66f20. Partialindexpatchforcapacitytestfailed(CRLF); no workingtestwasremoved, sourcecommitsremainedgreenonpreviouslyrunchecks; capacitytestincludedwithfollowingcredential-formatcycle.

Credentialformat red1frozenreferencevectorrefused -> versionlabelscrypt-v1. ReferencecomputedindependentlyofadapterwithstdlibscryptpasswordIndependent reference phrase,saltbytes00..0f,N131072/r8/p1/dklen32; frozenhex284a357c3ae912808cf3c68ca883509118d444d42a43507b54bcc9b5eec718dc. Malformedhashfixtureprefixestightenedtov1(noassertion/casecountreduction)soinvalidcost/hexstilltestedafterversioning.

Cycle12HTTPguidancered1KeyErrorcan_rephrase/1PGskip -> green12HTTPcases12PGskips. Preserved fixed domainmessage/field/rephraseflag, no offendingtext. Versioncycle23selectedgreen. No furtherprivateextractorsorinputechoes introduced.

Cycle13Inviteorderingred1modelreceivednoteonunknownInvite/1PGskip -> green21application/repositorycases20PGskips. Addedshortrequire_invite readbeforemodel, thenatomicconsumerecheckaftermodel outsidewriteTxn. Underagepriorityandconcurrentone-winner behaviorretained. No modelbudgetspentforinvalid/alreadyusedInvites.

InitialT6matrix34/34localkills,exactbytesrestored; PostgreSQLmatrixrequiresCI. Clockadapterred1localdate14!=15 atUTCboundary ->green3selected; preservedexistingClock.todaylocal-calendardatecontractandUTCnowforexpiry. Runtimeuseshostcalendarconfiguration,notviewer-controlledtime. No newproducttimezonechoice.

AdditionalUnicodecasefold/NFKCuniqueness/logincasesalreadygreen; full604passed75PGskips24.81s. Availabilityregression thenredblockedrepositoryprobeTimeoutErrorwhileKDFpaused; movedverificationoutsiderepositorytransactionandfreshlyrecheckedhashbeforeSessionwrite, green1local1PGskip. This avoids holding the global demo write lock during expensive crypto.

14:54+05:30 continued block: availability regressions red/green committed c4699c0 (KDF outside transaction), b4f15fe (remote time bounds), 60cc62d (duplicate normalized email503 ->409, Invite retry). Restored full checks606passed77PostgreSQLskips26.95s; frontend build/typecheck green,6browser9.0s. Two-axis review: Spec0; Standards1 contradictory DESIGN current-state assertions, corrected. Initial default-codepage doc edit failed safely on DESIGN; reran explicitly UTF-8; no source/test expectation change. Expanded mutations now running alone.

15:04+05:30: final local mutation matrix43/43killed, oldT5matrix14/14killed, exact source restoration verified. Issue13 follow-up added two per-database persisted-note recipient-view cases plus concrete H1 HTTP contract; test setup attribute typo corrected before behavioral assertions, no implementation/old assertion weakened. Final restored suite608passed79PostgreSQLskips24.52s. Rule5partial,3/6domain0/6complete-ruleE2E unchanged. PR/remoteCI next; no merge/deploy/T7.

Resumed17:29:04+05:30 after user Continue. Prior block last recorded work15:04; the intervening gap is not counted as active effort and its exact stop time is unverified. Final review follow-up found two additional stale TESTING statuses and one HTTP error-envelope wording mismatch; documentation corrected without product/test changes. PR publication and CI follow-up now.
