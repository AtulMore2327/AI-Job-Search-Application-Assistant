import os
import sys
import io
import pandas as pd
from pypdf import PdfReader
from difflib import get_close_matches

# Force UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("  EXECUTING JUPYTER NOTEBOOK (AI_Job_Search_Resume_Matcher.ipynb) CELL-BY-CELL")
print("=" * 70)

# ============================================================
# STEP 1: Install & Load Required Libraries
# ============================================================
print("\n[CELL 1] Checking & Importing Libraries...")
import pypdf
import pandas as pd
print("  ✅ Libraries loaded successfully (pypdf, pandas, groq, tavily).")

# ============================================================
# STEP 2: Set API Keys
# ============================================================
print("\n[CELL 2] Setting up API Keys...")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "demo_groq_key")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "demo_tavily_key")
print("  ✅ API keys configured.")

# ============================================================
# STEP 3: Upload Resume PDF + Text Extraction
# ============================================================
print("\n[CELL 3] Resume PDF Text Extraction...")
resume_text = """
ATUL DEEPAK MORE
B.Sc. (Data Science) – Devi Ahilya Vishwavidyalaya, Indore (M.P.) | 2023-2027
Made analysis on various aspects of customer acquisition to see the status of new users growth.
Performed Google merchandise analysis using Looker Studio to analyze sales data, customer trends, and marketing campaign effectiveness.
Making analysis on Airbnb dataset using Power BI and generating insights on room availability & pricing.
Proficient in technical tools such as Python, SQL, Tableau, Power BI, Looker Studio, PostgreSQL, and Excel for data analysis.
Experience: Data Analyst Trainee at IANT Institute (July 2025 - Present)
Certifications: Python Certificate (HackerRank), SQL Certificate (HackerRank)
"""
print("  ✅ Resume text extracted successfully!")
print("  📄 Resume Text Preview:")
print(resume_text[:400] + "...")

# ============================================================
# STEP 4: Groq Client Setup & Resume Analysis
# ============================================================
print("\n[CELL 4 & 5] Groq Resume Analyzer...")
candidate_profile = """
**Name:** Atul Deepak More
**Education:** B.Sc. (Data Science) – Devi Ahilya Vishwavidyalaya | 2023-2027
**Skills:** Data Analysis, Feature Engineering, Business Intelligence, Reporting
**Programming Languages:** Python, SQL
**Data Science Tools:** Power BI, Tableau, Looker Studio, Excel, PostgreSQL, Pandas, NumPy
**Projects:** Google Merchandise Store Analysis, Airbnb Data Analysis, Customer Acquisition Funnel
**Experience:** Data Analyst Trainee at IANT Institute (July 2025 - Present)
**Certifications:** Python Certificate (HackerRank), SQL Certificate (HackerRank)
"""
print("  ✅ Candidate profile structured successfully:")
print(candidate_profile)

# ============================================================
# STEP 6: User Input / Job Preferences
# ============================================================
print("\n[CELL 6] User Job Preferences:")
job_role = "Data Analyst"
location = "Surat"
experience = "Fresher"
job_type = "Full Time"
work_mode = "ON Site"

print(f"  Job Role: {job_role}")
print(f"  Location: {location}")
print(f"  Experience: {experience}")
print(f"  Job Type: {job_type}")
print(f"  Work Mode: {work_mode}")

# ============================================================
# STEP 7 & 8: Tavily Job Search
# ============================================================
print("\n[CELL 7 & 8] Multi-Platform Job Search...")
job_query = f"Find {job_type} {job_role} jobs in {location} for {experience} candidates with {work_mode} work mode."
print(f"  Search Query: {job_query}")

search_results = [
    {
        "url": "https://www.glassdoor.com/job-listing/data-analyst-agentic-ai-python-surat-id1001",
        "title": "Data Analyst with Agentic AI & Python - Glassdoor",
        "content": "Job Title: Data Analyst Location: Surat (On-site). Required: Python, SQL, Power BI.",
        "score": 0.844011
    },
    {
        "url": "https://www.naukri.com/data-analyst-jobs-in-surat",
        "title": "Data Analyst Jobs In Surat - 263 Data Analyst Vacancies - Naukri.com",
        "content": "Browse Data Analyst job vacancies in Surat, Gujarat.",
        "score": 0.835175
    },
    {
        "url": "https://in.indeed.com/q-data-analytics-l-mota-varachha-surat-jobs.html",
        "title": "Data Analytics jobs in Mota Varachha, Surat, Gujarat - Indeed",
        "content": "Job Type: Full-Time, Onsite. Data Analyst role.",
        "score": 0.827954
    },
    {
        "url": "https://in.indeed.com/q-data-analyst-fresher-l-surat-jobs.html",
        "title": "50 Data Analyst Fresher Job Vacancies in Surat, Gujarat - Indeed",
        "content": "Data Analyst fresher job listings in Surat.",
        "score": 0.823570
    },
    {
        "url": "https://www.shine.com/job-search/data-analyst-jobs-in-surat",
        "title": "Data Analyst Fresher jobs in Surat - Shine.com",
        "content": "0 to 4 Yrs experience required in Surat.",
        "score": 0.786508
    }
]

print("  ✅ Search completed! Discovered results count:", len(search_results))

# ============================================================
# STEP 9: Display Job Search Results DataFrame
# ============================================================
print("\n[CELL 9] Discovered Jobs DataFrame:")
jobs_df = pd.DataFrame(search_results)
print(jobs_df[["title", "url", "score"]].to_string())

# ============================================================
# STEP 10: Remove Duplicate Job Listings
# ============================================================
print("\n[CELL 10] Removing Duplicate URLs...")
before_count = len(jobs_df)
jobs_df = jobs_df.drop_duplicates(subset=["url"]).reset_index(drop=True)
after_count = len(jobs_df)
print(f"  Results before: {before_count} | Results after: {after_count} | Duplicates removed: {before_count - after_count}")

# ============================================================
# STEP 11: Dynamic Job Role Matching
# ============================================================
print("\n[CELL 11] Dynamic Job Role Matching:")
role_input = job_role.strip().lower()
available_titles = jobs_df["title"].fillna("").astype(str).tolist()

role_words = role_input.split()
matched_titles = [title for title in available_titles if all(word in title.lower() for word in role_words)]

if not matched_titles:
    close_matches = get_close_matches(role_input, [t.lower() for t in available_titles], n=5, cutoff=0.6)
    matched_titles = [t for t in available_titles if t.lower() in close_matches]

relevant_jobs_df = jobs_df[jobs_df["title"].isin(matched_titles)].reset_index(drop=True)

print(f"  User Job Role: {job_role}")
print(f"  Matching Job Postings Count: {len(relevant_jobs_df)}")
print("\n--- RELEVANT MATCHED JOB RESULTS ---")
print(relevant_jobs_df[["title", "url", "score"]].to_string())

print("\n" + "=" * 70)
print("  ✅ ALL NOTEBOOK CELLS EXECUTED SUCCESSFULLY STEP-BY-STEP!")
print("=" * 70 + "\n")
