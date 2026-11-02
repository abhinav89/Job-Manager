"""Agent-friendly commands; the dashboard is not needed for any command here."""
import argparse
import asyncio
from contextlib import redirect_stdout
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import subprocess
from sqlalchemy.exc import SQLAlchemyError
from pypdf.errors import PyPdfError


def parser():
    p = argparse.ArgumentParser(prog="cv-tailor", description="Your local career workspace. AI agents write; these commands validate and save.")
    p.add_argument("--json", action="store_true", help="Machine-readable output")
    p.add_argument("--data-dir", help="Workspace directory (default ~/.cv-tailor)")
    groups = p.add_subparsers(dest="group", required=True)
    for name in ("init", "status", "doctor"):
        groups.add_parser(name)
    schema = groups.add_parser("schema")
    schema.add_argument("kind")
    groups.add_parser("templates").add_subparsers(dest="action", required=True).add_parser("list")
    profile = groups.add_parser("profile").add_subparsers(dest="action", required=True)
    profile.add_parser("get")
    for action in ("set", "import"):
        command = profile.add_parser(action)
        command.add_argument("--input", required=True, help="JSON file or - for stdin")
        command.add_argument("--revision", type=int)
    extract = profile.add_parser("extract-text")
    extract.add_argument("file")
    apps = groups.add_parser("applications").add_subparsers(dest="action", required=True)
    listing = apps.add_parser("list")
    listing.add_argument("--status")
    listing.add_argument("--company")
    listing.add_argument("--archived", choices=["yes", "no", "all"], default="all")
    apps.add_parser("stats")
    for action in ("get", "update", "archive", "restore", "delete"):
        command = apps.add_parser(action)
        command.add_argument("id", type=int)
        if action != "get":
            command.add_argument("--revision", required=True, type=int)
            command.add_argument("--request-id")
        if action == "update":
            command.add_argument("--input", required=True)
    add = apps.add_parser("add")
    add.add_argument("--input", required=True)
    add.add_argument("--request-id")
    context = groups.add_parser("context").add_subparsers(dest="action", required=True).add_parser("export")
    context.add_argument("--task", default="resume")
    context.add_argument("--application", type=int)
    drafts = groups.add_parser("drafts").add_subparsers(dest="action", required=True)
    listing = drafts.add_parser("list")
    listing.add_argument("--application", type=int)
    drafts.add_parser("get").add_argument("id", type=int)
    for action in ("import", "revise"):
        command = drafts.add_parser(action)
        command.add_argument("--kind", required=True)
        command.add_argument("--input", required=True)
        command.add_argument("--application", type=int)
        command.add_argument("--request-id")
        command.add_argument("--parent", type=int, required=action == "revise")
        command.add_argument("--evidence", help="JSON file of explicit personal facts supplied by the user, scoped to this conversation")
    apply = drafts.add_parser("apply")
    apply.add_argument("id", type=int)
    apply.add_argument("--revision", type=int, required=True, help="Current application revision")
    export = drafts.add_parser("export")
    export.add_argument("id", type=int)
    export.add_argument("--format", choices=["text", "json", "tex", "pdf", "docx"], default="text")
    export.add_argument("--output", required=True)
    resume = groups.add_parser("resume").add_subparsers(dest="action", required=True)
    for action in ("blocks", "patch", "check"):
        command = resume.add_parser(action)
        command.add_argument("id", type=int)
        if action == "patch":
            command.add_argument("--input", required=True)
            command.add_argument("--request-id")
            command.add_argument("--evidence")
    jobs = groups.add_parser("jobs").add_subparsers(dest="action", required=True)
    jobs.add_parser("fetch").add_argument("url")
    search = jobs.add_parser("search")
    search.add_argument("keyword")
    search.add_argument("--sources", help="Comma-separated source names")
    practice = groups.add_parser("practice").add_subparsers(dest="action", required=True)
    problems = practice.add_parser("problems")
    problems.add_argument("--id", type=int)
    run = practice.add_parser("run")
    run.add_argument("--input", required=True, help="Python source file or - for stdin")
    run.add_argument("--stdin", default="")
    save = practice.add_parser("save")
    save.add_argument("--kind", required=True, choices=["interview_feedback", "interview_plan", "code_review", "code_problems", "cheat_sheet"])
    save.add_argument("--input", required=True)
    save.add_argument("--application", type=int)
    save.add_argument("--request-id")
    save.add_argument("--evidence")
    dashboard = groups.add_parser("dashboard")
    dashboard.add_argument("action", nargs="?", choices=["install", "start"], default="start")
    dashboard.add_argument("--port", type=int, default=8000)
    dashboard.add_argument("--no-open", action="store_true")
    return p


def input_text(path):
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8-sig")


def input_json(path):
    return json.loads(input_text(path))


def dispatch(a):
    from cv_tailor.config import data_dir, capabilities
    from cv_tailor import workspace as w
    from cv_tailor.database import init_db
    if a.group == "templates":
        from cv_tailor.services.templates import TEMPLATE_CATALOG
        return TEMPLATE_CATALOG
    if a.group == "schema":
        return w.schema_for(a.kind).model_json_schema()
    if a.group in {"status", "doctor"}:
        from cv_tailor.dashboard import assets_dir
        return {"data_dir": str(data_dir()), "database": str(data_dir()/"cv-tailor.sqlite3"),
                "initialized": (data_dir()/"cv-tailor.sqlite3").exists(), "ai": capabilities(),
                "dashboard_installed": assets_dir().joinpath("index.html").exists() and importlib.util.find_spec("fastapi") is not None,
                "python": sys.version.split()[0], "node": shutil.which("node"),
                "execution": os.getenv("EXECUTION_BACKEND", "local"),
                "pdf": bool((Path(sys.executable).parent / ("tectonic.exe" if os.name == "nt" else "tectonic")).exists() or shutil.which("xelatex") or shutil.which("tectonic"))}
    if a.group == "dashboard":
        from cv_tailor.dashboard import install, start
        return install() if a.action == "install" else start(a.port, not a.no_open)
    init_db()
    if a.group == "init":
        return {"initialized": True, "data_dir": str(data_dir()), "ai": capabilities()}
    if a.group == "profile":
        if a.action == "get":
            return w.profile_get()
        if a.action == "extract-text":
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(a.file).pages)
            if not text.strip():
                raise w.WorkspaceError("No selectable text found. Supply text or use your agent's OCR capability.")
            return {"text": text}
        return w.profile_save(input_json(a.input), a.revision)
    if a.group == "applications":
        if a.action == "list":
            return w.applications_list(a.status, a.company, {"yes": True, "no": False, "all": None}[a.archived])
        if a.action == "stats":
            return w.application_stats()
        if a.action == "get":
            return w.application_get(a.id)
        if a.action == "add":
            return w.application_add(input_json(a.input), a.request_id)
        if a.action == "delete":
            return w.application_delete(a.id, a.revision, a.request_id)
        payload = input_json(a.input) if a.action == "update" else {"is_archived": a.action == "archive"}
        return w.application_update(a.id, payload, a.revision, a.request_id)
    if a.group == "context":
        return w.context_export(a.task, a.application)
    if a.group == "drafts":
        if a.action == "list":
            return w.drafts_list(a.application)
        if a.action == "get":
            return w.draft_get(a.id)
        if a.action in {"import", "revise"}:
            return w.import_draft(a.kind, input_json(a.input), a.application, a.request_id, a.parent, input_json(a.evidence) if a.evidence else None)
        if a.action == "apply":
            return w.apply_draft(a.id, a.revision)
        output = Path(a.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(w.export_draft(a.id, a.format))
        return {"output": str(output)}
    if a.group == "resume":
        if a.action == "blocks":
            return w.resume_blocks(a.id)
        if a.action == "patch":
            return w.resume_patch(a.id, input_json(a.input), a.request_id, input_json(a.evidence) if a.evidence else None)
        from cv_tailor.services.pdf_service import compile_latex_to_pdf, pdf_page_count
        from cv_tailor.services.ats_check import ats_check
        draft = w.draft_get(a.id)
        if draft["type"] != "resume":
            raise w.WorkspaceError("Select a resume draft")
        pdf = compile_latex_to_pdf(draft["content"])
        return {"pages": pdf_page_count(pdf), "one_page": pdf_page_count(pdf) == 1, "ats": ats_check(pdf)}
    if a.group == "jobs":
        if a.action == "fetch":
            from cv_tailor.services.safe_fetch import fetch_job_text
            return {"url": a.url, "text": fetch_job_text(a.url)}
        from cv_tailor.services.job_scraper_service import fetch_remote_jobs
        with redirect_stdout(sys.stderr):
            jobs, sources = asyncio.run(fetch_remote_jobs(query=a.keyword, sources=a.sources.split(",") if a.sources else None, limit=12))
        return {"jobs": jobs, "sources": sources}
    if a.group == "practice":
        if a.action == "save":
            return w.import_draft(a.kind, input_json(a.input), a.application, a.request_id, evidence=input_json(a.evidence) if a.evidence else None)
        if a.action == "problems":
            from cv_tailor.services.problems.code_problems import get_all_problems, get_problem_by_id
            return w.require(get_problem_by_id(a.id), "Problem") if a.id else get_all_problems()
        from cv_tailor.services.code_service import run_python_code
        return run_python_code(input_text(a.input), a.stdin)


def main(argv=None):
    # Agent harnesses pipe stdio; Windows otherwise uses the legacy code page.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    # Global options also work after subcommands, useful for agent invocations.
    argv = list(sys.argv[1:] if argv is None else argv)
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument("--json", action="store_true")
    global_parser.add_argument("--data-dir")
    global_args, rest = global_parser.parse_known_args(argv)
    a = parser().parse_args(rest)
    a.json, a.data_dir = global_args.json, global_args.data_dir
    from cv_tailor.config import configure
    configure(a.data_dir)
    try:
        result = dispatch(a)
        if result is not None:
            print(json.dumps(result, ensure_ascii=False, indent=None if a.json else 2, default=str))
        return 0
    except (ValueError, OSError, RuntimeError, ImportError, SQLAlchemyError, subprocess.SubprocessError, PyPdfError) as exc:
        if isinstance(exc, ImportError):
            message = f"Optional dependency missing: {exc}. Install the corresponding dashboard, ai, or browser extra."
        elif isinstance(exc, SQLAlchemyError):
            message = "Workspace write could not complete. Refresh the record before retrying; reuse the request ID for an identical create/import."
        else:
            message = str(exc)
        error = {"error": {"code": getattr(exc, "code", "operation_failed"), "message": message}}
        print(json.dumps(error, ensure_ascii=False) if a.json else message, file=sys.stdout if a.json else sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
