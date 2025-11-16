// Main JavaScript for Django Skeleton

// Initialize Alpine.js components
document.addEventListener('alpine:init', () => {
    // Global Alpine data or components can be defined here
    Alpine.data('globalSearch', () => ({
        query: '',
        results: [],
        loading: false,

        async search() {
            if (this.query.length < 2) {
                this.results = [];
                return;
            }

            this.loading = true;
            // Implement search logic here
            setTimeout(() => {
                this.loading = false;
            }, 500);
        }
    }));
});

// HTMX Event Handlers
document.body.addEventListener('htmx:configRequest', (event) => {
    // Add CSRF token to all HTMX requests
    event.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
});

document.body.addEventListener('htmx:afterSwap', (event) => {
    // Re-initialize any JavaScript components after HTMX swap
    console.log('HTMX content swapped');
});

document.body.addEventListener('htmx:sendError', (event) => {
    console.error('HTMX request failed:', event.detail);
    showNotification('Request failed. Please try again.', 'error');
});

// Utility Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showNotification(message, type = 'info') {
    // Create and show a notification
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-md bg-${type === 'error' ? 'red' : 'green'}-100 text-${type === 'error' ? 'red' : 'green'}-800 fade-in z-50`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

// Auto-hide messages after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
    const messages = document.querySelectorAll('[x-data="{ show: true }"]');
    messages.forEach(message => {
        setTimeout(() => {
            // Trigger Alpine.js to hide the message
            message.__x.$data.show = false;
        }, 5000);
    });
});

// Enable HTMX debugging in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    htmx.config.useTemplateFragments = true;
    htmx.logAll();
}

// Custom HTMX extension for handling JSON responses
htmx.defineExtension('json-enc', {
    onEvent: function(name, evt) {
        if (name === 'htmx:configRequest') {
            evt.detail.headers['Content-Type'] = 'application/json';
        }
    },
    encodeParameters: function(xhr, parameters, elt) {
        xhr.overrideMimeType('text/json');
        return JSON.stringify(parameters);
    }
});