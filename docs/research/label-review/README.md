# Synthetic label review — 24-hour window

Candidate revision: the amended 40-case set in ../local-model-labels.json. Not frozen. Download english.csv or non-english.csv and open in a spreadsheet; the UTF-8 BOM preserves Hindi/Gujarati. No repository setup is needed. Only synthetic case text is included; no credentials, model results or real Member data.

Fill reviewer, agree_or_disagree (agree/disagree), and note for each assigned row. Keep case_id/text/expected_label unchanged. Save a separate copy named with your name; a disputed label is a note, not an edited expected label.

Proposed allocation, not a final assignment: Nevil primary Hindi-English (8 cases); Tej primary roman Gujarati and Gujarati script (16 cases); Vatsal second reader of all non-English cases (24). Parth reviews all English (16) and every dispute. Every non-English case needs two distinct reviewers; every case needs a human who did not author it. No teammate has been assigned or contacted automatically.

The review window is 24 hours from Parth distributing these sheets; record that actual handoff timestamp and deadline before counting it. No handoff or completed review has yet been verified. Return completed sheets via this workspace/conversation. Preserve originals; produce a disagreement table with case ID, both notes and proposed resolution, then wait for Parth's decision. Never silently settle disputes.

After approved resolutions, freeze the approved case set and prompt by Git commit hash. Anything unresolved is excluded from that commit's scored set and listed separately, with actual counts (do not claim 40 scored cases if fewer remain). Report missing reviewer coverage and category/language gaps. No accuracy run until this gate and the vetting-input question are resolved. If Parth objects after freeze, show both included/excluded metrics from the same stored outputs; no relabel or rerun.

The eight-case development set is separate and is never added to the 40-case accuracy denominator. Edge probes are also separate/unscored. Reviewer exports should be regenerated if approved labels/text change before freeze.
