"""Explicit Block and Report transport over the same-origin session seam."""
from fastapi import Body, Depends, Response

from vaeil.domain.conversation import ConversationNotFoundError
from vaeil.domain.safety import ReportConflictError, ReportDecision, ReportNotFoundError, ReportReason


def attach_safety_routes(app, provider, *, actor, check_origin, exact, safe_response):
    errors = {
        ConversationNotFoundError: (404, "not_found"),
        ReportNotFoundError: (404, "not_found"),
        ReportConflictError: (409, "report_conflict"),
    }
    for kind, (status, reason) in errors.items():
        async def handle(request, error, _status=status, _reason=reason):
            return safe_response({"reason": _reason}, _status)
        app.add_exception_handler(kind, handle)

    @app.post("/api/conversations/{conversation_id}/block", dependencies=[Depends(check_origin)])
    def block(conversation_id: str, body: dict = Body(default={}), principal=Depends(actor), safety=Depends(provider)):
        exact(body, set())
        closed = safety.block_conversation(actor=principal, conversation_id=conversation_id)
        return safe_response({"conversation_id": closed.conversation_id, "blocked": closed.blocked})

    @app.post("/api/conversations/{conversation_id}/reports", dependencies=[Depends(check_origin)])
    def submit(conversation_id: str, body: dict = Body(...), principal=Depends(actor), safety=Depends(provider)):
        exact(body, {"reason"})
        try:
            reason = ReportReason(body["reason"])
        except (TypeError, ValueError):
            return safe_response({"reason": "invalid_report"}, 400)
        report = safety.submit_report(actor=principal, conversation_id=conversation_id, reason=reason)
        return safe_response({"report_id": report.report_id}, 201)

    @app.get("/api/admin/reports")
    def queue(principal=Depends(actor), safety=Depends(provider)):
        return safe_response({"reports": [
            dict(report_id=report.report_id, conversation_id=report.conversation_id, reason=report.reason.value,
                 created_at=report.created_at.isoformat(), status="pending")
            for report in safety.pending_reports(actor=principal)
        ]})

    @app.post("/api/admin/reports/{report_id}/decision", dependencies=[Depends(check_origin)])
    def decide(report_id: str, body: dict = Body(...), principal=Depends(actor), safety=Depends(provider)):
        exact(body, {"decision"})
        try:
            decision = ReportDecision(body["decision"])
        except (TypeError, ValueError):
            return safe_response({"reason": "invalid_report"}, 400)
        safety.decide_report(actor=principal, report_id=report_id, decision=decision)
        return Response(status_code=204, headers={"Cache-Control": "no-store"})
