#!/bin/bash
# Continuous Training Monitor - Updates every 30 seconds

OUTPUT_FILE="/tmp/claude-1000/-home-rohith-desktop-CommandCenter/tasks/b4e4805.output"

echo "Starting continuous training monitor..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    /home/rohith/desktop/CommandCenter/claude-rl-agent/monitor_training.sh
    echo ""
    echo "⏰ Next refresh in 30 seconds... (Ctrl+C to stop)"
    sleep 30
done
