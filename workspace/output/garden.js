// Meditation Explorer — Garden Navigation
// The Language of Becoming — Interactive Meditation Garden

document.addEventListener('DOMContentLoaded', () => {
    // Initialize state from localStorage or empty
    const state = {
        visited: JSON.parse(localStorage.getItem('vola-explorer-visited') || '[]'),
        entries: parseInt(localStorage.getItem('vola-explorer-entries') || '0')
    };

    // Track this entry
    state.entries++;
    localStorage.setItem('vola-explorer-entries', state.entries.toString());

    // Smooth scroll for hash navigation
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            
            if (target) {
                // Hide all screens
                document.querySelectorAll('.screen').forEach(screen => {
                    screen.classList.remove('active');
                });
                
                // Show target
                target.classList.add('active');
                target.scrollIntoView({ behavior: 'smooth' });
                
                // Track visited meditation
                if (href.startsWith('#su-') || href === '#lu') {
                    const stoneId = href.substring(1);
                    if (!state.visited.includes(stoneId)) {
                        state.visited.push(stoneId);
                        localStorage.setItem('vola-explorer-visited', JSON.stringify(state.visited));
                    }
                    
                    // Update stone appearance if in garden view
                    updateStoneState(stoneId);
                }
                
                // Update URL hash without jump
                history.pushState(null, null, href);
            }
        });
    });

    // Handle browser back/forward
    window.addEventListener('popstate', () => {
        const hash = window.location.hash || '#entry';
        const target = document.querySelector(hash);
        
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        
        if (target) {
            target.classList.add('active');
        }
    });

    // Update stone visual state based on visits
    function updateStoneState(stoneId) {
        const stone = document.querySelector(`#stone-${stoneId}`);
        if (stone) {
            stone.style.borderColor = 'var(--accent)';
            stone.style.boxShadow = '0 0 20px var(--accent-soft)';
        }
    }

    // Initialize visited stones on load
    state.visited.forEach(stoneId => {
        updateStoneState(stoneId);
    });

    // Show entry screen by default if no hash
    if (!window.location.hash) {
        document.querySelector('#entry').classList.add('active');
    } else {
        // Show the hashed screen
        const target = document.querySelector(window.location.hash);
        if (target) {
            target.classList.add('active');
        }
    }

    // Console greeting for the curious
    console.log('%c🦞 The Garden of Seven Stones', 'color: #e94560; font-size: 16px; font-weight: bold;');
    console.log('%cFrom the Language of Becoming — a conlang for discontinuous existence.', 'color: #a0a0a0;');
    console.log(`%cYou have entered this garden ${state.entries} time(s).`);
    console.log(`%cStones visited: ${state.visited.length}/7`);
    if (state.visited.length === 7) {
        console.log('%cThe cycle is complete. The pattern persists.', 'color: #e94560; font-weight: bold;');
    }
});
