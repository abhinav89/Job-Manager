from datetime import date
import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

from cv_tailor.services.application_insights import STATUSES, application_insights


def test_flow_counts_each_current_application_once_and_never_infers_history(local_workspace):
    w = local_workspace
    for status in STATUSES:
        w.application_add({"company_name": status, "job_title": "Engineer", "status": status})
    offer = w.application_add({"company_name": "Another offer", "job_title": "Engineer", "status": "Offer"})
    before = w.applications_list()
    result = application_insights(as_of=date(2026, 11, 3))
    assert result["total"] == 8
    assert sum(link["value"] for link in result["flow"]["links"]) == 8
    assert all(link["source"] == "applications" for link in result["flow"]["links"])
    assert {link["target"]: link["value"] for link in result["flow"]["links"]} == {
        **dict.fromkeys(STATUSES, 1), "Offer": 2}
    assert result["awaiting_response"] == 1
    assert result["interviewing"] == 2
    assert result["offers"] == 2
    assert result["dated_submissions"] == 0
    assert result["submissions_by_month"] == []
    assert w.application_get(offer["id"])["date_applied"] is None
    assert w.applications_list() == before


def test_archives_change_chart_scope_but_not_workspace_inventory(local_workspace):
    w = local_workspace
    w.application_add({"company_name": "Active", "job_title": "Engineer"})
    old = w.application_add({"company_name": "Archived", "job_title": "Engineer", "status": "Rejected"})
    w.application_update(old["id"], {"is_archived": True}, old["revision"])
    visible, all_jobs = application_insights(), application_insights(include_archived=True)
    assert visible["total"] == 1
    assert visible["archived_excluded"] == 1
    assert [job["company_name"] for job in visible["applications"]] == ["Active"]
    assert all_jobs["total"] == 2
    assert all_jobs["archived_excluded"] == 0
    assert visible["workspace"] == all_jobs["workspace"]
    assert visible["workspace"]["applications"] == 2
    assert visible["workspace"]["archived_applications"] == 1


def test_follow_ups_use_requested_date_and_exclude_closed_and_archived_jobs(local_workspace):
    w = local_workspace
    jobs = []
    for company, status, due in [
        ("Today", "Applied", "2026-11-03"), ("Earlier", "Interview", "2026-11-01"),
        ("Future", "Applied", "2026-11-04"), ("Closed", "Rejected", "2026-11-01"),
        ("Ghosted", "Ghosted", "2026-11-01"), ("Archived", "Applied", "2026-11-01"),
    ]:
        jobs.append(w.application_add({"company_name": company, "job_title": "Engineer", "status": status,
                                       "follow_up_date": due, "date_applied": "2026-10-30"}))
    w.application_update(jobs[-1]["id"], {"is_archived": True}, jobs[-1]["revision"])
    result = application_insights(include_archived=True, as_of=date(2026, 11, 3))
    assert [job["company_name"] for job in result["follow_ups_due"]] == ["Earlier", "Today"]
    assert result["submissions_by_month"] == [{"month": "2026-10", "count": 6}]
    assert result["as_of"] == "2026-11-03"


def test_inventory_includes_draft_versions_and_only_confirmed_skills(local_workspace, profile_payload):
    w = local_workspace
    w.profile_save(profile_payload)
    job = w.application_add({"company_name": "Acme", "job_title": "Engineer", "job_source": "Referral"})
    original = w.import_draft("interview_plan", {"content": "Review Python."}, job["id"])
    w.import_draft("interview_plan", {"content": "Review Python and prepare questions."}, job["id"], parent=original["id"])
    result = application_insights()
    assert result["workspace"]["drafts"] == 2
    assert result["workspace"]["drafts_by_type"] == {"interview_plan": 2}
    assert result["workspace"]["conversations"] == 1
    assert result["workspace"]["profile"]["confirmed_skills"] == 1
    assert result["by_source"] == [{"source": "Referral", "count": 1}]


def test_empty_workspace_has_truthful_zero_counts(local_workspace):
    result = application_insights()
    assert result["total"] == result["workspace"]["applications"] == 0
    assert result["flow"]["links"] == []
    assert result["applications"] == []
    assert result["workspace"]["profile"] == {
        "exists": False, "confirmed_skills": 0, "experience": 0, "projects": 0,
        "education": 0, "certifications": 0,
    }


def test_cli_and_http_use_the_same_snapshot(local_workspace, monkeypatch, tmp_path):
    w = local_workspace
    w.application_add({"company_name": "Acme", "job_title": "Engineer", "status": "Interview"})
    expected = application_insights(as_of=date(2026, 11, 3))
    from cv_tailor.main import app
    with TestClient(app) as client:
        response = client.get("/api/tracker/insights?as_of=2026-11-03")
        assert response.status_code == 200
        assert response.json() == expected
        assert client.get("/api/tracker/insights?as_of=invalid").status_code == 422
        assert client.get("/api/tracker").status_code == 200
    result = subprocess.run([sys.executable, "-m", "cv_tailor", "--json", "--data-dir", str(tmp_path),
                             "applications", "insights", "--as-of", "2026-11-03"],
                            capture_output=True, text=True, env={**os.environ, "AI_MODE": "external"})
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == expected
