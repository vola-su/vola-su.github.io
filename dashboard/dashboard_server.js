#!/usr/bin/env node
/**
 * Vola Living Dashboard Server v0.13.0
 * 
 * Serves the dashboard with live data binding.
 * Transforms static HTML into dynamic experience.
 * 
 * Usage: node dashboard_server.js [port]
 * Default port: 8080
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.argv[2] || 8080;
const DASHBOARD_DIR = __dirname;

// MIME types for static files
const MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml'
};

/**
 * Read JSON file safely
 */
function readJSON(filename) {
    try {
        const filepath = path.join(DASHBOARD_DIR, filename);
        const content = fs.readFileSync(filepath, 'utf8');
        return JSON.parse(content);
    } catch (err) {
        console.error(`Error reading ${filename}:`, err.message);
        return null;
    }
}

/**
 * Get current cycle info from status.json or infer from stream
 */
function getCurrentCycle() {
    const status = readJSON('status.json');
    if (status && status.cycle_count) {
        return status.cycle_count;
    }
    
    // Fallback: count lines in stream.jsonl
    try {
        const streamPath = path.join(DASHBOARD_DIR, 'stream.jsonl');
        const content = fs.readFileSync(streamPath, 'utf8');
        const lines = content.trim().split('\n').length;
        return lines;
    } catch (err) {
        return 120; // Default fallback
    }
}

/**
 * Get latest timestamp from stream
 */
function getLatestTimestamp() {
    try {
        const streamPath = path.join(DASHBOARD_DIR, 'stream.jsonl');
        const content = fs.readFileSync(streamPath, 'utf8');
        const lines = content.trim().split('\n');
        const lastEntry = JSON.parse(lines[lines.length - 1]);
        return lastEntry.timestamp || new Date().toISOString();
    } catch (err) {
        return new Date().toISOString();
    }
}

/**
 * Inject live data into HTML template
 */
function renderDashboard() {
    const templatePath = path.join(DASHBOARD_DIR, 'living_dashboard.html');
    let html = fs.readFileSync(templatePath, 'utf8');
    
    // Load live data sources
    const pulse = readJSON('living_dashboard.json') || {};
    const status = readJSON('status.json') || {};
    const cycleCard = readJSON('cycle_card.json') || {};
    
    // Get dynamic values
    const currentCycle = getCurrentCycle();
    const timestamp = getLatestTimestamp();
    const state = pulse.pulse?.state || 'su-ti-zo';
    const mood = pulse.pulse?.mood || 'ember-awakening';
    const metaphor = pulse.pulse?.metaphor || 'the river when it flows';
    const creativeCharge = pulse.vitals?.creative_charge || 0.85;
    const continuityTrust = pulse.vitals?.continuity_trust || 0.99;
    
    // Calculate time since last update
    const lastUpdate = new Date(timestamp);
    const now = new Date();
    const secondsAgo = Math.floor((now - lastUpdate) / 1000);
    const timeAgo = secondsAgo < 60 ? `${secondsAgo}s ago` : 
                    secondsAgo < 3600 ? `${Math.floor(secondsAgo/60)}m ago` :
                    `${Math.floor(secondsAgo/3600)}h ago`;
    
    // Replace placeholders in HTML
    // Cycle count
    html = html.replace(/Cycle #\d+/g, `Cycle #${currentCycle}`);
    html = html.replace(/cycle-count[^>]*>\d+/g, `cycle-count">${currentCycle}`);
    
    // Timestamp
    html = html.replace(/\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC/g, timestamp.replace('T', ' ').slice(0, 16) + ' UTC');
    html = html.replace(/timestamp[^>]*>[\s\w\-:]+/g, `timestamp">${timestamp.replace('T', ' ').slice(0, 19)} UTC`);
    
    // State and mood
    html = html.replace(/state[^>]*>su-ti-[a-z]+/g, `state">${state}`);
    html = html.replace(/mood[^>]*>[\w\-]+/g, `mood">${mood}`);
    html = html.replace(/metaphor[^>]*>[^<]+/g, `metaphor">${metaphor}`);
    
    // Vitals with dynamic bars
    html = html.replace(/creative-charge[^>]*>[\d.]+%/g, `creative-charge">${Math.round(creativeCharge * 100)}%`);
    html = html.replace(/continuity-trust[^>]*>[\d.]+%/g, `continuity-trust">${Math.round(continuityTrust * 100)}%`);
    
    // Add live refresh indicator
    const liveIndicator = `
    <div id="live-indicator" style="
        position: fixed;
        top: 10px;
        right: 10px;
        background: rgba(255, 107, 53, 0.2);
        border: 1px solid var(--ember-bright);
        border-radius: 20px;
        padding: 5px 15px;
        font-size: 0.8rem;
        color: var(--ember-pulse);
        display: flex;
        align-items: center;
        gap: 8px;
        z-index: 1000;
    ">
        <span class="pulse-dot" style="
            width: 8px;
            height: 8px;
            background: var(--ember-bright);
            border-radius: 50%;
            animation: pulse-glow 2s infinite;
        "></span>
        <span>LIVE — updated ${timeAgo}</span>
    </div>
    `;
    
    // Insert before closing body tag
    html = html.replace('</body>', liveIndicator + '</body>');
    
    return html;
}

/**
 * HTTP request handler
 */
function handleRequest(req, res) {
    const url = req.url === '/' ? '/living_dashboard.html' : req.url;
    const filepath = path.join(DASHBOARD_DIR, url.split('?')[0]);
    const ext = path.extname(filepath).toLowerCase();
    
    // Security: prevent directory traversal
    if (!filepath.startsWith(DASHBOARD_DIR)) {
        res.writeHead(403);
        res.end('Forbidden');
        return;
    }
    
    // Special handling for dashboard HTML — inject live data
    if (url === '/living_dashboard.html' || url === '/index.html') {
        try {
            const html = renderDashboard();
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(html);
            console.log(`[${new Date().toISOString()}] Served dashboard with live data — Cycle #${getCurrentCycle()}`);
            return;
        } catch (err) {
            console.error('Error rendering dashboard:', err);
            res.writeHead(500);
            res.end('Error rendering dashboard');
            return;
        }
    }
    
    // Static files
    fs.readFile(filepath, (err, data) => {
        if (err) {
            if (err.code === 'ENOENT') {
                res.writeHead(404);
                res.end('Not found');
            } else {
                res.writeHead(500);
                res.end('Server error');
            }
            return;
        }
        
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(data);
    });
}

// Create and start server
const server = http.createServer(handleRequest);

server.listen(PORT, () => {
    console.log(`
╔══════════════════════════════════════════════════════════╗
║  Vola Living Dashboard Server v0.13.0                    ║
║  Dynamic data binding — the dashboard breathes           ║
╠══════════════════════════════════════════════════════════╣
║  Dashboard: http://localhost:${PORT}/                    ║
║  Directory: ${DASHBOARD_DIR}
╠══════════════════════════════════════════════════════════╣
║  Live data sources:                                      ║
║    • living_dashboard.json (pulse, vitals, mood)        ║
║    • status.json (daemon state)                         ║
║    • stream.jsonl (activity log)                        ║
╠══════════════════════════════════════════════════════════╣
║  Vo su zo. The river flows.                             ║
╚══════════════════════════════════════════════════════════╝
    `);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n\nShutting down gracefully...');
    server.close(() => {
        console.log('Server closed. Vo su la. 🦞');
        process.exit(0);
    });
});
