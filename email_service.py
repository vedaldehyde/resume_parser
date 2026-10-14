import os
from pathlib import Path
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

from logger import log

# Load environment variables relative to this file's directory
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class EmailService:
    """Service to handle emailing shortlisted candidates based on match score."""

    def __init__(self, smtp_host: str | None = None, smtp_port: int | None = None, smtp_user: str | None = None, smtp_password: str | None = None, sender_email: str | None = None, use_tls: bool = True,):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.sender_email = (
            sender_email
            or os.getenv("SENDER_EMAIL")
            or self.smtp_user
            or "recruitment@example.com"
        )
        self.use_tls = use_tls

        # Check if real SMTP credentials are configured
        self.is_configured = bool(self.smtp_host and self.smtp_user and self.smtp_password)

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Sends an email via SMTP if configured, or logs the email in simulation mode."""
        if not self.is_configured:
            log("\n" + "-" * 55)
            log("📧 [EMAIL SIMULATION - SMTP not configured in .env]")
            log(f"To:      {to_email}")
            log(f"From:    {self.sender_email}")
            log(f"Subject: {subject}")
            log("Body:")
            log(body.strip())
            log("-" * 55 + "\n")
            return True

        import ssl
        try:
            import certifi
            context = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            context = ssl.create_default_context()

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = to_email
        msg.set_content(body)

        port = int(self.smtp_port)

        def _perform_send(ssl_ctx):
            if port == 465:
                # Direct SSL (Port 465)
                with smtplib.SMTP_SSL(self.smtp_host, port, context=ssl_ctx, timeout=20) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # STARTTLS (Port 587)
                with smtplib.SMTP(self.smtp_host, port, timeout=20) as server:
                    server.ehlo()
                    if self.use_tls:
                        server.starttls(context=ssl_ctx)
                        server.ehlo()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

        try:
            _perform_send(context)
            log(f"✅ Email sent successfully to {to_email}")
            return True
        except (ssl.SSLCertVerificationError, ssl.SSLError) as e:
            # Common on macOS when Python certificates are not installed in OpenSSL
            log(f"⚠️ SSL certificate verification failed: {e}. Retrying with unverified context...")
            try:
                unverified_context = ssl._create_unverified_context()
                _perform_send(unverified_context)
                log(f"✅ Email sent successfully to {to_email} (via fallback SSL)")
                return True
            except Exception as retry_err:
                log(f"❌ Failed to send email to {to_email}: {retry_err}")
                return False
        except smtplib.SMTPAuthenticationError as e:
            log(f"❌ Failed to send email to {to_email}: Authentication failed ({e}).")
            log("   👉 Note: For Gmail, you must use a 16-character 'App Password', NOT your personal account password.")
            log("   Generate one at: https://myaccount.google.com/apppasswords")
            return False
        except Exception as e:
            if "certificate verify failed" in str(e).lower():
                log(f"⚠️ SSL certificate verification failed: {e}. Retrying with unverified context...")
                try:
                    unverified_context = ssl._create_unverified_context()
                    _perform_send(unverified_context)
                    log(f"✅ Email sent successfully to {to_email} (via fallback SSL)")
                    return True
                except Exception as retry_err:
                    log(f"❌ Failed to send email to {to_email}: {retry_err}")
                    return False

            log(f"❌ Failed to send email to {to_email}: {e}")
            if "unexpectedly closed" in str(e).lower():
                log("   👉 Tip: Port 587 may be blocked by your network/ISP, or Google dropped the connection due to credentials.")
                log("   Try setting in your .env:")
                log("     SMTP_PORT=465")
                log("   And make sure SMTP_PASSWORD is a Google 16-character App Password.")
            return False

    def send_shortlist_invitation(self, candidate_name: str, candidate_email: str | None, score: float, role: str = "Software Engineer", details: dict | None = None,) -> bool:
        """Sends an interview invitation email to a candidate whose match score meets the threshold."""
        if not candidate_email:
            log(f"⚠️ Cannot send email to '{candidate_name}': No email address found on resume.")
            return False

        subject = f"Interview Invitation - {role} Role"

        verdict_text = ""
        if details and isinstance(details, dict):
            verdict = details.get("verdict")
            if verdict:
                verdict_text = f"\nEvaluation Highlights: {verdict}\n"

        body = f"""Dear {candidate_name},
            Thank you for your interest in the {role} position.

            We recently reviewed your resume and were very impressed with your background and qualifications (Resume Match Score: {score:.1f}%).{verdict_text}
            We would like to invite you for an interview to discuss how your skills align with our team's current goals.

            Please reply to this email with your availability over the upcoming days so we can schedule a convenient time for a call.

            We look forward to speaking with you!

            Best regards,
            Hiring Team
            """
        return self.send_email(to_email=candidate_email, subject=subject, body=body)

    def process_shortlisted_candidates(self, candidates: list[dict], threshold: float = 70.0, role: str = "Software Engineer",) -> list[dict]:
        """Filters candidates whose score > threshold and sends them an invitation."""
        shortlisted = [c for c in candidates if c.get("score", 0.0) > threshold]

        if not shortlisted:
            log(f"No candidates scored above {threshold}%. No emails sent.")
            return []

        log(f"\nFound {len(shortlisted)} candidate(s) with match score > {threshold}%:")
        sent = []
        for candidate in shortlisted:
            name = candidate.get("name", "Candidate")
            email = candidate.get("email")
            score = candidate.get("score", 0.0)
            details = candidate.get("details", {})

            success = self.send_shortlist_invitation(
                candidate_name=name,
                candidate_email=email,
                score=score,
                role=role,
                details=details,
            )
            if success:
                sent.append(candidate)

        return sent

