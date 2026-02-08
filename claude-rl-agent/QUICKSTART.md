# 🚀 Quick Start - Automated Claude→LLaMA Training

**Get the fully automated engine running in 3 commands (2 minutes)**

---

## ⚡ Setup (One-Time, 2 Minutes)

```bash
cd /home/rohith/desktop/CommandCenter/claude-rl-agent

# Step 1: Install automated hooks
./run.sh engine install

# Step 2: Add alias (copy the command shown, then)
source ~/.bashrc

# Step 3: Start the engine
./run.sh engine start
```

**Done!** The engine is now running and will auto-capture all Claude interactions.

---

## 📊 Check Status Anytime

```bash
./run.sh status
```

Shows:
- ✅ Engine status (running/stopped)
- ✅ Traces captured
- ✅ Progress to training threshold
- ✅ Next steps

---

## 🎮 All Commands

### Automated Engine (Recommended)

```bash
# Install hooks (one time)
./run.sh engine install

# Start background daemon
./run.sh engine start

# Check status
./run.sh engine status

# Stop daemon
./run.sh engine stop
```

### Manual Capture (Alternative)

```bash
# Run demonstration
./run.sh capture --demo

# Interactive capture session
./run.sh capture --interactive
```

### Training & Deployment

```bash
# Build dataset (automatic at 50 traces)
./run.sh build-dataset

# Train LLaMA (coming Week 2)
./run.sh train --phase sft
./run.sh train --phase ppo

# Deploy to Ollama
./run.sh deploy --test
```

### Status & Monitoring

```bash
# Overall status
./run.sh status

# View live logs
tail -f logs/capture_engine_$(date +%Y%m%d).log

# Count traces
ls -1 data/traces/traces.jsonl | wc -l
```

---

## 🎯 How It Works

### After Setup

Every time you use Claude:

```bash
claude "your prompt here"
```

The engine automatically:
1. ✅ Captures your prompt
2. ✅ Runs Claude normally (you see normal output)
3. ✅ Captures Claude's response
4. ✅ Extracts tool calls
5. ✅ Extracts reasoning signals
6. ✅ Stores trace
7. ✅ Counts toward training threshold

At 50 traces:
- ✅ Auto-builds dataset
- ✅ Auto-triggers training (Week 2)

### What Gets Captured

For every Claude interaction:
- User prompt
- Claude's complete response
- Tool sequence (Read → Grep → Bash → etc.)
- Reasoning chains ("First...", "Then...", "Next...")
- Exploration depth (minimal/thorough)
- Constraint detection
- Self-corrections
- Workflow design

---

## 📈 Example Usage

### Day 1: Setup

```bash
cd /home/rohith/desktop/CommandCenter/claude-rl-agent

./run.sh engine install
# (follow printed instructions to add alias)
source ~/.bashrc

./run.sh engine start

./run.sh status
# Shows: Engine running, 0 traces
```

### Day 2-14: Use Claude Normally

```bash
# Just use Claude for any task
claude "what's the difference between transformer 1 and 2?"

# Output:
🎯 Running Claude Code CLI (auto-capturing)...
[Claude's normal response]
✅ Interaction auto-captured

# Check progress
./run.sh status
# Shows: 23 traces captured, 27 until auto-train
```

### Week 2: Automatic Training

```bash
# After 50th trace, engine automatically:
# - Builds dataset
# - Triggers SFT training (when implemented)
# - Deploys model (when implemented)

# You see in logs:
🎯 Training threshold reached!
🚀 Triggering Automated Training Pipeline
✅ Dataset built: bc_dataset_20260208.jsonl
⏳ SFT training triggered
```

---

## 🔧 Troubleshooting

### Engine not starting?

```bash
# Check logs
tail -20 logs/daemon-error.log

# Try starting manually
python src/agent.py engine start
```

### CLI wrapper not capturing?

```bash
# Verify alias
alias | grep claude

# Test wrapper directly
/home/rohith/.../claude_cli_wrapper.sh "test"

# Check logs
tail -f logs/cli_wrapper.log
```

### No traces showing up?

```bash
# Check if daemon is running
./run.sh status

# Check trace directory
ls -lh data/traces/

# Process manually
python engine/process_raw_trace.py data/traces/raw/<file>.jsonl
```

---

## 💡 Tips

### For Maximum Coverage

Use **both** automated methods:

1. **CLI Wrapper** - Captures when you use `claude` alias
2. **Daemon** - Monitors all Claude log files

Install both:
```bash
# CLI wrapper
./run.sh engine install
(add alias)

# Systemd service
sudo cp engine/claude-rl-capture.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now claude-rl-capture
```

### For Development

Monitor in real-time:
```bash
# Terminal 1: Engine logs
tail -f logs/capture_engine_*.log

# Terminal 2: Use Claude
claude "your prompts"

# Terminal 3: Check status
watch -n 5 './run.sh status'
```

---

## 📚 Next Steps

1. **This Week**: Setup engine (3 commands above)
2. **Week 1-2**: Use Claude normally, collect 50-500 traces
3. **Week 2**: Engine auto-trains
4. **Week 3-6**: Implement PPO trainer
5. **Week 7+**: LLaMA replaces Claude

---

## 🎯 Success Criteria

- **Week 1**: 50 traces captured (MVP dataset)
- **Week 2**: 500 traces captured (production dataset)
- **Week 2**: First SFT model trained
- **Week 6**: PPO-aligned model
- **Month 6**: LLaMA indistinguishable from Claude (>45%)

---

**The engine is ready! Start it now and let it run!** 🚀
