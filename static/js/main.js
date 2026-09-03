/**
 * main.js - Client-side interactivity for Personal Expense Tracker
 * Handles mobile navbar toggle, alert dismissals, delete confirmation modals, and Chart.js helpers.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Navbar Toggle
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    // 2. Alert Dismissal
    const alertCloseButtons = document.querySelectorAll('.alert-close');
    alertCloseButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alert = e.target.closest('.alert');
            if (alert) {
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';
                setTimeout(() => alert.remove(), 250);
            }
        });
    });

    // Auto-dismiss success flash messages after 5 seconds
    const successAlerts = document.querySelectorAll('.alert-success');
    successAlerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';
                setTimeout(() => alert.remove(), 250);
            }
        }, 5000);
    });

    // 3. Delete Confirmation Modal
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const itemTitle = button.getAttribute('data-item-title') || 'this expense';
            const confirmed = window.confirm(`Are you sure you want to delete "${itemTitle}"? This action cannot be undone.`);
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });
});
