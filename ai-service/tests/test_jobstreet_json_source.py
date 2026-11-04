import asyncio
from unittest.mock import AsyncMock
from urllib.parse import parse_qs

import httpx
import pytest

from cv_tailor.services import job_scraper_service
from cv_tailor.services.job_sources import jobstreet_json as source
from cv_tailor.services.job_sources.common import JobSourceError


def posting(identifier="123", **fields):
    return {"id": identifier, "title": "Python Automation Developer",
        "advertiser": {"description": "Example Company"},
        "locations": [{"label": "Taguig City, Metro Manila", "countryCode": "PH"}],
        "salaryLabel": "₱90,000 – ₱95,000 per month", "workTypes": ["Full time"],
        "teaser": "Build <strong>Python</strong> workflows.", **fields}


def test_maps_ph_records_without_turning_previews_into_full_descriptions():
    record = source.parse_results({"data": [posting()], "totalCount": 1})[0]
    assert record["job_url"] == "https://ph.jobstreet.com/job/123"
    assert record["source_job_id"] == "123"
    assert record["salary_range"] == "₱90,000 – ₱95,000 per month"
    assert record["job_type"] == "Full time"
    assert record["location"] == "Taguig City, Metro Manila"
    assert record["job_description"] == ""
    assert record["short_description"] == "Build Python workflows."


def test_deduplicates_ids_preserves_unknowns_and_excludes_wrong_market():
    payload = {"data": [posting("1", advertiser={}, salaryLabel="", workTypes=[], locations=[]),
                        posting("1"), posting("2", locations=[{"label": "Singapore", "countryCode": "SG"}])],
               "totalCount": 3}
    records = source.parse_results(payload)
    assert len(records) == 1
    assert records[0]["company_name"] is None
    assert records[0]["salary_range"] is None
    assert records[0]["location"] is None
    assert records[0]["job_type"] is None


@pytest.mark.parametrize("payload", [{}, {"data": None}, {"data": [], "totalCount": 10}, {"data": [posting(True)]}])
def test_changed_or_unusable_payload_is_not_a_successful_empty_search(payload):
    with pytest.raises(JobSourceError) as error:
        source.parse_results(payload)
    assert error.value.status == "layout_changed"
    assert source.parse_results({"data": [], "totalCount": 0}) == []


def mock_client(monkeypatch, handler):
    original = httpx.AsyncClient
    monkeypatch.setattr(source.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    monkeypatch.setattr(source.asyncio, "sleep", AsyncMock())


def test_limits_pages_and_does_not_send_account_credentials(monkeypatch):
    requests = []
    def handler(request):
        requests.append(request)
        assert "authorization" not in request.headers
        assert "cookie" not in request.headers
        query = parse_qs(request.url.query.decode())
        assert query["siteKey"] == ["PH-Main"]
        return httpx.Response(200, json={"data": [posting()], "totalCount": 500})
    mock_client(monkeypatch, handler)
    jobs, status = asyncio.run(source.fetch_jobs("python automation", limit=1))
    assert status == "ok"
    assert len(jobs) == len(requests) == 1
    assert parse_qs(requests[0].url.query.decode())["pageSize"] == ["1"]


@pytest.mark.parametrize("code,status", [(403, "blocked"), (429, "rate_limited"), (404, "not_found"), (503, "network_error")])
def test_reports_http_failures_without_fake_empty_results(monkeypatch, code, status):
    mock_client(monkeypatch, lambda request: httpx.Response(code, text="Unavailable"))
    assert asyncio.run(source.fetch_jobs("python")) == ([], status)


def test_preserves_earlier_results_when_a_later_page_fails(monkeypatch):
    def handler(request):
        page = parse_qs(request.url.query.decode())["page"][0]
        if page == "2":
            return httpx.Response(429)
        return httpx.Response(200, json={"data": [posting(str(index)) for index in range(20)], "totalCount": 100})
    mock_client(monkeypatch, handler)
    jobs, status = asyncio.run(source.fetch_jobs("python", limit=25))
    assert len(jobs) == 20
    assert status == "partial"


def test_experimental_source_runs_only_when_explicitly_selected(monkeypatch):
    normal, experimental = AsyncMock(return_value=([], "no_results")), AsyncMock(return_value=([], "ok"))
    monkeypatch.setattr(job_scraper_service, "SOURCE_REGISTRY", {
        "normal": ("Normal", normal, "httpx"),
        "jobstreet-json": ("JobStreet PH (JSON)", experimental, "httpx")})
    asyncio.run(job_scraper_service.fetch_remote_jobs("python"))
    normal.assert_awaited_once()
    experimental.assert_not_awaited()
    asyncio.run(job_scraper_service.fetch_remote_jobs("python", sources=["jobstreet-json"]))
    experimental.assert_awaited_once()
