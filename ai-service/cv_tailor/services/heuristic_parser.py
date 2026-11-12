import re

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
    skip_keywords = {"resume", "curriculum", "vitae", "cv", "page", "phone", "email", "address", "contact"}
    for line in lines[:5]:
        clean = re.sub(r'[^a-zA-Z\s]', '', line).strip()
        words = clean.split()
        if 2 <= len(words) <= 4 and not any(w.lower() in skip_keywords for w in words):
            first_name = words[0]
            last_name = " ".join(words[1:])
            break

    # Sections parsing
    sections = {}
    current_sec = "header"
    sections[current_sec] = []

    sec_patterns = {
        "education": r'^(?:education|academic\s+background|academics|qualifications)\b',
        "experience": r'^(?:experience|work\s+experience|professional\s+experience|employment\s+history|work\s+history)\b',
        "skills": r'^(?:skills|technical\s+skills|core\s+competencies|technologies|expertise)\b',
        "projects": r'^(?:projects|personal\s+projects|academic\s+projects)\b',
        "certifications": r'^(?:certifications|certificates|licenses)\b',
    }

    for line in lines:
        matched_sec = None
        for sec, pattern in sec_patterns.items():
            if re.match(pattern, line, re.IGNORECASE) and len(line) < 40:
                matched_sec = sec
                break
        if matched_sec:
            current_sec = matched_sec
            if current_sec not in sections:
                sections[current_sec] = []
        else:
            sections.setdefault(current_sec, []).append(line)

    # Parse skills
    skills_list = []
    if "skills" in sections:
        skill_text = " ".join(sections["skills"])
        raw_skills = re.split(r'[,|•·;\n/]+', skill_text)
        for s in raw_skills:
            s_clean = s.strip().strip("-*•")
            if s_clean and len(s_clean) < 40 and not re.match(r'^(?:skills|languages|tools|technologies):?$', s_clean, re.I):
                skills_list.append({"skill_name": s_clean})

    # Parse education
    education_list = []
    if "education" in sections:
        edu_lines = sections["education"]
        if edu_lines:
            school = edu_lines[0] if len(edu_lines) > 0 else ""
            course = edu_lines[1] if len(edu_lines) > 1 else ""
            education_list.append({
                "school_name": school[:100],
                "course": course[:100],
                "location": "",
                "description": " ".join(edu_lines[2:])[:500] if len(edu_lines) > 2 else ""
            })

    # Parse experience
    experience_list = []
    if "experience" in sections:
        exp_lines = sections["experience"]
        if exp_lines:
            company = exp_lines[0] if len(exp_lines) > 0 else ""
            title = exp_lines[1] if len(exp_lines) > 1 else ""
            desc = " ".join(exp_lines[2:]) if len(exp_lines) > 2 else ""
            experience_list.append({
                "company": company[:100],
                "job_title": title[:100],
                "location": "",
                "date_range": "",
                "description": desc[:1000]
            })

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
        "projects": [],
        "skills": skills_list[:25],
        "certifications": [],
    }
