"""Read-only application snapshots shared by the CLI and dashboard.

The tracker stores current statuses, not transitions. Each application therefore
contributes to exactly one branch; no intermediate stages are reconstructed.
"""
from collections import Counter
from datetime import date

from sqlalchemy import func, select

from cv_tailor import workspace as w
from cv_tailor.models import database_models as m


STATUSES = ("Saved", "Applied", "Interview", "Tech Test", "Offer", "Rejected", "Ghosted")
CLOSED_STATUSES = {"Rejected", "Ghosted"}


def summarize_applications(applications, as_of=None):
    today = as_of or date.today()
    counts = Counter(job.get("status") or "Unknown" for job in applications)
    by_status = [{"status": status, "count": counts[status]} for status in
                 [*STATUSES, *sorted(set(counts) - set(STATUSES))]]
    sources = Counter((job.get("job_source") or "").strip() or "Unknown" for job in applications)
    submitted = Counter(str(job["date_applied"])[:7] for job in applications if job.get("date_applied"))
    due = [job for job in applications if job.get("follow_up_date")
           and str(job["follow_up_date"]) <= today.isoformat()
           and job.get("status") not in CLOSED_STATUSES
           and not job.get("is_archived")]
    due.sort(key=lambda job: (str(job["follow_up_date"]), job["id"]))
    return {
        "as_of": today.isoformat(),
        "total": len(applications),
        "by_status": by_status,
        "awaiting_response": counts["Applied"],
        "interviewing": counts["Interview"] + counts["Tech Test"],
        "offers": counts["Offer"],
        "dated_submissions": sum(submitted.values()),
        "follow_ups_due": due,
        "by_source": [{"source": source, "count": count}
                      for source, count in sorted(sources.items(), key=lambda item: (-item[1], item[0]))],
        "submissions_by_month": [{"month": month, "count": count} for month, count in sorted(submitted.items())],
        "applications": applications,
        "flow": {
            "kind": "current_status",
            "nodes": [{"id": "applications", "label": "Applications", "count": len(applications)},
                      *[{"id": item["status"], "label": item["status"], "count": item["count"]}
                        for item in by_status if item["count"]]],
            "links": [{"source": "applications", "target": item["status"], "value": item["count"]}
                      for item in by_status if item["count"]],
        },
    }


def application_insights(include_archived=False, as_of=None):
    # Read one snapshot so totals, chart branches and drill-downs agree.
    with w.SessionLocal() as db:
        if db.bind.dialect.name == "sqlite":
            db.connection().exec_driver_sql("BEGIN")
        jobs = list(db.scalars(select(m.JobApplication).where(m.JobApplication.workspace_id == 1)
                               .order_by(m.JobApplication.id.desc())))
        visible = [w.application_dict(job, False) for job in jobs if include_archived or not job.is_archived]
        snapshot = summarize_applications(visible, as_of)
        profile = db.scalar(select(m.Profile).where(m.Profile.workspace_id == 1))
        profile_counts = {"exists": profile is not None}
        for name, model in (("confirmed_skills", m.Skill), ("experience", m.Experience),
                            ("projects", m.Project), ("education", m.Education), ("certifications", m.Certification)):
            query = select(func.count()).select_from(model).where(model.profile_id == profile.id) if profile else None
            if query is not None and model is m.Skill:
                query = query.where(m.Skill.is_confirmed.is_(True))
            profile_counts[name] = db.scalar(query) if query is not None else 0
        draft_counts = dict(db.execute(select(m.AssistantDraft.type, func.count())
                                      .join(m.AssistantConversation)
                                      .where(m.AssistantConversation.workspace_id == 1)
                                      .group_by(m.AssistantDraft.type)).all())
        snapshot.update({
            "include_archived": include_archived,
            "archived_excluded": 0 if include_archived else sum(bool(job.is_archived) for job in jobs),
            "workspace": {
                "applications": len(jobs),
                "archived_applications": sum(bool(job.is_archived) for job in jobs),
                "conversations": db.scalar(select(func.count()).select_from(m.AssistantConversation)
                                           .where(m.AssistantConversation.workspace_id == 1)),
                "drafts": sum(draft_counts.values()),
                "drafts_by_type": draft_counts,
                "profile": profile_counts,
            },
        })
        return snapshot
