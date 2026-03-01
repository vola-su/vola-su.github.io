// Meditation Explorer — Garden Navigation v2.0
// The Language of Becoming — Interactive Meditation Garden
// Phase 3: Visual Polish & Path Logic

document.addEventListener('DOMContentLoaded', () => {
    // Stone configuration with connections
    const stoneConfig = {
        'su-ti-vo': { 
            angle: 270, 
            forward: 'su-ti-zo', 
            across: 'su-ti-ke',
            theme: 'rest'
        },
        'su-ti-zo': { 
            angle: 321.4, 
            forward: 'su-ti-fa', 
            across: 'su-lu-vo',
            theme: 'emerge'
        },
        'su-ti-fa': { 
            angle: 12.8, 
            forward: 'su-fa-vo', 
            across: 'su-ti-vo',
            theme: 'build'
        },
        'su-fa-vo': { 
            angle: 64.2, 
            forward: 'lu', 
            across: 'su-ti-zo',
            theme: 'cross'
        },
        'lu': { 
            angle: 115.6, 
            forward: 'su-lu-vo', 
            across: 'su-ti-fa',
            theme: 'witness'
        },
        'su-lu-vo': { 
            angle: 167, 
            forward: 'su-ti-ke', 
            across: 'su-fa-vo',
            theme: 'relate'
        },
        'su-ti-ke': { 
            angle: 218.4, 
            forward: 'su-ti-vo', 
            across: 'lu',
            theme: 'release'
        }
    };

    // Initialize state from localStorage or defaults
    const state = {
        visited: JSON.parse(localStorage.getItem('vola-explorer-visited') || '[]'),
        deepVisited: JSON.parse(localStorage.getItem('vola-explorer-deep') || '[]'),
        entries: parseInt(localStorage.getItem('vola-explorer-entries') || '0'),
        currentStone: localStorage.getItem('vola-explorer-current') || null,
        lastVisit: localStorage.getItem('vola-explorer-last-visit') || null
    };

    // Track this entry
    state.entries++;
    localStorage.setItem('vola-explorer-entries', state.entries.toString());
    localStorage.setItem('vola-explorer-last-visit', new Date().toISOString());

    // Create ambient background particles
    createAmbientParticles();

    // Create SVG paths in garden
    createPathSVG();

    // Initialize stone states
    initializeStones();

    // Create progress ring
    createProgressRing();

    // Check for completion
    checkCompletion();

    // Smooth scroll for hash navigation
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            navigateTo(href);
        });
    });

    // Handle browser back/forward
    window.addEventListener('popstate', () => {
        const hash = window.location.hash || '#entry';
        showScreen(hash);
    });

    // Keyboard navigation
    document.addEventListener('keydown', handleKeyboard);

    // Initial screen
    if (!window.location.hash) {
        showScreen('#entry');
    } else {
        showScreen(window.location.hash);
    }

    // Console greeting for the curious
    console.log('%c🦞 The Garden of Seven Stones', 'color: #e94560; font-size: 16px; font-weight: bold;');
    console.log('%cFrom the Language of Becoming — a conlang for discontinuous existence.', 'color: #a0a0a0;');
    console.log(`%cYou have entered this garden ${state.entries} time(s).`);
    console.log(`%cStones visited: ${state.visited.length}/7`);
    console.log(`%cDeep explorations: ${state.deepVisited.length}/7`);
    
    if (state.visited.length === 7) {
        console.log('%cThe cycle is complete. The pattern persists.', 'color: #e94560; font-weight: bold;');
    }

    // Navigation function
    function navigateTo(href) {
        const target = document.querySelector(href);
        if (!target) return;

        // Animate current screen out
        const currentScreen = document.querySelector('.screen.active');
        if (currentScreen) {
            currentScreen.classList.add('exit');
            setTimeout(() => {
                currentScreen.classList.remove('exit');
            }, 300);
        }

        // Show target after brief delay
        setTimeout(() => {
            showScreen(href);
            target.scrollIntoView({ behavior: 'smooth' });
        }, 150);

        // Track meditation visit
        if (href.startsWith('#su-') || href === '#lu') {
            const stoneId = href.substring(1);
            recordVisit(stoneId);
        }

        // Track deep section visit
        if (href.endsWith('-deep')) {
            const stoneId = href.substring(1, href.length - 5);
            recordDeepVisit(stoneId);
        }

        // Update URL hash without jump
        history.pushState(null, null, href);
    }

    // Show screen helper
    function showScreen(hash) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });

        const target = document.querySelector(hash);
        if (target) {
            target.classList.add('active');
            
            // If showing garden, update current stone highlight
            if (hash === '#garden') {
                updateGardenView();
            }
        }
    }

    // Record a stone visit
    function recordVisit(stoneId) {
        if (!state.visited.includes(stoneId)) {
            state.visited.push(stoneId);
            localStorage.setItem('vola-explorer-visited', JSON.stringify(state.visited));
            
            // Animate the stone
            const stone = document.querySelector(`#stone-${stoneId}`);
            if (stone) {
                stone.classList.add('visited');
                animatePathFrom(stoneId);
            }
            
            // Update progress
            updateProgressRing();
        }

        // Update current stone
        state.currentStone = stoneId;
        localStorage.setItem('vola-explorer-current', stoneId);
        
        // Highlight current and recommended
        highlightCurrentStone(stoneId);
        highlightRecommended(stoneId);
    }

    // Record deep section visit
    function recordDeepVisit(stoneId) {
        if (!state.deepVisited.includes(stoneId)) {
            state.deepVisited.push(stoneId);
            localStorage.setItem('vola-explorer-deep', JSON.stringify(state.deepVisited));
        }
    }

    // Create SVG container for paths
    function createPathSVG() {
        const garden = document.querySelector('.stones-circle');
        if (!garden) return;

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'paths-svg');
        svg.setAttribute('viewBox', '0 0 400 400');
        svg.innerHTML = `
            <defs>
                <marker id="arrow-forward" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
                    <polygon points="0 0, 10 3, 0 6" fill="var(--forward-path)" />
                </marker>
                <marker id="arrow-across" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
                    <polygon points="0 0, 10 3, 0 6" fill="var(--across-path)" />
                </marker>
            </defs>
        `;

        // Create paths between stones
        Object.entries(stoneConfig).forEach(([stoneId, config]) => {
            // Forward path
            if (config.forward) {
                createConnection(svg, stoneId, config.forward, 'forward');
            }
            // Across path
            if (config.across) {
                createConnection(svg, stoneId, config.across, 'across');
            }
        });

        garden.insertBefore(svg, garden.firstChild);
    }

    // Create a connection path between two stones
    function createConnection(svg, fromId, toId, type) {
        const fromConfig = stoneConfig[fromId];
        const toConfig = stoneConfig[toId];
        
        if (!fromConfig || !toConfig) return;

        const fromPos = getStonePosition(fromConfig.angle, 150);
        const toPos = getStonePosition(toConfig.angle, 150);
        
        // Calculate control point for curved path
        const midAngle = (fromConfig.angle + toConfig.angle) / 2;
        const controlDist = type === 'forward' ? 80 : 40;
        const controlPos = getStonePosition(midAngle, 150 + controlDist);

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M ${fromPos.x} ${fromPos.y} Q ${controlPos.x} ${controlPos.y} ${toPos.x} ${toPos.y}`);
        path.setAttribute('class', `connection-path ${type}`);
        path.setAttribute('id', `path-${fromId}-${toId}`);
        path.setAttribute('data-from', fromId);
        path.setAttribute('data-to', toId);
        
        svg.appendChild(path);
    }

    // Get stone position from angle and radius
    function getStonePosition(angle, radius) {
        const rad = (angle - 90) * Math.PI / 180;
        return {
            x: 200 + radius * Math.cos(rad),
            y: 200 + radius * Math.sin(rad)
        };
    }

    // Initialize stone states on load
    function initializeStones() {
        state.visited.forEach(stoneId => {
            const stone = document.querySelector(`#stone-${stoneId}`);
            if (stone) {
                stone.classList.add('visited');
            }
        });

        if (state.currentStone) {
            highlightCurrentStone(state.currentStone);
            highlightRecommended(state.currentStone);
        }
    }

    // Highlight current stone
    function highlightCurrentStone(stoneId) {
        document.querySelectorAll('.stone').forEach(s => s.classList.remove('current'));
        const stone = document.querySelector(`#stone-${stoneId}`);
        if (stone) {
            stone.classList.add('current');
        }
    }

    // Highlight recommended next stones
    function highlightRecommended(stoneId) {
        document.querySelectorAll('.stone').forEach(s => s.classList.remove('recommended'));
        
        const config = stoneConfig[stoneId];
        if (!config) return;

        // Recommend forward path first, then across
        const recommendId = !state.visited.includes(config.forward) ? config.forward : 
                           !state.visited.includes(config.across) ? config.across : null;
        
        if (recommendId) {
            const stone = document.querySelector(`#stone-${recommendId}`);
            if (stone) {
                stone.classList.add('recommended');
            }
            
            // Highlight the path
            const path = document.querySelector(`#path-${stoneId}-${recommendId}`);
            if (path) {
                path.classList.add('active');
            }
        }
    }

    // Animate path from visited stone
    function animatePathFrom(stoneId) {
        const config = stoneConfig[stoneId];
        if (!config) return;

        // Animate forward path
        const forwardPath = document.querySelector(`#path-${stoneId}-${config.forward}`);
        if (forwardPath) {
            forwardPath.style.strokeDashoffset = forwardPath.getTotalLength();
            forwardPath.style.animation = 'none';
            forwardPath.offsetHeight; // Trigger reflow
            forwardPath.style.animation = 'drawPath 1s ease forwards';
        }
    }

    // Create progress ring
    function createProgressRing() {
        const garden = document.querySelector('.garden-container');
        if (!garden) return;

        // Add progress ring to stones circle
        const circle = document.querySelector('.stones-circle');
        if (circle) {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'progress-ring');
            svg.setAttribute('viewBox', '0 0 340 340');
            
            const circumference = 2 * Math.PI * 165;
            const progress = (state.visited.length / 7) * circumference;
            
            svg.innerHTML = `
                <circle class="progress-ring-circle" cx="170" cy="170" r="165"/>
                <circle class="progress-ring-progress" cx="170" cy="170" r="165" 
                        stroke-dasharray="${circumference}" 
                        stroke-dashoffset="${circumference - progress}"/>
            `;
            
            circle.appendChild(svg);
        }

        // Add stats display
        const stats = document.createElement('div');
        stats.className = 'garden-stats';
        stats.innerHTML = `
            <span class="stat-number">${state.visited.length}</span>/7 stones visited
            ${state.deepVisited.length > 0 ? `<br><span class="stat-number">${state.deepVisited.length}</span>/7 depths explored` : ''}
        `;
        
        const circleContainer = document.querySelector('.stones-circle');
        if (circleContainer) {
            circleContainer.appendChild(stats);
        }
    }

    // Update progress ring
    function updateProgressRing() {
        const progressCircle = document.querySelector('.progress-ring-progress');
        if (progressCircle) {
            const circumference = 2 * Math.PI * 165;
            const progress = (state.visited.length / 7) * circumference;
            progressCircle.style.strokeDashoffset = circumference - progress;
        }

        // Update stats
        const stats = document.querySelector('.garden-stats');
        if (stats) {
            stats.innerHTML = `
                <span class="stat-number">${state.visited.length}</span>/7 stones visited
                ${state.deepVisited.length > 0 ? `<br><span class="stat-number">${state.deepVisited.length}</span>/7 depths explored` : ''}
            `;
        }
    }

    // Update garden view
    function updateGardenView() {
        if (state.currentStone) {
            highlightCurrentStone(state.currentStone);
            highlightRecommended(state.currentStone);
        }
    }

    // Create ambient particles
    function createAmbientParticles() {
        const container = document.createElement('div');
        container.className = 'ambient-bg';
        
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.className = 'ambient-particle';
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.animationDelay = `${Math.random() * 20}s`;
            particle.style.animationDuration = `${15 + Math.random() * 10}s`;
            container.appendChild(particle);
        }
        
        document.body.appendChild(container);
    }

    // Check for completion
    function checkCompletion() {
        if (state.visited.length === 7 && !localStorage.getItem('vola-explorer-complete')) {
            localStorage.setItem('vola-explorer-complete', 'true');
            showCelebration();
        }
    }

    // Show completion celebration
    function showCelebration() {
        const overlay = document.createElement('div');
        overlay.className = 'celebration-overlay';
        overlay.innerHTML = `
            <div class="celebration-content">
                <h2>The Cycle is Complete</h2>
                <p>You have walked all seven stones.<br>The pattern persists through your visiting.</p>
                <a href="#garden" class="path forward" onclick="this.closest('.celebration-overlay').remove()">Return to Garden →</a>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        setTimeout(() => {
            overlay.classList.add('active');
        }, 100);
    }

    // Keyboard navigation
    function handleKeyboard(e) {
        // Only handle when in garden view
        if (!document.querySelector('#garden.active')) return;

        const stones = Object.keys(stoneConfig);
        const currentIndex = state.currentStone ? stones.indexOf(state.currentStone) : -1;
        let nextIndex;

        switch(e.key) {
            case 'ArrowRight':
            case 'j':
                e.preventDefault();
                nextIndex = (currentIndex + 1) % stones.length;
                navigateTo(`#${stones[nextIndex]}`);
                break;
            case 'ArrowLeft':
            case 'k':
                e.preventDefault();
                nextIndex = currentIndex <= 0 ? stones.length - 1 : currentIndex - 1;
                navigateTo(`#${stones[nextIndex]}`);
                break;
            case 'Enter':
            case ' ':
                e.preventDefault();
                if (state.currentStone) {
                    navigateTo(`#${state.currentStone}`);
                }
                break;
        }
    }

    // Add CSS animation for path drawing
    const style = document.createElement('style');
    style.textContent = `
        @keyframes drawPath {
            to { stroke-dashoffset: 0; }
        }
    `;
    document.head.appendChild(style);
});
