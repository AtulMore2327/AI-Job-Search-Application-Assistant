# GitHub Code Explanation Guide (Hindi & English)

## Project Title: 10X AI Job Search & Application Assistant

Ye document aapko GitHub par mojood is pooray project ki **File-by-File** aur **Module-by-Module** working samjhane ke liye banaya gaya hai.

---

## 🏗️ 1. High-Level Flow (Project Kaise Kaam Karta Hai?)

```
[ User (Dashboard UI / Login) ]
              │
              ▼
    [ FastAPI Backend (app/main.py) ]
        ├── 1. Resume Upload  ──► [ PyPDF + Groq LLM (resume_analyzer.py) ]
        ├── 2. Job Search     ──► [ Tavily Search (tavily_search.py) + Deduplicator ]
        ├── 3. Match Engine   ──► [ Weighted Scoring (matcher.py) + Skill Gap ]
        ├── 4. Content Writer ──► [ Groq AI Application Writer (application_writer.py) ]
        └── 5. Database       ──► [ SQLite Database (db.py) ]
```

---

## 📁 2. Directory Structure & File Explanation

### 🟢 `app/` Directory (Backend Logic)

#### A. Core Setup Files
1. **`app/main.py`**
   - **Kaam:** FastAPI application ka entry point.
   - **Details:** Yeh file server chalu karti hai, CORS allow karti hai, saare API routes include karti hai, aur `frontend/index.html` dashboard ko browser me serve karti hai.

2. **`app/config.py`**
   - **Kaam:** Configuration & Environment settings.
   - **Details:** `.env` file se API keys (`GROQ_API_KEY`, `TAVILY_API_KEY`) aur `DATABASE_PATH` load karta hai. Agar keys na milen, to system automatic **DEMO MODE** me shift ho jata hai.

#### B. API Controllers (`app/api/`)
1. **`routes_resume.py`**: Candidate ka PDF resume upload aur parse karne ka endpoint (`/api/resume/upload`).
2. **`routes_jobs.py`**: LinkedIn, Naukri, Indeed, Glassdoor aadi par jobs search karne aur URL classify karne ke endpoints.
3. **`routes_match.py`**: Candidate profile aur Job Description (JD) ka **Match Score %** aur **Skill Gap** calculate karne ka endpoint (`/api/match`).
4. **`routes_application.py`**: Tailored Cover Letter, HR Email body, aur LinkedIn message generate karne ke endpoints (`/api/application/generate`).
5. **`routes_auth.py`**: Users ke Login, Register (Sign-Up), aur profile check karne ke endpoints (`/api/auth/login`, `/api/auth/register`).

#### C. Business Logic Services (`app/services/`)
1. **`resume_analyzer.py`**: `pypdf` se resume ka text extract karta hai aur Groq LLM ki madad se Name, Email, Skills, Experience, Projects ko JSON me convert karta hai.
2. **`job_discovery.py` & `tavily_search.py`**: Multi-platform portals par candidate ki position search karta hai.
3. **`deduplicator.py`**: `rapidfuzz` library se duplicate jobs (jo alag portals par same post hain) ko identify aur remove karta hai.
4. **`matcher.py`**: Candidates aur Jobs ke bich weighted fit score nikalta hai:
   - **Skills:** 45% weight
   - **Experience:** 20% weight
   - **Education:** 10% weight
   - **Projects:** 15% weight
   - **Keywords:** 10% weight
5. **`skill_gap.py`**: Skills ko 4 categories me divide karta hai: Matched, Partial, Missing Must-Have, Missing Nice-to-Have.
6. **`application_writer.py`**: Candidate ki real resume information ke basis par bina kisi fake detail ke genuine Cover Letter aur HR Emails likhta hai.

#### D. Database Layer (`app/database/`)
1. **`db.py` & `connection.py`**: SQLite local database (`data/job_search.db`) se connection setup karta hai aur 5 main tables manage karta hai: `users`, `candidate_profiles`, `jobs`, `job_matches`, `applications`.

---

### 🎨 `frontend/` Directory (User Interface)

1. **`index.html`**
   - **Kaam:** Complete glassmorphism web dashboard UI.
   - **Features:** Real-time statistics cards, tabbed navigation (Resume Upload, Job Search, Match Analyzer, Application Generator, Tracker), aur top-right par **Glassmorphism Login/Register Modal**.

---

### 📄 `docs/` Directory (Documentation Files)

1. **`project_brief.md`**: Academic aur industrial presentation ke liye detailed project brief document.
2. **`problem_statement_doc.md`**: Project me solve kiye gaye 4 main problem statements ka detailed analysis.
3. **`code_explanation.md`**: Codebase ki complete architecture guide.

---

### 🚀 Root Files

1. **`run.py`**: Server launch script (`python run.py`).
2. **`requirements.txt`**: Project ki saari Python dependencies (`fastapi`, `uvicorn`, `groq`, `tavily-python`, `pypdf`, `rapidfuzz`, etc.).
3. **`Procfile` & `render.yaml`**: Cloud hosting (Render.com) par 1-click live deployment ke liye configuration files.

---

## 🎯 Resume & Viva Interview Tip

Jab bhi aapse koi puche ki ye project kaise kaam karta hai, aap yeh keh sakte hain:

> *"Is project me FastAPI + Python ka backend setup hai. Jab user PDF resume upload karta hai, PyPDF aur Groq LLM resume ko JSON Profile me parse karte hain. User ke target job role ke liye Tavily multi-portal search adapter public job boards (LinkedIn, Naukri, Indeed, Glassdoor) se vacancies fetch karta hai. Dual fuzzy matching (`rapidfuzz`) se duplicates filter hote hain. Phir hamara deterministic matcher Candidate profile aur JD ke bich 5-weighted dimensions par 0-100% match score nikalta hai, skill gaps dikhata hai, aur Groq LLM automatic tailored cover letters & emails generate karta hai."*
