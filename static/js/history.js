document.addEventListener('DOMContentLoaded', () => {
    // --- Dark Mode Theme Toggle ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');

    function updateThemeUI(isDark) {
        if (isDark) {
            document.body.classList.add('dark-mode');
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
        } else {
            document.body.classList.remove('dark-mode');
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'block';
        }
    }

    const isDarkTheme = localStorage.getItem('theme') === 'dark';
    updateThemeUI(isDarkTheme);

    themeToggleBtn.addEventListener('click', () => {
        const isDark = document.body.classList.toggle('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        updateThemeUI(isDark);
    });

    // --- Logout Handler ---
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/auth/logout', { method: 'POST' });
                if (response.ok) {
                    window.location.href = '/login';
                }
            } catch (err) {
                console.error("Logout failed:", err);
            }
        });
    }

    // --- Filter & Search state variables ---
    const searchInput = document.getElementById('search-input');
    const filterSeverity = document.getElementById('filter-severity');
    const sortBy = document.getElementById('sort-by');
    const historyContainer = document.getElementById('history-container');

    const analysisPanel = document.getElementById('analysis-panel');
    let searchDebounceTimeout = null;
    let reportsList = []; // local cache of fetched reports

    // Fetch reports from API
    async function fetchReports() {
        const queryParams = new URLSearchParams({
            search: searchInput.value.trim(),
            severity: filterSeverity.value,
            sort_by: sortBy.value
        });
        
        try {
            const response = await fetch(`/api/reports?${queryParams.toString()}`);
            const result = await response.json();
            
            if (response.ok) {
                reportsList = result.reports;
                renderReportsList(reportsList);
                checkURLParameters();
            } else {
                showToast(result.error || 'Failed to fetch reports.', 'error');
            }
        } catch (err) {
            console.error("Fetch reports error:", err);
            showToast('Network error loading history.', 'error');
        }
    }

    // Render reports cards
    function renderReportsList(reports) {
        historyContainer.innerHTML = '';
        
        if (reports.length === 0) {
            historyContainer.innerHTML = `
                <div class="empty-state">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    <p>No medical reports found matching your criteria.</p>
                </div>
            `;
            return;
        }

        reports.forEach(report => {
            const dateObj = new Date(report.upload_date);
            const formattedDate = dateObj.toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
            });

            const card = document.createElement('div');
            card.className = 'history-card';
            card.innerHTML = `
                <div class="report-meta">
                    <span class="report-title">${report.report_name}</span>
                    <span class="report-date">Uploaded: ${formattedDate}</span>
                </div>
                <div>
                    <span class="badge ${report.severity.toLowerCase()}">${report.severity}</span>
                </div>
                <div style="font-weight: 500; font-size: 0.85rem; color: var(--text-muted);">
                    ${Object.keys(report.key_findings).length} Biomarkers
                </div>
                <div class="history-actions">
                    <button class="btn btn-secondary btn-view" data-id="${report.id}" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">View</button>
                    <a href="/api/reports/${report.id}/download" class="btn btn-primary" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Download</a>
                    <button class="btn btn-secondary btn-delete" data-id="${report.id}" style="padding: 0.4rem 0.8rem; font-size: 0.8rem; border-color: rgba(239, 68, 68, 0.2); color: #ef4444;">Delete</button>
                </div>
            `;
            
            // Event listeners
            card.querySelector('.btn-view').addEventListener('click', () => showReportAnalysis(report.id));
            card.querySelector('.btn-delete').addEventListener('click', () => deleteReport(report.id));
            
            historyContainer.appendChild(card);
        });
    }

    // View specific report analysis
    function showReportAnalysis(reportId) {
        const report = reportsList.find(r => r.id === reportId);
        if (!report) return;

        // Cancel any active speech reading
        stopVoiceSummary();

        // Title and header actions
        document.getElementById('view-report-name').textContent = report.report_name;
        
        const dateObj = new Date(report.upload_date);
        const formattedDate = dateObj.toLocaleDateString('en-US', {
            month: 'long', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
        });
        document.getElementById('view-report-date').textContent = `Uploaded on ${formattedDate}`;

        // Badge update
        const badge = document.getElementById('view-severity-badge');
        badge.className = `badge ${report.severity.toLowerCase()}`;
        badge.textContent = report.severity;

        // Download href link
        document.getElementById('view-download-pdf').href = `/api/reports/${report.id}/download`;

        // Summary Text
        document.getElementById('view-summary').textContent = report.summary;
        document.getElementById('view-deficiency-text').textContent = report.deficiency_summary || 'No deficiency summary available.';

        // Alerts Banners List
        const alertsContainer = document.getElementById('view-alerts-list');
        alertsContainer.innerHTML = '';
        if (report.alerts && report.alerts.length > 0) {
            report.alerts.forEach(alertText => {
                const alertBox = document.createElement('div');
                alertBox.className = 'alert-item-card';
                alertBox.innerHTML = `
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
                    </svg>
                    <span>${alertText}</span>
                `;
                alertsContainer.appendChild(alertBox);
            });
        }

        // Biomarker list table rows
        const tableBody = document.getElementById('view-biomarker-rows');
        tableBody.innerHTML = '';

        const ranges = {
            "Hemoglobin": "12.0 - 17.5 g/dL",
            "Glucose": "70 - 100 mg/dL (Fasting)",
            "Vitamin D": "30.0 - 100.0 ng/mL",
            "Vitamin B12": "200.0 - 900.0 pg/mL",
            "Cholesterol": "< 200 mg/dL",
            "HDL": "> 40 mg/dL",
            "LDL": "< 100 mg/dL",
            "Triglycerides": "< 150 mg/dL",
            "TSH": "0.4 - 4.5 uIU/mL",
            "Platelets": "150,000 - 450,000 /uL",
            "RBC": "4.0 - 5.9 million/uL",
            "WBC": "4,500 - 11,000 /uL",
            "Creatinine": "0.6 - 1.2 mg/dL",
            "ALT": "< 56 U/L",
            "AST": "< 40 U/L",
            "Bilirubin": "0.1 - 1.2 mg/dL",
            "BUN": "7.0 - 20.0 mg/dL"
        };

        const findingsKeys = Object.keys(report.key_findings);
        if (findingsKeys.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center;">No structured biomarkers were parsed from this report.</td>
                </tr>
            `;
        } else {
            findingsKeys.forEach(key => {
                const finding = report.key_findings[key];
                const referenceRange = finding.reference_range || ranges[key] || "N/A";
                const suggestion = finding.suggestion || "—";
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td style="font-weight: 600; color: var(--text-main);">${key}</td>
                    <td>${finding.value} ${finding.unit}</td>
                    <td>${referenceRange}</td>
                    <td><span class="status-badge ${finding.status.toLowerCase()}">${finding.status}</span></td>
                    <td style="font-size: 0.82rem; color: var(--text-muted);">${suggestion}</td>
                `;
                tableBody.appendChild(row);
            });
        }

        // Doctor Suggestions section
        const suggestionsSection = document.getElementById('view-suggestions-section');
        const suggestionsList = document.getElementById('view-suggestions-list');
        suggestionsList.innerHTML = '';
        const suggestions = report.suggestions || [];
        if (suggestions.length > 0) {
            suggestions.forEach(s => {
                const li = document.createElement('li');
                li.textContent = s;
                suggestionsList.appendChild(li);
            });
            suggestionsSection.style.display = 'block';
        } else {
            suggestionsSection.style.display = 'none';
        }

        // Show panel
        analysisPanel.classList.add('active');
        analysisPanel.scrollIntoView({ behavior: 'smooth' });
    }

    // Delete a report
    async function deleteReport(reportId) {
        if (!confirm('Are you sure you want to permanently delete this report and its files?')) {
            return;
        }

        try {
            const response = await fetch(`/api/reports/${reportId}`, { method: 'DELETE' });
            const result = await response.json();
            
            if (response.ok) {
                showToast('Report deleted successfully!', 'success');
                // If the deleted report is currently open in analysis, hide panel
                if (analysisPanel.classList.contains('active')) {
                    analysisPanel.classList.remove('active');
                }
                stopVoiceSummary();
                fetchReports(); // reload history list
            } else {
                showToast(result.error || 'Failed to delete report.', 'error');
            }
        } catch (err) {
            console.error("Delete report error:", err);
            showToast('Network error deleting report.', 'error');
        }
    }

    // --- Web Speech API Voice Summary implementation (Bonus Feature) ---
    const voicePlayBtn = document.getElementById('voice-play-btn');
    const voiceStopBtn = document.getElementById('voice-stop-btn');
    let currentSpeechUtterance = null;

    function playVoiceSummary() {
        if (!('speechSynthesis' in window)) {
            showToast('Your browser does not support Speech Synthesis API.', 'error');
            return;
        }

        const summaryText = document.getElementById('view-summary').textContent.trim();
        if (!summaryText) return;

        window.speechSynthesis.cancel(); // clear previous speech queue

        currentSpeechUtterance = new SpeechSynthesisUtterance(summaryText);
        
        // Visual indicator swapping
        currentSpeechUtterance.onstart = () => {
            voicePlayBtn.style.display = 'none';
            voiceStopBtn.style.display = 'inline-flex';
        };

        currentSpeechUtterance.onend = currentSpeechUtterance.onerror = () => {
            voicePlayBtn.style.display = 'inline-flex';
            voiceStopBtn.style.display = 'none';
        };

        window.speechSynthesis.speak(currentSpeechUtterance);
    }

    function stopVoiceSummary() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            voicePlayBtn.style.display = 'inline-flex';
            voiceStopBtn.style.display = 'none';
        }
    }

    voicePlayBtn.addEventListener('click', playVoiceSummary);
    voiceStopBtn.addEventListener('click', stopVoiceSummary);


    // --- Search input event triggers (with debouncing) ---
    searchInput.addEventListener('input', () => {
        clearTimeout(searchDebounceTimeout);
        searchDebounceTimeout = setTimeout(() => {
            fetchReports();
        }, 350);
    });

    filterSeverity.addEventListener('change', fetchReports);
    sortBy.addEventListener('change', fetchReports);


    // Check if redirect parameters exist (e.g. view_id parameter from Dashboard)
    function checkURLParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const viewId = urlParams.get('view_id');
        if (viewId) {
            const reportIdNum = parseInt(viewId);
            // Verify if the report exists in our reports list, then trigger view
            const hasReport = reportsList.some(r => r.id === reportIdNum);
            if (hasReport) {
                showReportAnalysis(reportIdNum);
                
                // Clear URL parameters without reloading page to clean address bar
                window.history.replaceState({}, document.title, window.location.pathname);
            }
        }
    }

    // Initial load
    fetchReports();

    // Utility: Show Toast Notifications
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${message}</span>`;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s reverse forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});
