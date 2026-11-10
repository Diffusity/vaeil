"""Same-origin demo application; admission and real-data APIs arrive in T6."""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from datetime import date
from pathlib import Path
import os
from vaeil.adapters.readiness import check_database_ready

from vaeil.domain import (
    MemberIdentity, Member, Pseudonym, build_values_profile, RelationshipIntent,
    LifeStage, Interest, CoreValue, CommunicationStyle, PaceAndLifestyle,
    ConversationRevealState, project_member_for_viewer, serialize_member_view,
)

FRONTEND_DIST = Path(os.environ.get(
    "VAEIL_FRONTEND_DIR", str(Path(__file__).resolve().parents[2] / "frontend" / "dist"),
))


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
    def anonymous_member(request: Request):
        if request.query_params:
            raise HTTPException(400, "This fictional demo does not accept parameters.")
        view = project_member_for_viewer(member, viewer_id="demo-viewer", conversation=context)
        return JSONResponse(serialize_member_view(view), headers={"Cache-Control": "no-store"})

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/ready")
    async def ready(available: bool = Depends(check_database_ready)):
        return JSONResponse(
            {"status": "ready" if available else "unavailable"},
            status_code=200 if available else 503, headers={"Cache-Control": "no-store"},
        )

    @app.get("/")
    def index():
        index_file = FRONTEND_DIST / "index.html"
        if not index_file.is_file():
            return PlainTextResponse("Build the demo first: npm.cmd run build --prefix frontend", status_code=503)
        return FileResponse(index_file, headers={"Cache-Control": "no-store"})

    assets = FRONTEND_DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")
    return app
