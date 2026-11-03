import json
from pathlib import Path
import subprocess
import sys
import unicodedata

import pytest
from pydantic import ValidationError
from pypdf import PdfReader

from cv_tailor.models.schemas import JobApplicationCreate, JobApplicationUpdate, UserProfile
from cv_tailor.services.latex_assembly import assemble_latex
from cv_tailor.services.templates import TEMPLATES, TEMPLATE_CATALOG

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("template_id", TEMPLATES)
def test_template_choice_round_trips_through_workspace(local_workspace, profile_payload, template_id):
    workspace = local_workspace
    profile = workspace.profile_save({**profile_payload, "preferred_template": template_id})
    assert profile["preferred_template"] == template_id
    application = workspace.application_add({"company_name": "Example", "job_title": "Engineer"})
    assert application["template_id"] == template_id
    updated = workspace.application_update(application["id"], {"template_id": template_id}, application["revision"])
    assert updated["template_id"] == template_id


@pytest.mark.parametrize("template_id", TEMPLATES)
def test_gallery_is_a_real_one_page_text_pdf_for_each_template(template_id):
    for app in ("landing", "frontend"):
        folder = ROOT / app / "public" / "resume-templates"
        reader = PdfReader(folder / f"{template_id}.pdf")
        assert len(reader.pages) == 1
        text = "".join(unicodedata.normalize("NFKC", reader.pages[0].extract_text()).split())
        assert all(word in text for word in ("REINAEL", "YABUT", "Parallaxx", "Python", "HolyAngelUniversity"))
        assert (folder / f"{template_id}.png").read_bytes().startswith(b"\x89PNG")
    assert (ROOT / "landing/public/resume-templates" / f"{template_id}.pdf").read_bytes() == (ROOT / "frontend/public/resume-templates" / f"{template_id}.pdf").read_bytes()


@pytest.mark.parametrize("template_id", list(TEMPLATES)[2:])
def test_new_layouts_escape_facts_and_resolve_all_slots(profile_payload, template_id):
    profile = UserProfile.model_validate({**profile_payload, "first_name": "Alex & Co"})
    latex = assemble_latex(profile, {"summary": "Python & SQL: 20%", "skills": {"Languages": "Python & SQL"}}, template_id)
    assert r"ALEX \& CO" in latex
    assert r"Python \& SQL: 20\%" in latex
    assert "<<" not in latex
    assert r"\end{document}" in latex


def test_template_ids_are_validated_and_cli_catalog_matches():
    for model, payload in ((JobApplicationCreate, {"company_name": "Example", "job_title": "Engineer"}), (JobApplicationUpdate, {})):
        with pytest.raises(ValidationError):
            model.model_validate({**payload, "template_id": "not-a-template"})
    result = subprocess.run([sys.executable, "-m", "cv_tailor", "--json", "templates", "list"], cwd=ROOT / "ai-service", capture_output=True, text=True, check=True)
    envelope = json.loads(result.stdout)
    assert envelope == TEMPLATE_CATALOG
