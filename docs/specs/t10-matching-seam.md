# T10 Matching seam — approved

22 November 2026. Based on [MVP #7](https://github.com/Diffusity/vaeil/issues/7), merged T1/T2/T5/T6/T8/T9 and working Plan B. Approved by Parth on 24 November 2026; tracked in #34. T11 owns Block/Report controls; T10 must already honor stored Block outcomes through the existing Conversation seam.

## First end-to-end slice

An Admin proposes Matches using admitted Members with completed Values Profiles. Two fictional Members see an anonymous Match card. One acceptance leaves the proposal pending; the other creates exactly one anonymous Conversation and exposes its link only to the two participants. A decline closes that proposal and permanently excludes that unordered pair.

## Proposed ranking policy

Use only the six structured fields. Compare equal enum codes for the single-choice fields. For interests and values, use set intersection divided by set union (Jaccard overlap). Use these proposed weights:

| Structured field | Weight |
| --- | ---: |
| Values | 30 |
| Relationship intent | 25 |
| Communication style | 15 |
| Pace and lifestyle | 15 |
| Interests | 10 |
| Life stage | 5 |

Use integer basis points: a single-choice equality contributes `weight * 100` or zero; a set contributes `(weight * 100 * shared_count) // union_count`. Sum the contributions (0–10,000). Values and intent carry the most weight; set overlap rewards agreement without favoring longer lists. No eligibility threshold or new preference filters. About, Pseudonym, private identity, demographics outside the structured fields, and AI are never inputs. Pin a worked example using existing codes: values `{honesty, kindness}` vs `{honesty}` contributes 1,500, matching intent and style 2,500 + 1,500, disjoint interests and different pace/life stage zero; total 5,500.

Rank by descending score, then ascending canonical pair of stable internal Member IDs. IDs break ties only, never enter partner payloads, and make ranking invariant to input order. Proposed small batch policy: walk that order once, greedily take disjoint pairs, and keep at most one pending proposal per Member. A repeat batch must not duplicate pending rows. A revealed Conversation frees the Member for other partners. **Proposed for MVP:** do not reintroduce a pair that already opened a Conversation; this avoids proposing an already introduced pair again after Reveal and is a decision for review rather than an existing permanent exclusion rule. If rematching former partners is desired, say so before tests.

## Interfaces and invariants

| Public seam | Proposed interface and observable result |
| --- | --- |
| Pure score/ranking | `compatibility_score(left: ValuesProfile, right: ValuesProfile) -> int`; `rank_pairs(profiles_by_member_id, *, excluded_pairs, unavailable_ids) -> tuple[RankedPair, ...]`. Domain deals only in complete scores, unordered distinct pairs and deterministic order; application supplies current eligible inputs. |
| Admin triggers proposals | `MatchingApplication.propose_matches(*, actor) -> int`; `POST /api/admin/matches` empty body returns a created count. Read approved Member and completed profile records, pending reservations, terminal pair history and active/Blocked Conversations in the same transaction that writes the proposed batch. No client-supplied candidate list, rankings or Member IDs. |
| Member reads own Match | `MatchingApplication.read_matches(*, actor)`; `GET /api/me/matches`. Explicit envelope with opaque Match ID, viewer decision/Match state and partner view. The nested partner view is exactly `PreRevealMemberView(pseudonym, values_profile)`. Only after both accept add the authorized Conversation link. Render partner information for the proposal with the existing two-field view and encoder; never use a historic Reveal to project a new Match and never expose a real Member ID, score or private identity. |
| Member chooses | `MatchingApplication.decide_match(*, actor, match_id, decision)`; `POST /api/me/matches/{match_id}/decision` with exactly `accept` or `decline`. A participant can submit only their own decision; identical repeat is idempotent and conflicting/terminal changes get a safe 409. Never open on first acceptance or after a decline. Return a safe not-found response to outsiders and missing IDs. |

Each operation rechecks stored authority, and browser mutations use the existing cookie/Origin checks and no-store responses. Proposal and second acceptance recheck admission, profile completion, Block, and active slot from current storage; second acceptance commits its decision and the Conversation through the existing serialized Repository transaction. On conflict or a write failure, no partial second acceptance or extra Conversation survives. Reuse Conversation slot rules rather than duplicating them in React. No live LLM, explanation text, Icebreakers, score UI, or new private unwrap.

## Acceptance and estimate

- Pin exact score arithmetic, field exclusions, tie-break order, symmetry, and identical results under input permutations. Confirm draft/ineligible profiles, declined/Blocked pairs and Members in active Conversations never enter a proposal. Pin what happens after Reveal and on repeated batches.
- Real HTTP/browser: Admin triggers, outsider and forged body refused, both accept before the anonymous link appears, and decline prevents any later reproposal. Exact nested partner keys and canaries; HTML-like text stays inert; no DOB, phone, legal name, email, or photo leaks. Cover stale sign-in responses for the private page.
- Both SQLite/PostgreSQL: competing batch requests and repeated/competing accepts produce at most one proposal per eligible Member and one Conversation; second-acceptance conflict/rollback preserves repository state. Use the same contract selection on both sides of the mutation run. Mutations: bypass complete-profile/Block/decline/active checks, unstable tie-break, open after one acceptance, broaden the partner view. Keep Rule 5 partial until deployed evidence closes it.
- Previous plan: **1.5 optimistic sessions, 2–3 ordinary** for T10. Keep one Admin button and a plain Member card. T11 Block/Report and T13 demo/evaluation remain required before the final checkpoint; don't spend remaining freeze capacity on optional features.

Approved: weights/rounding, canonical tie-break, one pending proposal per Member with greedy batches, and no repeat introduction of an already accepted pair. Use tests first only after this seam is agreed.
