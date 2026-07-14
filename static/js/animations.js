// static/js/animations.js

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Intersection Observer for scroll animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.05 // Trigger when 5% visible
    };

    let batch = [];
    let batchTimeout = null;

    const scrollObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                batch.push(entry.target);
                observer.unobserve(entry.target);
            }
        });

        if (batch.length > 0) {
            if (!batchTimeout) {
                batchTimeout = setTimeout(() => {
                    // Assign staggered delays to this specific batch
                    batch.forEach((el, index) => {
                        // Max cap stagger delay so it doesn't take forever
                        const delay = Math.min(index * 0.05, 0.8);
                        el.style.transitionDelay = `${delay}s`;
                        
                        // Force browser reflow to apply delay before adding class
                        void el.offsetWidth;
                        
                        el.classList.add('is-visible');
                    });
                    
                    // Reset batch
                    batch = [];
                    batchTimeout = null;
                }, 15); // Small debounce to collect all elements intersecting in this scroll frame
            }
        }
    }, observerOptions);

    // Function to set up elements for scroll animation
    const initScrollAnimations = () => {
        // Find all cards and list items that aren't already observed
        const elementsToAnimate = document.querySelectorAll('.stat-card, .dashboard-card, tbody tr, .test-item-card, .package-item-card');
        
        elementsToAnimate.forEach((el) => {
            if (!el.classList.contains('scroll-observed')) {
                el.classList.add('scroll-observed');
                scrollObserver.observe(el);
            }
        });
    };

    // Initial setup
    initScrollAnimations();

    // Re-run setup when AJAX content loads (MutationObserver)
    const tableBodyObserver = new MutationObserver((mutations) => {
        let shouldReinit = false;
        mutations.forEach(mutation => {
            if (mutation.addedNodes.length > 0) {
                shouldReinit = true;
            }
        });
        if (shouldReinit) {
            initScrollAnimations();
        }
    });

    // Observe table bodies for dynamically injected rows
    document.querySelectorAll('tbody').forEach(tbody => {
        tableBodyObserver.observe(tbody, { childList: true });
    });
});
