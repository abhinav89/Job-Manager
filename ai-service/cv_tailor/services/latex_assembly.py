from cv_tailor.models.schemas import UserProfile
from cv_tailor.services.templates import TEMPLATES

_HEADING_STYLES = {
    "classic": {"name_color": "NavyBlue", "name_vspace": "2pt", "small_prefix": r"\small ", "block_vspace": "-12pt"},
    "modern": {"name_color": "primaryColor", "name_vspace": "4pt", "small_prefix": r"\small\color{textColor} ", "block_vspace": "-10pt"},
}


def _escape_latex(text: str | None) -> str:
    replacements = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "%": r"\%",
                    "&": r"\&", "$": r"\$", "#": r"\#", "_": r"\_",
                    "~": r"\textasciitilde{}", "^": r"\^{}"}
    return "".join(replacements.get(char, char) for char in str(text or ""))


def _link(target: str, display: str, icon: str = "") -> str:
    from urllib.parse import urlsplit, quote
    if urlsplit(target).scheme not in {"http", "https", "mailto"}:
        return _escape_latex(display)
    encoded = quote(target, safe=":/?=&@-_.~+#%")
    encoded = encoded.replace("%", r"\%").replace("#", r"\#")
    return r"\href{" + encoded + "}{" + icon + r"\underline{" + _escape_latex(display) + "}}"


def _build_contact_line(profile: UserProfile) -> tuple[str, str]:
    parts = []
    if profile.mobile_no:
        parts.append(r"\faPhone\ " + _escape_latex(profile.mobile_no))
    if profile.email:
        parts.append(_link("mailto:" + profile.email, profile.email, r"\faEnvelope\ "))
    for value, icon in ((profile.linkedin, r"\faLinkedinSquare\ "), (profile.github, r"\faGithub\ ")):
        if value:
            parts.append(_link(value, value.removeprefix("https://").removeprefix("http://"), icon))
    portfolio = ""
    if profile.portfolio:
        portfolio = r"\\ " + _link(profile.portfolio, profile.portfolio.removeprefix("https://").removeprefix("http://"), r"\faGlobe\ ")
    return " $|$ ".join(parts), portfolio


def _build_heading(profile: UserProfile, template_id: str = "classic") -> str:
    name = _escape_latex(f"{profile.first_name or ''} {profile.last_name or ''}".upper())
    contact_line, portfolio_line = _build_contact_line(profile)
    style = _HEADING_STYLES.get(template_id, _HEADING_STYLES["classic"])
    return (
        r"\begin{center}" + "\n"
        r"    {\Huge \textbf{\textcolor{" + style["name_color"] + r"}{" + name + r"}}} \\ \vspace{" + style["name_vspace"] + r"}" + "\n"
        "    " + style["small_prefix"] + contact_line + portfolio_line + "\n"
        r"    \vspace{" + style["block_vspace"] + r"}" + "\n"
        r"\end{center}"
    )


def _build_education(profile: UserProfile) -> str:
    lines = []
    if not profile.education:
        return r"    \item {No education history provided.}"
    for edu in profile.education:
        desc = edu.description or ""
        lines.append(r"    \resumeSubheading")
        lines.append(f"      {{{_escape_latex(edu.school_name)}}}{{{_escape_latex(edu.location)}}}")
        lines.append(f"      {{{_escape_latex(edu.course + (' --- ' + desc if desc else ''))}}}{{{_escape_latex(edu.date_range)}}}")
    return "\n".join(lines)


def _build_experience(entries: list) -> str:
    lines = []
    if not entries:
        return r"    \item {No experience entries provided.}"
    for exp in entries:
        lines.append(r"    \resumeSubheading")
        lines.append(f"      {{{_escape_latex(exp['company'])}}}{{{_escape_latex(exp['location'])}}}")
        lines.append(f"      {{{_escape_latex(exp['title'])}}}{{{_escape_latex(exp['date'])}}}")
        lines.append(r"      \resumeItemListStart")
        for b in exp.get("bullets", []):
            lines.append(f"        \\resumeItem{{{_escape_latex(b)}}}")
        lines.append(r"      \resumeItemListEnd")
        lines.append("")
    return "\n".join(lines)


def _build_projects(entries: list) -> str:
    lines = []
    if not entries:
        return r"      \item {No projects provided.}"
    for proj in entries:
        lines.append(r"      \resumeProjectHeading")
        lines.append(f"          {{\\textbf{{{_escape_latex(proj['name'])}}} $|$ \\emph{{{_escape_latex(proj['tech'])}}}}}{{\\textbf{{\\small {_escape_latex(proj['date'])}}}}}")
        lines.append(r"          \resumeItemListStart")
        for b in proj.get("bullets", []):
            lines.append(f"            \\resumeItem{{{_escape_latex(b)}}}")
        lines.append(r"          \resumeItemListEnd")
        lines.append(r"          \vspace{-13pt}")
        lines.append("")
    return "\n".join(lines)


def _build_skills(skills_dict: dict) -> str:
    lines = []
    if not skills_dict:
        return r"     \item {No skills provided.}"
    for category, items in skills_dict.items():
        lines.append(f"     \\textbf{{{_escape_latex(category)}}}{{: {_escape_latex(items)}}} \\\\")
    return "\n".join(lines)


def _build_certifications(cert_line: str) -> str:
    if not cert_line or not cert_line.strip():
        return ""
    cert_line = _escape_latex(cert_line).replace(" | ", " $|$ ")
    return r"""\section{Certifications}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     """ + cert_line + r"""
    }}
 \end{itemize}"""


def assemble_latex(profile: UserProfile, ai_content: dict, template_id: str = "classic", section_order: list[str] | None = None) -> str:
    doc = TEMPLATES.get(template_id, TEMPLATES["classic"])

    num_exp = len(ai_content.get("experience", []))
    num_proj = len(ai_content.get("projects", []))
    if (num_exp + num_proj) <= 3:
        doc = doc.replace(r"\vspace{-4pt}", r"\vspace{2pt}")
        doc = doc.replace(r"\vspace{-5pt}", r"\vspace{0pt}")
        doc = doc.replace(r"\vspace{-7pt}", r"\vspace{-3pt}")
        doc = doc.replace(r"\vspace{-2pt}", r"\vspace{1pt}")
        doc = doc.replace(r"\vspace{-16pt}", r"\vspace{-4pt}")
        doc = doc.replace(r"\vspace{-13pt}", r"\vspace{-2pt}")

    heading = _build_heading(profile, template_id)

    doc = doc.replace("<<HEADING>>", heading)
    doc = doc.replace("<<SUMMARY>>", _escape_latex(ai_content.get("summary", "")))
    doc = doc.replace("<<EDUCATION>>", _build_education(profile))
    doc = doc.replace("<<EXPERIENCE>>", _build_experience(ai_content.get("experience", [])))
    doc = doc.replace("<<PROJECTS>>", _build_projects(ai_content.get("projects", [])))
    doc = doc.replace("<<SKILLS>>", _build_skills(ai_content.get("skills", {})))
    doc = doc.replace("<<CERTIFICATIONS>>", _build_certifications(ai_content.get("certifications", "")))
    import re
    matches = list(re.finditer(r"(?m)^\\section\{([^}]+)\}", doc))
    if matches:
        end = doc.index(r"\end{document}")
        sections = {m.group(1): doc[m.start():matches[i+1].start() if i+1 < len(matches) else end]
                    for i, m in enumerate(matches)}
        if not ai_content.get("projects"):
            sections.pop("Projects", None)
        aliases = {"skills": "Technical Skills", "work experience": "Experience", "professional summary": "Summary"}
        order = [aliases.get(name.lower(), name) for name in (section_order or sections)]
        order = list(dict.fromkeys([*order, *sections]))
        doc = doc[:matches[0].start()] + "\n".join(sections[name] for name in order if name in sections) + doc[end:]
    return doc
