import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)



def test_validate_preferences_endpoint_success():
    payload = {
        "target_role": "Data Analyst",
        "location": "Surat",
        "experience_level": "Fresher",
        "employment_type": "Full-time",
        "work_mode": "Hybrid",
        "preferred_companies": ["ABC Corp"],
        "skills": ["Python", "SQL"],
        "salary_min": 300000,
        "salary_max": 600000,
        "search_freshness": "30d",
        "result_limit": 50
    }
    response = client.post("/jobs/preferences/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["target_role"] == "Data Analyst"
    assert data["location"] == "Surat"
    assert data["salary_min"] == 300000


def test_validate_preferences_endpoint_validation_error():
    # Empty target role
    payload = {
        "target_role": "   ",
        "location": "Surat"
    }
    response = client.post("/jobs/preferences/validate", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_generate_queries_endpoint():
    payload = {
        "preferences": {
            "target_role": "Data Analyst",
            "location": "Surat",
            "experience_level": "Fresher",
            "employment_type": "Full-time",
            "work_mode": "Onsite",
            "preferred_companies": ["Tech Giant"],
            "skills": ["Python", "SQL"]
        },
        "candidate_profile": None
    }
    response = client.post("/jobs/queries/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_queries"] >= 5
    assert data["target_role"] == "Data Analyst"
    assert data["location"] == "Surat"
    assert len(data["queries"]) == data["total_queries"]
    
    # Verify each query object has required fields
    first_q = data["queries"][0]
    assert "query_string" in first_q
    assert "platform" in first_q
    assert "query_type" in first_q
    assert "description" in first_q


def test_execute_search_endpoint():
    payload = {
        "queries": [
            {
                "query_string": '"Data Analyst" "Surat"',
                "platform": "General",
                "query_type": "Base",
                "description": "Primary search"
            }
        ],
        "limit_per_query": 5
    }
    
    mock_discovery_result = {
        "total_results": 1,
        "successful_queries": 1,
        "failed_queries": 0,
        "platform_counts": {"Naukri": 1},
        "results": [
            {
                "title": "Data Analyst in Surat",
                "url": "https://www.naukri.com/job/123",
                "platform": "Naukri",
                "snippet": "Job in Surat",
                "score": 0.9,
                "query": '"Data Analyst" "Surat"',
                "discovered_at": "2026-09-24T11:30:00Z",
                "raw_data": {}
            }
        ],
        "errors": []
    }
    
    from unittest.mock import patch
    with patch("app.services.job_discovery.JobDiscoveryService.discover_jobs", return_value=mock_discovery_result):
        response = client.post("/jobs/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 1
        assert data["results"][0]["platform"] == "Naukri"


def test_classify_job_urls_endpoint():
    payload = {
        "urls": [
            "https://www.linkedin.com/jobs/view/123456",
            "https://www.naukri.com/data-analyst-jobs-in-surat"
        ],
        "fetch_html": False
    }
    
    response = client.post("/jobs/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["classification"] == "INDIVIDUAL_JOB"
    assert data[1]["classification"] == "SEARCH_PAGE"


def test_extract_full_jd_endpoint():
    payload = {
        "urls": ["https://example.com/job/101"]
    }
    
    mock_extract_result = [
        {
            "job_id": "job_101",
            "url": "https://example.com/job/101",
            "accessible": True,
            "raw_jd_text": "Clean JD text for Data Analyst in Surat",
            "text_length": 42,
            "truncated": False,
            "error": None
        }
    ]
    
    with patch("app.services.jd_extractor.FullJDExtractor.extract_jd_batch", return_value=mock_extract_result):
        response = client.post("/jobs/jd/extract", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["job_id"] == "job_101"
        assert "Data Analyst" in data[0]["raw_jd_text"]


def test_analyze_jd_endpoint():
    payload = {
        "job_id": "job_test_123",
        "raw_jd_text": "We are hiring a Data Analyst proficient in Python and SQL in Surat."
    }
    
    mock_analysis_dict = {
        "job_id": "job_test_123",
        "title": "Data Analyst",
        "company": "Tech Corp",
        "location": "Surat",
        "responsibilities": ["Analyze databases"],
        "required_skills": ["Python", "SQL"],
        "preferred_skills": [],
        "technical_skills": ["Python", "SQL"],
        "soft_skills": [],
        "qualifications": [],
        "education_requirements": "B.S. degree",
        "experience_requirements": "1-3 years",
        "employment_type": "Full-time",
        "work_mode": "Onsite",
        "salary_information": None,
        "benefits": [],
        "keywords": ["python", "sql", "data analyst"],
        "seniority_level": "Mid",
        "industry": "Technology",
        "summary": "Data Analyst position in Surat.",
        "raw_jd_text": payload["raw_jd_text"],
        "extracted_at": "2026-09-24T12:00:00Z"
    }
    
    mock_settings = MagicMock()
    mock_settings.GROQ_API_KEY = "gsk_mock_valid_key"
    with patch("app.services.jd_analyzer.get_settings", return_value=mock_settings), \
         patch("groq.Groq") as mock_groq_class:
        mock_instance = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content=json.dumps(mock_analysis_dict)))]
        mock_instance.chat.completions.create.return_value = mock_completion
        mock_groq_class.return_value = mock_instance
        
        response = client.post("/jobs/jd/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job_test_123"
        assert data["title"] == "Data Analyst"
        assert "Python" in data["required_skills"]
