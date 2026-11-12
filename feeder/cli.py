"""
Job-Manager Standalone Feeder CLI.
Runs independently to pull live openings from Greenhouse, Lever, RSS, or files,
and pushes them into Job-Manager's central repository.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict, List
import requests

from feeder.sources.greenhouse import DEFAULT_GREENHOUSE_COMPANIES, fetch_greenhouse_jobs
from feeder.sources.lever import DEFAULT_LEVER_COMPANIES, fetch_lever_jobs
from feeder.sources.json_feeder import load_jobs_from_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("job-feeder")

DEFAULT_API_URL = "http://localhost:8000/api"


def push_jobs_to_backend(jobs: List[Dict[str, Any]], source_name: str, api_url: str = DEFAULT_API_URL) -> bool:
    """Sends a batch of jobs to Job-Manager's feeder ingestion endpoint."""
    if not jobs:
        logger.info("No jobs to push.")
        return True

    endpoint = f"{api_url.rstrip('/')}/feeder/jobs/ingest"
    payload = {
        "source_name": source_name,
        "jobs": jobs,
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"✅ Successfully ingested {data.get('ingested_count', 0)} jobs from {source_name} into Job-Manager.")
            return True
        else:
            logger.error(f"❌ Backend returned error {resp.status_code}: {resp.text}")
            return False
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ Job-Manager backend is not running on :8000. Writing directly to local service.")
        try:
            # Fallback to direct import when backend isn't up
            from cv_tailor.services.job_repository_service import job_repo_service
            for j in jobs:
                job_repo_service.add_job(j)
            logger.info(f"✅ Stored {len(jobs)} jobs directly into local repository service.")
            return True
        except Exception as e:
            logger.error(f"Failed local store: {e}")
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

    args = parser.parse_args()

    if not args.command or args.command == "run-all":
        logger.info("🚀 Starting comprehensive Job Feeder run across all configured sources...")
        total_ingested = 0

        # 1. Greenhouse
        for comp in DEFAULT_GREENHOUSE_COMPANIES:
            logger.info(f"Checking Greenhouse board for {comp['name']}...")
            jobs = fetch_greenhouse_jobs(comp["name"], comp["token"], limit=8)
            if jobs:
                push_jobs_to_backend(jobs, f"Greenhouse-{comp['name']}", getattr(args, "api_url", DEFAULT_API_URL))
                total_ingested += len(jobs)

        # 2. Lever
        for comp in DEFAULT_LEVER_COMPANIES:
            logger.info(f"Checking Lever board for {comp['name']}...")
            jobs = fetch_lever_jobs(comp["name"], comp["token"], limit=8)
            if jobs:
                push_jobs_to_backend(jobs, f"Lever-{comp['name']}", getattr(args, "api_url", DEFAULT_API_URL))
                total_ingested += len(jobs)

        logger.info(f"🎉 Feeder run complete! Total jobs collected & processed: {total_ingested}")
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
