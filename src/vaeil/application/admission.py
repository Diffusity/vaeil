"""Authentication and atomic admission; transport never supplies authority."""
from dataclasses import dataclass, field
from datetime import date, timedelta
import hashlib
from vaeil.domain import Applicant, Invite, MemberIdentity, Verdict, redeem_invite, vet
from vaeil.domain.admission import validate_application_note
from vaeil.domain.authentication import (PrincipalRecord, ApplicationRecord, Role, AdmissionStatus,
                                         AdmissionDecision, AuthenticationError, AccessDeniedError, normalize_login_email)
from vaeil.domain.privacy import PrivateRecord, PrivateText
from vaeil.domain.repository import AuditEvent, AuditKind, StoredSession, MemberNotFoundError
from vaeil.domain.profile import ProfileDraftInput, build_profile_draft, profile_draft_payload, build_values_profile
from vaeil.domain.member import Member, project_own_profile
from vaeil.domain.pseudonym import PseudonymAlreadySetError, validate_pseudonym_candidate

SESSION_LIFETIME = timedelta(hours=24)


@dataclass(frozen=True, slots=True)
class ApplicationSubmission(PrivateRecord):
    __getstate__ = PrivateRecord.__getstate__
    identity: MemberIdentity = field(repr=False)
    invite_code: str = field(repr=False)
    application_note: str = field(repr=False)
    password_hash: PrivateText = field(repr=False)

    def __post_init__(self):
        if not isinstance(self.identity, MemberIdentity) or not isinstance(self.invite_code, str):
            raise TypeError("Use a private identity and Invite.")
        object.__setattr__(self, "application_note", validate_application_note(self.application_note, owner=self.identity))
        object.__setattr__(self, "password_hash", PrivateText(self.password_hash))


@dataclass(frozen=True, slots=True)
class ApplicationReceipt:
    applicant_id: str
    admission: AdmissionStatus


@dataclass(frozen=True, slots=True)
class SessionPrincipal:
    principal_id: str
    role: Role
    admission: AdmissionStatus


class SessionGrant(PrivateRecord):
    __slots__ = ("_token", "principal", "expires_at")

    def __init__(self, token, principal, expires_at):
        self._token, self.principal, self.expires_at = token, principal, expires_at

    @property
    def token(self):
        """Transient response secret for the explicit Set-Cookie transport only."""
        return self._token

    def __repr__(self):
        return "<private session grant>"

    __str__ = __repr__


def token_digest(token: str) -> str:
    if not isinstance(token, str) or not token:
        raise AuthenticationError("Invalid credentials.")
    return hashlib.sha256(token.encode()).hexdigest()


class AdmissionApplication:
    def __init__(self, repository, *, passwords, tokens, clock, model):
        self.repository, self.passwords, self.tokens = repository, passwords, tokens
        self.clock, self.model = clock, model
        # Unknown accounts perform the same verifier work, without disclosing existence.
        self._dummy_hash = passwords.hash_password("unusable dummy credential")

    def _event(self, unit, kind, subject_id, actor_id=None):
        unit.append_audit(AuditEvent(self.tokens.new_id(), self.clock.now(), actor_id, subject_id, kind))

    def apply(self, command: ApplicationSubmission) -> ApplicationReceipt:
        if not isinstance(command, ApplicationSubmission):
            raise TypeError("Use a private application submission.")
        identity = command.identity
        redeem_invite(Invite(command.invite_code, "application"), identity.date_of_birth, self.clock)
        note = validate_application_note(command.application_note, owner=identity)
        verdict = vet(Applicant(identity.date_of_birth, note), self.model)
        approved = verdict is Verdict.APPROVED
        admission = AdmissionStatus.APPROVED if approved else AdmissionStatus.NEEDS_REVIEW
        # Input email is already opaque: only the persistence mapper constructs its lookup key.
        principal = PrincipalRecord(identity, identity.email, command.password_hash,
                                    Role.MEMBER if approved else Role.APPLICANT, admission)
        with self.repository.transaction() as unit:
            unit.consume_invite(command.invite_code, principal_id=identity.member_id)
            unit.add_application(ApplicationRecord(principal, note))
            self._event(unit, AuditKind.INVITE_REDEEMED, identity.member_id)
            self._event(unit, AuditKind.VETTING_APPROVED if approved else AuditKind.VETTING_NEEDS_REVIEW, identity.member_id)
            unit.commit()
        return ApplicationReceipt(identity.member_id, admission)

    def login(self, email: str, password: str) -> SessionGrant:
        key = normalize_login_email(email)
        with self.repository.transaction() as unit:
            principal = unit.get_principal_by_email(key)
            valid = self.passwords.verify_password(password, self._dummy_hash if principal is None else principal.password_hash)
            if not valid or principal is None:
                raise AuthenticationError("Invalid credentials.")
            token = self.tokens.new_token()
            expires = self.clock.now() + SESSION_LIFETIME
            unit.put_session(StoredSession(PrivateText(token_digest(token)), principal.identity.member_id, expires))
            unit.commit()
        return SessionGrant(token, self._principal(principal), expires)

    def session(self, raw_token: str) -> SessionPrincipal:
        with self.repository.transaction() as unit:
            session = unit.get_session(token_digest(raw_token))
            if session is None or session.expires_at <= self.clock.now():
                raise AuthenticationError("Invalid credentials.")
            principal = unit.get_principal(session.principal_id)
            if principal is None:
                raise AuthenticationError("Invalid credentials.")
            return self._principal(principal)

    def logout(self, raw_token: str) -> None:
        self.session(raw_token)
        with self.repository.transaction() as unit:
            unit.delete_session(token_digest(raw_token))
            unit.commit()

    @staticmethod
    def _principal(principal):
        return SessionPrincipal(principal.identity.member_id, principal.role, principal.admission)

    def _require(self, unit, actor, role):
        principal = unit.get_principal(actor.principal_id) if isinstance(actor, SessionPrincipal) else None
        if principal is None or principal.role is not role or principal.admission is not AdmissionStatus.APPROVED:
            raise AccessDeniedError("Access is not permitted.")
        return principal

    def pending_applications(self, *, actor: SessionPrincipal):
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.ADMIN)
            return unit.list_pending_applications()

    def decide_admission(self, *, actor: SessionPrincipal, applicant_id: str, decision: AdmissionDecision):
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.ADMIN)
            unit.set_admission_decision(applicant_id, decision)
            kind = AuditKind.ADMISSION_APPROVED if decision is AdmissionDecision.APPROVE else AuditKind.ADMISSION_REJECTED
            self._event(unit, kind, applicant_id, actor.principal_id)
            unit.commit()

    def seed_admin(self, *, email: str, password: str):
        key = normalize_login_email(email)
        with self.repository.transaction() as unit:
            existing = unit.get_principal("admin")
            if existing is not None:
                if (existing.role is not Role.ADMIN or existing.login_email != PrivateText(key)
                        or not self.passwords.verify_password(password, existing.password_hash)):
                    raise AccessDeniedError("Admin configuration does not match the seeded principal.")
                return
            principal = PrincipalRecord(MemberIdentity("admin", "Admin", email, None, date(2000, 1, 1)),
                                        PrivateText(key), self.passwords.hash_password(password), Role.ADMIN, AdmissionStatus.APPROVED)
            unit.add_principal(principal)
            unit.commit()


    def own_profile(self, *, actor: SessionPrincipal):
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.MEMBER)
            try:
                return project_own_profile(unit.get_member(actor.principal_id))
            except MemberNotFoundError:
                return DraftReceipt(unit.get_onboarding_draft(actor.principal_id))

    def save_own_profile(self, *, actor: SessionPrincipal, draft: ProfileDraftInput):
        with self.repository.transaction() as unit:
            principal = self._require(unit, actor, Role.MEMBER)
            normalized = build_profile_draft(draft, owner=principal.identity)
            try:
                existing = unit.get_member(actor.principal_id)
            except MemberNotFoundError:
                existing = None
            if existing is not None and normalized.pseudonym is not None:
                raise PseudonymAlreadySetError("Pseudonym is fixed once set.")
            previous = unit.get_onboarding_draft(actor.principal_id)
            candidate = normalized.pseudonym or previous.pseudonym
            if existing is None and (not normalized.complete or candidate is None):
                unit.save_onboarding_draft(actor.principal_id, normalized)
                unit.commit()
                return DraftReceipt(normalized)
            data = profile_draft_payload(normalized)
            data.pop("pseudonym")
            profile = build_values_profile(owner=principal.identity, **data)
            if existing is None:
                pseudonym = validate_pseudonym_candidate(actor.principal_id, candidate, identity=principal.identity)
                member = Member(principal.identity, pseudonym, profile)
                unit.add_member(member)
            else:
                member = Member(existing.identity, existing.pseudonym, profile)
                unit.update_values_profile(actor.principal_id, profile)
            unit.commit()
            return project_own_profile(member)


@dataclass(frozen=True, slots=True)
class DraftReceipt:
    values_profile: ProfileDraftInput
    complete: bool = False
