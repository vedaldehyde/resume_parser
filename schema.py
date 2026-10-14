from pydantic import BaseModel

class JobDescription(BaseModel):
    role: str
    required_skills: list[str]
    preffered_skills: list[str]
    minimum_experience: float | None
    education_requirements: list[str]
    responsiblities: list[str]

class MatchResult(BaseModel):
    score: float
    details: dict

class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None
    description: str | None = None
    skills_used: list[str] = []

class Resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience_years : float | None = None
    skills: list[str] = []
    experiences: list[Experience]
    education: list[str] = []
    projects: list[str] = []
    certifications: list[str] = []