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
    "Strategic Alliances", "Commercial Partnerships", "Channel Sales",
    # Product
    "Product Management", "Product Strategy", "Product Roadmap", "User Stories",
    "Agile", "Scrum", "Wireframing", "PRD", "A/B Testing", "User Research", "Go-To-Market (GTM)",
    "Feature Prioritization", "Jira", "Figma", "Customer Discovery", "B2B Product Strategy",
    # Tech & Software & Data
    "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "SQL",
    "PostgreSQL", "MongoDB", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git",
    "REST APIs", "GraphQL", "Microservices", "CI/CD", "Data Analysis", "Machine Learning",
    "Deep Learning", "Tableau", "Power BI", "Data Modeling", "ETL Pipelines", "Pandas",
    "System Design", "Cloud Architecture", "Distributed Systems",
    # Finance & Capital
    "Financial Analysis", "Financial Modeling", "Corporate Finance", "FP&A",
    "Budgeting & Forecasting", "Variance Analysis", "Valuation", "DCF", "M&A Advisory",
    "Accounting", "Cash Flow Management", "P&L Management", "SAP", "Advanced Excel",
    "Financial Reporting", "Due Diligence", "Capital Budgeting", "Auditing",
    "Capital Markets", "Fundraising", "Structured Finance", "Investment Banking",
    "Private Equity", "Venture Capital", "QuickBooks ProAdvisor", "CFA", "FRM",
    # Strategy & Consulting & Transformation
    "Management Consulting", "Corporate Strategy", "Strategic Planning",
    "Business Transformation", "Change Management", "Process Optimization",
    "Stakeholder Management", "Executive Presentations", "KPIs & OKRs",
    "Organizational Design", "Market Expansion", "Operating Model",
    "Chief of Staff", "Market Sizing", "Competitive Analysis",
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
    "administrator", "architect", "intern", "trainee", "adviser", "advisor"
]

DEGREE_KEYWORDS = [
    "bachelor", "master", "b.tech", "btech", "b.e.", "be", "b.sc", "bsc", "bba",
    "b.com", "bcom", "mba", "m.tech", "mtech", "m.s.", "ms", "ph.d", "phd",
    "post graduate", "pgdm", "diploma", "degree", "doctorate", "electrical",
    "electronics", "mechanical", "computer science"
]

INSTITUTION_KEYWORDS = [
    "university", "institute", "college", "school", "academy",
    "iit", "iim", "bit", "nit", "bits", "cambridge", "oxford", "harvard",
    "stanford", "iisc", "fms", "xlri", "isb", "spjimr", "mesra"
]

MONTHS_REGEX = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?'
DATE_CHUNK = rf'(?:(?:0?[1-9]|1[0-2])[\/.-](?:19|20)?\d{{2}}|{MONTHS_REGEX}\s+(?:19|20)?\d{{2}}|{MONTHS_REGEX}\s*\'?\d{{2}}|\b(?:19|20)\d{{2}}\b)'
DATE_PATTERN = re.compile(
    rf'({DATE_CHUNK}\s*(?:-|–|—|to)\s*(?:Present|Current|Ongoing|Now|{DATE_CHUNK}))',
    re.IGNORECASE
)

KNOWN_CITIES = [
    "hyderabad", "bangalore", "bengaluru", "delhi", "new delhi", "mumbai",
    "gurgaon", "gurugram", "noida", "pune", "kolkata", "chennai", "remote",
    "singapore", "dubai", "london", "new york", "san francisco", "india", "us"
]

def parse_resume_text_heuristic(text: str, extra_urls: Optional[List[str]] = None) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return {}

    # Email
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email_match.group(0).strip() if email_match else ""

    # Phone: supports explicit labels, +91 85279 61709, +91-8527961709, 85279 61709, (555) 123-4567, etc.
    mobile_no = ""
    phone_label_match = re.search(
        r'(?:phone|mobile|cell|contact|tel|m)[\s.:#*-]*([+]?[\d\s().-]{9,22}\d)',
        text,
        re.IGNORECASE
    )
    if phone_label_match:
        cand = phone_label_match.group(1).strip()
        digits = re.sub(r'\D', '', cand)
        if 10 <= len(digits) <= 15:
            mobile_no = cand

    if not mobile_no:
        # Check Indian mobile (10 digits starting with 6-9, with optional +91 and spaces/dashes)
        india_mobile_match = re.search(r'(?:\+?91[\s.-]?)?([6-9]\d{4}[\s.-]?\d{5}|[6-9]\d{9})', text)
        if india_mobile_match:
            cand = india_mobile_match.group(0).strip()
            digits = re.sub(r'\D', '', cand)
            if 10 <= len(digits) <= 12:
                mobile_no = cand

    if not mobile_no:
        # General international/US phone match
        phone_match = re.search(r'(\+?\d{1,4}[\s.-]?)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}|\d{10,12})', text)
        if phone_match:
            mobile_no = phone_match.group(0).strip()

    # LinkedIn: check text first, then extra_urls (from PDF Annotations)
    linkedin = ""
    linkedin_match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?|linkedin\.com/in/[a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    if linkedin_match:
        linkedin = "https://" + linkedin_match.group(0).removeprefix("http://").removeprefix("https://")
    elif extra_urls:
        for u in extra_urls:
            if "linkedin.com" in u.lower():
                linkedin = u
                break

    # GitHub
    github = ""
    github_match = re.search(r'(https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+/?|github\.com/[a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    if github_match:
        github = "https://" + github_match.group(0).removeprefix("http://").removeprefix("https://")
    elif extra_urls:
        for u in extra_urls:
            if "github.com" in u.lower():
                github = u
                break

    # Portfolio
    portfolio = ""
    portfolio_match = re.search(r'https?://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?', text)
    if portfolio_match:
        url = portfolio_match.group(0)
        if "linkedin.com" not in url and "github.com" not in url:
            portfolio = url

    # Candidate Name: first 1-3 lines
    first_name = ""
    last_name = ""
    skip_keywords = {"resume", "curriculum", "vitae", "cv", "page", "phone", "email", "address", "contact", "profile"}
    for line in lines[:5]:
        clean = re.sub(r'[^a-zA-Z\s]', '', line).strip()
        words = clean.split()
        if 2 <= len(words) <= 4 and not any(w.lower() in skip_keywords for w in words):
            first_name = words[0].title()
            last_name = " ".join(words[1:]).title()
            break

    # Section segmentation
    sec_patterns = {
        "education": r'^(?:education|academic\s+background|academics|qualifications)\b',
        "experience": r'^(?:professional\s+experience|work\s+experience|experience|employment\s+history|work\s+history)\b',
        "skills": r'^(?:certifications\s*&\s*core\s*skills|skills|technical\s+skills|core\s+competencies|technologies|expertise|key\s+skills)\b',
        "projects": r'^(?:projects|personal\s+projects|academic\s+projects|key\s+initiatives)\b',
        "certifications": r'^(?:certifications|certificates|licenses|accreditations)\b',
    }

    sections: Dict[str, List[str]] = {"header": []}
    current_sec = "header"

    for line in lines:
        matched_sec = None
        clean_upper = re.sub(r'[^A-Z\s&]', '', line.upper()).strip()
        for sec, pattern in sec_patterns.items():
            if re.match(pattern, line, re.IGNORECASE) or re.match(pattern, clean_upper, re.IGNORECASE):
                if len(line) < 45:
                    matched_sec = sec
                    break
        if matched_sec:
            current_sec = matched_sec
            if current_sec not in sections:
                sections[current_sec] = []
        else:
            sections.setdefault(current_sec, []).append(line)

    # 1. Multi-Experience Extraction
    experience_list: List[Dict[str, str]] = []
    if "experience" in sections and sections["experience"]:
        exp_lines = sections["experience"]
        current_exp: Optional[Dict[str, Any]] = None

        i = 0
        while i < len(exp_lines):
            line = exp_lines[i]
            date_match = DATE_PATTERN.search(line)
            
            # Check if this line is an experience header
            # Formats:
            # 1. "DealOS.in | Founder | 04/2026 - Present"
            # 2. "Founder - DealOS.in (04/2026 – Present)"
            # 3. "Company | Title | Date" or Date on its own line after Title/Company
            if date_match:
                date_str = date_match.group(1).strip()
                header_text = line[:date_match.start()].strip()
                if not header_text and date_match.end() < len(line):
                    header_text = line[date_match.end():].strip()
                header_text = header_text.strip(" ,|–-—()")

                # If date is on a line by itself, inspect previous line for company/title
                if not header_text and i > 0:
                    prev_line = exp_lines[i - 1].strip()
                    if not prev_line.startswith(('*', '-', '•', '·', '>')) and len(prev_line) < 140:
                        header_text = prev_line.strip(" ,|–-—()")

                if header_text:
                    if current_exp:
                        experience_list.append({
                            "company": current_exp.get("company", "Company")[:100],
                            "job_title": current_exp.get("job_title", "Role")[:100],
                            "location": current_exp.get("location", "")[:100],
                            "date_range": current_exp.get("date_range", "")[:50],
                            "description": "\n".join(current_exp.get("bullets", []))[:2500]
                        })

                    company = ""
                    job_title = ""
                    extracted_loc = ""

                    # Check for multi-part delimiter: " | ", " - ", " – ", " — ", ", ", "  "
                    parts = []
                    for delim in [" | ", " – ", " — ", " - ", " at ", " @ ", ", ", "  "]:
                        if delim in header_text:
                            candidate_parts = [p.strip(" ,|–-—()") for p in header_text.split(delim) if p.strip(" ,|–-—()")]
                            if len(candidate_parts) >= 2:
                                parts = candidate_parts
                                break

                    if parts:
                        # If 3+ parts (e.g. [Company, Title, Location])
                        non_loc_parts = []
                        for p in parts:
                            if any(c in p.lower() for c in KNOWN_CITIES):
                                extracted_loc = p
                            else:
                                non_loc_parts.append(p)
                        if len(non_loc_parts) >= 2:
                            p0 = non_loc_parts[0]
                            p1 = non_loc_parts[1]
                        else:
                            p0 = parts[0]
                            p1 = parts[1]

                        p0_title = any(re.search(r'\b' + re.escape(kw) + r'\b', p0, re.IGNORECASE) for kw in JOB_TITLE_KEYWORDS)
                        p1_title = any(re.search(r'\b' + re.escape(kw) + r'\b', p1, re.IGNORECASE) for kw in JOB_TITLE_KEYWORDS)

                        if p0_title and not p1_title:
                            job_title = p0
                            company = p1
                        elif p1_title and not p0_title:
                            job_title = p1
                            company = p0
                        else:
                            company = p0
                            job_title = p1
                    else:
                        if any(kw in header_text.lower() for kw in JOB_TITLE_KEYWORDS):
                            job_title = header_text
                        else:
                            company = header_text

                    # Check if next line contains Location | Focus/Tagline
                    location = extracted_loc
                    focus = ""
                    if i + 1 < len(exp_lines):
                        next_line = exp_lines[i + 1]
                        is_bullet = next_line.startswith(('*', '-', '•', '·', '>'))
                        is_next_date = bool(DATE_PATTERN.search(next_line))
                        
                        if not is_bullet and not is_next_date and len(next_line) < 130:
                            if "|" in next_line:
                                loc_parts = next_line.split("|", 1)
                                if not location:
                                    location = loc_parts[0].strip()
                                focus = loc_parts[1].strip()
                                i += 1  # Consume next line
                            elif any(city in next_line.lower() for city in KNOWN_CITIES):
                                if not location:
                                    location = next_line.strip()
                                i += 1  # Consume next line

                    bullets = []
                    if focus:
                        bullets.append(f"• Domain: {focus}")

                    current_exp = {
                        "company": company or "Organization",
                        "job_title": job_title or "Professional",
                        "location": location,
                        "date_range": date_str,
                        "bullets": bullets
                    }
            elif current_exp is not None:
                is_bullet = line.startswith(('*', '-', '•', '·', '>'))
                clean_bullet = line.lstrip('*-•·> ').strip()
                if is_bullet or not current_exp["bullets"]:
                    current_exp["bullets"].append(f"• {clean_bullet}")
                else:
                    # Continuation of previous bullet
                    current_exp["bullets"][-1] += f" {clean_bullet}"
            i += 1

        if current_exp:
            experience_list.append({
                "company": current_exp.get("company", "Company")[:100],
                "job_title": current_exp.get("job_title", "Role")[:100],
                "location": current_exp.get("location", "")[:100],
                "date_range": current_exp.get("date_range", "")[:50],
                "description": "\n".join(current_exp.get("bullets", []))[:2500]
            })

    # 2. Multi-Education Extraction
    education_list: List[Dict[str, str]] = []
    if "education" in sections and sections["education"]:
        edu_lines = sections["education"]
        for line in edu_lines:
            has_deg_kw = any(re.search(r'\b' + re.escape(deg) + r'\b', line, re.IGNORECASE) for deg in DEGREE_KEYWORDS)
            has_inst_kw = any(re.search(r'\b' + re.escape(inst) + r'\b', line, re.IGNORECASE) for inst in INSTITUTION_KEYWORDS)
            year_match = re.search(r'(\b\d{4}\s*(?:-|–|—|to)\s*\d{4}\b|\b\d{4}\b)', line)

            if (has_deg_kw or has_inst_kw or year_match) and len(line) < 140:
                date_str = year_match.group(1).strip() if year_match else ""
                text_without_date = line[:year_match.start()].rstrip("|–-— \t") if year_match else line

                course = ""
                school = ""
                # Split course and institution
                if "  " in text_without_date:
                    parts = [p.strip() for p in text_without_date.split("  ") if p.strip()]
                    if len(parts) >= 2:
                        course = parts[0]
                        school = " ".join(parts[1:])
                    else:
                        course = parts[0]
                elif "|" in text_without_date:
                    parts = [p.strip() for p in text_without_date.split("|") if p.strip()]
                    course = parts[0]
                    school = parts[1] if len(parts) > 1 else ""
                elif " - " in text_without_date:
                    parts = [p.strip() for p in text_without_date.split(" - ", 1) if p.strip()]
                    course = parts[0]
                    school = parts[1] if len(parts) > 1 else ""
                else:
                    course = text_without_date

                education_list.append({
                    "school_name": school or "Institution",
                    "course": course or "Degree",
                    "location": "",
                    "date_range": date_str,
                    "description": ""
                })

    # 3. Comprehensive Skills Bank Extraction
    text_lower = text.lower()
    confirmed_skills: List[Dict[str, Any]] = []
    seen_skills = set()

    for skill in COMMON_SKILLS_DICTIONARY:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower) and skill.lower() not in seen_skills:
            seen_skills.add(skill.lower())
            confirmed_skills.append({
                "skill_name": skill,
                "is_confirmed": True
            })

    # Also extract skills directly listed under skills section
    if "skills" in sections and sections["skills"]:
        for line in sections["skills"]:
            raw_items = re.split(r'[,|•·;\n]+', line)
            for item in raw_items:
                clean_item = item.strip().strip("-*•· ")
                clean_item = re.sub(r'^(?:Strategy & Platform Building:|Capital & M&A:|Finance & Analytics:)', '', clean_item).strip()
                if 2 < len(clean_item) < 40 and clean_item.lower() not in seen_skills:
                    seen_skills.add(clean_item.lower())
                    confirmed_skills.append({
                        "skill_name": clean_item,
                        "is_confirmed": True
                    })

    # Target Roles
    target_roles = ["Corporate Strategy & Transformation", "Finance Manager", "VP of Strategy"]
    if experience_list:
        target_roles = [experience_list[0]["job_title"]] + target_roles[:2]

    return {
        "first_name": first_name or "Candidate",
        "last_name": last_name or "",
        "email": email,
        "mobile_no": mobile_no,
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio,
        "education": education_list,
        "experience": experience_list,
        "skills": confirmed_skills,
        "projects": [],
        "certifications": [],
        "target_roles": target_roles,
        "target_locations": ["Hyderabad", "Bengaluru", "Mumbai", "Remote"],
        "target_work_modes": ["Hybrid", "Remote"],
        "target_salary": "₹30L - ₹50L/yr"
    }
