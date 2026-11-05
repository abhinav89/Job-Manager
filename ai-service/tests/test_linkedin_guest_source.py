"""Exercise the opt-in collector through HTTP fixtures, without site requests."""
import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from cv_tailor.services import job_scraper_service
from cv_tailor.services.job_sources import linkedin_guest as source
from cv_tailor.services.job_sources.common import USER_AGENT


def card(identifier):
    return f'''<div class="base-search-card">
        <a class="base-card__full-link" href="https://ph.linkedin.com/jobs/view/developer-{identifier}"></a>
        <h3>Python Automation Developer</h3><h4>Example Company</h4>
        <span class="job-search-card__location">Manila, Philippines</span>
        <time datetime="2026-11-05"></time></div>'''


DETAIL = '''<div class="show-more-less-html__markup">Build Python automation.</div>
    <li class="description__job-criteria-item"><h3>Employment type</h3>
    <span class="description__job-criteria-text">Contract</span></li>'''
EMPTY = "<!DOCTYPE html>\n\n<!---->"


def mock_client(monkeypatch, handler):
    original = httpx.AsyncClient
    monkeypatch.setattr(source.httpx, "AsyncClient", lambda **kwargs:
        original(transport=httpx.MockTransport(handler), **kwargs))
    sleep = AsyncMock()
    monkeypatch.setattr(source.asyncio, "sleep", sleep)
    return sleep


def test_registry_collects_complete_jobs_with_no_account_session(monkeypatch):
    requests = []
    def handler(request):
        requests.append(request)
        assert request.headers["user-agent"] == USER_AGENT
        assert "authorization" not in request.headers
        assert "cookie" not in request.headers
        if request.url.path.endswith("/search"):
            assert request.url.params["keywords"] == "Python & JavaScript"
            assert request.url.params["location"] == "Philippines"
            assert "f_WT" not in request.url.params
            return httpx.Response(200, text=card(1) + card(2) + card(3),
                                  headers={"set-cookie": "anonymous=example; Path=/"})
        assert request.url.path.startswith("/jobs-guest/jobs/api/jobPosting/")
        return httpx.Response(200, text=DETAIL)
    sleep = mock_client(monkeypatch, handler)
    jobs, statuses = asyncio.run(job_scraper_service.fetch_remote_jobs(
        "Python & JavaScript", sources=["linkedin-guest"], limit=2))
    assert statuses == {"LinkedIn PH (Guest)": "ok"}
    assert len(jobs) == 2
    assert len(requests) == 3
    assert jobs[0]["job_description"] == "Build Python automation."
    assert jobs[0]["job_url"] == "https://www.linkedin.com/jobs/view/1/"
    assert jobs[0]["job_type"] == "Contract"
    assert jobs[0]["posted_at"] == "2026-11-05"
    assert jobs[0]["salary_range"] is None
    assert sleep.await_count == 2
    assert all(0 < call.args[0] <= 3 for call in sleep.await_args_list)


def test_experimental_sources_are_excluded_from_defaults(monkeypatch):
    normal = AsyncMock(return_value=([], "no_results"))
    guest = AsyncMock(return_value=([], "ok"))
    jobstreet = AsyncMock(return_value=([], "ok"))
    monkeypatch.setattr(job_scraper_service, "SOURCE_REGISTRY", {
        "normal": ("Normal", normal, "httpx"),
        "linkedin-guest": ("LinkedIn PH (Guest)", guest, "httpx"),
        "jobstreet-json": ("JobStreet PH (JSON)", jobstreet, "httpx"),
    })
    asyncio.run(job_scraper_service.fetch_remote_jobs("python"))
    normal.assert_awaited_once()
    guest.assert_not_awaited()
    jobstreet.assert_not_awaited()


@pytest.mark.parametrize("code,status", [
    (401, "blocked"), (403, "blocked"), (429, "rate_limited"),
    (404, "not_found"), (503, "network_error"), (302, "blocked"),
])
def test_search_failure_is_not_reported_as_zero_results(monkeypatch, code, status):
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(code, headers={"location": "https://example.com/login"})
    mock_client(monkeypatch, handler)
    assert asyncio.run(source.fetch_jobs("python")) == ([], status)
    assert len(requests) == 1


def test_detail_refusal_stops_requests_and_keeps_only_a_preview(monkeypatch):
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, text=card(1) + card(2)) if len(requests) == 1 else httpx.Response(429)
    mock_client(monkeypatch, handler)
    jobs, status = asyncio.run(source.fetch_jobs("python", limit=2))
    assert status == "partial"
    assert len(jobs) == 1
    assert jobs[0]["job_description"] == ""
    assert len(requests) == 2


def test_removed_job_is_skipped_without_losing_the_next_posting(monkeypatch):
    def handler(request):
        if request.url.path.endswith("/search"):
            return httpx.Response(200, text=card(1) + card(2))
        if request.url.path.endswith("/1"):
            return httpx.Response(404)
        return httpx.Response(200, text=DETAIL)
    mock_client(monkeypatch, handler)
    jobs, status = asyncio.run(source.fetch_jobs("python", limit=2))
    assert status == "ok"
    assert [job["source_job_id"] for job in jobs] == ["2"]


def test_pagination_uses_ten_result_offsets_and_deduplicates(monkeypatch):
    offsets = []
    def handler(request):
        if request.url.path.endswith("/search"):
            offset = int(request.url.params["start"])
            offsets.append(offset)
            body = "".join(card(index) for index in range(1, 11)) if offset == 0 else card(1) + card(11)
            return httpx.Response(200, text=body)
        return httpx.Response(200, text=DETAIL)
    mock_client(monkeypatch, handler)
    jobs, status = asyncio.run(source.fetch_jobs("python", limit=11))
    assert status == "ok"
    assert [job["source_job_id"] for job in jobs] == [str(index) for index in range(1, 12)]
    assert offsets == [0, 10]


def test_repeated_page_stops_collection(monkeypatch):
    offsets = []
    def handler(request):
        if request.url.path.endswith("/search"):
            offsets.append(request.url.params["start"])
            return httpx.Response(200, text="".join(card(index) for index in range(1, 11)))
        return httpx.Response(200, text=DETAIL)
    mock_client(monkeypatch, handler)
    jobs, status = asyncio.run(source.fetch_jobs("python", limit=25))
    assert status == "ok"
    assert len(jobs) == 10
    assert offsets == ["0", "10"]


@pytest.mark.parametrize("body,status", [
    (EMPTY, "no_results"), ("", "layout_changed"),
    ("<title>Verify you are human</title>", "blocked"),
])
def test_known_empty_response_is_distinct_from_missing_or_challenge_html(monkeypatch, body, status):
    mock_client(monkeypatch, lambda request: httpx.Response(200, text=body))
    assert asyncio.run(source.fetch_jobs("python")) == ([], status)


def test_connection_failure_is_explicit(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("Offline", request=request)
    mock_client(monkeypatch, handler)
    assert asyncio.run(source.fetch_jobs("python")) == ([], "network_error")


@pytest.mark.parametrize("limit", [0, -1, 51, True, 1.5])
def test_invalid_limits_are_rejected(limit):
    with pytest.raises(ValueError):
        asyncio.run(source.fetch_jobs(limit=limit))


def test_maximum_page_budget_is_enforced(monkeypatch):
    requests = []
    def handler(request):
        requests.append(request)
        if request.url.path.endswith("/search"):
            offset = int(request.url.params["start"])
            return httpx.Response(200, text="".join(card(index) for index in range(offset + 1, offset + 11)))
        return httpx.Response(200, text=DETAIL)
    mock_client(monkeypatch, handler)
    jobs, status = asyncio.run(source.fetch_jobs("python", limit=50))
    assert status == "ok"
    assert len(jobs) == 40
    assert len(requests) == 44
