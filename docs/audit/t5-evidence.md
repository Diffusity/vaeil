# T5 persistence evidence

## Cycle1 — Member round trip / explicit mapper

Approved seam: docs/specs/t5-persistence-seam.md. SQLite round-trip red: missing persistence module; boundary red: exact approved fourth site missing. Unauthorized mapper controls pass (wrong module or wrong function rejected). Green9targeted cases including purity,1Postgres skip locally. Test setup correction imported PrivateText/PrivateDate from their existing privacy module, no assertion weakened or new domain re-export added.

SQLAlchemy Core2.1.8 pinned after checking official PyPI release; psycopg3.3.8 pinned. One implementation and explicit mapping reconstruct MemberIdentity wrappers and complete ValuesProfile. Raw rows remain inside the adapter, SQL echo off/parameters hidden. Explicit commit persists, transaction context rollback on exit. Later cycles supply uniqueness/concurrency, audit/rollback, Conversation and sessions; do not claim these implemented now. No T4 files cherry-picked; branch based on masterf47d768.

Contract fixture supports file SQLite and loopback-only disposable PostgreSQL. PostgreSQL is deliberately skipped without VAEIL_TEST_POSTGRES_URL; CI service supplies it. A per-test database is created/dropped through external driver setup, never production Neon. CI result pending; no two-database pass claimed yet.

## Cycle2 — durable Pseudonym policy and uniqueness
Red10SQLitefailures: equivalentsdidnotraise,invalidformat/reserved/identifier/selfnameaccepted,andconcurrentclaimsbot hsaved. Green48targeted11PostgresskipsincludingexistingPseudonymandpuritytests. Sharedpurevalidate_pseudonym_candidateextractedwithoutchangingoldDirectoryseam; SQLusesitplusunique normalizedcolumn. SQLiteBEGINIMMEDIATEandPostgresdatabase-scopedadvisorytransactionlockserialize multirowoperations, withuniquenessstill enforcedbyDB. Throughputtradeoff: demo transactions serialize, nothigh-scaleclaim. CIcycle1passed bothdatabases; cycle2CIpending. One mistypedtestfilepathran0tests; correctedcommandgreen, notcountedasevidence.
