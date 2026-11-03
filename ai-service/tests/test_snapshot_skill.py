import json
import os
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree


SCRIPT = Path(__file__).resolve().parents[2] / ".agents/skills/cv-snapshot/scripts/create_snapshot.py"


def snapshot(directory, *arguments):
    return subprocess.run([sys.executable, str(SCRIPT), "--data-dir", str(directory),
                           "--as-of", "2026-11-03", *arguments],
                          capture_output=True, text=True, encoding="utf-8", env={**os.environ, "AI_MODE": "external"})


def test_snapshot_artifacts_use_selected_database_without_mutating_records(local_workspace, tmp_path):
    w = local_workspace
    w.application_add({"company_name": "Acme", "job_title": "Engineer", "status": "Interview",
                       "job_source": '<script>alert("source")</script>'})
    archived = w.application_add({"company_name": "Earlier", "job_title": "Engineer", "status": "Rejected"})
    w.application_update(archived["id"], {"is_archived": True}, archived["revision"])
    before = w.applications_list()
    result = snapshot(tmp_path)
    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["total"] == manifest["archived_excluded"] == 1
    paths = {name: Path(path) for name, path in manifest["files"].items()}
    assert all(path.is_relative_to(tmp_path / "snapshots") and path.is_file() for path in paths.values())
    data = json.loads(paths["snapshot.json"].read_text(encoding="utf-8"))
    assert [job["company_name"] for job in data["applications"]] == ["Acme"]
    assert sum(link["value"] for link in data["flow"]["links"]) == 1
    ElementTree.parse(paths["application-flow.svg"])
    report = paths["snapshot.html"].read_text(encoding="utf-8")
    assert '<script>' not in report
    assert '&lt;script&gt;' in report
    assert w.applications_list() == before
    included = snapshot(tmp_path, "--include-archived")
    assert included.returncode == 0, included.stderr
    assert json.loads(included.stdout)["total"] == 2
    assert json.loads(included.stdout)["files"] != manifest["files"]


def test_empty_snapshot_requires_no_profile_or_dashboard(local_workspace, tmp_path):
    result = snapshot(tmp_path)
    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["total"] == 0
    root = ElementTree.parse(manifest["files"]["application-flow.svg"]).getroot()
    assert "No applications in this snapshot." in "".join(root.itertext())
    assert json.loads(Path(manifest["files"]["snapshot.json"]).read_text(encoding="utf-8"))["workspace"]["profile"]["exists"] is False


def test_snapshot_preserves_existing_files_and_does_not_initialize_missing_workspace(local_workspace, tmp_path):
    missing = tmp_path / "missing"
    result = snapshot(missing)
    assert result.returncode != 0
    assert "not initialized" in result.stderr
    assert not missing.exists()
    output = tmp_path / "chosen report"
    result = snapshot(tmp_path, "--output-dir", str(output))
    assert result.returncode == 0, result.stderr
    previous = (output / "snapshot.json").read_bytes()
    local_workspace.application_add({"company_name": "New", "job_title": "Engineer"})
    repeated = snapshot(tmp_path, "--output-dir", str(output))
    assert repeated.returncode != 0
    assert "already exist" in repeated.stderr
    assert (output / "snapshot.json").read_bytes() == previous
