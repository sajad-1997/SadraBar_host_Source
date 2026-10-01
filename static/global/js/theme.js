/* ==================== Global Theme System ==================== */

// Theme Management
(function() {
    'use strict';

    // Check for saved theme preference or default to system preference
    const getPreferredTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };

    // Apply theme to document
    const setTheme = (theme) => {
        if (theme === 'dark') {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
        localStorage.setItem('theme', theme);
        
        // Update Chart.js colors if available
        if (typeof Chart !== 'undefined') {
            Chart.defaults.color = theme === 'dark' ? '#cbd5e1' : '#475569';
            Chart.defaults.borderColor = theme === 'dark' ? 'rgba(148, 163, 184, 0.15)' : 'rgba(100, 116, 139, 0.15)';
        }
    };

    // Initialize theme on page load
    const initTheme = () => {
        const preferredTheme = getPreferredTheme();
        setTheme(preferredTheme);
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                setTheme(e.matches ? 'dark' : 'light');
            }
        });
    };

    // Toggle theme function
    window.toggleTheme = () => {
        const currentTheme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }
})();

/* ==================== Common Utilities ==================== */

// Password toggle functionality
window.togglePassword = function(inputId, toggleButton) {
    const passwordInput = document.getElementById(inputId);
    if (!passwordInput) return;
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        if (toggleButton) {
            toggleButton.textContent = '🙈';
        }
    } else {
        passwordInput.type = 'password';
        if (toggleButton) {
            toggleButton.textContent = '👁️';
        }
    }
};

// Form validation helper
window.validateForm = function(formElement) {
    const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = 'var(--global-danger)';
            isValid = false;
        } else {
            input.style.borderColor = 'var(--global-border)';
        }
    });
    
    return isValid;
};

// Auto-dismiss alerts after 5 seconds
window.setupAutoDismissAlerts = function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.3s ease';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
};

// Copy to clipboard helper
window.copyToClipboard = function(text, buttonElement) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = buttonElement.textContent;
        buttonElement.textContent = '✓ کپی شد';
        setTimeout(() => {
            buttonElement.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
};

// Initialize common functionality on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Setup auto-dismiss alerts
    setupAutoDismissAlerts();
    
    // Add form validation listeners
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
});
