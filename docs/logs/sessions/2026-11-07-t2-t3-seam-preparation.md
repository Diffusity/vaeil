# Schedule approval and T2/T3 seam preparation

Working block **2026-11-07 16:06:09–16:07:23 Asia/Calcutta** (10:36:09–10:37:23 UTC), based on observed clock readings; subsequent commit/publication bookkeeping excluded. No inferred full human session or pretracking time.

Applied explicit approval of the reduced schedule and human-review baseline. Preserved the 4.5-session gap as an unresolved capacity risk. Read implement/TDD/codebase-design skills, canonical T2 #9 and T3 #10 (no comments), domain vocabulary and assumptions. No approved method-level T2/T3 seam found. TDD explicitly requires confirming new public seams before tests; prepared docs/specs/t2-t3-seams.md for that focused confirmation. No definition re-interview, no product stubs/tests/code yet, no runtime/model/process/provisioning work.

Updated spec/DESIGN/assumptions and approval record, assumption validation green. New proposed interfaces are a ConversationDirectory owning lifecycle invariants and the existing identity projection, plus two synthetic same-origin HTTP endpoints for T3. Consent/threshold implementation remains T8, storage atomicity T5. Next: confirm interfaces, then show first red runs and continue vertical red-green cycles with T3 overlap. No teammate assignment or newly published ticket.
