"""
Batch File Feeder for Job-Manager.
Reads external JSON or CSV job listings produced by external scrapers or crawlers.
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def load_jobs_from_file(file_path: str) -> List[Dict[str, Any]]:
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    jobs: List[Dict[str, Any]] = []

    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                jobs = data
            elif isinstance(data, dict) and "jobs" in data:
                jobs = data["jobs"]
    elif path.suffix.lower() in [".csv", ".tsv"]:
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                jobs.append({
                    "company_name": row.get("company_name") or row.get("company") or "Unknown Employer",
                    "job_title": row.get("job_title") or row.get("title") or "Open Role",
                    "job_url": row.get("job_url") or row.get("url") or "",
                    "location": row.get("location") or "Remote / Flexible",
                    "source": row.get("source") or "CSV Import",
                    "work_arrangement": row.get("work_arrangement") or "Hybrid",
                    "salary_range": row.get("salary_range") or "Competitive",
                    "job_description": row.get("job_description") or row.get("description") or "",
                })

    return jobs
