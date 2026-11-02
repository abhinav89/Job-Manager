"""Original one-page layouts sharing the structured resume content contract."""

LAYOUT_STYLES = {
    "minimal": dict(font="helvet", size=10, margin="0.7in", accent="252525", name_size=28, centered=False, rule=False),
    "serif": dict(font="tgpagella", size=11, margin="0.7in", accent="242424", name_size=27, centered=True, rule=True),
    "executive": dict(font="charter", size=11, margin="0.65in", accent="25394A", name_size=32, centered=False, rule=True),
    "technical": dict(font="lmodern", size=10, margin="0.6in", accent="255B65", name_size=25, centered=False, rule=True),
    "compact": dict(font="helvet", size=10, margin="0.48in", accent="303030", name_size=23, centered=False, rule=True),
    "sidebar": dict(font="helvet", size=10, margin="0.55in", accent="285A71", name_size=29, centered=False, rule=False),
}

DEFAULT_SECTION_ORDER = {
    "minimal": ["Summary", "Experience", "Projects", "Technical Skills", "Education", "Certifications"],
    "serif": ["Summary", "Education", "Experience", "Projects", "Technical Skills", "Certifications"],
    "executive": ["Summary", "Experience", "Technical Skills", "Projects", "Education", "Certifications"],
    "technical": ["Summary", "Technical Skills", "Projects", "Experience", "Education", "Certifications"],
    "compact": ["Summary", "Experience", "Projects", "Technical Skills", "Education", "Certifications"],
    "sidebar": ["Technical Skills", "Education", "Certifications", "Summary", "Experience", "Projects"],
}


def _template(template_id, style):
    font = "\\usepackage{" + style["font"] + "}"
    if style["font"] in {"helvet", "lmodern"}:
        font += r"\renewcommand{\familydefault}{\sfdefault}"
    heading_font = r"\ttfamily\bfseries" if template_id == "technical" else r"\bfseries"
    rule = r"[\color{accent}\titlerule]" if style["rule"] else ""
    spacing = "6pt" if template_id == "compact" else "11pt"
    preamble = r"""\documentclass[letterpaper,<<SIZE>>pt]{article}
\usepackage[margin=<<MARGIN>>]{geometry}
\usepackage[T1]{fontenc}
<<FONT>>
\usepackage{titlesec,xcolor,enumitem,tabularx,fontawesome}
\usepackage[hidelinks]{hyperref}
\definecolor{accent}{HTML}{<<ACCENT>>}
\definecolor{sidebarBackground}{HTML}{EDF2F5}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{3pt}
\setlength{\tabcolsep}{0pt}
\setlength{\emergencystretch}{1em}
\urlstyle{same}
\raggedright
\titleformat{\section}{\normalsize<<SECTION_FONT>>\color{accent}}{}{0em}{}<<RULE>>
\titlespacing*{\section}{0pt}{<<SPACING>>}{5pt}
\setlist[itemize]{leftmargin=1.1em,itemsep=2pt,parsep=0pt,topsep=3pt}
\newcommand{\resumeItem}[1]{\item #1}
\newcommand{\resumeSubheading}[4]{\item\begin{tabularx}{\linewidth}{@{}X@{\hspace{0.6em}}r@{}}\textbf{#1}&{\small #2}\\\textit{#3}&{\small #4}\end{tabularx}}
\newcommand{\resumeProjectHeading}[2]{\item\begin{tabularx}{\linewidth}{@{}X@{\hspace{0.6em}}r@{}}#1&#2\end{tabularx}}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0pt,label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}}
\begin{document}
<<HEADING>>
"""
    for key, value in {
        "SIZE": style["size"], "MARGIN": style["margin"], "FONT": font,
        "ACCENT": style["accent"], "SECTION_FONT": heading_font, "RULE": rule, "SPACING": spacing,
    }.items():
        preamble = preamble.replace("<<" + key + ">>", str(value))
    if template_id == "compact":
        preamble = preamble.replace(r"\begin{document}", r"\linespread{0.96}" + "\n" + r"\begin{document}")
    if template_id == "sidebar":
        body = r"""\noindent\colorbox{sidebarBackground}{\begin{minipage}[t]{0.27\textwidth}
\vspace{6pt}\hspace{5pt}\begin{minipage}{\dimexpr\linewidth-10pt\relax}
<<LEFT>>
\end{minipage}\vspace{8pt}
\end{minipage}}\hfill\begin{minipage}[t]{0.65\textwidth}\vspace{0pt}
<<RIGHT>>
\end{minipage}
"""
    else:
        body = "<<BODY>>\n"
    return preamble + body + r"\end{document}" + "\n"


ADDITIONAL_TEMPLATES = {key: _template(key, style) for key, style in LAYOUT_STYLES.items()}
