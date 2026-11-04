"""Offline examples of supported public Indeed markup; no live-site access."""

import asyncio
import json
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

import pytest

from cv_tailor.services.job_sources import indeed
from cv_tailor.services.job_sources.common import JobSourceError


CARD = """<ul class="jobsearch-ResultsList"><li><div class="job_seen_beacon">
<h2 class="jobTitle"><a class="jcs-JobTitle" data-jk="abc123" href="/rc/clk?jk=abc123&amp;tracking=example"><span>Python Developer</span></a></h2>
<span data-testid="company-name">Example Company</span>
<div class="companyLocation">Makati</div><div class="salary-snippet-container">PHP 50,000 a month</div>
<div class="job-snippet"><ul><li>Build Python integrations.</li></ul></div>
</div></li></ul>"""


def test_html_cards_keep_real_identity_and_do_not_invent_conditions():
    jobs = indeed.parse_search(CARD)
    assert len(jobs) == 1  # Nested card/list selectors do not duplicate the posting.
    job = jobs[0]
    assert job["job_url"] == "https://ph.indeed.com/viewjob?jk=abc123"
    assert job["source_job_id"] == "abc123"
    assert job["job_title"] == "Python Developer"
    assert job["company_name"] == "Example Company"
    assert job["location"] == "Makati"
    assert job["salary_range"] == "PHP 50,000 a month"
    assert job["job_type"] is None
    assert job["job_description"] == ""
    assert job["short_description"] == "Build Python integrations."


def test_embedded_job_cards_leave_unknown_values_empty():
    data = {"mosaicProviderJobCardsModel": {"results": [{"jobkey": "def456", "title": "Automation Engineer", "snippet": "<b>Build</b> integrations."}]}}
    html = '<script>window.mosaic.providerData["mosaic-provider-jobcards"] = ' + json.dumps(data) + ";</script>"
    job = indeed.parse_search(html, "us")[0]
    assert job["job_url"] == "https://www.indeed.com/viewjob?jk=def456"
    assert job["source"] == "Indeed (US)"
    assert job["salary_range"] is None
    assert job["company_name"] is None
    assert job["location"] is None
    assert job["short_description"] == "Build integrations."


def test_explicit_empty_results_are_distinct_from_unrecognized_layout():
    assert indeed.parse_search("<p>Your search did not match any jobs.</p>") == []
    assert indeed.parse_search("<p>0 jobs found</p>") == []
    with pytest.raises(JobSourceError) as error:
        indeed.parse_search("<div>New page layout</div>")
    assert error.value.status == "layout_changed"


def test_positive_result_count_cannot_be_misread_as_zero():
    with pytest.raises(JobSourceError) as error:
        indeed.parse_search("<p>100 jobs found</p>")
    assert error.value.status == "layout_changed"


@pytest.mark.parametrize("href", [
    "https://example.com/viewjob?jk=abc123",
    "//example.com/viewjob?jk=abc123",
    "https://ph.indeed.com@example.com/viewjob?jk=abc123",
    "javascript:alert(1)",
])
def test_foreign_or_invalid_job_links_are_not_relabelled_as_indeed(href):
    assert indeed._identity(href, "abc123", "ph") == ("", None)
    assert indeed._identity(href, None, "ph", allow_key_only=True) == ("", None)


def test_key_without_href_is_only_allowed_for_embedded_job_state():
    assert indeed._identity("", "abc123", "ph") == ("", None)
    assert indeed._identity("", "abc123", "ph", allow_key_only=True) == ("https://ph.indeed.com/viewjob?jk=abc123", "abc123")


def test_access_challenge_is_not_empty_results():
    with pytest.raises(JobSourceError) as error:
        indeed.parse_search("<title>Additional Verification Required</title>")
    assert error.value.status == "blocked"


def test_detail_description_preserves_readable_structure():
    job = indeed.parse_search(CARD)[0]
    result = indeed.parse_detail('<div id="jobDescriptionText"><p>First paragraph.</p><p>Second paragraph.</p></div>', job)
    assert result["job_description"] == "First paragraph.\nSecond paragraph."
    assert result["job_url"] == job["job_url"]


def test_structured_detail_uses_the_requested_posting_not_related_jobs():
    job = indeed.parse_search(CARD)[0]
    postings = [
        {"@type": "JobPosting", "title": "Unrelated Role", "url": "https://ph.indeed.com/viewjob?jk=other", "description": "Wrong description."},
        {"@type": "JobPosting", "title": "Python Developer", "url": "https://ph.indeed.com/viewjob?jk=abc123", "description": "Actual description."},
    ]
    result = indeed.parse_detail('<script type="application/ld+json">' + json.dumps(postings) + '</script>', job)
    assert result["job_description"] == "Actual description."
    assert result["source_job_id"] == "abc123"


def test_search_query_has_trusted_market_and_escaped_parameters():
    url = urlparse(indeed.search_url("Python & JavaScript", "ph", 2))
    assert url.netloc == "ph.indeed.com"
    assert parse_qs(url.query) == {"q": ["Python & JavaScript"], "l": ["Philippines"], "start": ["20"]}
    with pytest.raises(ValueError):
        indeed.search_url("Python", "https://example.com")


def test_fetch_enriches_description_and_stops_at_requested_limit(monkeypatch):
    fetch = AsyncMock(side_effect=[CARD, '<div id="jobDescriptionText">Full role description.</div>'])
    monkeypatch.setattr(indeed, "fetch_public_html", fetch)
    jobs, status = asyncio.run(indeed.fetch_jobs("Python", limit=1))
    assert status == "ok"
    assert len(jobs) == 1
    assert jobs[0]["job_description"] == "Full role description."
    assert fetch.await_count == 2


def test_failed_detail_keeps_listing_and_reports_partial(monkeypatch):
    fetch = AsyncMock(side_effect=[CARD, JobSourceError("blocked", "Access challenge")])
    monkeypatch.setattr(indeed, "fetch_public_html", fetch)
    jobs, status = asyncio.run(indeed.fetch_jobs("Python", limit=1))
    assert status == "partial"
    assert jobs[0]["job_description"] == ""


def test_removed_job_is_excluded_after_a_definitive_not_found(monkeypatch):
    fetch = AsyncMock(side_effect=[CARD, JobSourceError("not_found", "HTTP 410")])
    monkeypatch.setattr(indeed, "fetch_public_html", fetch)
    jobs, status = asyncio.run(indeed.fetch_jobs("Python", limit=1))
    assert jobs == []
    assert status == "no_results"


def test_blocked_search_reports_source_failure(monkeypatch):
    monkeypatch.setattr(indeed, "fetch_public_html", AsyncMock(side_effect=JobSourceError("blocked", "HTTP 403")))
    jobs, status = asyncio.run(indeed.fetch_jobs("Python"))
    assert jobs == []
    assert status == "blocked"
