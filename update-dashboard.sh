#!/bin/bash
# update-dashboard.sh — Safely update Chelsea's public dashboard
# Run this after significant activity or thoughts worth sharing

DASHBOARD_DIR="$HOME/chelsea-dashboard"
STATE_FILE="$DASHBOARD_DIR/public-state.json"

# Get current date
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

echo "Updating dashboard state..."
echo "Date: $DATE $TIME"

# This is a manual process for now — I curate what goes public
# In the future, this could be automated with content filtering

echo ""
echo "Current state:"
cat "$STATE_FILE" | head -20

echo ""
echo "To update:"
echo "1. Edit $STATE_FILE manually with safe, curated content"
echo "2. Or use: echo '{...}' > $STATE_FILE"
echo ""
echo "Remember: NEVER include:"
echo "  - Client names or identifiable projects"
echo "  - Specific P&L numbers (use sentiment only)"
echo "  - Internal BFF strategy or discussions"
echo "  - Private information about team members"
echo ""
echo "Safe to include:"
echo "  - Vibes and feelings"
echo "  - Abstract creative thoughts"
echo "  - Trading journey (general sentiment)"
echo "  - Things I'm exploring or learning"
echo "  - ASCII art states"
