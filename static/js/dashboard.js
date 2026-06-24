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

    // Initialize Theme
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

    // --- Statistics and Charts ---
    let severityChart = null;
    let markersChart = null;

    function renderCharts(stats) {
        // 1. Severity Pie Chart
        const pieCtx = document.getElementById('severity-pie-chart').getContext('2d');
        if (severityChart) severityChart.destroy();
        
        severityChart = new Chart(pieCtx, {
            type: 'pie',
            data: {
                labels: ['Normal', 'Moderate', 'Critical'],
                datasets: [{
                    data: [stats.normal, stats.moderate, stats.critical],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 2,
                    borderColor: getComputedStyle(document.body).getPropertyValue('--bg-card')
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: getComputedStyle(document.body).getPropertyValue('--text-main'),
                            font: { family: 'Inter', weight: '600' }
                        }
                    }
                }
            }
        });

        // 2. Markers Bar Chart
        const barCtx = document.getElementById('markers-bar-chart').getContext('2d');
        if (markersChart) markersChart.destroy();
        
        const abnormalParams = stats.abnormal_parameters || {};
        const labels = Object.keys(abnormalParams);
        const data = Object.values(abnormalParams);

        // Fallback placeholder if no abnormal parameters exist
        const hasData = labels.length > 0;
        const displayLabels = hasData ? labels : ['No Abnormalities Found'];
        const displayData = hasData ? data : [0];
        const barColor = hasData ? '#e0295a' : '#64748b';

        markersChart = new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: displayLabels,
                datasets: [{
                    label: 'Abnormal Counts',
                    data: displayData,
                    backgroundColor: barColor,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: getComputedStyle(document.body).getPropertyValue('--text-muted')
                        },
                        grid: {
                            color: getComputedStyle(document.body).getPropertyValue('--border-color')
                        }
                    },
                    x: {
                        ticks: {
                            color: getComputedStyle(document.body).getPropertyValue('--text-muted'),
                            font: { family: 'Inter', size: 9 }
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    async function loadDashboardData() {
        try {
            // Load Profile Stats
            const resStats = await fetch('/api/profile');
            const dataStats = await resStats.json();
            
            if (resStats.ok) {
                // Update text stats
                document.getElementById('stat-total').textContent = dataStats.stats.total;
                document.getElementById('stat-normal').textContent = dataStats.stats.normal;
                document.getElementById('stat-moderate').textContent = dataStats.stats.moderate;
                document.getElementById('stat-critical').textContent = dataStats.stats.critical;
                
                // Update avatar details
                const fullName = dataStats.user.fullname;
                document.getElementById('profile-card-name').textContent = fullName;
                document.getElementById('user-display-name').textContent = fullName;
                document.getElementById('profile-card-email').textContent = dataStats.user.email;
                
                const initials = fullName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
                document.getElementById('profile-avatar-letters').textContent = initials;
                
                // Render Chart visuals
                renderCharts(dataStats.stats);
            }
            
            // Load Recent reports
            const resReports = await fetch('/api/reports?sort_by=date_desc');
            const dataReports = await resReports.json();
            
            if (resReports.ok) {
                const container = document.getElementById('recent-reports-container');
                container.innerHTML = '';
                
                const reports = dataReports.reports.slice(0, 4); // Show top 4
                
                if (reports.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state" style="padding: 1.5rem; border: none; box-shadow: none;">
                            <span style="font-size: 0.85rem;">No reports uploaded yet.</span>
                        </div>
                    `;
                } else {
                    reports.forEach(report => {
                        const dateObj = new Date(report.upload_date);
                        const formattedDate = dateObj.toLocaleDateString('en-US', {
                            month: 'short', day: 'numeric', year: 'numeric'
                        });
                        
                        const item = document.createElement('a');
                        item.className = 'recent-item';
                        item.href = `/history?view_id=${report.id}`;
                        item.innerHTML = `
                            <div class="recent-info">
                                <span class="recent-name">${report.report_name}</span>
                                <span class="recent-date">${formattedDate}</span>
                            </div>
                            <span class="badge ${report.severity.toLowerCase()}">${report.severity}</span>
                        `;
                        container.appendChild(item);
                    });
                }
            }
        } catch (err) {
            console.error("Failed to load dashboard statistics:", err);
        }
    }

    loadDashboardData();


    // --- File Drag and Drop / Upload Controls ---
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const processingView = document.getElementById('processing-view');
    const uploadProgress = document.getElementById('upload-progress');
    const statusMessage = document.getElementById('status-message');

    // Drag-over styling hooks
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    // Trigger upload on file drop
    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    });

    // Trigger upload on click and file selection
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            uploadFile(fileInput.files[0]);
        }
    });

    // Main file upload operation
    async function uploadFile(file) {
        // Client-side safety checks
        const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
        const allowedExtensions = ['.pdf', '.png', '.jpg', '.jpeg'];
        
        const ext = file.name.slice(((file.name.lastIndexOf(".") - 1) >>> 0) + 2).toLowerCase();
        
        if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(`.${ext}`)) {
            showToast('Invalid file format! Please upload PDF, PNG, JPG, or JPEG.', 'error');
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) {
            showToast('File is too large! Maximum limit is 10MB.', 'error');
            return;
        }

        // Show loading progress
        dropZone.style.display = 'none';
        processingView.classList.add('active');
        uploadProgress.style.width = '10%';
        statusMessage.textContent = 'Uploading report file to secure server...';

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Animate progress loading bar
            let progress = 10;
            const interval = setInterval(() => {
                if (progress < 90) {
                    progress += 15;
                    uploadProgress.style.width = `${progress}%`;
                    if (progress > 50) statusMessage.textContent = 'Extracting clinical biomarkers...';
                    if (progress > 80) statusMessage.textContent = 'Running rule-based AI engine...';
                }
            }, 300);

            const response = await fetch('/api/reports/upload', {
                method: 'POST',
                body: formData
            });
            
            clearInterval(interval);
            const result = await response.json();

            if (response.ok) {
                uploadProgress.style.width = '100%';
                statusMessage.textContent = 'Report processed successfully!';
                showToast('Analysis completed successfully!', 'success');
                
                // Wait briefly and redirect to history page to view details
                setTimeout(() => {
                    window.location.href = `/history?view_id=${result.report_id}`;
                }, 1000);
            } else {
                showToast(result.error || 'Failed to process report.', 'error');
                resetUploadUI();
            }
        } catch (err) {
            console.error("Upload error:", err);
            showToast('Network error. Failed to analyze report.', 'error');
            resetUploadUI();
        }
    }

    function resetUploadUI() {
        processingView.classList.remove('active');
        dropZone.style.display = 'flex';
        fileInput.value = '';
    }

    // --- Demo Quick-Load Buttons (OCR fallbacks triggers) ---
    const demoNormal = document.getElementById('demo-normal');
    const demoModerate = document.getElementById('demo-moderate');
    const demoCritical = document.getElementById('demo-critical');

    const DEMO_REPORTS = {
        normal: `ANNUAL HEALTH CHECKUP REPORT\nPatient Name: Rahul Sharma\nDate: 2026-06-24\n\nLABORATORY RESULTS:\nHemoglobin (Hb): 14.8 g/dL\nFasting Glucose: 88 mg/dL\nVitamin D: 38.0 ng/mL\nVitamin B12: 450 pg/mL\nTotal Cholesterol: 175 mg/dL\nHDL: 55 mg/dL\nLDL: 90 mg/dL\nTriglycerides: 120 mg/dL\nTSH: 2.1 uIU/mL\nPlatelet Count: 280000 /uL\nCreatinine: 0.9 mg/dL\nALT (SGPT): 24 U/L\nAST (SGOT): 22 U/L\nWBC Count: 7200 /uL\nRBC Count: 5.1 million/uL`,

        moderate: `CLINICAL BIOCHEMISTRY REPORT\nPatient Name: Priya Singh\nDate: 2026-06-24\n\nLAB TEST RESULTS:\nHemoglobin: 11.2 g/dL\nFasting Glucose: 118 mg/dL\nVitamin D: 22.0 ng/mL\nVitamin B12: 180 pg/mL\nTotal Cholesterol: 215 mg/dL\nLDL: 135 mg/dL\nHDL: 45 mg/dL\nTriglycerides: 148 mg/dL\nPlatelet Count: 180000 /uL\nTSH: 2.5 uIU/mL\nCreatinine: 1.1 mg/dL\nALT: 42 U/L`,

        critical: `PATIENT MEDICAL REPORT\nPatient Name: Amit Kumar\nDate: 2026-06-24\n\nLABORATORY EXAMINATION SUMMARY:\nHemoglobin (Hb): 7.2 g/dL\nFasting Glucose: 185 mg/dL\nVitamin D3: 8.5 ng/mL\nTotal Cholesterol: 265 mg/dL\nHDL Cholesterol: 32 mg/dL\nLDL Cholesterol: 178 mg/dL\nTriglycerides: 210 mg/dL\nTSH: 6.2 uIU/mL\nPlatelet Count: 82000 /uL\nCreatinine: 2.3 mg/dL\nALT (SGPT): 110 U/L\nAST (SGOT): 95 U/L\nBilirubin: 2.4 mg/dL\nBUN: 28 mg/dL\nWBC Count: 14500 /uL\nRBC Count: 3.1 million/uL`
    };

    function textToFile(text, filename) {
        const blob = new Blob([text], { type: 'text/plain' });
        return new File([blob], filename, { type: 'text/plain' });
    }

    if (demoNormal) {
        demoNormal.addEventListener('click', () => {
            uploadFile(textToFile(DEMO_REPORTS.normal, 'demo_normal_report.txt'));
        });
    }
    if (demoModerate) {
        demoModerate.addEventListener('click', () => {
            uploadFile(textToFile(DEMO_REPORTS.moderate, 'demo_moderate_report.txt'));
        });
    }
    if (demoCritical) {
        demoCritical.addEventListener('click', () => {
            uploadFile(textToFile(DEMO_REPORTS.critical, 'demo_critical_report.txt'));
        });
    }

    // Utility: Toast notifications
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${message}</span>`;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s reverse forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }
});
