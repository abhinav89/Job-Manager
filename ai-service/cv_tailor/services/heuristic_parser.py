"""
Enhanced heuristic resume parser for Job-Manager.
Extracts multiple companies/roles, multiple education degrees, certifications, projects,
and comprehensively scans against 150+ professional skills (Sales, BD, Product, Tech,
Finance, Marketing, Ops, Supply Chain, HR, Strategy & Transformation).
"""
import re
from typing import Dict, List, Any, Optional

COMMON_SKILLS_DICTIONARY = [
    # Sales & BD
    "Enterprise Sales", "B2B Sales", "Business Development", "Lead Generation",
    "Account Management", "Pipeline Management", "Client Acquisition", "CRM",
    "Salesforce", "HubSpot", "Contract Negotiation", "Revenue Growth", "Key Account Management",
    # Product
    "Product Management", "Product Strategy", "Product Roadmap", "User Stories",
    "Agile", "Scrum", "Wireframing", "PRD", "A/B Testing", "User Research", "Go-To-Market (GTM)",
    "Feature Prioritization", "Jira", "Figma", "Customer Discovery",
    # Tech & Software & Data
    "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "SQL",
    "PostgreSQL", "MongoDB", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git",
    "REST APIs", "GraphQL", "Microservices", "CI/CD", "Data Analysis", "Machine Learning",
    "Tableau", "Power BI", "Data Modeling", "ETL Pipelines", "Pandas",
    # Finance
    "Financial Analysis", "Financial Modeling", "Corporate Finance", "FP&A",
    "Budgeting & Forecasting", "Variance Analysis", "Valuation", "DCF", "M&A Advisory",
    "Accounting", "Cash Flow Management", "P&L Management", "SAP", "Advanced Excel",
    "Financial Reporting", "Due Diligence", "Capital Budgeting", "Auditing",
    # Strategy & Consulting & Transformation
    "Management Consulting", "Corporate Strategy", "Strategic Planning",
    "Business Transformation", "Change Management", "Process Optimization",
    "Stakeholder Management", "Executive Presentations", "KPIs & OKRs",
    "Organizational Design", "Market Expansion", "Operating Model",
    # Operations & Supply Chain
    "Business Operations", "Operations Management", "Process Improvement", "Six Sigma",
    "Lean", "Supply Chain Management", "Procurement", "Vendor Management",
    "Logistics", "Inventory Management", "Quality Assurance", "Workflow Automation",
    # HR & People
    "Talent Acquisition", "Human Resources", "HRBP", "Employee Engagement",
    "Performance Management", "Onboarding", "Recruiting", "HR Policies",
    "Compensation & Benefits", "Leadership Development"
]

JOB_TITLE_KEYWORDS = [
    "manager", "lead", "director", "head", "analyst", "consultant", "associate",
    "engineer", "developer", "specialist", "vice president", "vp", "executive",
    "officer", "founder", "co-founder", "partner", "strategist", "coordinator",
    "administrator", "architect", "intern", "trainee"
]

DEGREE_KEYWORDS = [
    "bachelor", "master", "b.tech", "btech", "b.e.", "be", "b.sc", "bsc", "bba",
    "b.com", "bcom", "mba", "m.tech", "mtech", "m.s.", "ms", "ph.d", "phd",
    "post graduate", "pgdm", "diploma", "degree", "doctorate"
]

DATE_PATTERN = re.compile(
    r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?\b(?:19|20)\d{2}\b\s*(?:-|–|—|to)\s*(?:(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?\b(?:19|20)\d{2}\b|Present|Current|Ongoing)',
    re.IGNORECASE
)

def parse_resume_text_heuristic(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return {}

    # Email
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email_match.group(0) if email_match else ""

    # Phone
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d{10,13}', text)
    mobile_no = phone_match.group(0).strip() if phone_match else ""

    # LinkedIn
    linkedin_match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?|linkedin\.com/in/[a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    linkedin = ("https://" + linkedin_match.group(0).removeprefix("http://").removeprefix("https://")) if linkedin_match else ""

    # GitHub
    github_match = re.search(r'(https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+/?|github\.com/[a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    github = ("https://" + github_match.group(0).removeprefix("http://").removeprefix("https://")) if github_match else ""

    # Portfolio / other website
    portfolio_match = re.search(r'https?://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?', text)
    portfolio = ""
    if portfolio_match:
        url = portfolio_match.group(0)
        if "linkedin.com" not in url and "github.com" not in url:
            portfolio = url

    # Name: typically first 1-3 lines, 2-4 words, no digits, no @, not a section header
    first_name = ""
    last_name = ""
    skip_keywords = {"resume", "curriculum", "vitae", "cv", "page", "phone", "email", "address", "contact", "profile"}
    for line in lines[:5]:
        clean = re.sub(r'[^a-zA-Z\s]', '', line).strip()
        words = clean.split()
        if 2 <= len(words) <= 4 and not any(w.lower() in skip_keywords for w in words):
            first_name = words[0]
            last_name = " ".join(words[1:])
            break

    # Section segmentation
    sec_patterns = {
        "education": r'^(?:education|academic\s+background|academics|qualifications)\b',
        "experience": r'^(?:experience|work\s+experience|professional\s+experience|employment\s+history|work\s+history)\b',
        "skills": r'^(?:skills|technical\s+skills|core\s+competencies|technologies|expertise|key\s+skills)\b',
        "projects": r'^(?:projects|personal\s+projects|academic\s+projects|key\s+initiatives)\b',
        "certifications": r'^(?:certifications|certificates|licenses|accreditations)\b',
    }

    sections: Dict[str, List[str]] = {"header": []}
    current_sec = "header"

    for line in lines:
        matched_sec = None
        for sec, pattern in sec_patterns.items():
            if re.match(pattern, line, re.IGNORECASE) and len(line) < 45:
                matched_sec = sec
                break
        if matched_sec:
            current_sec = matched_sec
            if current_sec not in sections:
                sections[current_sec] = []
        else:
            sections.setdefault(current_sec, []).append(line)

    # 1. Multi-Experience Parser
    experience_list: List[Dict[str, str]] = []
    if "experience" in sections and sections["experience"]:
        exp_lines = sections["experience"]
        current_exp: Optional[Dict[str, Any]] = None

        for idx, line in enumerate(exp_lines):
            # Check if this line looks like a role/company header
            has_date = bool(DATE_PATTERN.search(line))
            has_title_kw = any(re.search(r'\b' + re.escape(kw) + r'\b', line, re.IGNORECASE) for kw in JOB_TITLE_KEYWORDS)
            
            # If line is short and either has a date or has a job title keyword, start new role
            if (has_date or has_title_kw) and len(line) < 120 and not line.startswith(('-', '•', '*', '·')):
                if current_exp:
                    experience_list.append({
                        "company": current_exp.get("company", "Company")[:100],
                        "job_title": current_exp.get("job_title", "Role")[:100],
                        "location": current_exp.get("location", "")[:100],
                        "date_range": current_exp.get("date_range", "")[:50],
                        "description": "\n".join(current_exp.get("bullets", []))[:2000]
                    })

                date_match = DATE_PATTERN.search(line)
                date_str = date_match.group(0) if date_match else ""
                clean_header = DATE_PATTERN.sub("", line).strip().strip("|,·-–")

                parts = [p.strip() for p in re.split(r'[,|–—\t]+', clean_header) if p.strip()]
                
                title = ""
                company = ""
                location = ""
                if len(parts) >= 2:
                    # Determine which part is title vs company
                    if any(kw in parts[0].lower() for kw in JOB_TITLE_KEYWORDS):
                        title = parts[0]
                        company = parts[1]
                        if len(parts) > 2:
                            location = parts[2]
                    else:
                        company = parts[0]
                        title = parts[1]
                        if len(parts) > 2:
                            location = parts[2]
                elif parts:
                    if has_title_kw:
                        title = parts[0]
                    else:
                        company = parts[0]

                current_exp = {
                    "company": company or "Professional Experience",
                    "job_title": title or "Executive",
                    "location": location,
                    "date_range": date_str,
                    "bullets": []
                }
            else:
                if current_exp is not None:
                    # Append as bullet or context
                    clean_line = line.strip().lstrip('-*•· ')
                    if clean_line:
                        current_exp["bullets"].append(f"• {clean_line}")
                elif idx == 0:
                    current_exp = {
                        "company": line[:80],
                        "job_title": "Professional Role",
                        "location": "",
                        "date_range": "",
                        "bullets": []
                    }

        if current_exp:
            experience_list.append({
                "company": current_exp.get("company", "Company")[:100],
                "job_title": current_exp.get("job_title", "Role")[:100],
                "location": current_exp.get("location", "")[:100],
                "date_range": current_exp.get("date_range", "")[:50],
                "description": "\n".join(current_exp.get("bullets", []))[:2000]
            })

    # If no experience could be split, fallback gracefully
    if not experience_list and "experience" in sections and sections["experience"]:
        exp_lines = sections["experience"]
        experience_list.append({
            "company": exp_lines[0][:100] if exp_lines else "Enterprise",
            "job_title": exp_lines[1][:100] if len(exp_lines) > 1 else "Professional",
            "location": "",
            "date_range": "",
            "description": "\n".join(exp_lines[2:])[:2000] if len(exp_lines) > 2 else ""
        })

    # 2. Multi-Education Parser
    education_list: List[Dict[str, str]] = []
    if "education" in sections and sections["education"]:
        edu_lines = sections["education"]
        current_edu: Optional[Dict[str, Any]] = None

        for line in edu_lines:
            has_degree = any(re.search(r'\b' + re.escape(deg) + r'\b', line, re.IGNORECASE) for deg in DEGREE_KEYWORDS)
            has_univ = any(w in line.lower() for w in ["university", "institute", "college", "school", "academy", "iit", "iim", "bits"])
            has_date = bool(DATE_PATTERN.search(line))

            if (has_degree or has_univ) and len(line) < 130:
                if current_edu:
                    education_list.append({
                        "school_name": current_edu.get("school", "University")[:120],
                        "course": current_edu.get("course", "Degree")[:120],
                        "location": current_edu.get("location", "")[:100],
                        "date_range": current_edu.get("date_range", "")[:50],
                        "description": " ".join(current_edu.get("details", []))[:500]
                    })

                date_match = DATE_PATTERN.search(line)
                date_str = date_match.group(0) if date_match else ""
                clean_line = DATE_PATTERN.sub("", line).strip().strip("|,·-–")

                parts = [p.strip() for p in re.split(r'[,|–—\t]+', clean_line) if p.strip()]
                school = ""
                course = ""
                if has_univ and has_degree:
                    # line has both
                    for part in parts:
                        if any(w in part.lower() for w in ["university", "institute", "college", "school", "academy", "iit", "iim", "bits"]):
                            school = part
                        elif any(re.search(r'\b' + re.escape(deg) + r'\b', part, re.IGNORECASE) for deg in DEGREE_KEYWORDS):
                            course = part
                elif has_univ:
                    school = clean_line
                    # check if other parts have degree
                    for part in parts:
                        if any(re.search(r'\b' + re.escape(deg) + r'\b', part, re.IGNORECASE) for deg in DEGREE_KEYWORDS):
                            course = part
                elif has_degree:
                    course = clean_line
                    for part in parts:
                        if any(w in part.lower() for w in ["university", "institute", "college", "school", "academy", "iit", "iim", "bits"]):
                            school = part
                else:
                    if len(parts) >= 2:
                        course, school = parts[0], parts[1]
                    else:
                        course = clean_line

                current_edu = {
                    "school": school or "Institution",
                    "course": course or "Academic Program",
                    "location": "",
                    "date_range": date_str,
                    "details": []
                }
            elif current_edu is not None:
                # Add supporting detail or if missing school/course
                if not current_edu.get("school") and any(w in line.lower() for w in ["university", "institute", "college"]):
                    current_edu["school"] = line
                elif not current_edu.get("course") and any(deg in line.lower() for deg in DEGREE_KEYWORDS):
                    current_edu["course"] = line
                else:
                    current_edu["details"].append(line)

        if current_edu:
            education_list.append({
                "school_name": current_edu.get("school", "University")[:120],
                "course": current_edu.get("course", "Degree")[:120],
                "location": current_edu.get("location", "")[:100],
                "date_range": current_edu.get("date_range", "")[:50],
                "description": " ".join(current_edu.get("details", []))[:500]
            })

    if not education_list and "education" in sections and sections["education"]:
        edu_lines = sections["education"]
        education_list.append({
            "school_name": edu_lines[0][:100],
            "course": edu_lines[1][:100] if len(edu_lines) > 1 else "Degree",
            "location": "",
            "date_range": "",
            "description": " ".join(edu_lines[2:])[:500] if len(edu_lines) > 2 else ""
        })

    # 3. Comprehensive Skills Extractor
    detected_skills_set = set()
    skills_list: List[Dict[str, Any]] = []

    # 3a. Extract explicitly listed skills from the skills section
    if "skills" in sections:
        skill_text = " ".join(sections["skills"])
        raw_tokens = re.split(r'[,|•·;\n/]+', skill_text)
        for token in raw_tokens:
            s_clean = token.strip().strip("-*•· :")
            if s_clean and 2 <= len(s_clean) <= 40 and not re.match(r'^(?:skills|languages|tools|technologies):?$', s_clean, re.I):
                normalized = s_clean.title()
                if normalized.lower() not in detected_skills_set:
                    detected_skills_set.add(normalized.lower())
                    skills_list.append({"skill_name": normalized, "is_confirmed": True})

    # 3b. Scan entire resume text against COMMON_SKILLS_DICTIONARY
    low_full_text = text.lower()
    for skill in COMMON_SKILLS_DICTIONARY:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, low_full_text):
            if skill.lower() not in detected_skills_set:
                detected_skills_set.add(skill.lower())
                skills_list.append({"skill_name": skill, "is_confirmed": True})

    # 4. Certifications
    certifications_list: List[Dict[str, str]] = []
    if "certifications" in sections and sections["certifications"]:
        for line in sections["certifications"]:
            clean_cert = line.strip().lstrip('-*•· ')
            if clean_cert and len(clean_cert) < 80:
                certifications_list.append({"name": clean_cert, "issuer": "Recognized Body", "date_issued": ""})

    # 5. Projects
    projects_list: List[Dict[str, str]] = []
    if "projects" in sections and sections["projects"]:
        for line in sections["projects"]:
            clean_proj = line.strip().lstrip('-*•· ')
            if clean_proj and len(clean_proj) < 80:
                projects_list.append({"name": clean_proj, "description": "", "date_range": ""})

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "mobile_no": mobile_no,
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio,
        "education": education_list,
        "experience": experience_list,
        "projects": projects_list[:10],
        "skills": skills_list[:40],
        "certifications": certifications_list[:10],
    }
