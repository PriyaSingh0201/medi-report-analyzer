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

    // --- Fetch and Display Profile Details ---
    async function loadProfileData() {
        try {
            const response = await fetch('/api/profile');
            const result = await response.json();
            
            if (response.ok) {
                const user = result.user;
                const stats = result.stats;
                
                // Update basic user labels
                document.getElementById('profile-fullname').textContent = user.fullname;
                document.getElementById('profile-email').textContent = user.email;
                document.getElementById('profile-avatar').textContent = user.fullname.charAt(0).toUpperCase();
                
                // Format Registration Date
                const joinDate = new Date(user.created_at);
                const formattedDate = joinDate.toLocaleDateString('en-US', {
                    month: 'long', day: 'numeric', year: 'numeric'
                });
                document.getElementById('profile-joined').textContent = formattedDate;
                
                // Update total uploads count
                document.getElementById('profile-total-reports').textContent = stats.total;
            } else {
                showToast(result.error || 'Failed to load profile details.', 'error');
            }
        } catch (err) {
            console.error("Profile load error:", err);
            showToast('Network error loading profile stats.', 'error');
        }
    }

    loadProfileData();

    // --- Change Password Form Submit ---
    const changePasswordForm = document.getElementById('change-password-form');
    const successAlert = document.getElementById('success-alert');
    const successText = document.getElementById('success-text');
    const errorAlert = document.getElementById('error-alert');
    const errorText = document.getElementById('error-text');

    changePasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Clear previous notifications
        successAlert.classList.remove('visible');
        errorAlert.classList.remove('visible');

        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmNewPassword = document.getElementById('confirm-new-password').value;

        // Validations
        if (!currentPassword || !newPassword || !confirmNewPassword) {
            showError('All fields are required!');
            return;
        }

        if (newPassword.length < 8) {
            showError('New password must be at least 8 characters long!');
            return;
        }

        if (newPassword !== confirmNewPassword) {
            showError('New passwords do not match!');
            return;
        }

        try {
            const response = await fetch('/api/auth/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword,
                    confirm_new_password: confirmNewPassword
                })
            });
            const result = await response.json();

            if (response.ok) {
                successText.textContent = result.message || 'Password updated successfully!';
                successAlert.classList.add('visible');
                changePasswordForm.reset();
                showToast('Password changed successfully!', 'success');
                
                // Hide banner after 4 seconds
                setTimeout(() => {
                    successAlert.classList.remove('visible');
                }, 4000);
            } else {
                showError(result.error || 'Failed to change password.');
            }
        } catch (err) {
            console.error("Change password error:", err);
            showError('Network error. Please try again.');
        }
    });

    function showError(message) {
        errorText.textContent = message;
        errorAlert.classList.add('visible');
        showToast(message, 'error');
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
        }, 3000);
    }
});
