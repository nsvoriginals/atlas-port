# THIS SERVICE HANDLES INTERVIEW QUESTION GENERATION USING GROQ API
from groq import Groq
import os
from fastapi import HTTPException
from typing import Dict, Any, List
import json
import re

# INITIALIZE THE GROQ CLIENT
groq_client = Groq(api_key=os.getenv("GROQ_API"))

# MAIN FUNCTION TO GENERATE INTERVIEW QUESTIONS
async def generate_interview_questions(
    resume_data: Dict[str, Any],
    job_role: str,
    experience: str,
    topics: str = ""
) -> Dict[str, Any]:
    """
    Generate interview questions based on resume data, job role, and experience level.
    Uses Groq API instead of OpenAI.
    """
    try:
        # Extract relevant information from resume
        skills = []
        if "skills" in resume_data:
            for skill in resume_data["skills"]:
                if "keywords" in skill:
                    skills.extend(skill["keywords"])
        
        # Get projects information
        projects = []
        if "projects" in resume_data:
            for project in resume_data["projects"]:
                if "name" in project and project["name"]:
                    project_info = project["name"]
                    if "description" in project and project["description"]:
                        project_info += f": {project['description']}"
                    projects.append(project_info)
        
        # Create a simplified representation of the resume for the prompt
        resume_summary = {
            "name": resume_data.get("basics", {}).get("name", ""),
            "skills": skills,
            "projects": projects,
            "education": [edu.get("institution", "") for edu in resume_data.get("education", []) if "institution" in edu]
        }
        
        # Create the user message with all the required information
        user_message = f"""Generate 15 interview questions for this candidate.
Job Role: {job_role}
Experience Level: {experience}
Focus Topics: {topics}

Resume Summary:
{json.dumps(resume_summary, indent=2)}
"""

        # Create the system message with instructions on expected JSON format
        system_message = f"""You are an expert technical interviewer for {job_role} positions.
Generate interview questions for a {experience} level {job_role} candidate.
Topics to focus on: {topics if topics else 'General technical skills related to the role'}
The questions should be based on the candidate's resume and the job requirements.

Format the response as valid JSON with the following structure:
{{
  "candidate_profile": {{
    "experience_level": string,
    "key_skills": [string],  
    "primary_domain": string,
    "years_of_experience": string
  }},
  "interview_questions": [
    {{
      "id": number,
      "question": string,
      "expected_answer": string,
      "difficulty": "easy"|"medium"|"hard",
      "type": "technical"|"behavioral",
      "skill_tested": string
    }}
  ]
}}

IMPORTANT:
- Ensure ALL generated JSON is correctly formatted, with proper syntax and no missing fields.
- Each question MUST have ALL fields specified in the structure above.
- Each question MUST include "id", "question", "expected_answer", "difficulty", "type", and "skill_tested".
- The "difficulty" field MUST be one of: "easy", "medium", or "hard".
- The "type" field MUST be one of: "technical" or "behavioral".
"""

        # Make the API call to Groq
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
            response_format={"type": "json_object"}
        )
        
        # Extract and parse the generated content
        content = chat_completion.choices[0].message.content
        
        # Validate and potentially fix the JSON
        try:
            questions_data = json.loads(content)
            return questions_data
        except json.JSONDecodeError:
            # Attempt to fix common JSON issues
            fixed_json = fix_json_syntax(content)
            try:
                questions_data = json.loads(fixed_json)
                return questions_data
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON even after fixing: {str(e)}")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating interview questions: {str(e)}")

# FUNCTION TO FIX COMMON JSON SYNTAX ISSUES
def fix_json_syntax(json_str: str) -> str:
    """
    Attempt to fix common JSON syntax issues in model output.
    """
    import re

    # Remove markdown formatting
    json_str = re.sub(r'```(?:json)?|```', '', json_str).strip()

    # Replace unkeyed difficulty values with valid key-value pairs
    json_str = re.sub(r'\n\s*"?(easy|medium|hard)"?,?', r'\n"difficulty": "\1",', json_str)

    # Replace unkeyed type values with valid key-value pairs
    json_str = re.sub(r'\n\s*"?(technical|behavioral)"?,?', r'\n"type": "\1",', json_str)

    # Ensure all objects have correct commas between fields
    json_str = re.sub(r'(":[^"]*")(\s*")', r'\1,\2', json_str)

    # Remove trailing commas before closing braces/brackets
    json_str = re.sub(r',\s*([\]}])', r'\1', json_str)

    return json_str
