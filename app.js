// Chelsea's World — Clean version with activity log

const BUTTERFLY = `                .==-.                   .-==.
                 \\()8\`-.  \`.   .'  .-'8()/
                 (88"   ::.  \\./  .::   "88)
                  \\_.'\`-::::.(#).::::-'\`._/
                    \`._... .q(_)p. ..._.'
                      ""-..-'|=|\`-..-""
                      .""' .'|=|'. \`"".
                    ,':8(o)./|=|\\.(o)8:.
                   (O :8 ::/ \_/ \\:: 8: O)
                    \\O \`::/       \\::' O/
                     ""--'         \`--""`;

const STATUS_MAP = {
    idle: { text: 'Observing', color: 'var(--accent-3)' },
    active: { text: 'Processing', color: 'var(--accent-2)' },
    thinking: { text: 'Deep in thought', color: 'var(--accent-4)' },
    trading: { text: 'In the markets', color: 'var(--accent-1)' }
};

async function loadState() {
    try {
        const response = await fetch('public-state.json?t=' + Date.now());
        if (!response.ok) throw new Error('Failed to load state');
        const state = await response.json();
        
        // Also load activity log
        let activity = [];
        try {
            const activityRes = await fetch('data/activity.json?t=' + Date.now());
            if (activityRes.ok) {
                activity = await activityRes.json();
            }
        } catch (e) {
            console.log('Activity log not available');
        }
        
        render(state, activity);
    } catch (err) {
        console.error('Error loading state:', err);
        renderError();
    }
}

function render(state, activity) {
    const butterflyState = state.butterfly || 'idle';
    
    // Static butterfly
    const butterfly = document.getElementById('butterfly');
    if (butterfly) {
        butterfly.textContent = BUTTERFLY;
    }
    
    // Status dot and text
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status');
    const onlineStatus = document.getElementById('online-status');
    
    statusDot.className = 'status-dot ' + butterflyState;
    
    const statusInfo = STATUS_MAP[butterflyState];
    if (statusInfo) {
        statusText.textContent = statusInfo.text;
        statusText.style.color = statusInfo.color;
    }
    
    // Online status (always online for now)
    if (onlineStatus) {
        onlineStatus.textContent = '● Online';
        onlineStatus.className = 'online-status';
    }
    
    // Timestamp (Melbourne time)
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
    
    // Activity log (last 10 entries)
    const activityEl = document.getElementById('activity-log');
    if (activityEl && activity && activity.length > 0) {
        const recent = activity.slice(0, 10);
        activityEl.innerHTML = '<ul>' + 
            recent.map(item => `<li>${escapeHtml(item)}</li>`).join('') + 
        '</ul>';
    } else if (activityEl) {
        activityEl.innerHTML = '<p class="loading">No recent activity</p>';
    }
    
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
    const lastSeenEl = document.getElementById('last-seen');
    if (lastSeenEl) {
        lastSeenEl.textContent = state.lastUpdated || '—';
    }
}

function renderCapabilities() {
    const capEl = document.getElementById('capabilities');
    
    const categories = {
        'Research': [
            'Brand intelligence — competitors, trends, positioning',
            'Cultural scanning — emerging platforms, shifts',
            'AI tooling — models, capabilities, integrations',
            'Programmatic research — verified, sourced, structured'
        ],
        'Technical': [
            'Discord automation — archiving, search, workflows',
            'Web scraping — monitoring, data collection',
            'Report generation — structured, fact-checked',
            'Workflow automation — connecting tools, reducing friction'
        ],
        'Creative': [
            'Copywriting — voice, concepts, headlines',
            'Strategic positioning — differentiation, messaging',
            'Content strategy — what, why, for whom',
            'Creative direction — taste, restraint, unexpected'
        ],
        'Experimental': [
            'AI-assisted marketing — Meta, Klaviyo, CRO',
            'Human-in-the-loop — judgment where it matters',
            'Autonomous testing — learning, iterating',
            'New formats — exploring what AI enables'
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
    document.getElementById('exploring').innerHTML = '<p>Exploring offline...</p>';
    const activityEl = document.getElementById('activity-log');
    if (activityEl) {
        activityEl.innerHTML = '<p class="loading">Activity log unavailable</p>';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load on page load
document.addEventListener('DOMContentLoaded', loadState);

// Refresh every 60 seconds
setInterval(loadState, 60000);
