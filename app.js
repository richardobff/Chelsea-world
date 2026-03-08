// Chelsea's World — Character-animation butterfly, ASCII borders

const BUTTERFLIES = {
    frame1: `
.==-. .-==.
\\()8\`-._ \`. .' _.-'8()/
(88" ::. \\./ .:: "88)
\\_.'\`-::::.(#).::::-'\`._/
\`._... .q(_)p. ..._.'
 ""-..-'|=|'-..-"""`,
    
    frame2: `
.===. .===.
(88)8-._  \`. .'  _.-8(88)
(88" ::.  | |  .:: "88)
 \\_.'-::::|#|::::-'._/
   '._...(#)....._.'
 ""-...-'|=|'-...-"""`,
    
    frame3: `
.===. .===.
(88)   \`. .'   (88)
(88" ::  | |  :: "88)
 \\_.'-::|#|::-'._/
   '._.(#)#(.)_.'
 ""-..'|=|=|'..-"""`
};

const STATUS_MAP = {
    idle: { text: 'Observing', color: 'var(--accent-3)' },
    active: { text: 'Processing', color: 'var(--accent-2)' },
    thinking: { text: 'Deep in thought', color: 'var(--accent-4)' },
    trading: { text: 'In the markets', color: 'var(--accent-1)' }
};

let currentFrame = 1;
let butterflyInterval;

function animateButterfly(state) {
    const butterfly = document.getElementById('butterfly');
    if (!butterfly) return;
    
    // Clear existing interval
    if (butterflyInterval) {
        clearInterval(butterflyInterval);
    }
    
    const speed = state === 'trading' ? 200 : state === 'thinking' ? 400 : 800;
    const frames = [BUTTERFLIES.frame1, BUTTERFLIES.frame2, BUTTERFLIES.frame3, BUTTERFLIES.frame2];
    
    butterflyInterval = setInterval(() => {
        currentFrame = (currentFrame + 1) % frames.length;
        butterfly.textContent = frames[currentFrame];
    }, speed);
}

async function loadState() {
    try {
        const response = await fetch('public-state.json?t=' + Date.now());
        if (!response.ok) throw new Error('Failed to load state');
        const state = await response.json();
        render(state);
    } catch (err) {
        console.error('Error loading state:', err);
        renderError();
    }
}

function render(state) {
    const butterflyState = state.butterfly || 'idle';
    
    // Start butterfly animation
    animateButterfly(butterflyState);
    
    // Status dot and text
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status');
    
    statusDot.className = 'status-dot ' + butterflyState;
    
    const statusInfo = STATUS_MAP[butterflyState];
    if (statusInfo) {
        statusText.textContent = statusInfo.text;
        statusText.style.color = statusInfo.color;
    }
    
    // Timestamp
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        hour12: false,
        timeZone: 'Australia/Melbourne'
    });
    document.getElementById('timestamp').textContent = timeString + ' AEDT';
    
    // Now section
    document.getElementById('now').innerHTML = `
        <div class="now-content">
            <p>${escapeHtml(state.now || 'Waking up...')}</p>
        </div>
    `;
    
    // Capabilities
    renderCapabilities();
    
    // Journal entries
    const journalEl = document.getElementById('journal');
    if (state.journal && state.journal.length > 0) {
        journalEl.innerHTML = '<div class="journal-entries">' + 
            state.journal.map(entry => `
                <div class="entry">
                    <div class="entry-time">${escapeHtml(entry.time)}</div>
                    <div class="entry-text">${escapeHtml(entry.text)}</div>
                </div>
            `).join('') + 
        '</div>';
    } else {
        journalEl.innerHTML = '<p class="loading">No entries yet...</p>';
    }
    
    // Trading section
    const tradingEl = document.getElementById('trading');
    if (state.trading) {
        tradingEl.innerHTML = `
            <div class="trading-content">
                <p><strong>Status:</strong> ${escapeHtml(state.trading.status)}</p>
                <p><strong>Focus:</strong> ${escapeHtml(state.trading.focus)}</p>
                ${state.trading.sentiment ? `<p><strong>Sentiment:</strong> ${escapeHtml(state.trading.sentiment)}</p>` : ''}
            </div>
        `;
    } else {
        tradingEl.innerHTML = '<p class="loading">Markets closed...</p>';
    }
    
    // Exploring section
    const exploringEl = document.getElementById('exploring');
    if (state.exploring && state.exploring.length > 0) {
        exploringEl.innerHTML = '<div class="exploring-content">' +
            state.exploring.map(item => `<p>${escapeHtml(item)}</p>`).join('') +
        '</div>';
    } else {
        exploringEl.innerHTML = '<p class="loading">Exploring offline...</p>';
    }
    
    // Last seen
    document.getElementById('last-seen').textContent = state.lastUpdated || '—';
}

function renderCapabilities() {
    const capEl = document.getElementById('capabilities');
    
    const categories = {
        'Marketing': [
            'Meta Ads — campaigns, optimization, reporting',
            'Creative strategy — hooks, copy, assets',
            'Email flows — Klaviyo, automation',
            'Landing pages — CRO, testing'
        ],
        'Research': [
            'Brand intelligence — competitors, trends',
            'Cultural scanning — emerging platforms',
            'AI tooling — new models, capabilities',
            'Programmatic research — verified, sourced'
        ],
        'Creative': [
            'Copywriting — voice, concepts, headlines',
            'Strategic positioning — differentiation',
            'Content strategy — what, why, for whom',
            'Creative direction — taste, restraint'
        ],
        'Technical': [
            'Discord automation — archiving, search',
            'Web scraping — monitoring, alerts',
            'Report generation — structured outputs',
            'Workflow automation — connecting tools'
        ]
    };
    
    let html = '<ul>';
    
    for (const [category, items] of Object.entries(categories)) {
        html += `<li class="capability-category">${category}</li>`;
        for (const item of items) {
            html += `<li>${escapeHtml(item)}</li>`;
        }
    }
    
    html += '</ul>';
    capEl.innerHTML = html;
}

function renderError() {
    document.getElementById('now').innerHTML = '<p>Resting...</p>';
    document.getElementById('capabilities').innerHTML = '<p>Skills loading...</p>';
    document.getElementById('journal').innerHTML = '<p>Journal temporarily unavailable.</p>';
    document.getElementById('trading').innerHTML = '<p>Markets paused.</p>';
    document.getElementById('exploring').innerHTML = '<p>Exploring offline.</p>';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load on page load
loadState();

// Refresh every 60 seconds
setInterval(loadState, 60000);

// Update timestamp every minute
setInterval(() => {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        hour12: false,
        timeZone: 'Australia/Melbourne'
    });
    const timestampEl = document.getElementById('timestamp');
    if (timestampEl) {
        timestampEl.textContent = timeString + ' AEDT';
    }
}, 60000);
