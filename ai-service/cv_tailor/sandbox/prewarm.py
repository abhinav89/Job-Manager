"""Fetch TeX resources at image build time, before runtime networking is denied."""
from pathlib import Path
import subprocess
from templates import TEMPLATES

for name, template in TEMPLATES.items():
    fields = {
        "HEADING": r"\begin{center}{\Huge\textbf{Jane \{Doe\}}} \\ \faPhone\ 123 $|$ \href{mailto:jane\_test@example.com}{\faEnvelope\ jane\_test@example.com} $|$ \faLinkedinSquare\ linkedin $|$ \faGithub\ github $|$ \faGlobe\ portfolio\end{center}",
        "SUMMARY": r"Engineer building reliable applications. Literal \{braces\}, \#tags, 50\%, \$ values, snake\_case, \textbackslash{}, \textasciitilde{} and \^{}.",
        "EDUCATION": r"\resumeSubheading{University}{Remote}{Degree}{2026}",
        "EXPERIENCE": r"\resumeSubheading{Company}{Remote}{Engineer}{2026}\resumeItemListStart\resumeItem{Built tools.}\resumeItemListEnd",
        "PROJECTS": r"\resumeProjectHeading{\textbf{Project} $|$ \emph{Python \& SQL}}{2026}\resumeItemListStart\resumeItem{Built tools.}\resumeItemListEnd",
        "SKILLS": r"\textbf{Tools}{: Python}",
        "CERTIFICATIONS": r"\section{Certifications}A certificate",
    }
    for key, value in fields.items():
        template = template.replace("<<" + key + ">>", value)
    source = Path("/tmp") / f"{name}.tex"
    source.write_text(template)
    subprocess.run(["tectonic", "--outdir", "/tmp", str(source)], check=True)
    subprocess.run(["xelatex", "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", source.name], cwd="/tmp", check=True)

source = Path("/tmp/basic.tex")
source.write_text(r"\documentclass{article}\begin{document}Hello world \IfFileExists{missing-file.tex}{found}{unavailable}\end{document}")
subprocess.run(["tectonic", "--outdir", "/tmp", str(source)], check=True)
