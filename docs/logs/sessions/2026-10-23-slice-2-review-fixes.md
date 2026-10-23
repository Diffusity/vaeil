# Slice 2 review fixes

- User requested fixing both review findings and updating the existing PR.
- P1: added two tests through the approved scanner seam, bounded by a subprocess timeout. Before implementation, both 100 KB dot/hyphen-separated clean-input scans exceeded three seconds: **2 failed, 50 deselected**. Red commit: `31c8b46`.
- Existing review profiling had already isolated repeated suffix scans in the obfuscated-email pattern, so no further bisection or hypothesis search was needed. Restricted matching to the start of a local-part token instead of every internal word boundary. Existing supported-obfuscation tests remain green.
- Direct post-fix scans of both 100 KB inputs: approximately 0.0405 and 0.0353 seconds. Full suite: **107 passed**. All 12 requested detection/Pseudonym mutations still fail tests; sources restored. Updated TESTING counts, mutation results, regression explanation, and moved test citations.
- P3: marked the old local-folder preference superseded in `docs/logs/assumptions.md`. Repo identity remains unchanged; the actual folder is still `D:\vaili` because of the previously reported Windows lock.
- No new product assumptions, delivery behavior, or next-slice work. Rule 5 remains partial; counts stay 3 of 6 domain-level, 0 of 6 end-to-end. Existing PR #3 is the review surface.
