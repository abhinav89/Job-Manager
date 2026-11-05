import asyncio
import json
from unittest.mock import AsyncMock

import httpx
import pytest

from cv_tailor.services.job_sources import common
from cv_tailor.services import job_scraper_service


def test_json_ld_preserves_explicit_salary_and_remote_country_restrictions():
    posting = {"@type": "JobPosting", "title": "Python Engineer", "url": "https://ph.indeed.com/viewjob?jk=example",
        "description": "<p>Build <strong>APIs</strong>.</p>", "jobLocationType": "TELECOMMUTE",
        "applicantLocationRequirements": {"@type": "Country", "name": "Philippines"},
        "baseSalary": {"currency": "PHP", "value": {"minValue": 50000, "unitText": "MONTH"}}}
    html = '<script type="application/ld+json">' + json.dumps({"@graph": [posting]}) + '</script>'
    job = common.parse_json_ld_jobs(html, "Indeed (PH)")[0]
    assert job["location"] == "Remote (Philippines)"
    assert job["salary_range"] == "From PHP 50000 / MONTH"
    assert job["job_description"] == "Build APIs."
    assert job["company_name"] is None
    assert job["job_type"] is None


def test_job_record_requires_a_real_posting_url_and_preserves_unknowns():
    with pytest.raises(ValueError):
        common.job_record(source="Example", job_title="Engineer", job_url="javascript:alert(1)")
    job = common.job_record(source="Example", job_title="Engineer", job_url="https://example.com/job/1")
    assert job["salary_range"] is None
    assert job["location"] is None


@pytest.mark.parametrize("robots,code,expected,redirect", [
    ("User-agent: *\nDisallow: /jobs", 200, "robots_disallowed", False),
    ("User-agent: *\nDisallow:", 403, "blocked", False),
    ("User-agent: *\nDisallow:", 429, "rate_limited", False),
    ("User-agent: *\nDisallow: /private", 302, "robots_disallowed", True),
])
def test_transport_reports_access_failures_and_checks_redirect_destinations(monkeypatch, robots, code, expected, redirect):
    visited = []
    def handle(request):
        visited.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=robots)
        return httpx.Response(code, headers={"location": "/private"} if redirect else {}, text="Blocked")
    original_client = httpx.AsyncClient
    monkeypatch.setattr(common.httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(handle), **kwargs))
    monkeypatch.setattr(common.asyncio, "sleep", AsyncMock())
    monkeypatch.setattr(common, "_robots_cache", {})
    monkeypatch.setattr(common, "_next_request_at", {})
    with pytest.raises(common.JobSourceError) as error:
        asyncio.run(common.fetch_public_html("https://ph.indeed.com/jobs"))
    assert error.value.status == expected
    assert "/private" not in visited
    if expected == "robots_disallowed" and not redirect:
        assert visited == ["/robots.txt"]


def test_aggregator_handles_unknown_employers_and_preserves_distinct_postings(monkeypatch):
    jobs = [common.job_record(source="Example", source_job_id=identity, job_title="Engineer",
                             job_url=f"https://example.com/job/{identity}", job_type="PART_TIME") for identity in ("1", "2")]
    provider = AsyncMock(return_value=([*jobs, jobs[0]], "partial"))
    monkeypatch.setattr(job_scraper_service, "SOURCE_REGISTRY", {"example": ("Example", provider, "httpx")})
    results, statuses = asyncio.run(job_scraper_service.fetch_remote_jobs(sources=["example"], job_types=["part-time"], limit=3))
    assert results == jobs
    assert statuses == {"Example": "partial"}


def test_cli_limit_is_bounded_before_any_network_request():
    from cv_tailor.cli import parser
    assert parser().parse_args(["jobs", "search", "python", "--limit", "1"]).limit == 1
    with pytest.raises(SystemExit):
        parser().parse_args(["jobs", "search", "python", "--limit", "0"])
