# T1 private scalar serialization — resolved decision

Resolved 25 October 2026: Parth approved opaque private text **and date**, strict same-wrapper equality, unhashable values, redacted formatting and the exact three-function AST unwrap boundary. Test-only commit `34bb4e9` preceded implementation commits `30ddc9e` and `06fd4b6`; 401 tests pass. The proposal below is preserved as decision history, not a pending gate.

Latest user condition 3: every type holding private values must refuse generic serialization. Earlier approved field declarations use native `str` for legal name/email/phone. Those constraints conflict when private text itself is passed to the standard JSON encoder: it accepts str subtypes without invoking repr/str/reduction guards.

Current head `b1dd84a`, all 325 tests green. Generic **records** refuse pickle, reduction, copy/deepcopy, asdict/astuple, state export and root JSON mapping. Independent Standards and Spec reviews found no additional canonical record export bypass. The stricter scalar behavior is not covered by the current tests and is not implemented. No tests changed after `607062b`.

## Reproduction (synthetic data only)

```python
import json
from datetime import date
from vaeil.domain import MemberIdentity
identity = MemberIdentity("demo", "SyntheticNameZXQ", "synthetic@example.invalid", None, date(1987, 3, 14))
json.dumps(identity.legal_name)  # '"SyntheticNameZXQ"', not a TypeError
```

## Recommended: approve opaque private text and stricter tests

Keep the exact view field sets, but change private text field types on MemberIdentity, RevealedMemberView and OwnProfileView:

```diff
- legal_name: str
- email: str
- phone: str | None
+ legal_name: PrivateText
+ email: PrivateText
+ phone: PrivateText | None
```

PrivateText would be an immutable slotted opaque value, **not a str subclass or dataclass**, so generic JSON cannot encode it and asdict cannot recursively expose an internal string. Domain token checks and the explicit authorized view encoder deliberately unwrap it. PrivateDate can retain its guarded date-compatible representation: native JSON does not encode date objects. Public view field names and the explicit authorized JSON payload remain unchanged. This is a public field-type refinement requiring approval, not an implementation-only rename.

Proposed additional tests, **not applied or run**:

```diff
--- a/tests/test_member_identity_red.py
+++ b/tests/test_member_identity_red.py
@@
+@pytest.mark.parametrize("field_name", ["legal_name", "email", "phone"])
+def test_private_text_values_refuse_native_json(field_name):
+    value = getattr(identity(), field_name)
+    with pytest.raises(TypeError) as caught:
+        json.dumps(value)
+    assert_no_canary(str(caught.value))
+    assert_no_canary(repr(caught.value))
```

These are three added cases; no existing case, assertion, expected value or refusal is removed. They should fail against the current str-subtype implementation. Implementation would follow only after their red run and approval of this proposal. Existing equality assertions can remain; actual private payload export must use the explicit authorized encoder, with T5 persistence mapping still deferred.

## Alternative: explicitly limit the ban to whole records

Keep native str-compatible private fields and current tests, and explicitly approve that generic record export is refused while code already holding a private scalar can serialize it. Revise the condition and docs accordingly. This is a narrowing of the latest requirement and must not be assumed.

## Stop boundary

No further implementation, mutation rewrites, test edits, PR publication or local-model work until the user resolves this contract/test decision. The full mutation runner has been prepared but not executed; it must run after the boundary is settled. No mutation results are claimed. Five requested implementation cycles exist as separate commits; completion/velocity and PR remain pending.
