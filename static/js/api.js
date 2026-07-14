// Core API utility methods for Fetch

export const API_BASE = '/api';

export async function fetchAPI(endpoint, options = {}) {
    const defaultHeaders = {
        'Content-Type': 'application/json'
    };

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        
        // Handle unauthorized globally
        if (response.status === 401 && window.location.pathname !== '/') {
            window.location.href = '/';
            return;
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            logActivity('ERROR', `API Error [${response.status}] at ${endpoint}: ${data.error || 'Unknown'}`);
            throw new Error(data.error || 'API request failed');
        }

        return data;
    } catch (error) {
        throw error;
    }
}

// Global Activity Logger
export async function logActivity(action_type, description, user_name = null) {
    try {
        const payload = { action_type, description };
        if (user_name) payload.user_name = user_name;
        
        // We bypass fetchAPI here to avoid infinite error loops if logging fails
        await fetch(`${API_BASE}/logs/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    } catch(e) {
        console.error("Logging failed", e);
    }
}
