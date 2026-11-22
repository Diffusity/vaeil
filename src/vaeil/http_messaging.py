"""Explicit authorized Message payloads; no generic body-bearing record export."""
from fastapi import Body, Depends, Response
from vaeil.domain import messaging as m
from vaeil.domain.conversation import ConversationNotFoundError


def sender_payload(view):
    return dict(message_id=view.message_id, conversation_id=view.conversation_id,
        outcome=view.outcome.value, reason=None if view.reason is None else view.reason.value,
        review_state=view.review_state.value, identifier_reasons=[reason.value for reason in view.identifier_reasons],
        provenance=view.provenance.value, retry_allowed=view.retry_allowed, can_submit_for_review=view.can_submit_for_review,
        created_at=view.created_at.isoformat(), delivered_at=None if view.delivered_at is None else view.delivered_at.isoformat())


def attach_message_routes(app, provider, *, actor, check_origin, exact, safe_response):
    errors = {m.MessageValidationError: (400, 'invalid_message'), m.MessageConflictError: (409, 'message_conflict'),
        m.MessageActorError: (404, 'not_found'), m.MessageNotFoundError: (404, 'not_found'),
        ConversationNotFoundError: (404, 'not_found'), m.MessageBlockedError: (409, 'conversation_closed')}
    for kind, (status, reason) in errors.items():
        async def handle(request, error, _status=status, _reason=reason):
            return safe_response({'reason': _reason}, _status)
        app.add_exception_handler(kind, handle)

    @app.post('/api/conversations/{conversation_id}/messages', dependencies=[Depends(check_origin)])
    def send(conversation_id: str, body: dict = Body(...), principal=Depends(actor), messages=Depends(provider)):
        exact(body, {'request_id', 'text'})
        view = messages.send_message(actor=principal, conversation_id=conversation_id,
                                     request_id=body['request_id'], text=body['text'])
        return safe_response(sender_payload(view), 202)

    @app.get('/api/conversations/{conversation_id}/messages')
    def read(conversation_id: str, principal=Depends(actor), messages=Depends(provider)):
        view = messages.read_conversation(actor=principal, conversation_id=conversation_id)
        return safe_response(dict(conversation_id=view.conversation_id,
            delivered=[dict(message_id=item.message_id, sender_id=item.sender_id, text=item.text,
                            delivered_at=item.delivered_at.isoformat()) for item in view.delivered],
            attempts=[sender_payload(item) for item in view.attempts]))

    @app.post('/api/messages/{message_id}/review', dependencies=[Depends(check_origin)])
    def review(message_id: str, body: dict = Body(default={}), principal=Depends(actor), messages=Depends(provider)):
        exact(body, set())
        return safe_response(sender_payload(messages.submit_for_review(actor=principal, message_id=message_id)), 202)

    @app.get('/api/admin/messages')
    def queue(principal=Depends(actor), messages=Depends(provider)):
        views = messages.list_review_messages(actor=principal)
        return safe_response({'messages': [dict(message_id=item.message_id, conversation_id=item.conversation_id,
            sender_id=item.sender_id, text=item.text, outcome=item.outcome.value, review_state=item.review_state.value,
            identifier_reasons=[reason.value for reason in item.identifier_reasons]) for item in views]})

    @app.post('/api/admin/messages/{message_id}/decision', dependencies=[Depends(check_origin)])
    def decide(message_id: str, body: dict = Body(...), principal=Depends(actor), messages=Depends(provider)):
        exact(body, {'decision'})
        try:
            decision = m.MessageReviewDecision(body['decision'])
        except (TypeError, ValueError):
            raise m.MessageShapeError('Use a human Message review decision.') from None
        messages.decide_message(actor=principal, message_id=message_id, decision=decision)
        return Response(status_code=204, headers={'Cache-Control': 'no-store'})

    @app.post('/api/admin/messages/{message_id}/escalation-decision', dependencies=[Depends(check_origin)])
    def decide_escalation(message_id: str, body: dict = Body(...), principal=Depends(actor), messages=Depends(provider)):
        exact(body, {'decision'})
        try:
            decision = m.EscalationDecision(body['decision'])
        except (TypeError, ValueError):
            raise m.MessageShapeError('Use an Escalated queue decision.') from None
        messages.decide_escalation(actor=principal, message_id=message_id, decision=decision)
        return Response(status_code=204, headers={'Cache-Control': 'no-store'})
