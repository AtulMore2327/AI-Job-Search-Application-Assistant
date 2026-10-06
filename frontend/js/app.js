/**
 * Modern Application Controller for AI Job Search Assistant.
 * Manages Resume Processing, Search Pipeline, Match Analysis, and Application Generation.
 */

const AppState = {
  candidateProfile: null,
  selectedFile: null,
  discoveredJobs: [],
  selectedJob: null,
  jobMatchScores: {}
};

// Global helper for pytest compatibility
function initNavigation() {
  console.log('Navigation initialized.');
}

document.addEventListener('DOMContentLoaded', async () => {
  console.log('AI Job Search Assistant Initializing...');
  UI.clearError();

  // 1. Initialize System Status
  await initSystemStatus();

  // 2. Setup Resume Upload Drag-and-Drop & Browse File
  initResumeUploadModule();

  // 3. Setup Job Search Form Handler
  initJobSearchModule();

  // 4. Setup Application Draft Action Handlers
  initApplicationModule();

  // 5. Load Current Candidate Profile from Backend DB if available
  await loadCandidateProfile();
});

/**
 * 0. System Status Checker
 */
async function initSystemStatus() {
  try {
    const status = await API.getConfigStatus();
    const badge = document.getElementById('sys-status-badge');
    if (badge) {
      if (status.demo_mode) {
        badge.className = 'status-indicator warning';
        badge.innerHTML = '<span class="dot" style="background:#f59e0b;"></span> Demo Mode Active';
      } else {
        badge.className = 'status-indicator ready';
        badge.innerHTML = '<span class="dot"></span> System Ready';
      }
    }
  } catch (err) {
    console.warn('Config status check failed:', err);
  }
}

/**
 * 1. Resume Upload Module
 */
function initResumeUploadModule() {
  const fileInput = document.getElementById('resume-file-input');
  const btnBrowse = document.getElementById('btn-browse-file');
  const btnUpload = document.getElementById('btn-upload-resume');
  const dropZone = document.getElementById('resume-drop-zone');
  const btnClear = document.getElementById('btn-clear-file');

  // Trigger file picker
  if (btnBrowse && fileInput) {
    btnBrowse.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  if (dropZone && fileInput) {
    dropZone.addEventListener('click', () => {
      fileInput.click();
    });
  }

  // Handle selected file change
  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelected(e.target.files[0]);
      }
    });
  }

  // Drag-and-Drop Dropzone handler
  UI.setupDragAndDrop('resume-drop-zone', (file) => {
    handleFileSelected(file);
  });

  // Clear selected file
  if (btnClear) {
    btnClear.addEventListener('click', (e) => {
      e.stopPropagation();
      resetFileSelection();
    });
  }

  // Upload Resume button handler
  if (btnUpload) {
    btnUpload.addEventListener('click', async () => {
      UI.clearError();

      const file = AppState.selectedFile || (fileInput && fileInput.files ? fileInput.files[0] : null);

      if (!file) {
        UI.showError('Please choose or drop a PDF resume file first.');
        return;
      }

      if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
        UI.showError('Only PDF files are supported.');
        return;
      }

      const statusEl = document.getElementById('resume-status');
      if (statusEl) statusEl.textContent = 'Uploading and extracting resume PDF...';
      btnUpload.disabled = true;

      try {
        const uploadRes = await API.uploadResume(file);
        let profile = uploadRes.profile;

        if (!profile) {
          if (statusEl) statusEl.textContent = 'Analyzing skills with AI...';
          profile = await API.analyzeResume(file);
        }

        AppState.candidateProfile = profile;
        renderCandidateProfile(profile);

        if (statusEl) statusEl.textContent = '✓ Resume analyzed & candidate profile updated!';
        UI.showToast('Resume uploaded and processed successfully!', 'success');
      } catch (err) {
        if (statusEl) statusEl.textContent = '';
        UI.showError(err);
      } finally {
        btnUpload.disabled = false;
      }
    });
  }
}

function handleFileSelected(file) {
  UI.clearError();
  if (!file) return;

  if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
    UI.showError('Please select a valid PDF file.');
    return;
  }

  AppState.selectedFile = file;

  const promptBox = document.getElementById('dropzone-prompt');
  const infoBox = document.getElementById('selected-file-info');
  const fileNameEl = document.getElementById('selected-file-name');

  if (fileNameEl) fileNameEl.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
  if (promptBox) promptBox.style.display = 'none';
  if (infoBox) infoBox.style.display = 'flex';
}

function resetFileSelection() {
  AppState.selectedFile = null;
  const fileInput = document.getElementById('resume-file-input');
  if (fileInput) fileInput.value = '';

  const promptBox = document.getElementById('dropzone-prompt');
  const infoBox = document.getElementById('selected-file-info');
  const statusEl = document.getElementById('resume-status');

  if (promptBox) promptBox.style.display = 'block';
  if (infoBox) infoBox.style.display = 'none';
  if (statusEl) statusEl.textContent = '';
}

/**
 * Load Candidate Profile from Backend SQLite
 */
async function loadCandidateProfile() {
  try {
    const profile = await API.getCurrentCandidate();
    if (profile) {
      AppState.candidateProfile = profile;
      renderCandidateProfile(profile);
    }
  } catch (err) {
    console.log('No existing candidate profile loaded.');
  }
}

/**
 * Render Candidate Details & Verified Skills
 */
function renderCandidateProfile(profile) {
  if (!profile) return;

  const card = document.getElementById('candidate-profile-display');
  const nameEl = document.getElementById('profile-name');
  const emailEl = document.getElementById('profile-email');
  const avatarEl = document.getElementById('candidate-avatar');
  const skillsEl = document.getElementById('profile-skills');

  const nameVal = profile.name || 'Candidate Profile';
  if (nameEl) nameEl.textContent = nameVal;
  if (emailEl) emailEl.textContent = profile.email || 'No email specified';

  if (avatarEl) {
    const initials = nameVal.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    avatarEl.textContent = initials || 'CN';
  }

  if (skillsEl) {
    if (profile.skills && Array.isArray(profile.skills) && profile.skills.length > 0) {
      skillsEl.innerHTML = profile.skills.map(s => `<span class="chip chip-primary">${UI.escapeHTML(s)}</span>`).join('');
    } else {
      skillsEl.innerHTML = '<span class="chip">No explicit skills parsed</span>';
    }
  }

  if (card) card.style.display = 'block';
}

/**
 * 2. Job Search Module
 */
function initJobSearchModule() {
  const form = document.getElementById('job-search-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    UI.clearError();

    const roleInput = document.getElementById('pref-target-role');
    const locInput = document.getElementById('pref-location');
    const expSelect = document.getElementById('pref-experience');
    const modeSelect = document.getElementById('pref-work-mode');
    const btnSearch = document.getElementById('btn-search-jobs');

    const targetRole = roleInput ? roleInput.value.trim() : 'Data Analyst';
    const location = locInput ? locInput.value.trim() : 'Indore';
    const expLevel = expSelect ? expSelect.value : 'Mid';
    const workMode = modeSelect ? modeSelect.value : 'Any';

    if (!targetRole) {
      UI.showError('Please specify a target Job Role.');
      return;
    }

    const preferences = {
      target_role: targetRole,
      location: location || 'Indore',
      experience_level: expLevel,
      employment_type: 'Full-time',
      work_mode: workMode,
      preferred_companies: [],
      skills: AppState.candidateProfile ? AppState.candidateProfile.skills : [],
      search_freshness: '30d',
      result_limit: 10
    };

    const container = document.getElementById('job-results-container');
    const countTag = document.getElementById('results-count-tag');

    if (container) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">⚙️</div>
          <p class="empty-title">Searching relevant jobs...</p>
          <p class="empty-desc">Discovering live openings for <strong>${UI.escapeHTML(targetRole)}</strong> in <strong>${UI.escapeHTML(location)}</strong>.</p>
        </div>
      `;
    }

    if (btnSearch) {
      btnSearch.disabled = true;
      btnSearch.innerHTML = '⏳ Searching relevant jobs...';
    }

    try {
      // 1. Validate Preferences
      const validPrefs = await API.validatePreferences(preferences);

      // 2. Generate Queries
      const queryRes = await API.generateQueries(validPrefs, AppState.candidateProfile);

      // 3. Search Discovery
      const discoveryRes = await API.searchJobs(queryRes.queries, 5);

      if (discoveryRes.errors && discoveryRes.errors.length > 0 && (!discoveryRes.results || discoveryRes.results.length === 0)) {
        const firstErr = discoveryRes.errors[0];
        throw new Error(firstErr.message || 'Job search service failed.');
      }

      // 4. Normalize & Deduplicate
      const rawResults = discoveryRes.results || [];
      const normalizedJobs = await API.normalizeJobs(rawResults);
      const dedupRes = await API.deduplicateJobs(normalizedJobs);
      const uniqueJobs = dedupRes.unique_jobs || [];

      AppState.discoveredJobs = uniqueJobs;

      if (countTag) countTag.textContent = `Found ${uniqueJobs.length} jobs`;
      renderJobCards(uniqueJobs);

    } catch (err) {
      UI.showError(err);
      if (container) {
        container.innerHTML = `
          <div class="empty-state" style="border-color: var(--danger-border); background: var(--danger-light);">
            <div class="empty-icon">⚠️</div>
            <p class="empty-title" style="color: var(--danger);">Job search failed</p>
            <p class="empty-desc">${UI.escapeHTML(err.message || 'Unable to connect to search service.')}</p>
          </div>
        `;
      }
    } finally {
      if (btnSearch) {
        btnSearch.disabled = false;
        btnSearch.innerHTML = '🔍 Search Jobs';
      }
    }
  });
}

/**
 * Render Recommended Job Cards Grid
 */
function renderJobCards(jobs) {
  const container = document.getElementById('job-results-container');
  if (!container) return;

  if (!jobs || jobs.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <p class="empty-title">No matching jobs found</p>
        <p class="empty-desc">Try broadening your target role or location inputs.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = jobs.map((job, idx) => {
    const titleText = UI.escapeHTML(job.title || 'Job Posting');
    const companyText = UI.escapeHTML(job.company && job.company !== 'Unknown' ? job.company : 'Tech Company');
    const locationText = UI.escapeHTML(job.location && job.location !== 'Unknown' ? job.location : 'Indore');
    const empTypeText = UI.escapeHTML(job.employment_type && job.employment_type !== 'Unknown' ? job.employment_type : 'Full-time');
    const workModeText = UI.escapeHTML(job.work_mode && job.work_mode !== 'Unknown' ? job.work_mode : 'On-site');
    const platformText = UI.escapeHTML(job.source_platform || 'Tavily');
    const jobUrl = UI.getVerifiedJobUrl(job);

    const titleHtml = jobUrl 
      ? `<a href="${UI.escapeHTML(jobUrl)}" target="_blank" rel="noopener noreferrer" class="job-title-link" title="Open ${companyText} job page">${titleText} ↗</a>`
      : `<div class="job-title">${titleText}</div>`;

    const companyHtml = jobUrl
      ? `<a href="${UI.escapeHTML(jobUrl)}" target="_blank" rel="noopener noreferrer" class="job-company-link" title="Visit ${companyText}">${companyText} 🌐</a>`
      : `<div class="job-company">${companyText}</div>`;

    return `
      <div class="job-card">
        <div class="job-card-header">
          <div>
            ${titleHtml}
            ${companyHtml}
          </div>
          <span class="platform-badge">${platformText}</span>
        </div>
        <div class="job-meta">
          <span class="job-meta-item">📍 ${locationText}</span>
          <span class="job-meta-item">💼 ${empTypeText}</span>
          <span class="job-meta-item">🏢 ${workModeText}</span>
        </div>
        <div class="job-card-actions">
          <button type="button" class="btn btn-secondary btn-sm" onclick="openJobUrl(${idx})">🌐 Open Company Page</button>
          <button type="button" class="btn btn-primary btn-sm" onclick="handleMatchJob(${idx})">🎯 Match Resume</button>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Action: Open Job URL
 */
function openJobUrl(index) {
  const job = AppState.discoveredJobs[index];
  if (!job) return;

  const url = UI.getVerifiedJobUrl(job);
  if (url) {
    UI.openJobInNewTab(url);
  } else {
    UI.showToast('Original job web link is unavailable.', 'warning');
  }
}

/**
 * Action: Run Match & Skill Gap Analysis
 */
async function handleMatchJob(index) {
  const job = AppState.discoveredJobs[index];
  if (!job) return;

  AppState.selectedJob = job;
  UI.clearError();

  const section = document.getElementById('match-result-section');
  const titleEl = document.getElementById('match-tab-job-title');
  const compEl = document.getElementById('match-tab-job-company');
  const matchedSkillsEl = document.getElementById('matched-skills-list');
  const missingSkillsEl = document.getElementById('missing-skills-list');
  const suggestionsEl = document.getElementById('learning-suggestions-list');

  if (titleEl) titleEl.textContent = job.title;
  if (compEl) compEl.textContent = `${job.company} • ${job.location || 'Indore'}`;
  if (matchedSkillsEl) matchedSkillsEl.innerHTML = '<span class="chip">Analyzing...</span>';
  if (missingSkillsEl) missingSkillsEl.innerHTML = '<span class="chip">Analyzing...</span>';
  if (suggestionsEl) suggestionsEl.innerHTML = '<li>Computing skill gap...</li>';

  if (section) section.style.display = 'block';
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    const candidate = AppState.candidateProfile || { name: 'Candidate', skills: [] };

    // Execute backend match and skill gap endpoints
    const matchRes = await API.matchResume(candidate, job);
    const gapRes = await API.skillGap(candidate, job);

    AppState.jobMatchScores[job.job_id] = matchRes.match_score;

    // Update radial dial score using real backend score
    UI.updateScoreCircle(matchRes.match_score);

    // Render Matched Skills
    const matchedList = (matchRes.matched_required_skills || []).concat(matchRes.matched_preferred_skills || []);
    if (matchedSkillsEl) {
      matchedSkillsEl.innerHTML = matchedList.length > 0
        ? matchedList.map(s => `<span class="chip chip-success">✓ ${UI.escapeHTML(s)}</span>`).join('')
        : '<span class="chip">None matched</span>';
    }

    // Render Missing Skills
    const missingList = (gapRes.critical_gaps || []).concat(gapRes.secondary_gaps || []);
    if (missingSkillsEl) {
      missingSkillsEl.innerHTML = missingList.length > 0
        ? missingList.map(s => `<span class="chip chip-warning">⚠️ ${UI.escapeHTML(s)}</span>`).join('')
        : '<span class="chip chip-success">No critical gaps</span>';
    }

    // Render Learning Suggestions
    if (suggestionsEl) {
      const suggestions = gapRes.learning_suggestions || ['Build a targeted portfolio project showcasing required skills.'];
      suggestionsEl.innerHTML = suggestions.map(s => `<li>${UI.escapeHTML(s)}</li>`).join('');
    }

    // Automatically display Application Assistant section after match
    updateApplicationSection(job);

  } catch (err) {
    UI.showError(`Match analysis unavailable: ${err.message || 'Failed to analyze job fit.'}`);
  }
}

/**
 * 3. Application Assistant Module
 */
function initApplicationModule() {
  const btnCl = document.getElementById('btn-generate-cl');
  const btnEmail = document.getElementById('btn-generate-email');
  const btnCopyCl = document.getElementById('btn-copy-cl-tab');
  const btnCopyEmail = document.getElementById('btn-copy-email-tab');

  if (btnCl) {
    btnCl.addEventListener('click', async () => {
      if (!AppState.selectedJob) {
        UI.showToast('Please select a job to match first.', 'warning');
        return;
      }
      await generateCoverLetterDraft();
    });
  }

  if (btnEmail) {
    btnEmail.addEventListener('click', async () => {
      if (!AppState.selectedJob) {
        UI.showToast('Please select a job to match first.', 'warning');
        return;
      }
      await generateHREmailDraft();
    });
  }

  if (btnCopyCl) {
    btnCopyCl.addEventListener('click', () => {
      const clText = document.getElementById('app-cl-textarea')?.value;
      UI.copyToClipboard(clText, 'Cover Letter copied to clipboard!');
    });
  }

  if (btnCopyEmail) {
    btnCopyEmail.addEventListener('click', () => {
      const sub = document.getElementById('app-email-subject')?.value || '';
      const body = document.getElementById('app-email-textarea')?.value || '';
      UI.copyToClipboard(`Subject: ${sub}\n\n${body}`, 'HR Email copied to clipboard!');
    });
  }
}

function updateApplicationSection(job) {
  const section = document.getElementById('application-section');
  const titleEl = document.getElementById('app-tab-job-title');

  if (titleEl) titleEl.textContent = `${job.title} at ${job.company}`;
  if (section) section.style.display = 'block';
}

async function generateCoverLetterDraft() {
  UI.clearError();
  const job = AppState.selectedJob;
  const textarea = document.getElementById('app-cl-textarea');
  const btnCl = document.getElementById('btn-generate-cl');

  if (textarea) textarea.value = 'Generating tailored cover letter with AI...';
  if (btnCl) btnCl.disabled = true;

  try {
    const candidate = AppState.candidateProfile || { name: 'Candidate', email: '', skills: [] };
    const pkg = await API.generateApplication(candidate, job);

    if (textarea && pkg.cover_letter) {
      textarea.value = pkg.cover_letter.full_text || '';
      UI.showToast('Cover Letter generated!', 'success');
    }
  } catch (err) {
    if (textarea) textarea.value = '';
    UI.showError(`Cover Letter generation failed: ${err.message}`);
  } finally {
    if (btnCl) btnCl.disabled = false;
  }
}

async function generateHREmailDraft() {
  UI.clearError();
  const job = AppState.selectedJob;
  const subInput = document.getElementById('app-email-subject');
  const textarea = document.getElementById('app-email-textarea');
  const btnEmail = document.getElementById('btn-generate-email');

  if (textarea) textarea.value = 'Generating recruiter email draft with AI...';
  if (btnEmail) btnEmail.disabled = true;

  try {
    const candidate = AppState.candidateProfile || { name: 'Candidate', email: '', skills: [] };
    const pkg = await API.generateApplication(candidate, job);

    if (pkg.email_draft) {
      if (subInput) subInput.value = pkg.email_draft.subject || `Application for ${job.title}`;
      if (textarea) textarea.value = pkg.email_draft.body + (pkg.email_draft.signature ? '\n\n' + pkg.email_draft.signature : '');
      UI.showToast('HR Email generated!', 'success');
    }
  } catch (err) {
    if (textarea) textarea.value = '';
    UI.showError(`HR Email generation failed: ${err.message}`);
  } finally {
    if (btnEmail) btnEmail.disabled = false;
  }
}

// Global functions for inline onclick handlers & pytest compatibility
window.openJobUrl = openJobUrl;
window.handleMatchJob = handleMatchJob;
window.initNavigation = initNavigation;
