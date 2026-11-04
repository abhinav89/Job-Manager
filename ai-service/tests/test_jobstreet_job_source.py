"""Representative public JobStreet markup; tests make no network requests."""
import asyncio
import json
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

import pytest

from cv_tailor.services.job_sources import jobstreet
from cv_tailor.services.job_sources.common import JobSourceError


CARD = '''<article data-testid="job-card" data-job-id="12345678">
<a data-automation="jobTitle" href="/job/12345678?tracking=search">Python Automation Engineer</a>
<a data-automation="jobCompany">Example Labs</a>
<span data-automation="jobLocation">Makati City</span>
<span data-automation="jobSalary">₱50,000 – ₱70,000 per month</span>
<p data-automation="jobShortDescription">Build Python workflows.</p>
</article>'''


def test_jobstreet_card_keeps_source_link_salary_and_unknowns():
    jobs = jobstreet.parse_search_results(CARD + CARD)
    assert len(jobs) == 1
    job = jobs[0]
    assert job["job_url"] == "https://ph.jobstreet.com/job/12345678"
    assert job["source_job_id"] == "12345678"
    assert job["company_name"] == "Example Labs"
    assert job["salary_range"] == "₱50,000 – ₱70,000 per month"
    assert job["location"] == "Makati City"
    assert job["job_type"] is None
    assert job["job_description"] == ""
    assert job["short_description"] == "Build Python workflows."


def test_jobstreet_hydration_preserves_unknown_fields():
    data = {"search": {"results": {"jobs": [{"id": "12345679", "title": "Backend Engineer", "advertiser": {"description": "Example Co"}, "teaser": "Write <b>Python workflows.</b>"}]}}}
    html = '<script>window.SEEK_REDUX_DATA = ' + json.dumps(data) + ';</script>'
    job = jobstreet.parse_search_results(html)[0]
    assert job["job_description"] == ""
    assert job["short_description"] == "Write Python workflows."
    assert job["location"] is None
    assert job["salary_range"] is None
    assert job["job_type"] is None


def test_jobstreet_explicit_empty_differs_from_challenge_and_layout_change():
    assert jobstreet.parse_search_results("<h1>No jobs found</h1>") == []
    for html, status in [('<title>Just a moment...</title>', "blocked"), ("<main>New design</main>", "layout_changed"), ("<h1>10 jobs found</h1>", "layout_changed"), ("<h1>100 jobs found</h1>", "layout_changed")]:
        with pytest.raises(JobSourceError) as raised:
            jobstreet.parse_search_results(html)
        assert raised.value.status == status


def test_jobstreet_ignores_external_links_and_rejects_incomplete_cards():
    for html in [CARD.replace('/job/12345678?tracking=search', 'https://evil.example/job/12345678'), '<article data-testid="job-card">Missing title</article>']:
        with pytest.raises(JobSourceError):
            jobstreet.parse_search_results(html)


def test_jobstreet_native_query_and_bounded_collection(monkeypatch):
    url = urlparse(jobstreet.search_url("AI & Python", 2))
    assert url.hostname == "ph.jobstreet.com"
    assert parse_qs(url.query) == {"keywords": ["AI & Python"], "page": ["2"]}
    fetch = AsyncMock(return_value=CARD)
    monkeypatch.setattr(jobstreet, "fetch_public_html", fetch)
    jobs, status = asyncio.run(jobstreet.fetch_jobs("python", limit=1, fetch_details=False))
    assert status == "ok" and len(jobs) == 1
    assert fetch.await_count == 1


def test_jobstreet_reports_transport_block_and_partial_results(monkeypatch):
    fetch = AsyncMock(side_effect=JobSourceError("blocked", "Denied"))
    monkeypatch.setattr(jobstreet, "fetch_public_html", fetch)
    assert asyncio.run(jobstreet.fetch_jobs("python")) == ([], "blocked")
    fetch.side_effect = [CARD, JobSourceError("blocked", "Denied")]
    jobs, status = asyncio.run(jobstreet.fetch_jobs("python", limit=2, fetch_details=False))
    assert len(jobs) == 1 and status == "partial"


def test_jobstreet_detail_extracts_description_without_guessing_type():
    job = jobstreet.parse_search_results(CARD)[0]
    detail = jobstreet.parse_job_details('<div data-automation="jobAdDetails"><p>Maintain Python APIs.</p></div>', job)
    assert detail["job_description"] == "Maintain Python APIs."
    assert detail["job_type"] is None


def test_jobstreet_enriches_only_requested_results(monkeypatch):
    second_card = CARD.replace("12345678", "12345679")
    fetch = AsyncMock(side_effect=[CARD + second_card, '<div data-automation="jobAdDetails">Maintain Python APIs.</div>'])
    monkeypatch.setattr(jobstreet, "fetch_public_html", fetch)
    jobs, status = asyncio.run(jobstreet.fetch_jobs("python", limit=1))
    assert len(jobs) == 1 and status == "ok"
    assert jobs[0]["job_description"] == "Maintain Python APIs."
    assert jobs[0]["salary_range"] == "₱50,000 – ₱70,000 per month"
    assert fetch.await_count == 2
    assert fetch.await_args_list[1].args[0] == "https://ph.jobstreet.com/job/12345678"


@pytest.mark.parametrize("detail", [JobSourceError("blocked", "Denied"), "<main>Changed details</main>"])
def test_jobstreet_detail_failure_retains_preview_and_reports_partial(monkeypatch, detail):
    fetch = AsyncMock(side_effect=[CARD, detail])
    monkeypatch.setattr(jobstreet, "fetch_public_html", fetch)
    jobs, status = asyncio.run(jobstreet.fetch_jobs("python", limit=1))
    assert status == "partial" and len(jobs) == 1
    assert jobs[0]["short_description"] == "Build Python workflows."
    assert jobs[0]["job_description"] == ""


def test_jobstreet_does_not_refetch_complete_json_ld_description(monkeypatch):
    data = {"@context": "https://schema.org", "@type": "JobPosting", "title": "Python Engineer", "url": "https://ph.jobstreet.com/job/12345678", "description": "Build APIs."}
    fetch = AsyncMock(return_value='<script type="application/ld+json">' + json.dumps(data) + '</script>')
    monkeypatch.setattr(jobstreet, "fetch_public_html", fetch)
    jobs, status = asyncio.run(jobstreet.fetch_jobs("python", limit=1))
    assert status == "ok" and jobs[0]["job_description"] == "Build APIs."
    assert fetch.await_count == 1
