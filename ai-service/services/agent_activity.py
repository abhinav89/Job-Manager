"""Turn real agent tool callbacks into concise, user-visible activity."""
import asyncio
from contextvars import ContextVar

activity_sink = ContextVar("assistant_activity_sink", default=None)

LABELS = {
    "job_search_agent": "Consulting the Job Search Agent",
    "search_jobs": "Searching job sources",
    "get_search_profile": "Reading your confirmed profile",
    "select_search_result": "Opening the selected job",
    "get_application_context": "Reading application context",
    "research_company": "Researching the company",
    "extract_job_url": "Reading the job posting",
    "tailor_resume": "Tailoring your CV",
    "draft_cover_letter": "Drafting your cover letter",
    "prepare_interview": "Preparing for your interview",
    "create_cheat_sheet": "Creating an interview cheat sheet",
    "analyze_job_fit": "Checking job fit",
    "list_resume_blocks": "Reading resume Blocks",
    "check_resume": "Checking your resume",
    "revise_resume_summary": "Revising your summary",
    "revise_resume_bullet": "Revising your selected bullet",
    "list_applications": "Reading your applications",
    "propose_add_application": "Preparing an application proposal",
    "propose_application_change": "Preparing a tracker change",
}


def create_activity_callbacks(ctx):
    def emit(tool, status, details=None):
        if ctx.activity_callback:
            ctx.activity_callback({"tool": tool.name, "label": LABELS.get(tool.name, tool.name.replace("_", " ").capitalize()),
                                   "status": status, **({"details": details} if details else {})})

    async def before(tool, args, tool_context):
        details = {"keyword": str(args["keyword"])[:120]} if tool.name == "search_jobs" and args.get("keyword") else None
        emit(tool, "started", details)
        await asyncio.sleep(0)
        return None

    async def after(tool, args, tool_context, tool_response):
        failed = isinstance(tool_response, dict) and (tool_response.get("error") or tool_response.get("status") == "error")
        details = None
        if tool.name == "search_jobs" and isinstance(tool_response, dict):
            details = {"source_status": tool_response.get("source_status", {}), "results": len(tool_response.get("jobs", []))}
        elif tool.name == "research_company" and isinstance(tool_response, dict):
            details = {"sources": tool_response.get("sources", [])}
        emit(tool, "failed" if failed else "completed", details)
        await asyncio.sleep(0)
        return None

    async def on_error(tool, args, tool_context, error):
        emit(tool, "failed")
        await asyncio.sleep(0)
        return None

    return before, after, on_error
