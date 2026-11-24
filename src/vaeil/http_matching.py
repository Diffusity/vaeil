"""Explicit same-origin Match payloads and authenticated actions."""
from fastapi import Body, Depends, HTTPException

from vaeil.domain.matching import MatchConflictError, MatchDecision, MatchNotFoundError
from vaeil.domain.member import serialize_member_view


def match_payload(view):
    payload = dict(match_id=view.match_id, state=view.state,
                   decision=None if view.decision is None else view.decision.value,
                   partner=serialize_member_view(view.partner))
    if view.conversation_id is not None:
        payload["conversation_id"] = view.conversation_id
    return payload


def attach_matching_routes(app, provider, *, actor, check_origin, exact, safe_response):
    @app.exception_handler(MatchNotFoundError)
    async def not_found(request, error):
        return safe_response({"reason": "not_found"}, 404)

    @app.exception_handler(MatchConflictError)
    async def conflict(request, error):
        return safe_response({"reason": "match_conflict"}, 409)

    @app.post("/api/admin/matches", dependencies=[Depends(check_origin)])
    def propose(body: dict = Body(default={}), principal=Depends(actor), matching=Depends(provider)):
        exact(body, set())
        return safe_response({"created": matching.propose_matches(actor=principal)})

    @app.get("/api/me/matches")
    def matches(principal=Depends(actor), matching=Depends(provider)):
        return safe_response({"matches": [match_payload(view) for view in matching.read_matches(actor=principal)]})

    @app.post("/api/me/matches/{match_id}/decision", dependencies=[Depends(check_origin)])
    def decide(match_id: str, body: dict = Body(...), principal=Depends(actor), matching=Depends(provider)):
        exact(body, {"decision"})
        try:
            decision = MatchDecision(body["decision"])
        except (TypeError, ValueError):
            raise HTTPException(400, detail="Invalid Match decision.") from None
        return safe_response(match_payload(matching.decide_match(actor=principal, match_id=match_id, decision=decision)))
