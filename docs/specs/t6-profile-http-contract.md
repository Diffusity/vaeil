# T6 own-profile HTTP contract

For H1's structured form. This documents the implemented API; it does not expose another Member's profile. All responses are `Cache-Control: no-store`. Use relative URLs and the server's HttpOnly session cookie; never store or send a token in JSON. Mutations require the same-origin `Origin` header. Pending/rejected Applicants cannot use these routes.

## Read and save

`GET /api/me/profile` and `PUT /api/me/profile` require an admitted Member session. PUT accepts only `pseudonym`, `relationship_intent`, `life_stage`, `interests`, `values`, `communication_style`, `pace_and_lifestyle`, and `about`.

Choice codes are pinned by `tests/test_member_identity_red.py:302` and defined by the enum classes in `src/vaeil/domain/profile.py`; use those codes, with frontend display labels. Interests/values are arrays of distinct codes (0–5 for a draft, 1–5 for completion). About is normalized, scanned, self-name checked and capped at280 normalized code points; no truncation.

Example first complete write:

```json
{"pseudonym":"Comet","relationship_intent":"long_term","life_stage":"undergraduate","interests":["reading"],"values":["honesty"],"communication_style":"direct","pace_and_lifestyle":"quiet_and_routine","about":"I enjoy quiet walks."}
```

PUT is a replacement of the supplied profile draft, not a field merge. Missing choices become null, selections empty, About empty. Send the whole form on each save. A previously stored draft Pseudonym candidate may be used at completion when omitted from the complete write; a partial save without a candidate does not retain it in the new draft. Candidates are not reserved until completion.

Incomplete GET/PUT returns200:

```json
{"complete":false,"values_profile":{"pseudonym":null,"relationship_intent":null,"life_stage":null,"interests":[],"values":[],"communication_style":null,"pace_and_lifestyle":null,"about":""}}
```

Complete GET/PUT returns200, with exactly the authorized own-profile fields:

```json
{"pseudonym":"Comet","values_profile":{"relationship_intent":"long_term","life_stage":"undergraduate","interests":["reading"],"values":["honesty"],"communication_style":"direct","pace_and_lifestyle":"quiet_and_routine","about":"I enjoy quiet walks."},"legal_name":"Fictional Person","email":"fiction@example.invalid","phone":null,"date_of_birth":"1987-03-14"}
```

A complete response has no `complete` flag. After completion, omit `pseudonym` on updates; providing it again returns409 even if unchanged. All complete-profile fields must still be supplied. Neither response includes the application note. These own-profile identity fields must never be copied into recipient views or logs.

## Safe errors

400 means invalid shape/profile/code/safety input;401 missing/expired session;403 admission/authority or Origin refusal;409 fixed/taken Pseudonym;503 unavailable/busy infrastructure. Profile validation returns `reason`, safe `field`, fixed `message`, and `can_rephrase`; other errors return a fixed `reason` or fixed `detail`, depending on the validation path. Never infer successful storage on an error. Preserve form state to allow correction; do not render submitted input from server error text.

Registration/session routes and security settings remain in `t6-auth-admission-seam.md`. The minimal registration/session UI is implemented; H1 owns the later structured form.
