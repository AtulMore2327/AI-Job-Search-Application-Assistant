from fastapi.testclient import TestClient
from app.main import app
from app.config import reload_settings
from app.database import init_db

client = TestClient(app)


def test_tracker_endpoints_workflow(tmp_path, monkeypatch):
    # Set isolated DB path
    test_db = tmp_path / "routes_tracker_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db}")
    reload_settings()
    init_db()

    # 1. Save application package
    payload = {
        "package": {
            "job_id": "job_tr_10",
            "candidate_name": "Robin Hood",
            "company": "Nottingham Tech",
            "job_title": "Python Architect",
            "cover_letter": {
                "job_id": "job_tr_10",
                "candidate_name": "Robin Hood",
                "company": "Nottingham Tech",
                "job_title": "Python Architect",
                "greeting": "Dear Hiring Manager,",
                "opening": "Opening",
                "body": "Body",
                "closing": "Closing",
                "signature": "Robin Hood",
                "full_text": "Full text"
            },
            "email_draft": {
                "job_id": "job_tr_10",
                "subject": "App",
                "body": "Body",
                "signature": "Sig"
            },
            "linkedin_connection": {"job_id": "job_tr_10", "message": "Hi", "character_count": 2, "purpose": "connection"},
            "linkedin_recruiter": {"job_id": "job_tr_10", "message": "Hi", "character_count": 2, "purpose": "recruiter_outreach"},
            "linkedin_followup": {"job_id": "job_tr_10", "message": "Hi", "character_count": 2, "purpose": "followup"}
        },
        "status": "SAVED",
        "notes": "Saved for later"
    }

    res_save = client.post("/tracker/applications", json=payload)
    assert res_save.status_code == 201
    saved_data = res_save.json()
    app_id = saved_data["application_id"]
    assert app_id == "app_job_tr_10"
    assert saved_data["status"] == "SAVED"

    # 2. List tracked applications
    res_list = client.get("/tracker/applications")
    assert res_list.status_code == 200
    apps_list = res_list.json()
    assert len(apps_list) >= 1
    assert any(a["application_id"] == app_id for a in apps_list)

    # 3. Get application by ID
    res_get = client.get(f"/tracker/applications/{app_id}")
    assert res_get.status_code == 200
    assert res_get.json()["job_title"] == "Python Architect"

    # 4. Update status: SAVED -> APPLIED
    update_payload = {
        "status": "APPLIED",
        "notes": "Submitted application on portal"
    }
    res_update = client.patch(f"/tracker/applications/{app_id}/status", json=update_payload)
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["status"] == "APPLIED"
    assert "Submitted" in updated_data["notes"]

    # 5. Get Tracker Stats
    res_stats = client.get("/tracker/applications/stats")
    assert res_stats.status_code == 200
    stats_data = res_stats.json()
    assert stats_data["total_applications"] >= 1
    assert stats_data["applied_count"] >= 1

    # 6. Delete application
    res_del = client.delete(f"/tracker/applications/{app_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "success"

    # Verify 404 after deletion
    res_get_deleted = client.get(f"/tracker/applications/{app_id}")
    assert res_get_deleted.status_code == 404
