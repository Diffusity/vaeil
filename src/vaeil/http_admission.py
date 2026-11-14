"""Explicit authenticated HTTP payloads; submitted roles and private error echoes are refused."""
from datetime import date
import os
from fastapi import Body, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from vaeil.application.admission import ApplicationSubmission, DraftReceipt
from vaeil.domain import MemberIdentity, serialize_member_view
from vaeil.domain import InvalidInviteError, InviteAlreadyRedeemedError, UnderageError, FutureDateOfBirthError
from vaeil.domain import InvalidPseudonymError, PseudonymAlreadySetError, PseudonymTakenError
from vaeil.domain.admission import ApplicationNoteError
from vaeil.domain.authentication import AuthenticationError, AccessDeniedError, AdmissionConflictError, AdmissionDecision
from vaeil.domain.profile import InvalidValuesProfileError, ProfileDraftInput, profile_draft_payload
from vaeil.domain.repository import RepositoryError
from vaeil.adapters.authentication import PasswordPolicyError, PasswordBusyError

COOKIE = "vaeil_session"


def attach_admission_routes(app, provider):
    def safe_response(payload, status=200):
        return JSONResponse(payload, status_code=status, headers={"Cache-Control": "no-store"})

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        return safe_response({"reason": "invalid_request"}, 400)

    errors = {
        AuthenticationError: (401, "invalid_credentials"), AccessDeniedError: (403, "access_denied"),
        InvalidInviteError: (400, "invalid_invite"), InviteAlreadyRedeemedError: (409, "invite_used"),
        UnderageError: (400, "age_gate"), FutureDateOfBirthError: (400, "age_gate"),
        ApplicationNoteError: (400, "invalid_note"), InvalidValuesProfileError: (400, "invalid_profile"),
        InvalidPseudonymError: (400, "invalid_pseudonym"), PseudonymAlreadySetError: (409, "pseudonym_fixed"),
        PseudonymTakenError: (409, "pseudonym_taken"), AdmissionConflictError: (409, "admission_conflict"),
        RepositoryError: (503, "unavailable"), PasswordBusyError: (503, "busy"), PasswordPolicyError: (400, "password_policy"),
    }
    for error_type, (status, reason) in errors.items():
        async def handle(request, error, _status=status, _reason=reason):
            return safe_response({"reason": _reason}, _status)
        app.add_exception_handler(error_type, handle)

    def check_origin(request: Request):
        expected = str(request.base_url).rstrip("/")
        if request.headers.get("origin") != expected or request.headers.get("sec-fetch-site") == "cross-site":
            raise AccessDeniedError("Access is not permitted.")

    def actor(request: Request, application=Depends(provider)):
        return application.session(request.cookies.get(COOKIE, ""))

    def exact(body, required, optional=()):
        if set(body) - set(required) - set(optional) or set(required) - set(body):
            raise HTTPException(400, detail="Invalid request.")

    def principal_payload(principal):
        return dict(principal_id=principal.principal_id, role=principal.role.value, admission=principal.admission.value)

    def own_payload(view):
        if isinstance(view, DraftReceipt):
            return dict(complete=False, values_profile=profile_draft_payload(view.values_profile))
        return serialize_member_view(view)

    @app.post("/api/applications", dependencies=[Depends(check_origin)])
    def apply(body: dict = Body(...), application=Depends(provider)):
        exact(body, {"legal_name", "email", "date_of_birth", "invite_code", "password", "application_note"}, {"phone"})
        try:
            identity = MemberIdentity(application.tokens.new_id(), body["legal_name"], body["email"],
                                      body.get("phone"), date.fromisoformat(body["date_of_birth"]))
            command = ApplicationSubmission(identity, body["invite_code"], body["application_note"],
                                            application.passwords.hash_password(body["password"]))
        except (ValueError, TypeError):
            raise HTTPException(400, detail="Invalid request.") from None
        receipt = application.apply(command)
        return safe_response(dict(applicant_id=receipt.applicant_id, admission=receipt.admission.value), 202)

    @app.post("/api/sessions", dependencies=[Depends(check_origin)])
    def login(request: Request, body: dict = Body(...), application=Depends(provider)):
        exact(body, {"email", "password"})
        grant = application.login(body["email"], body["password"])
        response = safe_response(principal_payload(grant.principal))
        response.set_cookie(COOKIE, grant.token, max_age=86400, httponly=True, samesite="lax", path="/",
                            secure=request.url.scheme == "https" or os.environ.get("VAEIL_SECURE_COOKIES") == "1")
        return response

    @app.get("/api/session")
    def session(principal=Depends(actor)):
        return safe_response(principal_payload(principal))

    @app.delete("/api/session", dependencies=[Depends(check_origin)])
    def logout(request: Request, application=Depends(provider)):
        application.logout(request.cookies.get(COOKIE, ""))
        response = Response(status_code=204, headers={"Cache-Control": "no-store"})
        response.delete_cookie(COOKIE, path="/", httponly=True, samesite="lax",
                               secure=request.url.scheme == "https" or os.environ.get("VAEIL_SECURE_COOKIES") == "1")
        return response

    @app.get("/api/me/profile")
    def profile(principal=Depends(actor), application=Depends(provider)):
        return safe_response(own_payload(application.own_profile(actor=principal)))

    @app.put("/api/me/profile", dependencies=[Depends(check_origin)])
    def save_profile(body: dict = Body(...), principal=Depends(actor), application=Depends(provider)):
        exact(body, set(), {"pseudonym", "relationship_intent", "life_stage", "interests", "values",
                            "communication_style", "pace_and_lifestyle", "about"})
        try:
            draft = ProfileDraftInput(**body)
        except TypeError:
            raise HTTPException(400, detail="Invalid request.") from None
        return safe_response(own_payload(application.save_own_profile(actor=principal, draft=draft)))

    @app.get("/api/admin/applications")
    def applications(principal=Depends(actor), application=Depends(provider)):
        pending = application.pending_applications(actor=principal)
        return safe_response({"applications": [dict(applicant_id=item.principal.identity.member_id,
                                                     application_note=item.note) for item in pending]})

    @app.post("/api/admin/applications/{applicant_id}/decision", dependencies=[Depends(check_origin)])
    def decide(applicant_id: str, body: dict = Body(...), principal=Depends(actor), application=Depends(provider)):
        exact(body, {"decision"})
        try:
            decision = AdmissionDecision(body["decision"])
        except (ValueError, TypeError):
            raise HTTPException(400, detail="Invalid decision.") from None
        application.decide_admission(actor=principal, applicant_id=applicant_id, decision=decision)
        return Response(status_code=204, headers={"Cache-Control": "no-store"})
