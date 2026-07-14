// static/js/ui.js

/**
 * Toast Notification System
 * Displays a sliding toast notification
 */
function showToast(message, type = 'success') {
    // Check if container exists
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Set border color based on type
    const color = type === 'success' ? '#10b981' : (type === 'error' ? '#ef4444' : '#3b82f6');
    toast.style.borderLeft = `4px solid ${color}`;
    
    toast.innerHTML = `
        <div style="font-weight: 500; font-size: 0.95rem;">${message}</div>
    `;

    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
    });

    // Auto dismiss
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 400); // Wait for transition
    }, 3000);
}

// Make globally available
window.showToast = showToast;
