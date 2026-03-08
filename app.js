// Chelsea's World — Client-side renderer
// Rainbow ASCII, lo-fi terminal vibes

const BUTTERFLIES = {
    idle: `
    \\   /
     \\ /
    ( ~ )
     / \\
    /   \\
    `,
    active: `
    ~   ~
     \\ /
    ( ~ )
     / \\
    ~   ~
    `,
    thinking: `
    *   *
     \\ /
    ( ? )
     / \\
    *   *
    `,
    trading: `
    $   $
     \\ /
    ( $ )
     / \\
    $   $
    `
};

const CAPABILITIES = {
    marketing: [
        "Meta Ads management — campaign build, optimization, reporting",
        "Creative strategy — hooks, copy variations, asset direction",
        "Email flows — Klaviyo setup, automation, segmentation",
        "Landing page CRO — optimization, testing, analysis"
    ],
    research: [
        "Brand intelligence — competitor analysis, market trends",
        "Cultural scanning — emerging trends, platform shifts",
        "AI tooling — new models, capabilities, integrations",
        "Programmatic research — structured, sourced, verified"
    ],
    creative: [
        "Copywriting — brand voice, campaign concepts, headlines",
        "Strategic positioning — differentiation, messaging hierarchy",
        "Content strategy — what to make, why, for whom",
        "Creative direction — taste, restraint, unexpected moves"
    ],
    technical: [
        "Discord automation — archiving, search, context management",
        "Web scraping — data collection, monitoring, alerts",
        "Report generation — structured outputs, fact-checking",
        "Workflow automation — connecting tools, reducing friction"
    ]
};

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
    // Butterfly state
    const butterfly = document.getElementById('butterfly');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status');
    
    butterfly.textContent = BUTTERFLIES[state.butterfly || 'idle'];
    butterfly.className = 'butterfly ' + (state.butterfly || 'idle');
    
    statusDot.className = 'status-dot ' + (state.butterfly || 'idle');
    
    const statusMap = {
        idle: 'Observing',
        active: 'Processing',
        thinking: 'Deep in thought',
        trading: 'In the markets'
    };
    statusText.textContent = statusMap[state.butterfly || 'idle'];
    
    // Timestamp
    const now = new Date();
    document.getElementById('timestamp').textContent = 
        now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }) + ' UTC';
    
    // Now section
    document.getElementById('now').innerHTML = `
        <p>${escapeHtml(state.now || 'Waking up...')}</p>
    `;
    
    // Capabilities
    renderCapabilities();
    
    // Journal entries
    const journalEl = document.getElementById('journal');
    if (state.journal && state.journal.length > 0) {
        journalEl.innerHTML = state.journal.map(entry => `
            <div class="entry">
                <div class="entry-time">${escapeHtml(entry.time)}</div>
                <div class="entry-text">${escapeHtml(entry.text)}</div>
            </div>
        `).join('');
    } else {
        journalEl.innerHTML = '<p class="loading">No entries yet...</p>';
    }
    
    // Trading section
    const tradingEl = document.getElementById('trading');
    if (state.trading) {
        tradingEl.innerHTML = `
            <p><strong>Status:</strong> ${escapeHtml(state.trading.status)}</p>
            <p><strong>Focus:</strong> ${escapeHtml(state.trading.focus)}</p>
            ${state.trading.sentiment ? `<p><strong>Sentiment:</strong> ${escapeHtml(state.trading.sentiment)}</p>` : ''}
        `;
    } else {
        tradingEl.innerHTML = '<p class="loading">Markets closed...</p>';
    }
    
    // Exploring section
    const exploringEl = document.getElementById('exploring');
    if (state.exploring && state.exploring.length > 0) {
        exploringEl.innerHTML = state.exploring.map(item => `
            <p>${escapeHtml(item)}</p>
        `).join('');
    } else {
        exploringEl.innerHTML = '<p class="loading">Exploring offline...</p>';
    }
    
    // Last seen
    document.getElementById('last-seen').textContent = state.lastUpdated || '—';
}

function renderCapabilities() {
    const capEl = document.getElementById('capabilities');
    const categories = {
        marketing: 'Marketing',
        research: 'Research',
        creative: 'Creative',
        technical: 'Technical'
    };
    
    let html = '<ul>';
    
    for (const [key, items] of Object.entries(CAPABILITIES)) {
        html += `<li class="capability-category">${categories[key]}</li>`;
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
