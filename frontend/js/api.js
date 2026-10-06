/**
 * API Client Module for AI Job Assistant.
 * Centralizes REST API calls, candidate persistence, application tracking, and error mapping.
 */

const API = {
  baseUrl: (window.location.protocol === 'http:' || window.location.protocol === 'https:') && window.location.port === '8000' 
    ? '' 
    : 'http://127.0.0.1:8000',

  async _request(endpoint, options = {}) {
    const config = {
      headers: options.isFormData ? {} : { 'Content-Type': 'application/json', ...options.headers },
      ...options
    };

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, config);
      let data = {};
      try {
        data = await response.json();
      } catch (jsonErr) {
        data = {};
      }

      if (!response.ok) {
        let msg = 'An unexpected error occurred.';
        if (response.status === 400) {
          msg = data.detail || data.message || 'Invalid request parameters.';
        } else if (response.status === 422) {
          msg = 'Please check the uploaded file or inputs and try again.';
        } else if (response.status === 500) {
          msg = 'Something went wrong on the server. Please try again.';
        } else {
          msg = data.detail || data.message || `HTTP ${response.status} Error`;
        }

        if (typeof msg === 'object') {
          msg = JSON.stringify(msg);
        }
        throw new Error(msg);
      }
      return data;
    } catch (err) {
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        throw new Error('Unable to connect to server. Please check your connection.');
      }
      console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, err);
      throw err;
    }
  },

  // 0. Configuration & Status
  async getConfigStatus() {
    return this._request('/config/status');
  },

  // 1. Resume & Candidate Profile Endpoints
  async uploadResume(file) {
    if (!file) throw new Error('Please select a PDF resume.');
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      throw new Error('Please select a PDF resume.');
    }
    if (file.size > 15 * 1024 * 1024) {
      throw new Error('Resume file is too large (Maximum 15MB allowed).');
    }
    if (file.size === 0) {
      throw new Error('Selected PDF file is empty.');
    }

    const formData = new FormData();
    formData.append('file', file);
    return this._request('/resume/upload', {
      method: 'POST',
      body: formData,
      isFormData: true
    });
  },

  async analyzeResume(fileOrText) {
    if (!fileOrText) throw new Error('No resume content provided for analysis.');

    if (fileOrText instanceof File) {
      if (!fileOrText.name.toLowerCase().endsWith('.pdf') && fileOrText.type !== 'application/pdf') {
        throw new Error('Please select a PDF resume.');
      }
      const formData = new FormData();
      formData.append('file', fileOrText);
      return this._request('/resume/analyze', {
        method: 'POST',
        body: formData,
        isFormData: true
      });
    }

    const textVal = typeof fileOrText === 'string' ? fileOrText : (fileOrText.cleaned_text || String(fileOrText));
    if (!textVal.trim()) {
      throw new Error('Unable to read this PDF.');
    }

    return this._request('/resume/analyze', {
      method: 'POST',
      body: JSON.stringify({ resume_text: textVal })
    });
  },

  async getCurrentCandidate() {
    try {
      return await this._request('/resume/current');
    } catch (err) {
      return null;
    }
  },

  // 2. Preferences & Query Builder
  async validatePreferences(preferences) {
    return this._request('/jobs/preferences/validate', {
      method: 'POST',
      body: JSON.stringify(preferences)
    });
  },

  async generateQueries(preferences, candidateProfile = null) {
    return this._request('/jobs/queries/generate', {
      method: 'POST',
      body: JSON.stringify({
        preferences,
        candidate_profile: candidateProfile
      })
    });
  },

  // 3. Multi-Platform Job Discovery & Processing
  async searchJobs(queries, limitPerQuery = 10) {
    return this._request('/jobs/search', {
      method: 'POST',
      body: JSON.stringify({ queries, limit_per_query: limitPerQuery })
    });
  },

  async classifyJobURLs(urls, fetchHtml = false) {
    return this._request('/jobs/classify', {
      method: 'POST',
      body: JSON.stringify({ urls, fetch_html: fetchHtml })
    });
  },

  async normalizeJobs(rawResults) {
    return this._request('/jobs/normalize', {
      method: 'POST',
      body: JSON.stringify({ results: rawResults })
    });
  },

  async deduplicateJobs(jobs, similarityThreshold = 0.85) {
    return this._request('/jobs/deduplicate', {
      method: 'POST',
      body: JSON.stringify({ jobs, similarity_threshold: similarityThreshold })
    });
  },

  // 4. JD Extraction & Analysis
  async extractJD(jobsOrUrls) {
    const payload = typeof jobsOrUrls[0] === 'string' ? { urls: jobsOrUrls } : { jobs: jobsOrUrls };
    return this._request('/jobs/jd/extract', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async analyzeJD(jobId, rawJdText) {
    return this._request('/jobs/jd/analyze', {
      method: 'POST',
      body: JSON.stringify({ job_id: jobId, raw_jd_text: rawJdText })
    });
  },

  // 5. Matching & Skill Gap
  async matchResume(candidate, job, jdAnalysis = null, preferences = null) {
    return this._request('/jobs/match', {
      method: 'POST',
      body: JSON.stringify({ candidate, job, jd_analysis: jdAnalysis, preferences })
    });
  },

  async skillGap(candidate, job, jdAnalysis = null) {
    return this._request('/jobs/skill-gap', {
      method: 'POST',
      body: JSON.stringify({ candidate, job, jd_analysis: jdAnalysis })
    });
  },

  // 6. Application Package Generation
  async generateApplication(candidate, job, jdAnalysis = null, matchResult = null, skillGap = null) {
    return this._request('/applications/generate', {
      method: 'POST',
      body: JSON.stringify({
        candidate,
        job,
        jd_analysis: jdAnalysis,
        match_result: matchResult,
        skill_gap: skillGap
      })
    });
  },

  // 7. Tracker Endpoints
  async saveApplication(packageObj, status = 'SAVED', notes = '', appliedDate = null) {
    return this._request('/tracker/applications', {
      method: 'POST',
      body: JSON.stringify({
        package: packageObj,
        status,
        notes,
        applied_date: appliedDate
      })
    });
  },

  async listApplications(statusFilter = null) {
    const url = statusFilter ? `/tracker/applications?status_filter=${encodeURIComponent(statusFilter)}` : '/tracker/applications';
    return this._request(url);
  },

  async updateApplicationStatus(applicationId, status, notes = '', appliedDate = null) {
    const params = new URLSearchParams({ status });
    if (notes) params.append('notes', notes);
    if (appliedDate) params.append('applied_date', appliedDate);
    return this._request(`/tracker/applications/${applicationId}?${params.toString()}`, {
      method: 'PATCH'
    });
  },

  // 8. Dashboard Summary
  async getDashboardSummary() {
    return this._request('/dashboard/summary');
  }
};
