#!/bin/bash
# Watch Focus Guardian logs in real-time

echo "Watching Focus Guardian logs..."
echo "Press Ctrl+C to stop"
echo ""

tail -f /tmp/focus_guardian_debug.log 2>/dev/null || echo "No log file yet. Start Focus Guardian first."

