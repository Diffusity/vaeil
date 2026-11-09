"""The approved public synthetic HTTP seam; no auth or private-data input."""

from fastapi.testclient import TestClient


def test_demo_endpoint_projects_exact_anonymous_payload():
    from vaeil.web import create_app

    with TestClient(create_app()) as client:
        response = client.get("/api/demo/member")
    assert response.status_code == 200
    assert response.json() == {
        "pseudonym": "Comet",
        "values_profile": {
            "relationship_intent": "long_term", "life_stage": "undergraduate",
            "interests": ["reading"], "values": ["honesty"],
            "communication_style": "direct", "pace_and_lifestyle": "quiet_and_routine",
            "about": "",
        },
    }
