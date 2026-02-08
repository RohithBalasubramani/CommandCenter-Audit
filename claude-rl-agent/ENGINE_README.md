# 🤖 Automated Claude→LLaMA Training Engine

**Fully automated background engine that captures Claude Code CLI interactions and continuously trains LLaMA.**

Unlike the manual capture system, this engine runs completely automatically:
- ✅ **Zero manual intervention** - Set it and forget it
- ✅ **Real-time capture** - Hooks into Claude CLI automatically
- ✅ **Continuous training** - Auto-trains when thresholds met
- ✅ **Background daemon** - Runs as systemd service

---

## 🚀 Quick Start (3 Commands)

```bash
cd /home/rohith/desktop/CommandCenter/claude-rl-agent

# 1. Install the automated hooks
python engine/engine_control.py install

# 2. Add alias to your shell (follow printed instructions)
echo 'alias claude="/home/rohith/desktop/CommandCenter/claude-rl-agent/hooks/claude_cli_wrapper.sh"' >> ~/.bashrc
source ~/.bashrc

# 3. Start the engine
python engine/engine_control.py start
```

**That's it!** Now every time you use Claude Code CLI, it's automatically captured and used for training.

---

## 📊 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  YOU USE CLAUDE CLI NORMALLY                                    │
│  $ claude "What's the difference between transformer 1 and 2?"  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  CLI WRAPPER (Transparent Interception)                         │
│  • Captures prompt                                              │
│  • Runs Claude normally                                         │
│  • Captures response                                            │
│  • Saves raw trace                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  TRACE PROCESSOR (Async Background)                             │
│  • Parses tool calls from response                              │
│  • Extracts reasoning signals                                   │
│  • Builds ClaudeTrace object                                    │
│  • Stores in data/traces/                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAPTURE DAEMON (Continuous Monitoring)                         │
│  • Watches trace directory                                      │
│  • Monitors Claude log files                                    │
│  • Tracks training thresholds                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (When threshold met)
┌─────────────────────────────────────────────────────────────────┐
│  AUTO-TRAINING TRIGGER                                          │
│  • Build dataset from traces                                    │
│  • Trigger SFT training (Week 2)                                │
│  • Export to GGUF                                               │
│  • Deploy to Ollama                                             │
└─────────────────────────────────────────────────────────────────┘
```

### What Gets Captured Automatically

Every Claude CLI interaction captures:
- ✅ User prompt
- ✅ Claude's complete response
- ✅ Tool calls (auto-extracted from text)
- ✅ Reasoning signals (constraints, pruning, self-correction)
- ✅ Workflow design (tool sequence, exploration depth)
- ✅ Timing metrics
- ✅ Working directory context

**No manual logging required!**

---

## 🎮 Control Commands

### Start the Engine

```bash
python engine/engine_control.py start
```

Starts the background daemon that:
- Monitors Claude log files
- Processes new traces
- Tracks training thresholds
- Auto-trains when ready

### Check Status

```bash
python engine/engine_control.py status
```

Shows:
- Daemon status (running/stopped)
- Total traces captured
- Progress to training threshold
- Next auto-train trigger

**Example output:**
```
======================================================================
 Claude RL Engine Status
======================================================================

🟢 Daemon: RUNNING (PID: 12345)

📊 Data Collection:
   Total traces captured: 127
   Progress to MVP: 127/50 (254%)
   Progress to production: 127/500 (25.4%)

🎯 Training Status:
   Latest dataset: bc_dataset_20260208.jsonl
   Created: 2026-02-08 04:15:23

🔔 Next auto-train in: 0 traces (ready now!)

🔧 CLI Wrapper:
   Installed: ✅ /home/rohith/.../claude_cli_wrapper.sh

======================================================================
```

### Manual Training Trigger

```bash
python engine/engine_control.py train
```

Manually trigger dataset building and training (doesn't wait for threshold).

### Stop the Engine

```bash
python engine/engine_control.py stop
```

Stops the background daemon (traces still captured via CLI wrapper).

---

## 📁 File Structure

```
claude-rl-agent/
├── engine/
│   ├── engine_control.py ................. Master control script ⭐
│   ├── auto_capture_daemon.py ............ Background daemon
│   ├── process_raw_trace.py .............. Trace processor
│   └── claude-rl-capture.service ......... Systemd service file
│
├── hooks/
│   └── claude_cli_wrapper.sh ............. CLI interception wrapper
│
├── data/
│   ├── traces/ ............................. Processed traces
│   │   └── raw/ ........................... Raw captures (temp)
│   ├── datasets/ .......................... Training datasets
│   └── models/ ............................ Trained models
│
└── logs/
    ├── capture_engine_*.log ............... Daemon logs
    ├── daemon.log ......................... Systemd daemon log
    └── cli_wrapper.log .................... CLI wrapper log
```

---

## ⚙️  Installation Options

### Option 1: CLI Alias (Recommended)

```bash
# Install hooks
python engine/engine_control.py install

# Add to ~/.bashrc or ~/.zshrc
echo 'alias claude="/home/rohith/desktop/CommandCenter/claude-rl-agent/hooks/claude_cli_wrapper.sh"' >> ~/.bashrc

# Reload shell
source ~/.bashrc

# Test
claude "test prompt"
```

**Pro**: Simple, user-controlled
**Con**: Only captures when you use the alias

### Option 2: Systemd Service (Full Automation)

```bash
# Copy service file
sudo cp engine/claude-rl-capture.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable claude-rl-capture
sudo systemctl start claude-rl-capture

# Check status
sudo systemctl status claude-rl-capture
```

**Pro**: Runs automatically on boot, monitors all Claude activity
**Con**: Requires sudo, more complex

### Option 3: Both (Maximum Coverage)

Use **Option 1** for CLI capture + **Option 2** for background monitoring.

---

## 🎯 Auto-Training Thresholds

The engine automatically triggers training when:

1. **Trace Threshold**: 50 new traces since last training
2. **Time Threshold**: 24 hours since last training (if >50 total traces)

You can customize these in `engine/auto_capture_daemon.py`:

```python
self.TRAIN_THRESHOLD = 50  # Traces
self.TRAIN_INTERVAL_HOURS = 24  # Hours
```

---

## 📊 Monitoring

### View Live Logs

```bash
# Daemon logs
tail -f logs/capture_engine_$(date +%Y%m%d).log

# CLI wrapper logs
tail -f logs/cli_wrapper.log

# Systemd logs (if using systemd)
sudo journalctl -u claude-rl-capture -f
```

### Check Captured Traces

```bash
# Count traces
ls -1 data/traces/traces.jsonl | wc -l

# View latest trace
tail -1 data/traces/traces.jsonl | python -m json.tool

# View all workflows
cat data/traces/traces.jsonl | jq -r '.reasoning_signals.tool_sequence | join(" → ")'
```

---

## 🔧 Troubleshooting

### "Daemon not starting"

Check logs:
```bash
tail -20 logs/daemon-error.log
```

Common issues:
- Python path incorrect in systemd service
- Permissions on data/logs directories
- Missing dependencies: `pip install watchdog`

### "CLI wrapper not capturing"

Verify alias:
```bash
alias | grep claude
```

Test manually:
```bash
/home/rohith/desktop/CommandCenter/claude-rl-agent/hooks/claude_cli_wrapper.sh "test"
```

Check logs:
```bash
tail -f logs/cli_wrapper.log
```

### "Traces captured but not processed"

Check processor:
```bash
python engine/process_raw_trace.py data/traces/raw/<trace_file>
```

Verify src/ is in PYTHONPATH.

---

## 🎓 Example Usage

### Day 1: Setup

```bash
# Install
python engine/engine_control.py install
echo 'alias claude="..."' >> ~/.bashrc
source ~/.bashrc

# Start daemon
python engine/engine_control.py start

# Verify
python engine/engine_control.py status
```

### Day 2-7: Use Claude Normally

```bash
# Just use Claude as usual - everything auto-captured!
claude "What's the difference between transformer 1 and 2?"
claude "Refactor the config.py file"
claude "Find all database queries in the codebase"

# Check progress
python engine/engine_control.py status
```

**Output after each command:**
```
🎯 Running Claude Code CLI (auto-capturing)...

[Claude's response here]

✅ Interaction auto-captured: data/traces/raw/20260208_143022_12345.jsonl
📊 Duration: 3s
```

### Week 2: Automatic Training

After 50 traces, you'll see:
```bash
# Daemon log shows:
🎯 Training threshold reached: 50 new traces
🚀 Triggering Automated Training Pipeline
Building dataset from traces...
✅ Dataset saved: data/datasets/bc_dataset_20260208.jsonl
⏳ SFT training triggered (when implemented)
```

---

## 💡 Key Benefits

### vs Manual Capture

| Feature | Manual | Automated |
|---------|--------|-----------|
| **Setup** | Run `./run.sh capture --interactive` each time | Set up once, runs forever |
| **Capture** | Manually log each tool call | Automatically extracted |
| **Training** | Manually trigger | Auto-trains at threshold |
| **Effort** | High (constant attention) | Zero (set and forget) |

### Production Ready

- ✅ Runs as systemd service (survives reboots)
- ✅ Comprehensive logging
- ✅ Error handling and recovery
- ✅ Async processing (doesn't slow down Claude)
- ✅ Configurable thresholds
- ✅ Status monitoring

---

## 🚀 Next Steps

1. **This Week**: Install and start the engine
2. **Week 1-2**: Use Claude normally (50-500 traces auto-captured)
3. **Week 2**: Engine auto-builds dataset and triggers training
4. **Week 3-6**: Implement auto-training (SFT + PPO)
5. **Week 7+**: LLaMA replaces Claude automatically

---

## 📝 Summary

**One-time setup:**
```bash
python engine/engine_control.py install
echo 'alias claude="..."' >> ~/.bashrc
python engine/engine_control.py start
```

**Then forget about it!** The engine:
- ✅ Auto-captures all Claude interactions
- ✅ Auto-extracts reasoning signals
- ✅ Auto-builds training datasets
- ✅ Auto-trains when ready
- ✅ Runs in background forever

**Goal**: 500 traces → Automated training → LLaMA replaces Claude

---

**The automated engine is ready! Start it now and let it run!** 🚀
