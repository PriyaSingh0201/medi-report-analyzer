document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const errorAlert = document.getElementById('error-alert');
    const errorText = document.getElementById('error-text');
    const submitBtn = document.getElementById('submit-btn');

    // Utility: Show alerts
    function showAlert(message) {
        errorText.textContent = message;
        errorAlert.classList.add('visible');
    }

    // Utility: Hide alerts
    function hideAlert() {
        errorAlert.classList.remove('visible');
    }

    // Utility: Show Toast Notifications
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span>${message}</span>
        `;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s reverse forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Handle Login Submit
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();

            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;

            if (!email || !password) {
                showAlert('Please fill in all fields!');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Logging in...';

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const result = await response.json();

                if (response.ok) {
                    showToast('Login successful! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1000);
                } else {
                    showAlert(result.error || 'Invalid credentials!');
                }
            } catch (err) {
                showAlert('Network error. Please try again later.');
                console.error(err);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Log In';
            }
        });
    }

    // Handle Register Submit
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();

            const fullname = document.getElementById('fullname').value.trim();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;

            // Form Validations
            if (!fullname || !email || !password || !confirmPassword) {
                showAlert('All fields are required!');
                return;
            }

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                showAlert('Please enter a valid email address!');
                return;
            }

            if (password.length < 8) {
                showAlert('Password must be at least 8 characters long!');
                return;
            }

            if (password !== confirmPassword) {
                showAlert('Passwords do not match!');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Registering...';

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        fullname,
                        email,
                        password,
                        confirm_password: confirmPassword
                    })
                });
                const result = await response.json();

                if (response.ok) {
                    showToast(result.message, 'success');
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                } else {
                    showAlert(result.error || 'Registration failed.');
                }
            } catch (err) {
                showAlert('Network error. Please try again later.');
                console.error(err);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Register';
            }
        });
    }
});
