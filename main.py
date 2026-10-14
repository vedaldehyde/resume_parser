import os
from pathlib import Path
import time

from dotenv import load_dotenv

from email_service import EmailService
from logger import log
from resume_parser import ResumeParser

# Load environment variables relative to this file's directory
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def run_worker(
    poll_interval: int = 10,
    match_threshold: float = 70.0,
):
    """Worker service that continuously scans the resumes folder and emails shortlisted candidates."""
    api_key = os.getenv("GROC_API_KEY")
    model = os.getenv("GROC_MODEL")

    parser = ResumeParser(api_key=api_key, model=model)
    email_service = EmailService()

    log("=" * 60)
    log("🚀 Resume Parser Worker Service Started")
    log(f"   - Monitoring folder : {parser.resumes_folder}")
    log(f"   - Polling interval  : {poll_interval}s")
    log(f"   - Email threshold   : > {match_threshold}%")
    log("   - Press Ctrl+C to stop")
    log("=" * 60)

    try:
        while True:
            # 1. Scan for and process any new resumes
            extracted_resumes = parser.get_resume_json()

            # 2. If new resumes were processed, notify candidates scoring > threshold
            if extracted_resumes and parser.all_results:
                log(f"\nChecking candidates for email notifications (score > {match_threshold}%)...")
                job_role = (
                    parser.job_description.role
                    if parser.job_description
                    else "Software Engineer"
                )
                email_service.process_shortlisted_candidates(
                    candidates=parser.all_results,
                    threshold=match_threshold,
                    role=job_role,
                )

            # 3. Wait before checking again
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        log("\nWorker service stopped by user.")


def main():
    poll_interval = int(os.getenv("SCAN_INTERVAL_SECONDS", 10))
    match_threshold = float(os.getenv("MATCH_THRESHOLD", 70.0))
    run_worker(poll_interval=poll_interval, match_threshold=match_threshold)


if __name__ == "__main__":
    main()