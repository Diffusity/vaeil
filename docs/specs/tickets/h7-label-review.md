## Parent

Part of #7. Ready-for-human: synthetic multilingual label review, not domain/audit implementation.

## What to do

Review the amended candidate evaluation labels before the commit-hash freeze. Download docs/research/label-review/english.csv or non-english.csv; no repo installation needed. This explicitly requested review ticket is an exception to later H1-H6 publication timing; it assigns nobody.

## Acceptance criteria

- [ ] Every non-English case has two independent named human reviews; every case has at least one reviewer who did not write it. Parth reviews English and all disputes.
- [ ] Proposed only: Nevil primary Hindi-English, Tej primary roman Gujarati/Gujarati script, Vatsal second reader. Confirm ownership before assigning. Reviewer notes are preserved, not paraphrased away.
- [ ] Record actual sheet distribution timestamp and 24-hour deadline. Collect sheets and list every disagreement with the reviewers' notes for Parth; no silent label changes.
- [ ] Apply only changes Parth approves. Exclude unresolved cases from the scored frozen set and report them separately, including lost language/category coverage.
- [ ] Freeze by exact Git commit after review, record the approved prompt revision, and run no 40-case accuracy comparison before it. Later objections produce included/excluded reports from identical stored predictions, not reruns.
- [ ] Keep the separate eight development cases and five edge probes out of the accuracy denominator. The vetting-input contract is unresolved; reviewing a synthetic V snippet does not define the production questionnaire.
- [ ] Each teammate can explain the cases they reviewed and the rubric at the viva. No domain core, audit code or secrets touched.

## Estimate and gates

0.25 focused session per reviewer; 24-hour calendar review window. Proposed ownership only, no assignee. Fixtures are synthetic; exact moderation outcomes follow the approved rubric. Runtime/latency work may run independently, but accuracy waits for review/freeze. Unresolved vetting input remains Parth's decision.
