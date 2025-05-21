from fastapi import HTTPException
import pdfplumber
import docx
import spacy
import re
import datetime
from typing import Dict, Any, List, Optional, Union
from collections import defaultdict

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise RuntimeError("spaCy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm'.")


def extract_resume_data(text: str) -> Dict[str, Any]:
    """Extract structured resume data according to JSON Resume schema."""
    # Extract basic information
    name = extract_name(text)
    contact_info = extract_contact_info(text)
    summary = extract_summary(text)
    location = extract_location(text)
    
    # Extract sections
    skills = extract_skills(text)
    work_experience = extract_work_experience(text)
    education = extract_education(text)
    projects = extract_projects(text)
    languages = extract_languages(text)
    certifications = extract_certifications(text)
    interests = extract_interests(text)
    
    # Structure data according to JSON Resume schema
    resume_data = {
        "basics": {
            "name": name,
            "label": "",  # Professional title/label
            "image": "",
            "email": contact_info.get("email", ""),
            "phone": contact_info.get("phone", ""),
            "url": contact_info.get("url", ""),
            "summary": summary,
            "location": location,
            "profiles": contact_info.get("profiles", [])
        },
        "work": work_experience,
        "volunteer": [],  # Not implemented in this version
        "education": education,
        "awards": [],  # Not implemented in this version
        "certificates": certifications,
        "publications": [],  # Not implemented in this version
        "skills": skills,
        "languages": languages,
        "interests": interests,
        "references": [],  # Not implemented in this version
        "projects": projects
    }
    
    # Try to determine professional label from work experience
    if work_experience and "position" in work_experience[0] and work_experience[0]["position"]:
        resume_data["basics"]["label"] = work_experience[0]["position"]
    
    return resume_data



def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from an uploaded PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting PDF text: {str(e)}")
    return text.strip()


def extract_text_from_docx(docx_file) -> str:
    """Extract text from an uploaded DOCX file."""
    try:
        doc = docx.Document(docx_file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting DOCX text: {str(e)}")


# Helper functions for extracting specific resume components
def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract contact information including email, phone, and url."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(?:\+\d{1,3}[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b'
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*'
    linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9_-]+'
    github_pattern = r'github\.com/[a-zA-Z0-9_-]+'
    
    email = re.search(email_pattern, text)
    phone = re.search(phone_pattern, text)
    url = re.search(url_pattern, text)
    linkedin = re.search(linkedin_pattern, text)
    github = re.search(github_pattern, text)
    
    result = {
        "email": email.group(0) if email else "",
        "phone": phone.group(0) if phone else "",
        "url": url.group(0) if url else "",
        "profiles": []
    }
    
    if linkedin:
        full_url = linkedin.group(0)
        if not full_url.startswith("http"):
            full_url = "https://" + full_url
        result["profiles"].append({
            "network": "LinkedIn",
            "username": full_url.split('/')[-1],
            "url": full_url
        })
    
    if github:
        full_url = github.group(0)
        if not full_url.startswith("http"):
            full_url = "https://" + full_url
        result["profiles"].append({
            "network": "GitHub",
            "username": full_url.split('/')[-1],
            "url": full_url
        })
    
    return result


def extract_name(text: str) -> str:
    """Extract the name using Named Entity Recognition (NER) with spaCy."""
    # Get first few lines of text (where name typically appears)
    first_lines = "\n".join(text.split('\n')[:5])
    doc = nlp(first_lines)
    
    # Look for PERSON entities
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    
    # Fallback: Look for capitalized words at the beginning
    lines = text.split('\n')
    for line in lines[:3]:  # Check first 3 lines
        line = line.strip()
        if line and all(word[0].isupper() for word in line.split() if word):
            words = [w for w in line.split() if len(w) > 1]
            if len(words) >= 2 and len(words) <= 4:  # Reasonable name length
                return line
    
    return ""


def extract_summary(text: str) -> str:
    """Extract professional summary or objective from the resume."""
    patterns = [
        r'(?:SUMMARY|PROFILE|OBJECTIVE|PROFESSIONAL SUMMARY|ABOUT ME)(?:\s*:|\s*)\s*(.*?)(?:\n\n|\n[A-Z]+\s*(?::|$))',
        r'(?:Summary|Profile|Objective|Professional Summary|About Me)(?:\s*:|\s*)\s*(.*?)(?:\n\n|\n[A-Z]+\s*(?::|$))'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            summary = match.group(1).strip()
            # Clean up multi-line summary
            summary = re.sub(r'\s+', ' ', summary)
            return summary[:500]  # Limit to reasonable length
    
    return ""


def extract_skills(text: str) -> List[Dict[str, Union[str, List[str]]]]:
    """Extract skills and categorize them."""
    # Skill categories and associated keywords
    skill_categories = {
        "Programming Languages": [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Swift", "Kotlin", 
            "PHP", "Ruby", "Scala", "R", "MATLAB", "Perl", "Shell", "Bash", "SQL", "NoSQL"
        ],
        "Web Development": [
            "HTML", "CSS", "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask", 
            "Rails", "Spring", "ASP.NET", "Next.js", "Svelte", "jQuery", "Bootstrap", "Tailwind CSS"
        ],
        "Data Science": [
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", 
            "NumPy", "Data Mining", "Natural Language Processing", "Computer Vision", "Statistical Analysis"
        ],
        "DevOps": [
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Jenkins", "GitLab CI", "GitHub Actions",
            "Terraform", "Ansible", "Chef", "Puppet", "Prometheus", "Grafana"
        ],
        "Databases": [
            "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Oracle", "SQL Server", "Redis", "Cassandra", 
            "DynamoDB", "Elasticsearch", "Neo4j", "Firebase"
        ],
        "Tools": [
            "Git", "JIRA", "Confluence", "Slack", "Notion", "Asana", "Trello", "VS Code", "IntelliJ", 
            "PyCharm", "Jupyter", "Figma", "Photoshop", "Illustrator"
        ],
        "Methodologies": [
            "Agile", "Scrum", "Kanban", "Waterfall", "TDD", "BDD", "DDD", "SOLID", "Microservices", 
            "RESTful API", "GraphQL", "Design Patterns"
        ]
    }
    
    found_skills = []
    
    # First look for a skills section
    skills_section = re.search(r'(?:SKILLS|TECHNICAL SKILLS|EXPERTISE)(?:\s*:|\s*)(.*?)(?:\n\n|\n[A-Z]+\s*(?::|$))', 
                              text, re.DOTALL | re.IGNORECASE)
    
    skills_text = skills_section.group(1) if skills_section else text
    
    # Process each category
    for category, keywords in skill_categories.items():
        found_keywords = []
        for skill in keywords:
            # Use word boundaries to avoid partial matches
            if re.search(rf'\b{re.escape(skill)}\b', text, re.IGNORECASE):
                found_keywords.append(skill)
        
        if found_keywords:
            found_skills.append({
                "name": category,
                "level": "",
                "keywords": found_keywords
            })
    
    # Look for additional skills not in our predefined categories
    skills_pattern = r'\b(?:proficient in|experience with|knowledge of|skilled in|expertise in)\s+(.*?)(?:\.|,|\n)'
    skills_matches = re.finditer(skills_pattern, text, re.IGNORECASE)
    
    misc_skills = []
    for match in skills_matches:
        skill_text = match.group(1).strip()
        misc_skills.extend([s.strip() for s in skill_text.split(",") if s.strip()])
    
    if misc_skills:
        found_skills.append({
            "name": "Other Skills",
            "level": "",
            "keywords": list(set(misc_skills))
        })
    
    return found_skills


def extract_education(text: str) -> List[Dict[str, Union[str, List[str]]]]:
    """Extract education information."""
    education_section = re.search(r'(?:EDUCATION|ACADEMIC BACKGROUND|ACADEMIC CREDENTIALS)(?:\s*:|\s*)(.*?)(?:\n\n|\n[A-Z]+\s*(?::|$))', 
                                 text, re.DOTALL | re.IGNORECASE)
    
    if not education_section:
        return []
    
    education_text = education_section.group(1)
    
    # Define patterns for degree types and date ranges
    degree_pattern = r'\b(?:Bachelor|Master|Ph\.?D\.?|MBA|B\.S\.|M\.S\.|B\.A\.|M\.A\.|B\.Eng|M\.Eng|Associate|Diploma)\b'
    date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\.?\s+\d{4}\s*(?:-|–|to)\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\.?\s+\d{4}|Present|Current|Now)'
    year_pattern = r'\b\d{4}\s*(?:-|–|to)\s*(?:\d{4}|Present|Current|Now)\b'
    
    # Common institutions
    university_pattern = r'\b(?:University|College|Institute|School)\b'
    
    education_entries = []
    # Split by potential education entries (look for dates or degrees)
    potential_entries = re.split(r'\n\s*\n|\n(?=[A-Z])', education_text)
    
    for entry in potential_entries:
        if not entry.strip():
            continue
            
        degree_match = re.search(degree_pattern, entry, re.IGNORECASE)
        institution_match = re.search(university_pattern, entry, re.IGNORECASE)
        
        # Skip if no signs of education information
        if not (degree_match or institution_match):
            continue
            
        # Extract dates
        date_match = re.search(date_pattern, entry, re.IGNORECASE)
        if not date_match:
            date_match = re.search(year_pattern, entry)
            
        start_date = ""
        end_date = ""
        if date_match:
            date_text = date_match.group(0)
            parts = re.split(r'\s*(?:-|–|to)\s*', date_text)
            if len(parts) >= 2:
                start_date = parts[0].strip()
                end_date = parts[1].strip()
                
        # Extract institution
        institution = ""
        if institution_match:
            # Get the sentence containing the institution
            inst_sentence = re.search(r'[^.\n]*' + university_pattern + r'[^.\n]*', entry, re.IGNORECASE)
            if inst_sentence:
                institution = inst_sentence.group(0).strip()
                
        # Extract area of study and degree type
        area = ""
        study_type = ""
        if degree_match:
            degree_sentence = re.search(r'[^.\n]*' + degree_pattern + r'[^.\n]*', entry, re.IGNORECASE)
            if degree_sentence:
                degree_text = degree_sentence.group(0)
                study_type = degree_match.group(0)
                
                # Try to find the area of study (often follows "in" after the degree)
                area_match = re.search(r'\b' + re.escape(study_type) + r'(?:\sof\sScience|\sof\sArts)?\s+in\s+([^,.\n]+)', degree_text, re.IGNORECASE)
                if area_match:
                    area = area_match.group(1).strip()
        
        education_entries.append({
            "institution": institution,
            "url": "",
            "area": area,
            "studyType": study_type,
            "startDate": start_date,
            "endDate": end_date,
            "score": "",
            "courses": []
        })
    
    return education_entries


def extract_work_experience(text: str) -> List[Dict[str, Union[str, List[str]]]]:
    """Extract work experience information."""
    experience_section = re.search(r'(?:EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EMPLOYMENT HISTORY)(?:\s*:|\s*)(.*?)(?:\n\n|\n[A-Z]+\s*(?::|$))', 
                                   text, re.DOTALL | re.IGNORECASE)
    
    if not experience_section:
        return []
    
    experience_text = experience_section.group(1)
    
    # Define patterns for company names, job titles, and date ranges
    date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\.?\s+\d{4}\s*(?:-|–|to)\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\.?\s+\d{4}|Present|Current|Now)'
    year_pattern = r'\b\d{4}\s*(?:-|–|to)\s*(?:\d{4}|Present|Current|Now)\b'
    
    # Common job titles
    job_titles = [
        "Software Engineer", "Data Scientist", "Product Manager", "Project Manager",
        "Developer", "Engineer", "Analyst", "Consultant", "Designer", "Architect",
        "Director", "Manager", "Lead", "Head", "Chief", "Officer", "Associate",
        "Administrator", "Specialist", "Coordinator", "Supervisor"
    ]
    job_pattern = '|'.join(job_titles)
    
    work_entries = []
    
    # Split by potential work entries (look for dates)
    date_matches = list(re.finditer(date_pattern + '|' + year_pattern, experience_text, re.IGNORECASE))
    
    if date_matches:
        for i, date_match in enumerate(date_matches):
            start_idx = date_match.start()
            end_idx = date_matches[i+1].start() if i < len(date_matches) - 1 else len(experience_text)
            
            entry_text = experience_text[start_idx:end_idx].strip()
            if not entry_text:
                continue
                
            # Process this work entry
            date_text = date_match.group(0)
            parts = re.split(r'\s*(?:-|–|to)\s*', date_text)
            start_date = parts[0].strip() if len(parts) >= 2 else ""
            end_date = parts[1].strip() if len(parts) >= 2 else ""
            
            # Look for job title
            position = ""
            title_match = re.search(rf'\b({job_pattern})\b', entry_text, re.IGNORECASE)
            if title_match:
                position = title_match.group(0)
                
                # Try to get full job title (often includes words before/after the matched keyword)
                title_context = re.search(r'[^,.\n]*' + re.escape(position) + r'[^,.\n]*', entry_text)
                if title_context:
                    position = title_context.group(0).strip()
            
            # Look for company name (often near the beginning or near the job title)
            company = ""
            lines = entry_text.split('\n')
            for line in lines[:2]:  # Check first two lines
                if position and position in line:
                    # Company might be in the same line as the position
                    parts = line.split(position)
                    if parts[0].strip():
                        company = parts[0].strip().rstrip(',')
                    elif len(parts) > 1 and parts[1].strip():
                        company_match = re.search(r'(?:at|with|for)\s+([^,.\n]+)', parts[1])
                        if company_match:
                            company = company_match.group(1).strip()
            
            # If company still not found, look for capitalized words
            if not company and len(lines) > 0:
                words = lines[0].split()
                cap_words = [word for word in words if word and word[0].isupper()]
                if cap_words and position not in lines[0]:
                    company = ' '.join(cap_words)
            
            # Extract responsibilities/highlights
            highlights = []
            bullet_pattern = r'(?:•|-|\*|\d+\.)\s+([^\n]+)'
            bullet_matches = re.finditer(bullet_pattern, entry_text)
            
            for bullet in bullet_matches:
                highlights.append(bullet.group(1).strip())
            
            # Create a summary from the first few lines if no highlights found
            summary = ""
            if not highlights and len(lines) > 2:
                summary_lines = [line for line in lines[2:7] if line.strip()]  # Use a few lines after title/company
                if summary_lines:
                    summary = ' '.join(summary_lines)
            
            work_entries.append({
                "name": company,
                "position": position,
                "url": "",
                "startDate": start_date,
                "endDate": end_date,
                "summary": summary,
                "highlights": highlights
            })
    
    return work_entries


def extract_projects(text: str) -> List[Dict[str, Union[str, List[str]]]]:
    """Extract project information."""
    projects_section = re.search(r'(?:PROJECTS|PERSONAL PROJECTS|PROFESSIONAL PROJECTS)(?:\s*:|\s*)(.*?)(?:\n\n|\n[A-Z]+\s*(?::|$))', 
                                text, re.DOTALL | re.IGNORECASE)
    
    if not projects_section:
        return []
    
    projects_text = projects_section.group(1)
    
    # Split by potential project entries
    project_entries = re.split(r'\n\s*\n|\n(?=[A-Z][a-z])', projects_text)
    
    projects = []
    for entry in project_entries:
        if not entry.strip():
            continue
            
        lines = entry.split('\n')
        name = lines[0].strip() if lines else ""
        
        # Try to extract name from first line
        if name:
            # Remove potential markers at the start
            name = re.sub(r'^(?:•|-|\*|\d+\.)\s+', '', name)
            # Remove dates if they appear on the same line
            name = re.sub(r'\s*\(\d{4}(?:-\d{4})?\)\s*$', '', name)
            name = re.sub(r'\s*\d{4}(?:-\d{4})?\s*$', '', name)
        
        # Look for GitHub link
        url = ""
        github_match = re.search(r'(?:github\.com|repo|repository|source code|code)(?:[\s:]+)([^\s,]+)', entry, re.IGNORECASE)
        if github_match:
            url_candidate = github_match.group(1)
            if "github.com" in url_candidate or "http" in url_candidate:
                url = url_candidate
        
        # Extract date information
        date_match = re.search(r'\b(\d{4})(?:\s*-\s*(\d{4}|Present|Current))?\b', entry)
        start_date = date_match.group(1) if date_match else ""
        end_date = date_match.group(2) if date_match and date_match.group(2) else ""
        
        # Extract description and highlights
        description = ""
        highlights = []
        
        # Use lines after the first line for description
        if len(lines) > 1:
            desc_lines = []
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                    
                bullet_match = re.match(r'(?:•|-|\*|\d+\.)\s+(.*)', line)
                if bullet_match:
                    highlights.append(bullet_match.group(1))
                else:
                    desc_lines.append(line)
            
            if desc_lines:
                description = ' '.join(desc_lines)
        
        projects.append({
            "name": name,
            "startDate": start_date,
            "endDate": end_date,
            "description": description,
            "highlights": highlights,
            "url": url
        })
    
    return projects


def extract_languages(text: str) -> List[Dict[str, str]]:
    """Extract languages and fluency levels."""
    languages_section = re.search(r'(?:LANGUAGES|LANGUAGE SKILLS)(?:\s*:|\s*)(.*?)(?:\n\n|\n[A-Z]+\s*(?::|$))', 
                                 text, re.DOTALL | re.IGNORECASE)
    
    common_languages = [
        "English", "Spanish", "French", "German", "Chinese", "Mandarin", "Cantonese", 
        "Japanese", "Korean", "Russian", "Arabic", "Hindi", "Portuguese", "Italian",
        "Dutch", "Polish", "Turkish", "Vietnamese", "Thai", "Indonesian", "Swedish",
        "Norwegian", "Danish", "Finnish", "Greek"
    ]
    
    fluency_levels = ["Native", "Fluent", "Proficient", "Intermediate", "Beginner", "Basic"]
    
    languages = []
    
    # Search within languages section if found
    if languages_section:
        languages_text = languages_section.group(1)
        
        # Look for language: level patterns
        lang_level_pattern = r'({})\s*(?::|-)?\s*({})?'.format(
            '|'.join(common_languages), 
            '|'.join(fluency_levels)
        )
        
        matches = re.finditer(lang_level_pattern, languages_text, re.IGNORECASE)
        for match in matches:
            lang = match.group(1)
            fluency = match.group(2) if match.group(2) else "Proficient"  # Default if not specified
            
            languages.append({
                "language": lang,
                "fluency": fluency
            })
    
    # If no languages section found, search in full text
    if not languages:
        for lang in common_languages:
            if re.search(r'\b{}\b'.format(re.escape(lang)), text, re.IGNORECASE):
                # Try to find fluency level near the language mention
                context = re.search(r'[^.\n]*\b{}\b[^.\n]*'.format(re.escape(lang)), text, re.IGNORECASE)
                fluency = "Proficient"  # Default
                
                if context:
                    for level in fluency_levels:
                        if re.search(r'\b{}\b'.format(re.escape(level)), context.group(0), re.IGNORECASE):
                            fluency = level
                            break
                
                languages.append({
                    "language": lang,
                    "fluency": fluency
                })
    
    return languages


def extract_certifications(text: str) -> List[Dict[str, str]]:
    """Extract certifications."""
    cert_section = re.search(r'(?:CERTIFICATIONS|CERTIFICATES|PROFESSIONAL CERTIFICATIONS)(?:\s*:|\s*)(.*?)(?:\n\n|\n[A-Z]+\s*(?::|$))', 
                            text, re.DOTALL | re.IGNORECASE)
    
    if not cert_section:
        return []
    
    cert_text = cert_section.group(1)
    
    common_certs = [
        "AWS", "Azure", "Google Cloud", "CompTIA", "Cisco", "CCNA", "CCNP", "PMP", "Scrum",
        "Six Sigma", "ITIL", "Oracle", "Microsoft", "IBM", "SAP", "Salesforce", "CISA", "CISSP",
        "Security\\+", "Network\\+", "A\\+", "CFA", "CPA", "MCSA", "MCSE", "MCTS", "RHCE", "RHCSA"
    ]
    
    cert_pattern = '|'.join(common_certs)
    
    certifications = []
    
    # Split by lines or bullet points
    entries = re.split(r'\n|(?:•|-|\*|\d+\.)\s+', cert_text)
    
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
            
        # Look for certification names
        cert_match = re.search(rf'({cert_pattern})', entry, re.IGNORECASE)
        if cert_match:
            name = entry  # Use the full entry as name
            
            # Try to extract date
            date = ""
            date_match = re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)?\.?\s*\d{4}\b', entry)
            if date_match:
                date = date_match.group(0)
            
            # Try to extract issuer
            issuer = ""
            if "-" in entry:
                parts = entry.split("-")
                if len(parts) > 1:
                    issuer = parts[1].strip()
            
            certifications.append({
                "name": name,
                "date": date,
                "issuer": issuer,
                "url": ""
            })
    
    return certifications


def extract_location(text: str) -> Dict[str, str]:
    """Extract location information."""
    # Look for address patterns
    address_pattern = r'\b\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Lane|Ln|Drive|Dr)[.,]?\s+[A-Za-z\s]+(?:,\s*[A-Z]{2})?\s*\d{5}(?:-\d{4})?\b'
    address_match = re.search(address_pattern, text)
    
    # Look for "City, State" or "City, Country" patterns
    city_state_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*(?:[A-Z]{2}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
    location_match = re.search(city_state_pattern, text)
    
    address = ""
    city = ""
    region = ""
    postal_code = ""
    country_code = ""
    
    if address_match:
        address_text = address_match.group(0)
        address = address_text
        
        # Try to extract postal code
        zip_match = re.search(r'\b\d{5}(?:-\d{4})?\b', address_text)
        if zip_match:
            postal_code = zip_match.group(0)
        
        # Try to extract city and state
        city_state_match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})', address_text)
        if city_state_match:
            city = city_state_match.group(1).strip()
            region = city_state_match.group(2)
    
    elif location_match:
        location_text = location_match.group(0)
        parts = location_text.split(',')
        
        if len(parts) >= 2:
            city = parts[0].strip()
            state_or_country = parts[1].strip()
            
            # If it looks like a US state code
            if len(state_or_country) == 2 and state_or_country.isupper():
                region = state_or_country
                country_code = "US"
            else:
                country_code = state_or_country
    
    return {
        "address": address,
        "postalCode": postal_code,
        "city": city,
        "countryCode": country_code,
        "region": region
    }


def extract_interests(text: str) -> List[Dict[str, Union[str, List[str]]]]:
    """Extract interests/hobbies."""
    interests_section = re.search(r'(?:INTERESTS|HOBBIES|ACTIVITIES)(?:\s*:|\s*)(.*?)(?:\n\n|\n[A-Z]+\s*(?::|$))', 
                                 text, re.DOTALL | re.IGNORECASE)
    
    if not interests_section:
        return []
    
    interests_text = interests_section.group(1)
    
    # Split by commas, bullets, or new lines
    split_pattern = r'(?:,|\n|•|-|\*|\d+\.)'
    parts = re.split(split_pattern, interests_text)
    
    interests = []
    for part in parts:
        part = part.strip()
        if part:
            interests.append({
                "name": part,
                "keywords": []
            })
    
    return interests
