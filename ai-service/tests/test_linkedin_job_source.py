"""Synthetic public-page fixtures; these tests make no LinkedIn requests."""

import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cv_tailor.services.job_sources import linkedin
from cv_tailor.services.job_sources.common import JobSourceError


SEARCH_HTML = """
<div class="base-card base-search-card job-search-card">
  <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/python-engineer-12345?trackingId=example"></a>
  <h3 class="base-search-card__title">Python Engineer</h3>
  <h4 class="base-search-card__subtitle"><a>Example Company</a></h4>
  <span class="job-search-card__location">Philippines (Remote)</span>
  <time datetime="2026-11-05"></time>
</div>
"""
DETAIL_HTML = """
<h1>Python Engineer</h1>
<div class="show-more-less-html__markup"><p>Build Python services.</p><p>Maintain API integrations.</p></div>
<ul><li class="description__job-criteria-item"><h3 class="description__job-criteria-subheader">Employment type</h3>
<span class="description__job-criteria-text">Contract</span></li></ul>
"""


class LinkedInSourceTests(unittest.TestCase):
    def test_search_encodes_role_and_uses_ten_result_ph_pagination(self):
        parsed = urlsplit(linkedin.search_url("Python & JavaScript", page=2))
        self.assertEqual(parse_qs(parsed.query), {
            "keywords": ["Python & JavaScript"], "location": ["Philippines"],
            "start": ["20"],
        })

    def test_philippine_posting_links_are_canonicalized(self):
        html = SEARCH_HTML.replace("www.linkedin.com", "ph.linkedin.com")
        job = linkedin.parse_search(html)[0]
        self.assertEqual(job["source_job_id"], "12345")
        self.assertEqual(job["job_url"], "https://www.linkedin.com/jobs/view/12345/")

    def test_cards_preserve_unknowns_and_canonical_posting_identity(self):
        jobs = linkedin.parse_search(SEARCH_HTML + SEARCH_HTML)
        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job["job_url"], "https://www.linkedin.com/jobs/view/12345/")
        self.assertEqual(job["source_job_id"], "12345")
        self.assertEqual(job["company_name"], "Example Company")
        self.assertEqual(job["posted_at"], "2026-11-05")
        self.assertIsNone(job["salary_range"])
        self.assertIsNone(job["job_type"])
        self.assertEqual(job["job_description"], "")

    def test_missing_company_or_location_is_not_invented(self):
        html = '<div class="base-search-card"><a href="/jobs/view/42/"></a><h3>Engineer</h3></div>'
        job = linkedin.parse_search(html)[0]
        self.assertIsNone(job["company_name"])
        self.assertIsNone(job["location"])

    def test_rejects_foreign_or_nonposting_links(self):
        for url in (
            "https://example.com/jobs/view/42/",
            "https://www.linkedin.com/company/example/",
            "https://ph.linkedin.com.example.com/jobs/view/42/",
            "https://ph-linkedin.com/jobs/view/42/",
        ):
            html = f'<div class="base-search-card"><a class="base-card__full-link" href="{url}"></a><h3>Engineer</h3></div>'
            with self.assertRaises(JobSourceError) as error:
                linkedin.parse_search(html)
            self.assertEqual(error.exception.status, "layout_changed")

    def test_details_read_description_and_actual_employment_type(self):
        job = linkedin.parse_detail(DETAIL_HTML, linkedin.parse_search(SEARCH_HTML)[0])
        self.assertIn("Build Python services.", job["job_description"])
        self.assertIn("Maintain API integrations.", job["job_description"])
        self.assertEqual(job["job_type"], "Contract")
        self.assertIsNone(job["salary_range"])

    def test_empty_search_is_distinct_from_login_and_changed_layout(self):
        self.assertEqual(linkedin.parse_search("<p>No matching jobs found</p>"), [])
        for html, status in (
            ('<form action="/uas/login"></form>', "blocked"),
            ("<h1>Unexpected layout</h1>", "layout_changed"),
        ):
            with self.assertRaises(JobSourceError) as error:
                linkedin.parse_search(html)
            self.assertEqual(error.exception.status, status)

    def test_nonempty_count_without_recognizable_cards_is_layout_change(self):
        with self.assertRaises(JobSourceError) as error:
            linkedin.parse_search("<p>100 jobs</p>")
        self.assertEqual(error.exception.status, "layout_changed")

    def test_structured_detail_matches_posting_url(self):
        postings = [
            {"@type": "JobPosting", "url": "https://www.linkedin.com/jobs/view/777/", "title": "Other role", "description": "Unrelated description"},
            {"@type": "JobPosting", "url": "https://www.linkedin.com/jobs/view/python-engineer-12345", "title": "Python Engineer", "description": "Build Python tools", "employmentType": "PART_TIME"},
        ]
        html = '<script type="application/ld+json">' + json.dumps(postings) + '</script>'
        job = linkedin.parse_detail(html, linkedin.parse_search(SEARCH_HTML)[0])
        self.assertEqual(job["job_description"], "Build Python tools")
        self.assertEqual(job["job_type"], "PART_TIME")

    def test_robots_denial_is_reported_without_fetching_details(self):
        with patch.object(linkedin, "fetch_public_html", new=AsyncMock(side_effect=JobSourceError("robots_disallowed", "Not allowed"))) as fetch:
            jobs, status = asyncio.run(linkedin.fetch_jobs("Python"))
        self.assertEqual((jobs, status), ([], "robots_disallowed"))
        self.assertEqual(fetch.await_count, 1)

    def test_fetch_enriches_and_honors_result_limit(self):
        second = SEARCH_HTML.replace("12345", "67890").replace("Python Engineer", "API Engineer")
        with patch.object(linkedin, "fetch_public_html", new=AsyncMock(side_effect=[SEARCH_HTML + second, DETAIL_HTML])) as fetch:
            jobs, status = asyncio.run(linkedin.fetch_jobs("Python", limit=1))
        self.assertEqual(status, "ok")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["job_type"], "Contract")
        self.assertEqual(fetch.await_count, 2)

    def test_detail_failure_keeps_preview_and_reports_partial(self):
        with patch.object(linkedin, "fetch_public_html", new=AsyncMock(side_effect=[SEARCH_HTML, JobSourceError("blocked", "Verification required")])):
            jobs, status = asyncio.run(linkedin.fetch_jobs("Python", limit=1))
        self.assertEqual(status, "partial")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["job_description"], "")

    def test_fetch_continues_after_a_full_ten_card_page(self):
        first_page = "".join(SEARCH_HTML.replace("12345", str(1000 + index)) for index in range(10))
        second_page = SEARCH_HTML.replace("12345", "1010")
        responses = [first_page, *([DETAIL_HTML] * 10), second_page, DETAIL_HTML]
        with patch.object(linkedin, "fetch_public_html", new=AsyncMock(side_effect=responses)) as fetch:
            jobs, status = asyncio.run(linkedin.fetch_jobs("Python", limit=11))
        self.assertEqual(status, "ok")
        self.assertEqual(len(jobs), 11)
        self.assertEqual(jobs[-1]["source_job_id"], "1010")
        next_search = fetch.await_args_list[11].args[0]
        self.assertEqual(parse_qs(urlsplit(next_search).query)["start"], ["10"])

    def test_removed_posting_is_not_returned(self):
        with patch.object(linkedin, "fetch_public_html", new=AsyncMock(side_effect=[SEARCH_HTML, JobSourceError("not_found", "Removed")])):
            self.assertEqual(asyncio.run(linkedin.fetch_jobs("Python", limit=1)), ([], "no_results"))


if __name__ == "__main__":
    unittest.main()
