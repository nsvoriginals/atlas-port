from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.user_model import Resume, User
from schemas.resume_schema import ResumeCreate, ResumeResponse
from config.db import SessionLocal
from typing import Dict, Any, Optional
import re
from sqlalchemy.exc import IntegrityError

# Create dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

resume_router = APIRouter()

def get_default_resume_data():
    return {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "website": "",
        "twitter": "",
        "github": "",
        "summary": "",
        "experience": [],
        "projects": [],
        "education": [],
        "skills": [],
        "awards": [],
        "languages": [],
        "interests": [],
        "hobbies": [],
        "references": []
    }

@resume_router.get("/", response_model=ResumeResponse)
async def get_resume(
    user_id: int = Query(..., description="User ID"),
    latest: Optional[bool] = Query(False, description="Get the latest resume"),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Resume).filter(Resume.user_id == user_id)
        
        if latest:
            # Get the most recent resume based on updated_at
            resume = query.order_by(Resume.updated_at.desc()).first()
        else:
            resume = query.first()
            
        if not resume:
            # Create a new resume with default data
            default_data = get_default_resume_data()
            new_resume = Resume(
                user_id=user_id,
                resume_data=default_data,
                template_name="modern"
            )
            db.add(new_resume)
            db.commit()
            db.refresh(new_resume)
            return new_resume
            
        return resume
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching resume: {str(e)}"
        )

@resume_router.post("/", response_model=ResumeResponse)
async def create_resume(
    user_id: int = Query(..., description="User ID"),
    resume_data: ResumeCreate = None,
    template_name: str = "modern",
    db: Session = Depends(get_db)
):
    try:
        # Check if user already has a resume
        existing_resume = db.query(Resume).filter(Resume.user_id == user_id).first()
        
        if existing_resume:
            # Update existing resume
            existing_resume.resume_data = resume_data.dict()
            existing_resume.template_name = template_name
            # updated_at will be automatically updated by SQLAlchemy
            db.commit()
            db.refresh(existing_resume)
            return existing_resume
        
        # Create new resume
        new_resume = Resume(
            user_id=user_id,
            resume_data=resume_data.dict(),
            template_name=template_name
        )
        
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        return new_resume
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating/updating resume: {str(e)}"
        )

@resume_router.post("/format-latex")
async def format_latex_resume(
    user_id: int = Query(..., description="User ID to get resume data"),
    resume_data: ResumeCreate = None,
    db: Session = Depends(get_db)
):
    """Format LaTeX template with user's resume data"""
    try:
        # Check if user exists, if not create one
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # Create a new user with data from resume
            new_user = User(
                id=user_id,
                email=resume_data.email if resume_data else f"user{user_id}@example.com",
                name=resume_data.name if resume_data else f"User {user_id}",
                password="default_password"  # You might want to change this
            )
            db.add(new_user)
            try:
                db.commit()
                db.refresh(new_user)
            except IntegrityError as e:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Error creating user: {str(e)}"
                )
        
        # Get user's resume data
        resume = db.query(Resume).filter(Resume.user_id == user_id).first()
        
        if not resume:
            # Create a new resume with the provided data
            if not resume_data:
                raise HTTPException(
                    status_code=400,
                    detail="No resume data provided for new resume"
                )
            
            new_resume = Resume(
                user_id=user_id,
                resume_data=resume_data.dict(),
                template_name="modern"
            )
            db.add(new_resume)
            try:
                db.commit()
                db.refresh(new_resume)
                resume = new_resume
            except IntegrityError as e:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Error creating resume: {str(e)}"
                )
        
        # Use the hardcoded LaTeX template
        latex_template = get_latex_template()
        
        # Format the LaTeX template with resume data
        formatted_latex = format_latex_with_data(latex_template, resume.resume_data)
        
        return {
            "user_id": user_id,
            "formatted_latex": formatted_latex,
            "resume_data_used": resume.resume_data
        }
        
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error formatting LaTeX: {str(e)}"
        )

def get_latex_template() -> str:
    """Return the hardcoded LaTeX template"""
    return r"""
\documentclass[a4paper,10pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{url}
\usepackage{fontawesome}

% Page layout
\geometry{margin=0.75in}

% Colors
\definecolor{primary}{RGB}{0, 51, 102}
\definecolor{secondary}{RGB}{102, 102, 102}

% Hyperlink styling
\hypersetup{
    colorlinks=true,
    urlcolor=primary,
    linkcolor=primary,
    citecolor=primary
}

% Section formatting
\titleformat{\section}{\large\bfseries\color{primary}}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{1em}{1em}

% Custom spacing
\setlist[itemize]{
  topsep=4pt,
  partopsep=2pt,
  itemsep=3pt,
  parsep=0pt,
  leftmargin=1.5em,
  itemindent=0pt
}

% Custom commands
\newcommand{\resumeheading}[1]{\textbf{\color{primary}#1}}
\newcommand{\company}[1]{\textit{\color{secondary}#1}}
\newcommand{\duration}[1]{\hfill \textit{\color{secondary}#1}}
\newcommand{\contacticon}[1]{\makebox[1em]{\color{primary}#1}}

\begin{document}

% ===== HEADER =====
\begin{center}
    {\LARGE \textbf{\color{primary}{{name}}}}\\[0.2em]
    {\small
    \contacticon{\faMapMarker} {{location}} \quad \textbar \quad 
    \contacticon{\faEnvelope} \href{mailto:{{email}}}{{{email}}} \quad \textbar \quad 
    \contacticon{\faPhone} {{phone}}\\[0.2em]
    \contacticon{\faGlobe} \href{{{website}}}{{{website}}} \quad \textbar \quad 
    \contacticon{\faTwitter} {{twitter}} \quad \textbar \quad 
    \contacticon{\faGithub} {{github}}
    }
\end{center}

\vspace{0.5em}

% ===== SUMMARY =====
\noindent \textbf{\color{primary}Summary:} {{summary}}

% ===== EXPERIENCE =====
\section*{Experience}

{{#each experience}}
\resumeheading{{{position}}} \duration{{{duration}}} \\
\company{{{company}}} \\
\begin{itemize}
{{#each responsibilities}}
  \item {{this}}
{{/each}}
{{#if technologies}}
  \item Technologies: {{technologies}}
{{/if}}
\end{itemize}

{{/each}}

% ===== PROJECTS =====
\section*{Projects}

{{#each projects}}
\resumeheading{{{title}}} \\
\begin{itemize}
{{#each description}}
  \item {{this}}
{{/each}}
\end{itemize}

{{/each}}

% ===== EDUCATION =====
\section*{Education}

{{#each education}}
\resumeheading{{{institution}}} \\
{{degree}} {{#if status}}({{status}}){{/if}}

{{/each}}

% ===== SKILLS =====
\section*{Technical Skills}

\begin{itemize}
{{#each skills}}
  \item \textbf{{{category}}:} {{skills}}
{{/each}}
\end{itemize}

% ===== AWARDS =====
{{#if awards}}
\section*{Awards}

\begin{itemize}
{{#each awards}}
  \item \textbf{{{title}}} — {{organization}} {{#if date}}({{date}}){{/if}}
{{/each}}
\end{itemize}
{{/if}}

% ===== LANGUAGES =====
{{#if languages}}
\section*{Languages}

\begin{itemize}
{{#each languages}}
  \item {{language}} {{#if proficiency}}({{proficiency}}){{/if}}
{{/each}}
\end{itemize}
{{/if}}

% ===== INTERESTS =====
{{#if interests}}
\section*{Interests}

\begin{itemize}
{{#each interests}}
  \item {{this}}
{{/each}}
\end{itemize}
{{/if}}

% ===== HOBBIES =====
{{#if hobbies}}
\section*{Hobbies}

\begin{itemize}
{{#each hobbies}}
  \item {{this}}
{{/each}}
\end{itemize}
{{/if}}

% ===== REFERENCES =====
{{#if references}}
\section*{References}

\begin{itemize}
{{#each references}}
  \item \textbf{{{name}}, {{title}}, {{company}}:} ``{{quote}}''
{{/each}}
\end{itemize}
{{/if}}

\end{document}
    """

def format_latex_with_data(latex_template: str, resume_data: Dict[str, Any]) -> str:
    """
    Replace placeholders in LaTeX template with actual resume data
    Uses Handlebars-style templating for better control
    """
    formatted_latex = latex_template
    
    # Simple placeholder replacement for basic fields
    basic_fields = ['name', 'email', 'phone', 'location', 'website', 'twitter', 'github', 'summary']
    for field in basic_fields:
        value = resume_data.get(field, '')
        # Handle nested values for basics object
        if not value and 'basics' in resume_data:
            value = resume_data['basics'].get(field, '')
        # Escape special LaTeX characters
        value = escape_latex_special_chars(str(value))
        formatted_latex = formatted_latex.replace('{{' + field + '}}', value)
    
    # Handle arrays and complex structures
    formatted_latex = handle_experience_section(formatted_latex, resume_data.get('experience', []))
    formatted_latex = handle_projects_section(formatted_latex, resume_data.get('projects', []))
    formatted_latex = handle_education_section(formatted_latex, resume_data.get('education', []))
    formatted_latex = handle_skills_section(formatted_latex, resume_data.get('skills', []))
    formatted_latex = handle_awards_section(formatted_latex, resume_data.get('awards', []))
    formatted_latex = handle_languages_section(formatted_latex, resume_data.get('languages', []))
    formatted_latex = handle_interests_section(formatted_latex, resume_data.get('interests', []))
    formatted_latex = handle_hobbies_section(formatted_latex, resume_data.get('hobbies', []))
    formatted_latex = handle_references_section(formatted_latex, resume_data.get('references', []))
    
    return formatted_latex

def escape_latex_special_chars(text: str) -> str:
    """Escape special LaTeX characters"""
    if not text:
        return ""
    
    # Dictionary of LaTeX special characters and their escaped versions
    latex_special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '\\': r'\textbackslash{}'
    }
    
    for char, escaped in latex_special_chars.items():
        text = text.replace(char, escaped)
    
    return text

def handle_experience_section(latex: str, experience: list) -> str:
    """Handle experience section templating"""
    if not experience:
        # Remove the entire experience section if empty
        start_marker = '{{#each experience}}'
        end_marker = '{{/each}}'
        start_idx = latex.find(start_marker)
        end_idx = latex.find(end_marker, start_idx) + len(end_marker)
        if start_idx != -1 and end_idx != -1:
            return latex[:start_idx] + latex[end_idx:]
        return latex
    
    experience_text = ""
    for exp in experience:
        position = escape_latex_special_chars(exp.get('position', ''))
        company = escape_latex_special_chars(exp.get('company', ''))
        duration = escape_latex_special_chars(exp.get('duration', ''))
        
        exp_block = f"\\resumeheading{{{position}}} \\duration{{{duration}}} \\\\\n"
        exp_block += f"\\company{{{company}}} \\\\\n"
        exp_block += "\\begin{itemize}\n"
        
        # Add responsibilities
        responsibilities = exp.get('responsibilities', [])
        if isinstance(responsibilities, list):
            for resp in responsibilities:
                escaped_resp = escape_latex_special_chars(str(resp))
                exp_block += f"  \\item {escaped_resp}\n"
        elif isinstance(responsibilities, str):
            escaped_resp = escape_latex_special_chars(responsibilities)
            exp_block += f"  \\item {escaped_resp}\n"
        
        # Add technologies if present
        if exp.get('technologies'):
            tech = exp['technologies']
            if isinstance(tech, list):
                tech = ', '.join(str(t) for t in tech)
            tech = escape_latex_special_chars(str(tech))
            exp_block += f"  \\item Technologies: {tech}\n"
        
        exp_block += "\\end{itemize}\n\n"
        experience_text += exp_block
    
    # Replace the template section
    start_marker = '{{#each experience}}'
    end_marker = '{{/each}}'
    start_idx = latex.find(start_marker)
    end_idx = latex.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        return latex[:start_idx] + experience_text + latex[end_idx:]
    
    return latex

def handle_projects_section(latex: str, projects: list) -> str:
    """Handle projects section templating"""
    if not projects:
        # Remove the entire projects section if empty
        start_marker = '{{#each projects}}'
        end_marker = '{{/each}}'
        start_idx = latex.find(start_marker)
        end_idx = latex.find(end_marker, start_idx) + len(end_marker)
        if start_idx != -1 and end_idx != -1:
            return latex[:start_idx] + latex[end_idx:]
        return latex
    
    projects_text = ""
    for proj in projects:
        title = escape_latex_special_chars(proj.get('title', ''))
        proj_block = f"\\resumeheading{{{title}}} \\\\\n"
        proj_block += "\\begin{itemize}\n"
        
        descriptions = proj.get('description', [])
        if isinstance(descriptions, list):
            for desc in descriptions:
                escaped_desc = escape_latex_special_chars(str(desc))
                proj_block += f"  \\item {escaped_desc}\n"
        elif isinstance(descriptions, str):
            escaped_desc = escape_latex_special_chars(descriptions)
            proj_block += f"  \\item {escaped_desc}\n"
        
        proj_block += "\\end{itemize}\n\n"
        projects_text += proj_block
    
    # Replace the template section
    start_marker = '{{#each projects}}'
    end_marker = '{{/each}}'
    start_idx = latex.find(start_marker)
    end_idx = latex.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        return latex[:start_idx] + projects_text + latex[end_idx:]
    
    return latex

def handle_education_section(latex: str, education: list) -> str:
    """Handle education section templating"""
    if not education:
        start_marker = '{{#each education}}'
        end_marker = '{{/each}}'
        start_idx = latex.find(start_marker)
        end_idx = latex.find(end_marker, start_idx) + len(end_marker)
        if start_idx != -1 and end_idx != -1:
            return latex[:start_idx] + latex[end_idx:]
        return latex
    
    education_text = ""
    for edu in education:
        institution = escape_latex_special_chars(edu.get('institution', ''))
        degree = escape_latex_special_chars(edu.get('degree', ''))
        status = escape_latex_special_chars(edu.get('status', ''))
        
        edu_block = f"\\resumeheading{{{institution}}} \\\\\n"
        edu_block += f"{degree}"
        if status:
            edu_block += f" ({status})"
        edu_block += "\n\n"
        education_text += edu_block
    
    # Replace the template section
    start_marker = '{{#each education}}'
    end_marker = '{{/each}}'
    start_idx = latex.find(start_marker)
    end_idx = latex.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        return latex[:start_idx] + education_text + latex[end_idx:]
    
    return latex

def handle_skills_section(latex: str, skills: list) -> str:
    """Handle skills section templating"""
    if not skills:
        start_marker = '{{#each skills}}'
        end_marker = '{{/each}}'
        start_idx = latex.find(start_marker)
        end_idx = latex.find(end_marker, start_idx) + len(end_marker)
        if start_idx != -1 and end_idx != -1:
            return latex[:start_idx] + latex[end_idx:]
        return latex
    
    skills_text = ""
    for skill in skills:
        if isinstance(skill, dict):
            category = escape_latex_special_chars(skill.get('category', ''))
            skill_list = skill.get('skills', [])
            if isinstance(skill_list, list):
                skill_list = ', '.join(str(s) for s in skill_list if s)  # Filter out empty strings
            else:
                skill_list = str(skill_list)
            skill_list = escape_latex_special_chars(skill_list)
            if skill_list:  # Only add if there are actual skills
                skills_text += f"  \\item \\textbf{{{category}:}} {skill_list}\n"
        elif isinstance(skill, str):
            escaped_skill = escape_latex_special_chars(skill)
            skills_text += f"  \\item {escaped_skill}\n"
    
    # Replace the template section
    start_marker = '{{#each skills}}'
    end_marker = '{{/each}}'
    start_idx = latex.find(start_marker)
    end_idx = latex.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        return latex[:start_idx] + skills_text + latex[end_idx:]
    
    return latex

def handle_awards_section(latex: str, awards: list) -> str:
    """Handle awards section templating"""
    if not awards:
        # Remove the entire awards section
        start_marker = '{{#if awards}}'
        end_marker = '{{/if}}'
        start_idx = latex.find(start_marker)
        end_idx = latex.find(end_marker, start_idx) + len(end_marker)
        if start_idx != -1 and end_idx != -1:
            return latex[:start_idx] + latex[end_idx:]
        return latex
    
    awards_text = "\\section*{Awards}\n\n\\begin{itemize}\n"
    for award in awards:
        title = escape_latex_special_chars(award.get('title', ''))
        organization = escape_latex_special_chars(award.get('organization', ''))
        date = escape_latex_special_chars(award.get('date', ''))
        
        award_text = f"  \\item \\textbf{{{title}}}"
        if organization:
            award_text += f" — {organization}"
        if date:
            award_text += f" ({date})"
        award_text += "\n"
        awards_text += award_text
    awards_text += "\\end{itemize}\n"
    
    # Replace the template section
    start_marker = '{{#if awards}}'
    end_marker = '{{/if}}'
    start_idx = latex.find(start_marker)
    end_idx = latex.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        return latex[:start_idx] + awards_text + latex[end_idx:]
    
    return latex

def handle_languages_section(latex: str, languages: list) -> str:
    """Handle languages section templating"""
    if not languages:
        # Remove the entire languages section
        start_marker = '{{#if languages}}'
        end_marker = '{{/if}}'
        start_idx = latex.find(start_marker)
        end_idx = latex.find(end_marker, start_idx) + len(end_marker)
        if start_idx != -1 and end_idx != -1:
            return latex[:start_idx] + latex[end_idx:]
        return latex
    
    languages_text = "\\section*{Languages}\n\n\\begin{itemize}\n"
    for lang in languages:
        if isinstance(lang, dict):
            language = escape_latex_special_chars(lang.get('language', ''))
            proficiency = escape_latex_special_chars(lang.get('proficiency', ''))
            lang_text = f"  \\item {language}"
            if proficiency:
                lang_text += f" ({proficiency})"
            lang_text += "\n"
        else:
            lang_text = f"  \\item {escape_latex_special_chars(str(lang))}\n"
        languages_text += lang_text
    languages_text += "\\end{itemize}\n"
    
    # Replace the template section
    start_marker = '{{#if languages}}'
    end_marker = '{{/if}}'
    start_idx = latex.find(start_marker)
    end_idx = latex.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        return latex[:start_idx] + languages_text + latex[end_idx:]
    
    return latex

def handle_interests_section(latex: str, interests: list) -> str:
    """Handle interests section templating"""
    if not interests:
        # Remove the entire interests section
        start_marker = '{{#if interests}}'
        end_marker = '{{/if}}'
        start_idx = latex.find(start_marker)
        end_idx = latex.find(end_marker, start_idx) + len(end_marker)
        if start_idx != -1 and end_idx != -1:
            return latex[:start_idx] + latex[end_idx:]
        return latex
    
    interests_text = "\\section*{Interests}\n\n\\begin{itemize}\n"
    for interest in interests:
        escaped_interest = escape_latex_special_chars(str(interest))
        interests_text += f"  \\item {escaped_interest}\n"
    interests_text += "\\end{itemize}\n"
    
    # Replace the template section
    start_marker = '{{#if interests}}'
    end_marker = '{{/if}}'
    start_idx = latex.find(start_marker)
    end_idx = latex.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        return latex[:start_idx] + interests_text + latex[end_idx:]
    
    return latex

def handle_hobbies_section(latex: str, hobbies: list) -> str:
    """Handle hobbies section templating"""
    if not hobbies:
        # Remove the entire hobbies section
        start_marker = '{{#if hobbies}}'
        end_marker = '{{/if}}'
        start_idx = latex.find(start_marker)
        end_idx = latex.find(end_marker, start_idx) + len(end_marker)
        if start_idx != -1 and end_idx != -1:
            return latex[:start_idx] + latex[end_idx:]
        return latex
    
    hobbies_text = "\\section*{Hobbies}\n\n\\begin{itemize}\n"
    for hobby in hobbies:
        escaped_hobby = escape_latex_special_chars(str(hobby))
        hobbies_text += f"  \\item {escaped_hobby}\n"
    hobbies_text += "\\end{itemize}\n"
    
    # Replace the template section
    start_marker = '{{#if hobbies}}'
    end_marker = '{{/if}}'
    start_idx = latex.find(start_marker)
    end_idx = latex.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        return latex[:start_idx] + hobbies_text + latex[end_idx:]
    
    return latex

def handle_references_section(latex: str, references: list) -> str:
    """Handle references section templating"""
    if not references:
        # Remove the entire references section
        start_marker = '{{#if references}}'
        end_marker = '{{/if}}'
        start_idx = latex.find(start_marker)
        end_idx = latex.find(end_marker, start_idx) + len(end_marker)
        if start_idx != -1 and end_idx != -1:
            return latex[:start_idx] + latex[end_idx:]
        return latex
    
    references_text = "\\section*{References}\n\n\\begin{itemize}\n"
    for ref in references:
        name = escape_latex_special_chars(ref.get('name', ''))
        title = escape_latex_special_chars(ref.get('title', ''))
        company = escape_latex_special_chars(ref.get('company', ''))
        quote = escape_latex_special_chars(ref.get('quote', ''))
        
        ref_text = f"  \\item \\textbf{{{name}, {title}, {company}:}} ``{quote}''\n"
        references_text += ref_text
    references_text += "\\end{itemize}\n"
    
    # Replace the template section
    start_marker = '{{#if references}}'
    end_marker = '{{/if}}'
    start_idx = latex.find(start_marker)
    end_idx = latex.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        return latex[:start_idx] + references_text + latex[end_idx:]
    
    return latex

# Example usage and testing endpoint
@resume_router.get("/test-format")
async def test_latex_formatting():
    """Test endpoint to show how the formatting works"""
    
    sample_resume_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "location": "New York, NY",
        "website": "https://johndoe.com",
        "twitter": "@johndoe",
        "github": "@johndoe",
        "summary": "Full stack developer with 5+ years of experience building scalable web applications.",
        "experience": [
            {
                "position": "Senior Software Engineer",
                "company": "Tech Corp",
                "duration": "2020 — Present",
                "responsibilities": [
                    "Built scalable web applications using React and Node.js",
                    "Led team of 3 developers on major product features"
                ],
                "technologies": ["React", "Node.js", "PostgreSQL"]
            }
        ],
        "projects": [
            {
                "title": "Open Source Library",
                "description": [
                    "Created a popular JavaScript library with 1000+ GitHub stars",
                    "Used by major companies in production"
                ]
            }
        ],
        "education": [
            {
                "institution": "University of Technology",
                "degree": "Bachelor of Computer Science",
                "status": "completed"
            }
        ],
        "skills": [
            {
                "category": "Frontend",
                "skills": ["React", "Vue.js", "JavaScript", "TypeScript"]
            },
            {
                "category": "Backend", 
                "skills": ["Node.js", "Python", "PostgreSQL", "MongoDB"]
            }
        ],
        "awards": [],
        "languages": [],
        "interests": [],
        "hobbies": [],
        "references": []
    }
    
    formatted = format_latex_with_data(get_latex_template(), sample_resume_data)
    
    return {
        "sample_data": sample_resume_data,
        "formatted_result": formatted
    }