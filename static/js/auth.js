import { fetchAPI, logActivity } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const errorMsg = document.getElementById('error-message');
    const btn = document.getElementById('login-btn');
    const togglePasswordBtn = document.getElementById('toggle-password');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');

    if (togglePasswordBtn) {
        togglePasswordBtn.addEventListener('click', () => {
            const eyeIcon = document.getElementById('eye-icon');
            const eyeOffIcon = document.getElementById('eye-off-icon');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                if (eyeIcon) eyeIcon.style.display = 'none';
                if (eyeOffIcon) eyeOffIcon.style.display = 'block';
            } else {
                passwordInput.type = 'password';
                if (eyeIcon) eyeIcon.style.display = 'block';
                if (eyeOffIcon) eyeOffIcon.style.display = 'none';
            }
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorMsg.classList.add('hidden');
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // Simple styling for button processing state
            const originalText = btn.innerHTML;
            btn.innerHTML = 'Signing In...';
            btn.disabled = true;

            try {
                const res = await fetchAPI('/auth/login', {
                    method: 'POST',
                    body: JSON.stringify({ email, password })
                });

                if (res.user) {
                    await logActivity('LOGIN', `User successfully logged in.`);
                    window.location.href = '/dashboard';
                }
            } catch (err) {
                await logActivity('LOGIN_FAILED', `Failed login attempt for ${email}`, email);
                errorMsg.textContent = err.message;
                errorMsg.classList.remove('hidden');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }
});
