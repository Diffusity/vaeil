"""Same-origin demo application; admission and real-data APIs arrive in T6."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import date

from vaeil.domain import (
    MemberIdentity, Member, Pseudonym, build_values_profile, RelationshipIntent,
    LifeStage, Interest, CoreValue, CommunicationStyle, PaceAndLifestyle,
    ConversationRevealState, project_member_for_viewer, serialize_member_view,
)


def demo_member() -> Member:
    """Only fictional fixtures, including unmistakable private-value canaries."""
    identity = MemberIdentity("demo-subject", "DemoPrivateNameZXQ", "demo-private-zxq@example.invalid",
                              "+919876543210", date(1987, 3, 14))
    profile = build_values_profile(
        owner=identity, relationship_intent=RelationshipIntent.LONG_TERM,
        life_stage=LifeStage.UNDERGRADUATE, interests=[Interest.READING],
        values=[CoreValue.HONESTY], communication_style=CommunicationStyle.DIRECT,
        pace_and_lifestyle=PaceAndLifestyle.QUIET_AND_ROUTINE,
    )
    return Member(identity, Pseudonym("Comet"), profile)


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    member = demo_member()
    context = ConversationRevealState("demo-pair", ("demo-subject", "demo-viewer"), False)

    @app.get("/api/demo/member")
    def anonymous_member():
        view = project_member_for_viewer(member, viewer_id="demo-viewer", conversation=context)
        return JSONResponse(serialize_member_view(view), headers={"Cache-Control": "no-store"})

    return app
