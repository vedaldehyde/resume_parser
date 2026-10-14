# AI Resume Parser & Shortlisting Worker Service

An intelligent, automated resume parsing and candidate evaluation service powered by **Groq LLMs** and **Pydantic**. 

The service operates as a continuous background worker that monitors a designated folder for incoming resumes, extracts candidate information into structured data models, evaluates candidates against job descriptions, and automatically emails interview invitations to candidates scoring above a target threshold (e.g., > 70%).

---

## 🚀 Features

- **Multi-Format Extraction**: Parses resumes in `.pdf`, `.docx`, and `.txt` formats without losing structure or table contents.
- **Semantic Information Extraction**: Uses Groq-hosted open-weight LLMs (`openai/gpt-oss-20b`) to extract contact information, skills, experience, education, and projects into strongly validated Pydantic models.
- **Candidate Evaluation & Scoring**: Computes a match percentage score (0–100%) against customizable job requirements and provides a verdict with matching/missing skills.
- **Automated Worker Pipeline**: Continuously scans the `resumes/` folder at configurable intervals and skips already-processed files to avoid duplicate processing.
- **Email Automation**: Automatically sends interview invitation emails via SMTP (SSL/TLS) to candidates matching over 70%, with a safe simulation mode if SMTP credentials are not yet configured.

---

## 📁 Project Structure

```text
resume_parser/
├── resumes/                 # Folder where incoming resumes are placed
│   └── .gitkeep
├── ai_service.py            # Groq API client with structured JSON enforcement
├── parser_service.py        # File readers for PDF, DOCX, and TXT files
├── schema.py                # Pydantic schemas (Resume, JobDescription, MatchResult)
├── resume_parser.py         # Main ResumeParser pipeline and scoring engine
├── email_service.py         # SMTP email dispatcher with simulation fallback
├── main.py                  # Continuous worker service entry point
├── requirements.txt         # Project dependencies
├── .env.example             # Example environment configuration
└── .gitignore               # Git rules protecting secrets and local state
```

---

## 🛠️ Getting Started

### 1. Prerequisites
- **Python 3.10+**
- A **Groq API Key** (get one at [console.groq.com](https://console.groq.com/))
- (Optional) A **Google App Password** if you wish to send live emails via Gmail SMTP.

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/resume_parser.git
cd resume_parser
```

### 3. Set Up a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

*(Note for macOS users: If you experience SSL certificate errors, run `/Applications/Python\ 3.x/Install\ Certificates.command` or ensure `certifi` is installed).*

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:
```env
# Required
GROC_API_KEY=gsk_your_groq_api_key
GROC_MODEL=openai/gpt-oss-20b

# Worker Polling & Email Threshold
SCAN_INTERVAL_SECONDS=10
MATCH_THRESHOLD=70.0

# Optional SMTP Settings (leave empty for simulation mode)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_16_character_app_password
SENDER_EMAIL=your_email@gmail.com
```

> **Note on Gmail SMTP**: Standard Google passwords are not supported for SMTP. You must create a 16-character **App Password** from [Google Security - App Passwords](https://myaccount.google.com/apppasswords).

---

## 🖥️ Running the Worker Service

Start the background worker:
```bash
python main.py
```

1. The service will begin monitoring the `resumes/` folder.
2. Drop candidate resumes (`.pdf`, `.docx`, or `.txt`) into the `resumes/` folder.
3. The worker detects new files, parses their contents, evaluates candidates, prints candidate rankings to the terminal, and sends invitation emails to candidates who score above the threshold.
4. Press `Ctrl+C` to stop the worker at any time.

---

## ⚙️ How Candidate Scoring Works

Each candidate's structured resume is evaluated against a `JobDescription`:
- **Role & Minimum Experience**: Evaluated against candidate's work history.
- **Skills Match**: Compares mandatory (`required_skills`) and optional (`preffered_skills`).
- **Verdict & Score**: The AI model returns a score between 0 and 100 along with detailed matching analysis.

---

## 🔒 Security Best Practices

- **Never commit `.env`**: Contains sensitive API keys and SMTP credentials. The included `.gitignore` protects it by default.
- **Personal Resumes**: The `.gitignore` file ignores documents in `resumes/` to prevent personal candidate data from being exposed publicly.

