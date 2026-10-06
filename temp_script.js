
        let pipelineResults = null;

        function switchResumeTab(mode) {
            if(mode === 'file') {
                document.getElementById('fileSection').style.display = 'block';
                document.getElementById('textSection').style.display = 'none';
                document.getElementById('tabUpload').classList.add('active');
                document.getElementById('tabPaste').classList.remove('active');
            } else {
                document.getElementById('fileSection').style.display = 'none';
                document.getElementById('textSection').style.display = 'block';
                document.getElementById('tabUpload').classList.remove('active');
                document.getElementById('tabPaste').classList.add('active');
            }
        }

        function setRole(role) {
            document.getElementById('roleInput').value = role;
        }

        function setLoc(loc) {
            document.getElementById('locInput').value = loc;
        }

        let activeCandidateLoaded = false;
        let currentLoadedFileName = null;

        function fillSampleResume() {
            if (activeCandidateLoaded) {
                const sourceMsg = currentLoadedFileName ? `your uploaded file "${currentLoadedFileName}"` : "your current active resume profile";
                if (!confirm(`Loading sample data will replace ${sourceMsg}. Do you want to proceed?`)) {
                    return;
                }
            }
            switchResumeTab('text');
            document.getElementById('pasteText').value = 
`Rahul Sharma
Email: rahul.sharma@gmail.com | Phone: +91 9876543210
Education: B.Tech in Computer Science - Mumbai University (2024)

Skills: Python, SQL, PostgreSQL, Pandas, NumPy, Data Cleaning, Exploratory Data Analysis, Feature Engineering
Tools: Power BI, Tableau, Excel, Git, VS Code

Experience:
Data Analyst Trainee - Apex Tech Solutions (July 2024 - Present)
- Built interactive Power BI dashboards processing customer acquisition data.
- Executed SQL queries to clean and analyze daily sales datasets.

Projects:
- Airbnb Demand Forecast Dashboard: Power BI & Python project analyzing room pricing trends.
- E-Commerce Sales Pipeline: Python & SQL data extraction and visualization.`;
            analyzeText();
        }

        async function uploadFile(event) {
            const file = event.target.files[0];
            if(!file) return;

            const formData = new FormData();
            formData.append("file", file);

            try {
                const res = await fetch('/resume/upload', { method: 'POST', body: formData });
                const profile = await res.json();
                currentLoadedFileName = file.name;

                const badge = document.getElementById('fileBadge');
                if (badge) {
                    badge.innerText = `📄 Uploaded Resume: ${file.name}`;
                    badge.style.display = 'inline-block';
                }

                if (profile.raw_text) {
                    document.getElementById('pasteText').value = profile.raw_text;
                }

                showProfile(profile);
                showToast(`Resume "${file.name}" uploaded! Please enter/confirm location in Step 2 & click "FIND MATCHING JOBS".`);

                const locIn = document.getElementById('locInput');
                if (locIn) {
                    locIn.focus();
                    locIn.select();
                }
            } catch(e) {
                alert("Upload error: " + e.message);
            }
        }

        async function analyzeText() {
            const text = document.getElementById('pasteText').value;
            if(!text) return alert("Please paste resume text first!");

            const formData = new FormData();
            formData.append("text", text);

            try {
                const res = await fetch('/resume/analyze', { method: 'POST', body: formData });
                const profile = await res.json();
                showProfile(profile);
                showToast("Resume analyzed! Please enter/confirm location in Step 2 & click \"FIND MATCHING JOBS\".");

                const locIn = document.getElementById('locInput');
                if (locIn) {
                    locIn.focus();
                    locIn.select();
                }
            } catch(e) {
                alert("Error: " + e.message);
            }
        }

        function showProfile(profile) {
            activeCandidateLoaded = true;
            document.getElementById('profileBox').style.display = 'block';
            
            const name = profile.name || "Candidate Profile";
            document.getElementById('pName').innerText = name;
            document.getElementById('pAvatar').innerText = name.charAt(0).toUpperCase();

            let contactParts = [];
            if(profile.email) contactParts.push("✉️ " + profile.email);
            if(profile.phone) contactParts.push("📞 " + profile.phone);
            if(profile.location) contactParts.push("📍 " + profile.location);
            document.getElementById('pContact').innerText = contactParts.join('  |  ') || "Profile Active";

            // Auto-populate Location and Role inputs from parsed candidate profile
            if (profile.location) {
                document.getElementById('locInput').value = profile.location;
            }
            if (profile.target_role) {
                document.getElementById('roleInput').value = profile.target_role;
            }

            let eduText = "";
            if(profile.education && profile.education.length > 0) {
                const e = profile.education[0];
                let deg = (e.degree || "").replace(/^education:\s*/i, '').trim();
                let inst = (e.institution || "").replace(/^education:\s*/i, '').trim();
                let yr = (e.year || "").trim();

                if (inst && (deg.toLowerCase().includes(inst.toLowerCase()) || inst.toLowerCase().includes(deg.toLowerCase()))) {
                    inst = "";
                }

                eduText = "🎓 " + (deg || "Degree");
                if (inst) eduText += " – " + inst;
                if (yr && yr !== "Graduated" && yr !== "Relevant Grad" && !deg.includes(yr) && (!inst || !inst.includes(yr))) {
                    eduText += " (" + yr + ")";
                }
            } else if(profile.summary) {
                eduText = profile.summary;
            }
            document.getElementById('pEdu').innerText = eduText;
            document.getElementById('pSummary').innerText = profile.summary || "Candidate profile active in pipeline matching.";

            const allSkills = [...(profile.skills || []), ...(profile.tools || [])];
            const uniqueSkills = allSkills.filter((s, idx, self) => self.findIndex(x => x.toLowerCase() === s.toLowerCase()) === idx);
            document.getElementById('pSkills').innerHTML = uniqueSkills.map(s => `<span class="skill-tag">${s}</span>`).join('');
        }

        async function findJobs() {
            const roleVal = document.getElementById('roleInput').value.trim();
            const locVal = document.getElementById('locInput').value.trim();

            if (!roleVal) {
                alert("Please enter or select a Target Role / Title first!");
                document.getElementById('roleInput').focus();
                return;
            }
            if (!locVal) {
                alert("Please enter or select a City / Location first!");
                document.getElementById('locInput').focus();
                return;
            }

            const resultsSec = document.getElementById('resultsSection');
            if (resultsSec) {
                resultsSec.style.display = 'block';
                resultsSec.scrollIntoView({ behavior: 'smooth' });
            }

            const btn = document.getElementById('findBtn');
            btn.innerHTML = "⏳ Searching Vacancies Across Platforms...";
            btn.disabled = true;

            const prefs = {
                target_role: roleVal,
                location: locVal,
                work_mode: document.getElementById('modeInput').value,
                experience_level: document.getElementById('expInput').value,
                result_limit: 10
            };

            try {
                const res = await fetch('/search/jobs', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(prefs)
                });
                pipelineResults = await res.json();
                renderJobsList(pipelineResults.jobs, pipelineResults.match_results);

                btn.innerHTML = "🔍 FIND MATCHING JOBS ACROSS PLATFORMS";
                btn.disabled = false;
            } catch(e) {
                alert("Search error: " + e.message);
                btn.innerHTML = "🔍 FIND MATCHING JOBS ACROSS PLATFORMS";
                btn.disabled = false;
            }
        }

        let activeFilterMode = 'all';

        function filterJobsView(mode) {
            activeFilterMode = mode;
            const cAll = document.getElementById('filterChipAll');
            const cHigh = document.getElementById('filterChipHigh');
            const cRemote = document.getElementById('filterChipRemote');
            if (cAll) cAll.classList.toggle('active', mode === 'all');
            if (cHigh) cHigh.classList.toggle('active', mode === 'high');
            if (cRemote) cRemote.classList.toggle('active', mode === 'remote');

            if (pipelineResults)         function getAppliedTracker() {
            try {
                return JSON.parse(localStorage.getItem('ai_job_applied_tracker') || '{}');
            } catch(e) {
                return {};
            }
        }

        function recordJobStarted(jobId, company, title, method) {
            const key = jobId || (company + '_' + title).toLowerCase().replace(/[^a-z0-9]/g, '_');
            const tracker = getAppliedTracker();
            // Only set to STARTED if not already confirmed APPLIED
            if (!tracker[key] || tracker[key].status !== 'APPLIED') {
                tracker[key] = {
                    status: 'STARTED',
                    company: company,
                    title: title,
                    method: method,
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                };
                localStorage.setItem('ai_job_applied_tracker', JSON.stringify(tracker));
                updateAppliedCountUI();
            }
        }

        function confirmJobApplied(jobId, company, title) {
            const key = jobId || (company + '_' + title).toLowerCase().replace(/[^a-z0-9]/g, '_');
            const tracker = getAppliedTracker();
            const current = tracker[key] || {};
            tracker[key] = {
                status: 'APPLIED',
                company: company,
                title: title,
                method: current.method || 'Direct',
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            localStorage.setItem('ai_job_applied_tracker', JSON.stringify(tracker));
            updateAppliedCountUI();
            showToast(`✅ Job marked as CONFIRMED APPLIED!`);
            if (pipelineResults) {
                renderJobsList(pipelineResults.jobs, pipelineResults.match_results);
            }
        }

        function cancelJobTrack(jobId, company, title) {
            const key = jobId || (company + '_' + title).toLowerCase().replace(/[^a-z0-9]/g, '_');
            const tracker = getAppliedTracker();
            delete tracker[key];
            localStorage.setItem('ai_job_applied_tracker', JSON.stringify(tracker));
            updateAppliedCountUI();
            showToast(`↩️ Application status reset.`);
            if (pipelineResults) {
                renderJobsList(pipelineResults.jobs, pipelineResults.match_results);
            }
        }

        function updateAppliedCountUI() {
            const tracker = getAppliedTracker();
            let count = 0;
            Object.values(tracker).forEach(t => {
                if (t.status === 'APPLIED') count++;
            });
            const el = document.getElementById('appliedCountStat');
            if (el) {
                el.innerText = `${count} Confirmed`;
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            updateAppliedCountUI();
        });

        function renderJobsList(jobs, matches) {
            const list = document.getElementById('jobsList');
            const count = document.getElementById('resultCount');
            updateAppliedCountUI();

            if(!jobs || jobs.length === 0) {
                list.innerHTML = `
                <div class="step-card" style="text-align: center; padding: 2rem;">
                    <p style="color: var(--text-muted);">No vacancies found matching your criteria. Try adjusting location or role.</p>
                </div>`;
                count.innerText = "0 Vacancies Found";
                return;
            }

            let filteredJobs = jobs || [];
            if (activeFilterMode === 'high') {
                filteredJobs = filteredJobs.filter(j => {
                    const m = (matches || []).find(x => x.job_id === j.job_id) || {};
                    return (m.match_score || 0) >= 80;
                });
            } else if (activeFilterMode === 'remote') {
                filteredJobs = filteredJobs.filter(j => (j.work_mode || '').toLowerCase() === 'remote');
            }

            if(filteredJobs.length === 0) {
                list.innerHTML = `
                <div class="step-card" style="text-align: center; padding: 2rem;">
                    <p style="color: var(--text-muted);">No vacancies match the selected filter (${activeFilterMode}). Try switching back to "All Vacancies".</p>
                </div>`;
                count.innerText = `0 of ${jobs.length} Vacancies Displayed`;
                return;
            }

            count.innerText = `${filteredJobs.length} of ${jobs.length} Vacancies Displayed`;

            const tracker = getAppliedTracker();

            let html = "";
            filteredJobs.forEach((job) => {
                const idx = jobs.findIndex(j => j.job_id === job.job_id);
                const match = (matches || []).find(m => m.job_id === job.job_id) || {};
                const score = match.match_score || 0;
                const gap = match.skill_gap || {};
                const badgeClass = score >= 80 ? '' : 'medium';

                const jobKey = job.job_id || (job.company + '_' + job.title).toLowerCase().replace(/[^a-z0-9]/g, '_');
                const appliedInfo = tracker[jobKey];

                // Deduplicate matched skills case-insensitively
                const rawSkills = gap.matched_skills || [];
                const matchedSkills = rawSkills.filter((skill, index, self) =>
                    index === self.findIndex((s) => s.toLowerCase() === skill.toLowerCase())
                );

                // Deduplicate sources by platform name
                const uniqueSources = [];
                const seenPlatforms = new Set();
                (job.sources || []).forEach(s => {
                    const pName = s.platform || 'Platform';
                    if(!seenPlatforms.has(pName)) {
                        seenPlatforms.add(pName);
                        uniqueSources.push(s);
                    }
                });

                const compUrl = getCompanyOfficialPageUrl(job.company, job.location);
                let directUrl = job.canonical_url || (job.sources && job.sources[0] ? job.sources[0].url : '');
                
                // If URL points to generic aggregator search page, override with exact official company portal URL
                if (!directUrl || directUrl.includes('naukri.com/') || directUrl.includes('glassdoor.') || directUrl.includes('indeed.com/jobs') || directUrl.includes('/search') || directUrl === '#') {
                    directUrl = compUrl;
                }

                let appliedBadgeHtml = '';
                if (appliedInfo) {
                    if (appliedInfo.status === 'APPLIED') {
                        appliedBadgeHtml = `
                        <div class="match-badge" style="background: rgba(16, 185, 129, 0.25); border-color: #10b981; color: #34d399; font-weight: 800;" title="Applied at ${appliedInfo.time} via ${appliedInfo.method}">
                            ✓ CONFIRMED APPLIED (${appliedInfo.method})
                        </div>`;
                    } else if (appliedInfo.status === 'STARTED') {
                        appliedBadgeHtml = `
                        <div class="match-badge" style="background: rgba(245, 158, 11, 0.25); border-color: #f59e0b; color: #fbbf24; font-weight: 800;" title="Opened at ${appliedInfo.time} - Pending your confirmation">
                            ⏳ APPLICATION STARTED
                        </div>`;
                    }
                }

                const safeJobId = (job.job_id || '').replace(/'/g, "\\'");
                const safeJobComp = (job.company || '').replace(/'/g, "\\'");
                const safeJobTitle = (job.title || '').replace(/'/g, "\\'");

                let confirmBarHtml = '';
                if (appliedInfo && appliedInfo.status === 'STARTED') {
                    confirmBarHtml = `
                    <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 10px 14px; margin-top: 12px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                        <span style="font-size: 0.85rem; font-weight: 700; color: #fbbf24;">
                            ❓ Did you finish submitting your application on ${job.company}?
                        </span>
                        <div style="display: flex; gap: 8px;">
                            <button onclick="confirmJobApplied('${safeJobId}', '${safeJobComp}', '${safeJobTitle}')" class="action-btn" style="background: #10b981; color: white; border: none; font-size: 0.82rem; padding: 6px 14px;">
                                ✅ Yes, Applied!
                            </button>
                            <button onclick="cancelJobTrack('${safeJobId}', '${safeJobComp}', '${safeJobTitle}')" class="action-btn" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); font-size: 0.82rem; padding: 6px 12px;">
                                ↩️ No / Backed Out
                            </button>
                        </div>
                    </div>`;
                } else if (appliedInfo && appliedInfo.status === 'APPLIED') {
                    confirmBarHtml = `
                    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 8px 14px; margin-top: 12px; display: flex; align-items: center; justify-content: space-between;">
                        <span style="font-size: 0.82rem; font-weight: 700; color: #34d399;">
                            ✓ Application confirmed for ${job.company}.
                        </span>
                        <button onclick="cancelJobTrack('${safeJobId}', '${safeJobComp}', '${safeJobTitle}')" style="background: transparent; color: #a5b4fc; border: none; font-size: 0.8rem; cursor: pointer; text-decoration: underline;">
                            Reset Status
                        </button>
                    </div>`;
                }

                html += `
                <div class="job-card" style="${appliedInfo ? (appliedInfo.status === 'APPLIED' ? 'border: 1px solid rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.02);' : 'border: 1px solid rgba(245, 158, 11, 0.4); background: rgba(245, 158, 11, 0.02);') : ''}">
                    <div class="job-top">
                        <div>
                            <div class="job-title">
                                <a href="${directUrl}" target="_blank" rel="noopener noreferrer" style="color: #ffffff; text-decoration: none;" title="Direct official vacancy link for ${job.company} ${job.title}">
                                    ${job.title} ↗
                                </a>
                            </div>
                            <div class="job-company">
                                <a href="${compUrl}" target="_blank" rel="noopener noreferrer" style="color: var(--accent-cyan); text-decoration: underline; font-weight: 800;" title="Click to visit official ${job.company} careers page">
                                    🏢 ${job.company} ↗
                                </a>
                                &nbsp;•&nbsp; 📍 ${job.location} &nbsp;•&nbsp; 💼 ${job.work_mode}
                            </div>
                            <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-top: 4px;">
                                ✉️ Direct HR Email: <span style="color: #f1f5f9; background: rgba(56, 189, 248, 0.15); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(56, 189, 248, 0.3);">${(job.hr_email && job.hr_email.includes('@') && !job.hr_email.includes('indore.com') && !job.hr_email.includes('company.com')) ? job.hr_email : 'Apply via Official Company Portal'}</span>
                            </div>
                        </div>
                        <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                            ${appliedBadgeHtml}
                            <div class="match-badge ${badgeClass}">${score}% Match</div>
                        </div>
                    </div>

                    <p style="font-size: 0.9rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 1.2rem;">${job.description}</p>

                    <div style="margin-bottom: 12px;">
                        <span style="font-size: 0.8rem; font-weight: 700; color: var(--text-muted); display: block; margin-bottom: 4px;">YOUR MATCHED SKILLS:</span>
                        ${matchedSkills.map(s => `<span class="skill-tag" style="background: rgba(16, 185, 129, 0.15); color: #34d399; border-color: rgba(16, 185, 129, 0.3);">✓ ${s}</span>`).join('')}
                    </div>

                    <div class="job-actions">
                        <button onclick="directApplyToCompany(${idx})" class="action-btn" style="${appliedInfo && appliedInfo.status === 'APPLIED' ? 'background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #34d399;' : 'background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); color: #ffffff; border: none;'} font-weight: 800; font-size: 0.95rem; padding: 10px 18px;" title="Click to auto-download your PDFs and open the official company vacancy page directly!">
                            🚀 Direct Apply to Company (Auto-Download PDFs & Open Portal) ↗
                        </button>

                        <button onclick="openGmailWithAutoDownload(${idx})" class="action-btn" style="${appliedInfo && appliedInfo.status === 'APPLIED' ? 'background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #34d399;' : 'background: linear-gradient(135deg, #ea4335 0%, #c5221f 100%); color: #ffffff; border: none;'} font-weight: 800; font-size: 0.9rem; padding: 10px 16px;" title="Click to auto-download your Resume PDF and open Gmail with pre-filled HR email and Cover Letter!">
                            📧 Apply via Gmail ↗
                        </button>

                        ${uniqueSources.map(s => `<a href="${s.url}" target="_blank" class="action-btn">🌐 View on ${s.platform} ↗</a>`).join('')}

                        <button class="action-btn action-btn-primary" onclick="openModal(${idx})">
                            ✉️ Get Application Package (.txt)
                        </button>
                    </div>

                    ${confirmBarHtml}
                </div>
                `;
            });

            list.innerHTML = html;
        }

        function getCompanyOfficialPageUrl(company, location) {
            const cleanComp = (company || "Company").replace(" Indore", "").replace(" Surat", "").replace(" Pune", "").replace(" Delhi", "").trim();
            const knownPortals = {
                "teleperformance": "https://www.teleperformance.com/en-us/careers/",
                "tcs": "https://www.tcs.com/careers",
                "impetus": "https://www.impetus.com/careers/",
                "yash technologies": "https://www.yashtech.com/careers/",
                "webkul": "https://webkul.com/careers/",
                "systematix": "https://systematixinfotech.com/careers/",
                "flipkart": "https://www.flipkartcareers.com/",
                "zomato": "https://www.zomato.com/careers",
                "swiggy": "https://careers.swiggy.com/",
                "deqode": "https://deqode.com/careers/",
                "geeksforgeeks": "https://www.geeksforgeeks.org/careers/",
                "placementindia": "https://www.placementindia.com/"
            };
            
            const key = cleanComp.toLowerCase();
            for (const [k, url] of Object.entries(knownPortals)) {
                if (key.includes(k)) return url;
            }
            return `https://www.google.com/search?q=${encodeURIComponent(company + ' ' + (location || '') + ' official website careers overview')}`;
        }

        function directApplyToCompany(idx) {
            if (!pipelineResults || !pipelineResults.jobs || !pipelineResults.jobs[idx]) return;
            const job = pipelineResults.jobs[idx];
            const app = (pipelineResults.applications && pipelineResults.applications[idx]) ? pipelineResults.applications[idx] : null;
            const profile = pipelineResults.candidate_profile || {};

            // Step 1: Record application as STARTED (Pending user confirmation)
            recordJobStarted(job.job_id, job.company, job.title, 'Portal');

            const candName = (profile.name || "Candidate").replace(" [DEMO CANDIDATE]", "");
            const coverText = (app && app.package) ? (app.package.cover_letter || "") : "";
            const emailBody = (app && app.package) ? (app.package.hr_email_body || coverText) : coverText;

            const safeTitle = encodeURIComponent(job.title || 'Data Analyst');
            const safeComp = encodeURIComponent(job.company || 'Company');
            const safeCandName = candName.replace(/ /g, '_');
            const safeCompName = (job.company || 'Company').replace(/ /g, '_');

            // Download Resume PDF
            const link1 = document.createElement('a');
            link1.href = `/resume/download`;
            link1.download = `Resume_${safeCandName}.pdf`;
            document.body.appendChild(link1);
            link1.click();
            document.body.removeChild(link1);

            // Download Cover Letter PDF (staggered 200ms)
            setTimeout(() => {
                const link2 = document.createElement('a');
                link2.href = `/resume/cover-letter/download-pdf?title=${safeTitle}&company=${safeComp}&cover_letter=${encodeURIComponent(coverText)}`;
                link2.download = `Cover_Letter_${safeCandName}_${safeCompName}.pdf`;
                document.body.appendChild(link2);
                link2.click();
                document.body.removeChild(link2);
            }, 200);

            // Download HR Email PDF (staggered 400ms)
            setTimeout(() => {
                const link3 = document.createElement('a');
                link3.href = `/resume/hr-email/download-pdf?title=${safeTitle}&company=${safeComp}&email_body=${encodeURIComponent(emailBody)}`;
                link3.download = `HR_Email_${safeCandName}_${safeCompName}.pdf`;
                document.body.appendChild(link3);
                link3.click();
                document.body.removeChild(link3);
            }, 400);

            // Directly open official vacancy URL
            const compUrl = getCompanyOfficialPageUrl(job.company, job.location);
            let directUrl = job.canonical_url || (job.sources && job.sources[0] ? job.sources[0].url : '');
            
            if (!directUrl || directUrl.includes('naukri.com/') || directUrl.includes('glassdoor.') || directUrl.includes('indeed.com/jobs') || directUrl.includes('/search') || directUrl === '#') {
                directUrl = compUrl;
            }
            
            showToast(`🚀 PDFs Downloaded! Opening ${job.company} Portal...`);

            // Re-render UI to display yellow "APPLICATION STARTED" badge + confirmation buttons
            if (pipelineResults) {
                renderJobsList(pipelineResults.jobs, pipelineResults.match_results);
            }

            setTimeout(() => {
                window.open(directUrl, '_blank');
            }, 600);
        }

        function openGmailWithAutoDownload(idx) {
            if (!pipelineResults || !pipelineResults.jobs || !pipelineResults.jobs[idx]) return;
            const job = pipelineResults.jobs[idx];
            const app = (pipelineResults.applications && pipelineResults.applications[idx]) ? pipelineResults.applications[idx] : null;
            const profile = pipelineResults.candidate_profile || {};

            // Step 1: Record application as STARTED (Pending user confirmation)
            recordJobStarted(job.job_id, job.company, job.title, 'Gmail');
            
            let hrEmail = (job.hr_email && job.hr_email.includes('@') && !job.hr_email.includes('indore.com') && !job.hr_email.includes('company.com')) ? job.hr_email : "";
            const candName = (profile.name || "Candidate").replace(" [DEMO CANDIDATE]", "");
            const subject = app ? (app.package ? app.package.email_subject : `Application for ${job.title} Position - ${candName}`) : `Application for ${job.title} Position - ${candName}`;
            const coverText = (app && app.package) ? (app.package.cover_letter || "") : "";
            const emailBody = (app && app.package) ? (app.package.hr_email_body || coverText) : coverText;
            
            const body = emailBody + "\n\n📌 NOTE: Please find my attached Resume, Cover Letter, and HR Application PDFs attached for your review.";

            const safeTitle = encodeURIComponent(job.title || 'Data Analyst');
            const safeComp = encodeURIComponent(job.company || 'Company');
            const safeCandName = candName.replace(/ /g, '_');
            const safeCompName = (job.company || 'Company').replace(/ /g, '_');

            // Download PDF 1: Resume PDF
            const link1 = document.createElement('a');
            link1.href = `/resume/download`;
            link1.download = `Resume_${safeCandName}.pdf`;
            document.body.appendChild(link1);
            link1.click();
            document.body.removeChild(link1);

            // Download PDF 2: Cover Letter PDF (staggered 200ms)
            setTimeout(() => {
                const link2 = document.createElement('a');
                link2.href = `/resume/cover-letter/download-pdf?title=${safeTitle}&company=${safeComp}&cover_letter=${encodeURIComponent(coverText)}`;
                link2.download = `Cover_Letter_${safeCandName}_${safeCompName}.pdf`;
                document.body.appendChild(link2);
                link2.click();
                document.body.removeChild(link2);
            }, 200);

            // Download PDF 3: HR Email Draft PDF (staggered 400ms)
            setTimeout(() => {
                const link3 = document.createElement('a');
                link3.href = `/resume/hr-email/download-pdf?title=${safeTitle}&company=${safeComp}&subject=${encodeURIComponent(subject)}&email_body=${encodeURIComponent(emailBody)}`;
                link3.download = `HR_Email_${safeCandName}_${safeCompName}.pdf`;
                document.body.appendChild(link3);
                link3.click();
                document.body.removeChild(link3);
            }, 400);

            showToast(`📄 PDFs Downloaded! Opening Gmail...`);

            // Re-render UI to display yellow "APPLICATION STARTED" badge + confirmation buttons
            if (pipelineResults) {
                renderJobsList(pipelineResults.jobs, pipelineResults.match_results);
            }

            // Open Gmail Compose window (staggered 800ms)
            setTimeout(() => {
                const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(hrEmail)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
                window.open(gmailUrl, '_blank');
            }, 800);
        }

        function openModal(idx) {
            if(!pipelineResults || !pipelineResults.applications || !pipelineResults.applications[idx]) return;

            const app = pipelineResults.applications[idx];
            const pkg = app.package;

            document.getElementById('mJobTitle').innerText = app.title;
            document.getElementById('mCompany').innerText = "Company: " + app.company + " | Match Score: " + app.match_score + "%";
            document.getElementById('mSubject').value = pkg.email_subject || "";
            document.getElementById('mEmail').value = pkg.hr_email_body || "";
            document.getElementById('mCover').value = pkg.cover_letter || "";
            document.getElementById('mLinkedIn').value = pkg.linkedin_message || ("Dear Hiring Manager,\n\nI recently applied for the " + app.title + " role at " + app.company + ". I would love to connect and share how my data skills can contribute to your team.\n\nBest regards,\nCandidate");

            switchModalTab('email');
            document.getElementById('appModal').classList.add('active');
        }

        function switchModalTab(tab) {
            document.getElementById('mSectionEmail').style.display = tab === 'email' ? 'block' : 'none';
            document.getElementById('mSectionCover').style.display = tab === 'cover' ? 'block' : 'none';
            document.getElementById('mSectionLinkedIn').style.display = tab === 'linkedin' ? 'block' : 'none';

            document.getElementById('modalTabEmail').classList.toggle('active', tab === 'email');
            document.getElementById('modalTabCover').classList.toggle('active', tab === 'cover');
            document.getElementById('modalTabLinkedIn').classList.toggle('active', tab === 'linkedin');
        }

        function closeModal() {
            document.getElementById('appModal').classList.remove('active');
        }

        function copyField(id) {
            const el = document.getElementById(id);
            el.select();
            document.execCommand('copy');
            showToast("Copied to clipboard!");
        }

        async function downloadCoverLetterPDF() {
            const title = document.getElementById('mJobTitle').innerText;
            const company = document.getElementById('mCompany').innerText;
            const cover = document.getElementById('mCover').value || document.getElementById('mEmail').value;

            try {
                showToast("📄 Generating Cover Letter PDF document...");
                const res = await fetch('/resume/cover-letter/download-pdf', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title: title,
                        company: company,
                        cover_letter: cover
                    })
                });
                if (!res.ok) throw new Error("Failed to generate Cover Letter PDF");
                
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Cover_Letter_${title.replace(/[^a-z0-9]/gi, '_')}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                showToast("✅ Cover Letter PDF downloaded successfully!");
            } catch (ex) {
                showToast("Error downloading PDF: " + ex.message);
            }
        }

        async function downloadHREmailPDF() {
            const title = document.getElementById('mJobTitle').innerText;
            const company = document.getElementById('mCompany').innerText;
            const subject = document.getElementById('mSubject').value;
            const email = document.getElementById('mEmail').value;

            try {
                showToast("📧 Generating HR Email PDF document...");
                const res = await fetch('/resume/hr-email/download-pdf', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title: title,
                        company: company,
                        subject: subject,
                        email_body: email
                    })
                });
                if (!res.ok) throw new Error("Failed to generate HR Email PDF");
                
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `HR_Email_${title.replace(/[^a-z0-9]/gi, '_')}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                showToast("✅ HR Email PDF downloaded successfully!");
            } catch (ex) {
                showToast("Error downloading HR Email PDF: " + ex.message);
            }
        }

        function downloadApplicationPackage() {
            const title = document.getElementById('mJobTitle').innerText;
            const company = document.getElementById('mCompany').innerText;
            const subject = document.getElementById('mSubject').value;
            const email = document.getElementById('mEmail').value;
            const cover = document.getElementById('mCover').value;
            const linkedin = document.getElementById('mLinkedIn').value;

            const content = `=====================================================
APPLICATION PACKAGE FOR: ${title}
DETAILS: ${company}
DATE: ${new Date().toLocaleString()}
=====================================================

1. EMAIL SUBJECT LINE:
-----------------------------------------------------
${subject}

2. HR EMAIL BODY:
-----------------------------------------------------
${email}

3. FULL COVER LETTER:
-----------------------------------------------------
${cover}

4. LINKEDIN INMAIL / DIRECT MESSAGE:
-----------------------------------------------------
${linkedin}

=====================================================
Generated by 10X AI Job Search & Application Assistant
=====================================================`;

            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Application_${title.replace(/[^a-z0-9]/gi, '_')}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast("Full Application Package downloaded successfully!");
        }

        let pendingJobIdx = null;

        function openSMTPModal(jobIdx) {
            pendingJobIdx = jobIdx;
            document.getElementById('smtpModal').classList.add('active');
        }

        function closeSMTPModal() {
            document.getElementById('smtpModal').classList.remove('active');
        }

        async function saveSMTPConfigAndDispatch() {
            const email = document.getElementById('smtpEmailInput').value;
            const pass = document.getElementById('smtpPassInput').value;
            if (!email || !pass) {
                alert("Please enter both your Gmail Address and 16-character App Password.");
                return;
            }
            try {
                const res = await fetch('/config/smtp', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        sender_email: email,
                        sender_password: pass
                    })
                });
                const data = await res.json();
                showToast(data.message || "Email credentials saved!");
                closeSMTPModal();
                if (pendingJobIdx !== null) {
                    sendDirectAutoEmail(pendingJobIdx, null);
                }
            } catch (ex) {
                alert("Error saving SMTP config: " + ex.message);
            }
        }

        async function sendDirectAutoEmail(idx, btnEl) {
            if (!pipelineResults || !pipelineResults.jobs || !pipelineResults.jobs[idx]) return;
            const job = pipelineResults.jobs[idx];
            const app = (pipelineResults.applications && pipelineResults.applications[idx]) ? pipelineResults.applications[idx] : null;
            const profile = pipelineResults.candidate_profile || {};
            
            const hrEmail = job.hr_email || `hr@${job.company.toLowerCase().replace(/[^a-z0-9]/g, '')}.com`;
            const candName = (profile.name || "Candidate").replace(" [DEMO CANDIDATE]", "");
            const subject = app ? (app.package ? app.package.email_subject : `Application for ${job.title} Position - ${candName}`) : `Application for ${job.title} Position - ${candName}`;
            
            let body = "";
            if (app && app.package && app.package.hr_email_body) {
                body = app.package.hr_email_body;
            } else {
                body = `Dear Hiring Team at ${job.company},\n\nI am writing to express my strong interest in the ${job.title} position in ${job.location}.\n\nWith hands-on technical skills and project experience in data analytics, I am confident in adding immediate value to your team at ${job.company}.\n\n📌 NOTE: Please find my attached Resume PDF for your detailed review.\n\nBest regards,\n${candName}\n${profile.email || ''}\n${profile.phone || ''}`;
            }

            const originalText = btnEl ? btnEl.innerText : "";
            if (btnEl) {
                btnEl.innerText = "⏳ Sending Direct Email to HR...";
                btnEl.disabled = true;
            }

            try {
                const res = await fetch('/jobs/send-email', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        job_id: job.job_id,
                        to_email: hrEmail,
                        subject: subject,
                        body: body
                    })
                });
                const data = await res.json();
                
                if (data.status === "SENT_LIVE") {
                    showToast("✅ LIVE EMAIL SENT DIRECTLY TO HR! Resume PDF & Cover Letter attached.");
                } else {
                    // Open SMTP modal directly inside app (No Gmail web tabs)
                    openSMTPModal(idx);
                }
            } catch (e) {
                showToast("Email Dispatch error: " + e.message);
            } finally {
                if (btnEl) {
                    btnEl.innerText = originalText;
                    btnEl.disabled = false;
                }
            }
        }

        function openCompanyModal(companyName) {
            if (!companyName) return;
            document.getElementById('cCompanyName').innerText = "🏢 " + companyName;
            document.getElementById('cCompanyMeta').innerText = companyName + " — Official Company Page & Live Careers Hub";

            const officialSearchUrl = "https://www.google.com/search?q=" + encodeURIComponent(companyName + " official website careers overview");
            const linkedinSearchUrl = "https://www.linkedin.com/jobs/search/?keywords=" + encodeURIComponent(companyName);
            const googleCareersUrl = "https://www.google.com/search?q=" + encodeURIComponent(companyName + " jobs hiring");

            document.getElementById('cOfficialBtn').href = officialSearchUrl;
            document.getElementById('cLinkedInBtn').href = linkedinSearchUrl;
            document.getElementById('cGoogleBtn').href = googleCareersUrl;

            const cJobList = document.getElementById('cJobList');
            let matchingJobs = [];
            if (pipelineResults && pipelineResults.jobs) {
                matchingJobs = pipelineResults.jobs.filter(j => j.company.toLowerCase() === companyName.toLowerCase());
            }

            if (matchingJobs.length === 0) {
                cJobList.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px;">No other open positions found in current search. Use the links above to visit ${companyName}'s official careers portal directly.</div>`;
            } else {
                cJobList.innerHTML = matchingJobs.map((j) => {
                    const origIdx = pipelineResults.jobs.findIndex(x => x.job_id === j.job_id);
                    return `
                        <div style="background: rgba(255,255,255,0.05); padding: 10px 14px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--card-border);">
                            <div>
                                <div style="font-weight: 700; color: white;">${j.title}</div>
                                <div style="font-size: 0.8rem; color: var(--text-muted);">📍 ${j.location} • 💼 ${j.work_mode}</div>
                            </div>
                            <button class="action-btn action-btn-primary" style="padding: 4px 10px; font-size: 0.8rem;" onclick="closeCompanyModal(); openModal(${origIdx});">
                                ✉️ Get Application
                            </button>
                        </div>
                    `;
                }).join('');
            }

            document.getElementById('companyModal').classList.add('active');
        }

        function closeCompanyModal() {
            document.getElementById('companyModal').classList.remove('active');
        }

        function showToast(msg) {
            const toast = document.getElementById('toastMsg');
            toast.innerText = msg;
            toast.style.display = 'block';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 3000);
        }

        // DOM Ready setup
        window.addEventListener('DOMContentLoaded', () => {
            // Close modals on backdrop click
            const modal = document.getElementById('appModal');
            if (modal) {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) closeModal();
                });
            }
            const cModal = document.getElementById('companyModal');
            if (cModal) {
                cModal.addEventListener('click', (e) => {
                    if (e.target === cModal) closeCompanyModal();
                });
            }
            // Close modals on Escape key
            window.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    closeModal();
                    closeCompanyModal();
                }
            });
        });
    