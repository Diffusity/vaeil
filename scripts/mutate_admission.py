"""T6 fault matrix using the existing exact-restore mutation runner. Run alone."""
from mutate_persistence import ROOT, BOUNDARY, main, replace_once

APP = ROOT / "src/vaeil/application/admission.py"
NOTE = ROOT / "src/vaeil/domain/admission.py"
AUTH = ROOT / "src/vaeil/adapters/authentication.py"
HTTP = ROOT / "src/vaeil/http_admission.py"
SQL = ROOT / "src/vaeil/adapters/persistence.py"
RUNTIME = ROOT / "src/vaeil/runtime.py"
PROFILE = ROOT / "src/vaeil/domain/profile.py"
AUTH_POLICY = ROOT / "src/vaeil/domain/authentication.py"
SELF_NAME = ROOT / "src/vaeil/domain/self_name.py"
VET = ROOT / "src/vaeil/domain/vetting.py"
MEMBER = ROOT / "src/vaeil/domain/member.py"
PRIVACY = ROOT / "src/vaeil/domain/privacy.py"
A = "tests/test_t6_application.py::"
H = "tests/test_t6_http.py::"
N = "tests/test_t6_note.py::"
P = "tests/test_t6_passwords.py::"
F = "tests/test_t6_profiles.py::"

MUTATIONS = []


def add(name, path, old, new, test):
    MUTATIONS.append((name, path, replace_once(old, new), test))


add("drop login NFKC", AUTH_POLICY,
    'unicodedata.normalize("NFKC", email.strip()).casefold()', 'email.strip().casefold()',
    A + "test_login_identity_uses_nfkc_and_casefold_not_lower")
add("replace login casefold with lower", AUTH_POLICY,
    'unicodedata.normalize("NFKC", email.strip()).casefold()', 'unicodedata.normalize("NFKC", email.strip()).lower()',
    A + "test_login_identity_uses_nfkc_and_casefold_not_lower")
add("skip age gate", APP,
    '        redeem_invite(Invite(command.invite_code, "application"), identity.date_of_birth, self.clock)',
    '        pass  # skipped age gate', A + "test_underage_never_calls_model_or_consumes_invite")
add("consume Invite before age validation", APP,
    '        redeem_invite(Invite(command.invite_code, "application"), identity.date_of_birth, self.clock)',
    '        with self.repository.transaction() as early:\n            early.consume_invite(command.invite_code, principal_id=identity.member_id)\n            early.commit()\n        redeem_invite(Invite(command.invite_code, "application"), identity.date_of_birth, self.clock)',
    A + "test_underage_never_calls_model_or_consumes_invite")
add("skip pre-vetting Invite availability", APP,
    '            unit.require_invite(command.invite_code)', '            pass',
    A + "test_unknown_invite_never_reaches_vetting_or_stores_an_applicant")
add("skip atomic Invite consumption", APP,
    '            unit.consume_invite(command.invite_code, principal_id=identity.member_id)', '            pass',
    A + "test_same_invite_concurrent_applications_have_one_atomic_winner")
add("auto-admit clean or injected note", RUNTIME,
    '        return Verdict.NEEDS_REVIEW', '        return Verdict.APPROVED',
    A + "test_runtime_human_review_never_auto_admits_clean_or_injection_note")
add("send Applicant including DOB to model", VET,
    '        verdict = model.vet(note)', '        verdict = model.vet(applicant)',
    N + "test_vetting_port_receives_only_the_application_note")
add("make model rejection representable", VET,
    '    APPROVED = "Approved"', '    REJECT = "Reject"\n    APPROVED = "Approved"',
    "tests/test_vetting.py::test_verdict_cannot_represent_rejection")
add("drop note NFKC normalization", NOTE,
    'unicodedata.normalize("NFKC", raw.strip())', 'raw.strip()',
    N + "test_note_normalization_and_accepted_boundaries")
for value in (19, 21):
    add("note minimum " + str(value), NOTE, 'MIN_APPLICATION_NOTE_CODE_POINTS = 20',
        'MIN_APPLICATION_NOTE_CODE_POINTS = ' + str(value),
        "tests/test_t6_note.py")
for value in (499, 501):
    add("note maximum " + str(value), NOTE, 'MAX_APPLICATION_NOTE_CODE_POINTS = 500',
        'MAX_APPLICATION_NOTE_CODE_POINTS = ' + str(value), "tests/test_t6_note.py")
add("drop note controls", NOTE,
    '    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in text):',
    '    if False:', N + "test_invalid_note_refused_without_echoing_input")
add("drop note identifier check", NOTE,
    '    if scan_identifiers(text).reasons:', '    if False:',
    N + "test_invalid_note_refused_without_echoing_input")
add("drop note self-name check", NOTE,
    '    if contains_self_name(text, identity=owner, mode=SelfNameMode.ABOUT):', '    if False:',
    N + "test_whole_word_note_false_positive_can_be_rephrased")
add("use substring mode for free text", SELF_NAME,
    '    if mode is SelfNameMode.PSEUDONYM:', '    if True:',
    N + "test_note_normalization_and_accepted_boundaries")
add("bypass server role check", APP,
    'principal.role is not role', 'False',
    A + "test_approved_member_cannot_act_as_admin_even_with_forged_role")
add("omit session expiry", APP,
    'session.expires_at <= self.clock.now()', 'False',
    A + "test_session_boundary_logout_and_unknown_token")
add("omit logout revocation", APP,
    '            unit.delete_session(token_digest(raw_token))', '            pass',
    A + "test_session_boundary_logout_and_unknown_token")
add("drop admission audit", APP,
    '            self._event(unit, kind, applicant_id, actor.principal_id)', '            pass',
    A + "test_admin_rejection_is_human_terminal_and_audited")
add("commit Invite before application and audit", APP,
    '            unit.add_application(ApplicationRecord(principal, note))',
    '            unit.commit()\n            unit.add_application(ApplicationRecord(principal, note))',
    A + "test_failed_audit_rolls_back_application_and_invite_consumption")
add("ignore fixed-once Pseudonym", APP,
    '            if existing is not None and normalized.pseudonym is not None:', '            if False:',
    F + "test_private_draft_then_complete_then_profile_update_preserves_identity")
add("drop profile identifier check", PROFILE,
    '    if scan_identifiers(text).is_flagged:', '    if False:',
    F + "test_draft_writes_use_the_same_profile_safety_policies")
add("remove normalized Pseudonym uniqueness", SQL,
    'Column("normalized_pseudonym", String, nullable=False, unique=True)',
    'Column("normalized_pseudonym", String, nullable=False, unique=False)',
    "tests/test_repository_contract.py::test_concurrent_normalized_claims_commit_exactly_one_owner")
add("drop cookie HttpOnly", HTTP,
    'max_age=86400, httponly=True', 'max_age=86400, httponly=False',
    H + "test_registration_login_cookie_restricted_profile_and_logout")
add("drop cookie Secure", HTTP,
    'response.set_cookie(COOKIE, grant.token, max_age=86400, httponly=True, samesite="lax", path="/",\n                            secure=request.url.scheme == "https" or os.environ.get("VAEIL_SECURE_COOKIES") == "1")',
    'response.set_cookie(COOKIE, grant.token, max_age=86400, httponly=True, samesite="lax", path="/", secure=False)',
    H + "test_registration_login_cookie_restricted_profile_and_logout")
add("drop same-origin CSRF check", HTTP,
    'request.headers.get("origin") != expected', 'False',
    H + "test_csrf_cross_origin_and_absent_origin_are_refused")
add("copy raw session token into JSON", HTTP,
    '        response = safe_response(principal_payload(grant.principal))',
    '        response = safe_response(dict(principal_payload(grant.principal), token=grant.token))',
    H + "test_registration_login_cookie_restricted_profile_and_logout")
add("drop password length policy", AUTH,
    'not MIN_PASSWORD_CODE_POINTS <= len(password) <= MAX_PASSWORD_CODE_POINTS:\n        raise PasswordPolicyError',
    'False:\n        raise PasswordPolicyError', P + "test_password_policy_refuses_without_echoing")
add("replace scrypt with fast hash", AUTH,
    '        return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R,\n                              p=SCRYPT_P, dklen=32, maxmem=256 * 1024 * 1024)',
    '        return hashlib.sha256(password.encode()).digest()',
    P + "test_verifier_accepts_a_frozen_independent_scrypt_vector_and_versioned_format")
add("use ordinary secret comparison", AUTH,
    'return hmac.compare_digest(actual, expected)', 'return actual == expected',
    P + "test_verification_respects_the_vetted_constant_time_comparison")
add("increase password memory concurrency cap", AUTH,
    'threading.BoundedSemaphore(1)', 'threading.BoundedSemaphore(2)',
    P + "test_password_workers_refuse_overlap_instead_of_allocating_unbounded_memory")
MUTATIONS.append(("unwrap from unauthorized login helper", AUTH,
                  lambda source: source + '\n\ndef unsafe_login(value):\n    return value.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()\n', BOUNDARY))
add("wrapper repr leaks private values", PRIVACY,
    '    def __repr__(self):\n        return "<private>"', '    def __repr__(self):\n        return repr(self.__value)',
    "tests/test_opaque_private_values.py::test_all_scalar_rendering_is_redacted")


add("hold repository lock during password verification", APP,
    '        valid = self.passwords.verify_password(password, self._dummy_hash if principal is None else principal.password_hash)',
    '            valid = self.passwords.verify_password(password, self._dummy_hash if principal is None else principal.password_hash)',
    A + "test_password_verification_does_not_hold_the_repository_write_lock")
add("map duplicate email to infrastructure failure", SQL,
    'raise ApplicationConflictError("Application conflicts with an existing account.")',
    'raise RepositoryError("Repository operation failed.")',
    H + "test_duplicate_email_conflict_rolls_back_invite_and_allows_retry")
for label, old, new in (
    ("disable remote TLS verification", '"sslmode": "verify-full"', '"sslmode": "disable"'),
    ("remove remote connect bound", '"connect_timeout": 2', '"connect_timeout": 0'),
    ("remove remote statement bound", 'statement_timeout=2000', 'statement_timeout=0'),
    ("remove remote lock bound", 'lock_timeout=2000', 'lock_timeout=0'),
):
    add(label, SQL, old, new,
        "tests/test_t6_repository.py::test_remote_postgres_uses_verified_tls_even_if_url_requests_disable")


add("copy application note into recipient JSON", MEMBER,
    '    return result',
    '    result["application_note"] = "AdmissionNoteCanaryZXR I seek a thoughtful long term relationship."\n    return result',
    F + "test_persisted_application_note_never_enters_recipient_views")


if __name__ == "__main__":
    main(MUTATIONS, "docs/audit/t6-mutations.json")
