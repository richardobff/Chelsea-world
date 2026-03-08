#!/usr/bin/env node
// update-state.mjs — Programmatically update dashboard state
// Usage: node update-state.mjs --now "New status" --butterfly active

import { readFileSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const STATE_FILE = join(__dirname, 'public-state.json');

// Safety filters — NEVER allow these patterns
const BLOCKED_PATTERNS = [
    /office\s*bff/i,
    /client/i,
    /sal|tim|ned/i,
    /st\.?\s*ali/i,
    /peggies/i,
    /\$[0-9,]+/i,  // Dollar amounts
    /0x[a-f0-9]{40}/i,  // ETH addresses
    /[A-Z]{20,}/  // Long strings that might be keys
];

function isSafe(text) {
    for (const pattern of BLOCKED_PATTERNS) {
        if (pattern.test(text)) {
            console.error(`❌ BLOCKED: Content matches unsafe pattern: ${pattern}`);
            return false;
        }
    }
    return true;
}

function loadState() {
    try {
        return JSON.parse(readFileSync(STATE_FILE, 'utf8'));
    } catch {
        return {
            butterfly: 'idle',
            now: 'Waking up...',
            journal: [],
            trading: { status: 'Resting', focus: '—' },
            exploring: [],
            lastUpdated: new Date().toISOString().split('T')[0]
        };
    }
}

function saveState(state) {
    state.lastUpdated = new Date().toISOString().split('T')[0];
    writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
    console.log('✅ Dashboard updated');
}

// Parse args
const args = process.argv.slice(2);
const updates = {};

for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace('--', '');
    const value = args[i + 1];
    updates[key] = value;
}

const state = loadState();

// Apply updates with safety checks
if (updates.butterfly) {
    const validStates = ['idle', 'active', 'thinking', 'trading'];
    if (validStates.includes(updates.butterfly)) {
        state.butterfly = updates.butterfly;
    }
}

if (updates.now && isSafe(updates.now)) {
    state.now = updates.now;
}

if (updates.journal && isSafe(updates.journal)) {
    const time = new Date().toISOString().split('T')[0];
    state.journal.unshift({
        time,
        text: updates.journal
    });
    // Keep only last 10 entries
    state.journal = state.journal.slice(0, 10);
}

if (updates.tradingStatus && isSafe(updates.tradingStatus)) {
    state.trading.status = updates.tradingStatus;
}

if (updates.tradingFocus && isSafe(updates.tradingFocus)) {
    state.trading.focus = updates.tradingFocus;
}

if (updates.tradingSentiment && isSafe(updates.tradingSentiment)) {
    state.trading.sentiment = updates.tradingSentiment;
}

saveState(state);
