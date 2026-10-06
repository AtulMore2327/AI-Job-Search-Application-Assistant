# 10X AI Job Search & Application Assistant

A portfolio-quality, production-grade AI Job Search & Application Assistant built with Python, FastAPI, Groq, Tavily, Pydantic, and SQLite.

---

## 🌟 Key Features

1. **Resume Parser & Analyzer:** PDF text extraction (`pypdf`) with Groq LLM profile structuring (Candidate Profile, Education, Skills, Tools, Projects, Certifications).
2. **Multi-Platform Search Engine:** Dynamic query builder executing searches across public sources (LinkedIn, Naukri, Indeed, Glassdoor, Internshala, Shine, etc.).
3. **URL Classification & Filter:** Filters generic listing/search pages from true individual job postings.
4. **Cross-Platform Deduplication:** Deduplicates identical job postings across multiple platforms using `rapidfuzz` fuzzy matching and URL canonicalization.
5. **JD Extraction & Enrichment:** Extracts structured requirements, responsibilities, and qualifications.
6. **Deterministic Resume-JD Matcher:** Weighted scoring (Skills 45%, Experience 20%, Education 10%, Projects 15%, Keywords 10%) providing explainable match percentages.
7. **Skill Gap Analysis:** Categorizes skills into matched, partially matched, missing must-have, and missing nice-to-have.
8. **Personalized Application Writer:** Generates authentic, editable Cover Letters, HR Email bodies, Email subjects, and LinkedIn recruiter messages without fabricating facts.
9. **SQLite Database & Application Tracker:** Persistent storage of candidate profiles, search runs, matches, and job application status tracking.
10. **Modern Web Dashboard UI:** Sleek glassmorphism UI with real-time statistics, tabbed navigation, and interactive application management.

---

## 🏗️ Project Architecture

```text
AI_Job_Search_Application/
├── app/
│   ├── main.py                  # FastAPI Entry Point
│   ├── config.py                # Environment & Settings
│   ├── api/                     # REST API Routes (Resume, Jobs, Match, Application)
│   ├── models/                  # Pydantic Schemas (Candidate, Job, Match, Application)
│   ├── services/                # Business Logic (Analyzer, Deduplicator, Matcher, Writer, Pipeline)
│   ├── platforms/               # Search Adapters (Tavily, Base Adapters)
│   ├── database/                # SQLite Connection & Repositories
│   └── utils/                   # Text, URL, Logging & Retry Helpers
├── docs/
│   ├── project_brief.md         # Full Project Brief Documentation
│   └── problem_statement_doc.md # Comprehensive Problem Statements
├── frontend/
│   └── index.html               # Interactive Dashboard UI
├── tests/                       # Automated Pytest Suite
├── .env.example                 # Environment Variable Schema
├── requirements.txt             # Project Dependencies
├── run.py                       # Server Launch Script
└── README.md                    # Documentation
```

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
cd C:\Users\ASUS\.gemini\antigravity-ide\scratch\AI_Job_Search_Application
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
DEMO_MODE=false
DATABASE_PATH=data/job_search.db
PORT=8000
```

*(Note: If API keys are left blank, the system automatically runs in **DEMO MODE** with high-quality sample datasets.)*

### 3. Run Application Server

```bash
python run.py
```

- **Web Dashboard:** Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.
- **API Swagger Docs:** Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 🧪 Running Unit Tests

Execute the automated test suite with `pytest`:

```bash
pytest tests/test_text_and_urls.py tests/test_url_classifier.py tests/test_deduplicator.py tests/test_matcher_and_skill_gap.py tests/test_database_and_pipeline.py -v
```

---

## 🔒 Security & Access Guidelines

- Permitted public search methods only.
- No CAPTCHA or security control bypasses.
- Safe API key handling via `.env`.
- Explicit user approval required for job applications.
