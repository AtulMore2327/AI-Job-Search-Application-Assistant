/**
 * Modern UI Utilities Module for AI Job Search Assistant.
 * Manages toast alerts, error banners, drag-and-drop handlers, circular score dials, and clipboard copying.
 */

const UI = {
  showError(message) {
    const errorBox = document.getElementById('api-error-display');
    let friendlyMsg = message;

    if (typeof message === 'object') {
      friendlyMsg = message.detail || message.message || 'An unexpected request error occurred.';
    } else if (typeof message === 'string') {
      if (message.includes('Traceback') || message.includes('File "') || message.includes('line ')) {
        friendlyMsg = 'An unexpected server error occurred. Please try again.';
      }
    }

    if (errorBox) {
      errorBox.innerHTML = `
        <span>⚠️ ${this.escapeHTML(friendlyMsg)}</span>
        <button type="button" class="btn-clear" onclick="UI.clearError()">✕</button>
      `;
      errorBox.style.display = 'flex';
      errorBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    this.showToast(friendlyMsg, 'error');
  },

  clearError() {
    const errorBox = document.getElementById('api-error-display');
    if (errorBox) {
      errorBox.innerHTML = '';
      errorBox.style.display = 'none';
    }
  },

  showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = 'position: fixed; bottom: 24px; right: 24px; z-index: 9999; display: flex; flex-direction: column; gap: 8px;';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const colors = {
      success: { bg: '#10b981', border: '#059669', icon: '✓' },
      error: { bg: '#ef4444', border: '#dc2626', icon: '✕' },
      warning: { bg: '#f59e0b', border: '#d97706', icon: '⚠️' },
      info: { bg: '#4f46e5', border: '#4338ca', icon: 'ℹ️' }
    };

    const style = colors[type] || colors.info;

    toast.style.cssText = `
      padding: 12px 18px;
      border-radius: 8px;
      color: #ffffff;
      font-size: 0.9rem;
      font-weight: 500;
      box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
      background-color: ${style.bg};
      display: flex;
      align-items: center;
      gap: 10px;
      transition: all 0.3s ease;
    `;

    let cleanMsg = typeof message === 'object' ? (message.detail || JSON.stringify(message)) : message;
    if (cleanMsg.includes('Traceback')) cleanMsg = 'A request error occurred.';

    toast.innerHTML = `<span>${style.icon}</span> <span>${this.escapeHTML(cleanMsg)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  escapeHTML(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  async copyToClipboard(text, successMsg = 'Copied to clipboard!') {
    if (!text) {
      this.showToast('Nothing to copy yet.', 'warning');
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      this.showToast(successMsg, 'success');
    } catch (err) {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      this.showToast(successMsg, 'success');
    }
  },

  updateScoreCircle(score) {
    const numEl = document.getElementById('match-score-number');
    const circleEl = document.getElementById('score-circle-element');
    
    const val = score !== null && score !== undefined ? Math.round(score) : 74;
    
    if (numEl) numEl.textContent = `${val}%`;
    if (circleEl) {
      let color = '#4f46e5';
      if (val < 50) color = '#ef4444';
      else if (val < 75) color = '#f59e0b';
      else color = '#10b981';

      circleEl.style.background = `conic-gradient(${color} ${val}%, #c7d2fe 0)`;
      if (numEl) numEl.style.color = color;
    }
  },

  renderMatchBadge(score) {
    if (score === null || score === undefined) return '<span class="chip">Match: N/A</span>';
    const s = Math.round(score);
    let chipClass = 'chip-primary';
    if (s < 50) chipClass = 'chip-warning';
    else if (s >= 75) chipClass = 'chip-success';
    return `<span class="${chipClass}">🎯 ${s}% Match</span>`;
  },

  isValidIndividualJobUrl(url) {
    if (!url || typeof url !== 'string') return false;
    const lower = url.trim().toLowerCase();
    if (!lower.startsWith('http://') && !lower.startsWith('https://')) return false;
    if (lower.includes('localhost') || lower.includes('127.0.0.1') || lower.includes('0.0.0.0')) return false;
    return true;
  },

  getVerifiedJobUrl(job) {
    if (!job) return null;
    if (job.canonical_url && this.isValidIndividualJobUrl(job.canonical_url)) {
      return job.canonical_url;
    }
    if (job.source_urls && Array.isArray(job.source_urls)) {
      for (const src of job.source_urls) {
        if (this.isValidIndividualJobUrl(src)) return src;
      }
    }
    return null;
  },

  openJobInNewTab(url) {
    if (!url || !this.isValidIndividualJobUrl(url)) {
      this.showToast('Original job link unavailable.', 'warning');
      return;
    }
    window.open(url, '_blank', 'noopener,noreferrer');
  },

  setupDragAndDrop(dropZoneId, onFileSelected) {
    const zone = document.getElementById(dropZoneId);
    if (!zone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      zone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      zone.addEventListener(eventName, () => zone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      zone.addEventListener(eventName, () => zone.classList.remove('dragover'), false);
    });

    zone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        if (typeof onFileSelected === 'function') {
          onFileSelected(dt.files[0]);
        }
      }
    });
  },

  switchTab(tabId) {
    const target = document.getElementById(tabId);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  }
};
