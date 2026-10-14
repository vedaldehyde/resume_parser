import json
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from ai_service import AIService
from logger import log
from parser_service import ParserService
from schema import JobDescription, MatchResult, Resume

# Load environment variables relative to this file's directory
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class ResumeParser:
    """Service to parse resumes and evaluate them against job descriptions."""

    def __init__(self, api_key: str | None = None, model: str | None = None, job_description: JobDescription | None = None, resumes_folder: Path | str | None = None, log_file: Path | str | None = None,):
        self.api_key = api_key or os.getenv("GROC_API_KEY")
        self.model = model or os.getenv("GROC_MODEL")
        if not self.api_key:
            raise ValueError("API key not found. Please set GROC_API_KEY in .env or pass it to ResumeParser.")
        if not self.model:
            raise ValueError("Model not found. Please set GROC_MODEL in .env or pass it to ResumeParser.")

        self.client = Groq(api_key=self.api_key)
        self.ai_service = AIService()

        self.resumes_folder = Path(resumes_folder) if resumes_folder else BASE_DIR / "resumes"
        self.log_file = Path(log_file) if log_file else BASE_DIR / "processed_log.txt"
        self.file_parser = ParserService(self.resumes_folder, self.log_file)

        self.resume_schema = Resume.model_json_schema()
        self.match_schema = MatchResult.model_json_schema()
        self.job_schema = JobDescription.model_json_schema()

        self.job_description = job_description or self._default_job_description()
        self.all_results: list[dict] = []

        self.system_prompt = self._build_system_prompt()
        self.message_system = {
            "role": "system",
            "content": self.system_prompt,
        }

    @staticmethod
    def _default_job_description() -> JobDescription:
        """Returns a default job description if none is provided."""
        return JobDescription(
            role="Software Engineer",
            required_skills=["Python", "SQL"],
            preffered_skills=["Java", "C++", ".NET Core"],
            minimum_experience=1.0,
            education_requirements=["Bachelor's degree in Computer Science or related field"],
            responsiblities=[
                "Develop and maintain software applications",
                "Write clean, readable, and maintainable code",
                "Collaborate with cross-functional teams",
            ],
        )

    def _build_system_prompt(self) -> str:
        return (
            "You are an expert resume parser.\n"
            "Extract information from the resume based on its semantic meaning, not only based on exact section headings.\n\n"
            "Sections such as Experience, Professional History, Work History, Employment, and Internships "
            "may all contain relevant experience.\n"
            "Skills may appear in the skills section, work experience, internships, or projects.\n\n"
            f"Return ONLY valid JSON matching this schema:\n{json.dumps(self.resume_schema, indent=2)}\n\n"
            "Important rules:\n"
            "1. Do not invent information.\n"
            "2. If a value is not available, return null.\n"
            "3. If a list has no information, return an empty list.\n"
            "4. Include internships inside experiences.\n"
            "5. Extract skills mentioned across the entire resume."
        )

    def get_resume_text(self) -> list[str]:
        """Extracts text content from unread resume files."""
        return self.file_parser.process_folder()

    def parse_single_resume(self, text: str) -> Resume:
        """Sends resume text to the AI model and parses the response into a Resume model."""
        user_prompt = f"Parse the following resume:\n{text}"
        message_user = {
            "role": "user",
            "content": user_prompt,
        }

        data = self.ai_service.call_ai_model_with_json(
            client=self.client,
            model=self.model,
            message=message_user,
            system_message=self.message_system,
        )

        if "experiences" not in data or data["experiences"] is None:
            data["experiences"] = []

        return Resume(**data)

    def final_score(self, job: JobDescription | dict | str, resume: Resume | dict | str,) -> MatchResult:
        """Compares a candidate's resume against the job description and computes a score."""
        if hasattr(job, "model_dump_json"):
            job_text = job.model_dump_json(indent=2)
        elif isinstance(job, (dict, list)):
            job_text = json.dumps(job, indent=2)
        else:
            job_text = str(job)

        if hasattr(resume, "model_dump_json"):
            resume_text = resume.model_dump_json(indent=2)
        elif isinstance(resume, (dict, list)):
            resume_text = json.dumps(resume, indent=2)
        else:
            resume_text = str(resume)

        prompt = (
            "You are an HR recruiter.\n"
            "Compare the candidate's resume with the job description.\n\n"
            f"JOB DESCRIPTION:\n{job_text}\n\n"
            f"CANDIDATE RESUME:\n{resume_text}\n\n"
            "Return JSON matching this schema:\n"
            f"{json.dumps(self.match_schema, indent=2)}\n\n"
            "Requirements:\n"
            "1. 'score': Overall match percentage from 0 to 100 (number).\n"
            "2. 'details': An object containing:\n"
            "   - 'candidate_name': Candidate name\n"
            "   - 'matching_skills': List of matching skills\n"
            "   - 'missing_skills': List of missing important skills\n"
            "   - 'experience_requirement_met': Whether experience requirement is met (boolean)\n"
            "   - 'verdict': A short final verdict\n\n"
            "Keep the response concise and strictly adhere to the schema."
        )

        message = {
            "role": "user",
            "content": prompt,
        }
        data = self.ai_service.call_ai_model_with_json(
            client=self.client,
            model=self.model,
            message=message,
        )

        score = data.get("score")
        if score is None:
            score = data.get("overall_match_percentage", data.get("match_percentage", 0.0))

        details = data.get("details")
        if details is None or not isinstance(details, dict):
            details = {k: v for k, v in data.items() if k not in ("score", "overall_match_percentage")}

        return MatchResult(score=float(score), details=details)

    def get_resume_json(self, job: JobDescription | None = None) -> list[Resume]:
        """Processes all pending resumes, parses them, and scores them against the job description."""
        resume_texts = self.get_resume_text()
        if not resume_texts:
            log("No new resumes to process.")
            self.all_results = []
            return []

        target_job = job or self.job_description
        resumes: list[Resume] = []
        all_results: list[dict] = []

        log(f"\nProcessing {len(resume_texts)} new resume(s)...")

        for idx, text in enumerate(resume_texts, start=1):
            log(f"[{idx}/{len(resume_texts)}] Parsing resume...")
            resume_data = self.parse_single_resume(text)
            resumes.append(resume_data)

            candidate_name = resume_data.name or f"Candidate {idx}"
            log(f"[{idx}/{len(resume_texts)}] Evaluating {candidate_name} against job description...")
            result = self.final_score(job=target_job, resume=resume_data)
            log(f"[{idx}/{len(resume_texts)}] Score: {result.score}%")

            all_results.append({
                "name": candidate_name,
                "email": resume_data.email,
                "score": result.score,
                "details": result.details,
            })

        all_results.sort(key=lambda candidate: candidate["score"], reverse=True)
        self.all_results = all_results

        log("\n" + "=" * 55)
        log(f"{'CANDIDATE RANKINGS':^55}")
        log("=" * 55)
        for rank, candidate in enumerate(all_results, start=1):
            log(f"{rank}. {candidate['name']} - Score: {candidate['score']}%")
            verdict = candidate["details"].get("verdict")
            if verdict:
                log(f"   Verdict: {verdict}")
        log("=" * 55 + "\n")

        return resumes


# Backward compatibility alias
ResumerParser = ResumeParser

