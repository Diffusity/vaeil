"""Explicit authorized Reveal ceremony/state/partner transport."""
from fastapi import Body, Depends
from vaeil.domain import reveal as r
from vaeil.domain.member import serialize_member_view


def status_payload(view):
    return dict(conversation_id=view.conversation_id, eligible=view.eligible,
                viewer_consented=view.viewer_consented, revealed=view.revealed)


def attach_reveal_routes(app, provider, *, actor, check_origin, exact, safe_response):
    errors = {r.RevealEvidenceError: (400, 'invalid_reveal'), r.RevealActorError: (404, 'not_found'),
              r.RevealBlockedError: (409, 'conversation_closed'), r.RevealNotEligibleError: (409, 'not_eligible'),
              r.RevealCompletedError: (409, 'reveal_completed')}
    for kind, (status, reason) in errors.items():
        async def handle(request, error, _status=status, _reason=reason):
            return safe_response({'reason': _reason}, _status)
        app.add_exception_handler(kind, handle)

    @app.get('/api/conversations/{conversation_id}/reveal')
    def read(conversation_id: str, principal=Depends(actor), reveal=Depends(provider)):
        return safe_response(status_payload(reveal.read_reveal(actor=principal, conversation_id=conversation_id)))

    @app.put('/api/conversations/{conversation_id}/reveal/consent', dependencies=[Depends(check_origin)])
    def consent(conversation_id: str, body: dict = Body(default={}), principal=Depends(actor), reveal=Depends(provider)):
        exact(body, set())
        return safe_response(status_payload(reveal.set_reveal_consent(actor=principal, conversation_id=conversation_id, consent=True)))

    @app.delete('/api/conversations/{conversation_id}/reveal/consent', dependencies=[Depends(check_origin)])
    def withdraw(conversation_id: str, body: dict = Body(default={}), principal=Depends(actor), reveal=Depends(provider)):
        exact(body, set())
        return safe_response(status_payload(reveal.set_reveal_consent(actor=principal, conversation_id=conversation_id, consent=False)))

    @app.get('/api/conversations/{conversation_id}/partner')
    def partner(conversation_id: str, principal=Depends(actor), reveal=Depends(provider)):
        return safe_response(serialize_member_view(reveal.read_partner(actor=principal, conversation_id=conversation_id)))
