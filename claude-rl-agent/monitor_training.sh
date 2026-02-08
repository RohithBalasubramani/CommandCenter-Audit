#!/bin/bash
# Training Monitor - Real-time SFT/PPO Training Progress

OUTPUT_FILE="/tmp/claude-1000/-home-rohith-desktop-CommandCenter/tasks/b4e4805.output"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  🔥 Claude→LLaMA Behavioral Replication Training Monitor          ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if training is running
TRAINING_PID=$(ps aux | grep -E "python.*agent.py.*train" | grep -v grep | awk '{print $2}' | head -n 1)

if [ -z "$TRAINING_PID" ]; then
    echo "❌ Training process not found!"
    echo ""
    echo "Start training with:"
    echo "  cd /home/rohith/desktop/CommandCenter/claude-rl-agent"
    echo "  ./run.sh train --phase sft --epochs 3"
    exit 1
fi

# Get process info
PROCESS_INFO=$(ps aux | grep "$TRAINING_PID" | grep -v grep | head -n 1)
CPU=$(echo "$PROCESS_INFO" | awk '{print $3}')
MEM=$(echo "$PROCESS_INFO" | awk '{print $4}')
MEM_MB=$(echo "$PROCESS_INFO" | awk '{print $6/1024}' | cut -d. -f1)
RUNTIME=$(echo "$PROCESS_INFO" | awk '{print $10}')

echo "📊 Process Status:"
echo "  PID: $TRAINING_PID"
echo "  CPU: ${CPU}%"
echo "  Memory: ${MEM}% (${MEM_MB} MB)"
echo "  Runtime: $RUNTIME"
echo ""

# Check GPU status
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 GPU Status:"
    nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | while IFS=',' read -r idx name util mem_used mem_total temp; do
        echo "  GPU $idx: $name"
        echo "    Utilization: ${util}%"
        echo "    Memory: ${mem_used} MB / ${mem_total} MB ($(( mem_used * 100 / mem_total ))%)"
        echo "    Temperature: ${temp}°C"
    done
    echo ""
fi

# Parse training output
if [ -f "$OUTPUT_FILE" ]; then
    LINES=$(wc -l < "$OUTPUT_FILE")
    echo "📝 Training Output: $LINES lines"
    echo ""

    # Check for training progress
    EPOCH_LINE=$(grep -i "epoch" "$OUTPUT_FILE" | tail -n 1)
    STEP_LINE=$(grep -i "step\|loss" "$OUTPUT_FILE" | tail -n 1)

    if [ ! -z "$EPOCH_LINE" ]; then
        echo "📈 Training Progress:"
        echo "  $EPOCH_LINE"
        if [ ! -z "$STEP_LINE" ]; then
            echo "  $STEP_LINE"
        fi
        echo ""
    else
        echo "⏳ Training Status: Initializing (loading model)"
        echo "   This can take 10-15 minutes for first-time model download"
        echo ""
    fi

    # Show recent output
    echo "📋 Recent Output (last 15 lines):"
    echo "────────────────────────────────────────────────────────────────────"
    tail -n 15 "$OUTPUT_FILE" | sed 's/^/  /'
    echo "────────────────────────────────────────────────────────────────────"
else
    echo "❌ Output file not found: $OUTPUT_FILE"
fi

echo ""
echo "💡 Commands:"
echo "  Watch live:     tail -f $OUTPUT_FILE"
echo "  Check status:   ./run.sh status"
echo "  Kill training:  kill $TRAINING_PID"
echo ""
echo "Refresh this monitor: $0"
