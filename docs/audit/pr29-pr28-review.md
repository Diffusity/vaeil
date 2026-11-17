# PR29 and PR28 review against master — 17 November 2026

Pinned master a4036b6702aed3748680cb48542bb2186741078c. T7 PR29 head8fb4c0a579e509ceb7916facd00e512032b9f7c4; H1 PR28 head6789bcec0e535375374c84aa3e4c8d0c733fd4c4. Two independent parallel review axes follow the code-review skill. User explicitly authorizes finding resolution and merge commits, not deployment or T8 implementation.

## Standards

PR29: no documented-standard breach or actionable baseline smell. Domain/infrastructure separation, explicit mappings, independent recipient/review body views, transactional audit and synchronized vocabulary are preserved.

PR28: no documented-standard breach or actionable baseline smell. Stable codes and server-owned policy, isolated fictional fixtures, private browser-state handling and factual AI attribution are preserved. Corrective commit2d04057 also passed independent Standards inspection.

## Spec

PR29: no actionable finding against Issue25 and approved T7 seam.

PR28: one P2, stale profile expiry. An old GET or PUT401 could invoke the shared expiry callback after sign-out/new sign-in, clearing the new principal. Requirement: restricted/expired sessions must have correct sign-in/admission feedback; an obsolete response cannot override the newer explicit sign-in. Both new cases at frontend/tests/profile.spec.js:210 failed at the missing Signout assertion on a rebuilt unfixed H1. First stale-assets run excluded as setup failure. Commit2d04057 captures an effect generation for every load/save, invalidates it on cleanup, and checks it before expiry/state/error/finally. Both green18.8s; independent Spec recheck confirms closure.

## Integration and evidence

PR29 merged with merge commit b4d5ecadb1908aa68e1088d0a311f0ae33910d5b after final-head CI43939340020 passed. Issue25 closed. T7 mutations53/53 (23SQLite23Postgres6domain1AST); prior T5 27/27 and T6 69/69 also killed; browser5/5 recorded in T7 artifact.

H1 integrates that master with a merge commit, preserving authVersion session restoration, profile-request generation safety, ProfileForm, ConversationPanel and both fixture inputs. Both reviewers confirmed integration. Existing assertions unchanged; only two stricter browser cases added. Combined local checks:687passed124explicitPGskips55.99s; Ruff/assumptions/purity/AST green; TypeScript/build green;28browserpassed1.5minutes. Final integrated head requires Windows/container/shared-database CI before H1 merge.

H1 commits retain Nevil attribution and disclosed Codex assistance; review/integration uses project author. Issue26 intentionally remains open for Nevil understanding/viva handoff, not incomplete code. No teammate learning or human effort invented. Rule5partial, Rule3partial;3/6domain0/6complete-ruleE2E unchanged. No deployment/models/tunnels/T8 implementation. Final CI and merge outcomes are appended to the session log in the next authorized record.
