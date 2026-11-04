import sys
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cv_tailor.routers import scraper_routes
from cv_tailor.services.job_scraper_service import fetch_remote_jobs, fetch_arbeitnow_jobs


class DiscoverJobsTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_scraped_jobs_without_profile_or_ai_enrichment(self):
        jobs = [{
            "company_name": "Example Co",
            "job_title": "Python Developer",
            "job_url": "https://example.com/job",
            "location": "Remote",
            "salary_range": "Competitive",
            "job_description": "Build web services.",
            "short_description": "Build web services.",
            "job_type": "Full-Time",
            "source": "RemoteOK",
        }]
        fetch_jobs = AsyncMock(return_value=(jobs, {"remoteok": "ok"}))
        request = SimpleNamespace(session={"workspace_id": 7})

        with patch.object(scraper_routes, "fetch_remote_jobs", fetch_jobs):
            result = await scraper_routes.discover_jobs(
                keyword="python",
                sources="remoteok",
                job_types="Full-Time",
                request=request,
            )

        fetch_jobs.assert_awaited_once_with(
            query="python",
            sources=["remoteok"],
            job_types=["Full-Time"],
            limit=12,
        )
        self.assertIs(result["jobs"], jobs)
        self.assertEqual(result["total"], 1)
        self.assertNotIn("profile_defaults", result)
        self.assertNotIn("match_score", result["jobs"][0])
        self.assertNotIn("match_analysis", result["jobs"][0])

    async def test_an_empty_source_selection_searches_no_websites(self):
        fetch_jobs = AsyncMock(return_value=([], {}))
        request = SimpleNamespace(session={"workspace_id": 7})

        with patch.object(scraper_routes, "fetch_remote_jobs", fetch_jobs):
            await scraper_routes.discover_jobs(sources="", request=request)

        self.assertEqual(fetch_jobs.await_args.kwargs["sources"], [])

        jobs, source_status = await fetch_remote_jobs(sources=[])
        self.assertEqual(jobs, [])
        self.assertEqual(source_status, {})

    async def test_arbeitnow_returns_only_real_remote_matching_listings(self):
        response = {"data": [
            {"title": "Python Engineer", "company_name": "Example", "url": "https://example.com/jobs/1", "remote": True,
             "description": "<p>Build <strong>APIs</strong> with Python.</p>", "location": "Germany", "job_types": ["Full-Time"]},
            {"title": "Python Engineer", "company_name": "Office", "url": "https://example.com/jobs/2", "remote": False},
            {"title": "Python Engineer", "company_name": "Unknown", "url": "https://example.com/jobs/3"},
            {"title": "Python Engineer", "company_name": "Missing URL", "remote": True},
        ]}
        with patch("cv_tailor.services.job_scraper_service._httpx_get", new=AsyncMock(return_value=json.dumps(response))):
            jobs, status = await fetch_arbeitnow_jobs("python APIs")
        self.assertEqual(status, "ok")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["source"], "Arbeitnow")
        self.assertEqual(jobs[0]["job_description"], "Build APIs with Python.")
        self.assertEqual(jobs[0]["location"], "Germany")
        self.assertEqual(jobs[0]["salary_range"], "Not specified")

    async def test_arbeitnow_reports_feed_errors_without_fake_jobs(self):
        with patch("cv_tailor.services.job_scraper_service._httpx_get", new=AsyncMock(return_value="not-json")):
            jobs, status = await fetch_arbeitnow_jobs("python")
        self.assertEqual(jobs, [])
        self.assertEqual(status, "error")

    async def test_discovery_interleaves_sources_before_applying_result_limit(self):
        def listing(company, job_type="Full-Time"):
            return {"company_name": company, "job_title": "Developer", "job_type": job_type}
        registry = {
            "first": ("First", AsyncMock(return_value=([listing("A"), listing("B"), listing("C")], "ok")), "httpx"),
            "second": ("Second", AsyncMock(return_value=([listing("D"), listing("E")], "ok")), "httpx"),
        }
        with patch("cv_tailor.services.job_scraper_service.SOURCE_REGISTRY", registry):
            jobs, statuses = await fetch_remote_jobs(sources=["first", "second"], limit=3)
        self.assertEqual([job["company_name"] for job in jobs], ["A", "D", "B"])
        self.assertEqual(statuses, {"First": "ok", "Second": "ok"})

    async def test_import_records_listing_source(self):
        db = MagicMock()
        request = SimpleNamespace(session={"workspace_id": 7})
        payload = scraper_routes.ImportJobRequest(company_name="Example", job_title="Developer", source="Arbeitnow")
        await scraper_routes.import_scraped_job(payload, request, db)
        self.assertEqual(db.add.call_args.args[0].job_source, "Arbeitnow")
        self.assertEqual(db.add.call_args.args[0].workspace_id, 1)
        self.assertIsNone(db.add.call_args.args[0].location)
        self.assertIsNone(db.add.call_args.args[0].job_type)


if __name__ == "__main__":
    unittest.main()
