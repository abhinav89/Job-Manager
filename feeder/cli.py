"""
Job-Manager Standalone Feeder CLI.
Runs independently to pull live openings from Greenhouse, Lever, RSS, or files,
and pushes them into Job-Manager's central repository.
"""
from __future__ import annotations

import os
import argparse
import json
import logging
import sys
from typing import Any, Dict, List
import requests

from feeder.sources.greenhouse import DEFAULT_GREENHOUSE_COMPANIES, fetch_greenhouse_jobs
from feeder.sources.lever import DEFAULT_LEVER_COMPANIES, fetch_lever_jobs
from feeder.sources.json_feeder import load_jobs_from_file
from feeder.sources.india_jobboard import fetch_india_jobboard_jobs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("job-feeder")

DEFAULT_API_URL = os.getenv("JOB_MANAGER_API_URL", "http://localhost:8005/api")


def push_jobs_to_backend(jobs: List[Dict[str, Any]], source_name: str, api_url: str = DEFAULT_API_URL) -> bool:
    """Sends a batch of jobs to Job-Manager's feeder ingestion endpoint."""
    if not jobs:
        logger.info("No jobs to push.")
        return True

    if len(jobs) > 100:
        logger.info(f"Chunking {len(jobs)} jobs into batches of 100 for reliable ingestion...")
        overall_ok = True
        for idx in range(0, len(jobs), 100):
            chunk = jobs[idx : idx + 100]
            ok = push_jobs_to_backend(chunk, f"{source_name} [chunk {idx // 100 + 1}]", api_url)
            if not ok:
                overall_ok = False
        return overall_ok

    candidate_urls = [api_url]
    if "8000" in api_url:
        candidate_urls.append("http://localhost:8005/api")

    payload = {
        "source_name": source_name,
        "jobs": jobs,
    }

    for url in candidate_urls:
        endpoint = f"{url.rstrip('/')}/feeder/jobs/ingest"
        try:
            resp = requests.post(endpoint, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"✅ Successfully ingested {data.get('ingested_count', 0)} jobs from {source_name} into Job-Manager.")
                return True
            elif resp.status_code == 404 and url != candidate_urls[-1]:
                continue
            else:
                logger.error(f"❌ Backend returned error {resp.status_code}: {resp.text}")
        except requests.exceptions.ConnectionError:
            if url != candidate_urls[-1]:
                continue
            logger.warning("⚠️ Job-Manager backend is not reachable via HTTP. Writing directly to local repository service.")
            try:
                from cv_tailor.services.job_repository_service import job_repo_service
                job_repo_service.bulk_add_jobs(jobs)
                logger.info(f"✅ Stored {len(jobs)} jobs directly into local repository service.")
                return True
            except Exception as e:
                logger.error(f"Failed local store: {e}")
                return False

    return False


def main():
    parser = argparse.ArgumentParser(description="Job-Manager Independent Feeder CLI")
    subparsers = parser.add_subparsers(dest="command", help="Feeder command")

    # Command: greenhouse
    gh_parser = subparsers.add_parser("greenhouse", help="Fetch jobs from Greenhouse ATS boards")
    gh_parser.add_argument("--companies", type=str, default="", help="Comma-separated company tokens (e.g. stripe,figma)")
    gh_parser.add_argument("--limit", type=int, default=10, help="Max jobs per company")
    gh_parser.add_argument("--api-url", type=str, default=DEFAULT_API_URL, help="Job-Manager API URL")

    # Command: lever
    lever_parser = subparsers.add_parser("lever", help="Fetch jobs from Lever boards")
    lever_parser.add_argument("--companies", type=str, default="", help="Comma-separated company tokens")
    lever_parser.add_argument("--limit", type=int, default=10, help="Max jobs per company")
    lever_parser.add_argument("--api-url", type=str, default=DEFAULT_API_URL, help="Job-Manager API URL")

    # Command: import-file
    file_parser = subparsers.add_parser("import-file", help="Import jobs from JSON or CSV file")
    file_parser.add_argument("--path", type=str, required=True, help="Path to JSON or CSV file")
    file_parser.add_argument("--api-url", type=str, default=DEFAULT_API_URL, help="Job-Manager API URL")

    # Command: run-all
    all_parser = subparsers.add_parser("run-all", help="Run all automated feeder sources")
    all_parser.add_argument("--api-url", type=str, default=DEFAULT_API_URL, help="Job-Manager API URL")

    # Command: india-jobboard
    ij_parser = subparsers.add_parser("india-jobboard", help="Fetch all verified jobs from running india-jobboard")
    ij_parser.add_argument("--api-url", type=str, default=DEFAULT_API_URL, help="Job-Manager API URL")
    ij_parser.add_argument("--source-url", type=str, default="http://localhost:8000/api/jobs", help="india-jobboard API URL")
    ij_parser.add_argument("--max-pages", type=int, default=None, help="Max pages to fetch")

    args = parser.parse_args()

    if not args.command or args.command == "run-all":
        logger.info("🚀 Starting comprehensive Job Feeder run across all configured sources...")
        total_ingested = 0

        # 1. India Job Board (highest volume, curated Indian opportunities)
        logger.info("Connecting to India Job Board on port 8000...")
        india_jobs = fetch_india_jobboard_jobs()
        if india_jobs:
            push_jobs_to_backend(india_jobs, "India Job Board", getattr(args, "api_url", DEFAULT_API_URL))
            total_ingested += len(india_jobs)

        # 2. Greenhouse
        for comp in DEFAULT_GREENHOUSE_COMPANIES:
            logger.info(f"Checking Greenhouse board for {comp['name']}...")
            jobs = fetch_greenhouse_jobs(comp["name"], comp["token"], limit=8)
            if jobs:
                push_jobs_to_backend(jobs, f"Greenhouse-{comp['name']}", getattr(args, "api_url", DEFAULT_API_URL))
                total_ingested += len(jobs)

        # 3. Lever
        for comp in DEFAULT_LEVER_COMPANIES:
            logger.info(f"Checking Lever board for {comp['name']}...")
            jobs = fetch_lever_jobs(comp["name"], comp["token"], limit=8)
            if jobs:
                push_jobs_to_backend(jobs, f"Lever-{comp['name']}", getattr(args, "api_url", DEFAULT_API_URL))
                total_ingested += len(jobs)

        logger.info(f"🎉 Feeder run complete! Total jobs collected & processed: {total_ingested}")
        return

    if args.command == "india-jobboard":
        logger.info(f"Pulling all jobs from India Job Board ({args.source_url})...")
        jobs = fetch_india_jobboard_jobs(base_url=args.source_url, max_pages=args.max_pages)
        if jobs:
            push_jobs_to_backend(jobs, "India Job Board", args.api_url)
            logger.info(f"🎉 Ingestion finished: {len(jobs)} jobs processed from India Job Board.")
        return

    if args.command == "greenhouse":
        companies = DEFAULT_GREENHOUSE_COMPANIES
        if args.companies:
            companies = [{"name": c.strip().capitalize(), "token": c.strip().lower()} for c in args.companies.split(",")]
        for comp in companies:
            logger.info(f"Pulling jobs from Greenhouse for {comp['name']}...")
            jobs = fetch_greenhouse_jobs(comp["name"], comp["token"], limit=args.limit)
            push_jobs_to_backend(jobs, f"Greenhouse-{comp['name']}", args.api_url)

    elif args.command == "lever":
        companies = DEFAULT_LEVER_COMPANIES
        if args.companies:
            companies = [{"name": c.strip().capitalize(), "token": c.strip().lower()} for c in args.companies.split(",")]
        for comp in companies:
            logger.info(f"Pulling jobs from Lever for {comp['name']}...")
            jobs = fetch_lever_jobs(comp["name"], comp["token"], limit=args.limit)
            push_jobs_to_backend(jobs, f"Lever-{comp['name']}", args.api_url)

    elif args.command == "import-file":
        logger.info(f"Importing jobs from {args.path}...")
        jobs = load_jobs_from_file(args.path)
        push_jobs_to_backend(jobs, "File Import", args.api_url)


if __name__ == "__main__":
    main()
