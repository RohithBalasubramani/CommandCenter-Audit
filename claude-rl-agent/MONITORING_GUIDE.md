# 🔍 Training Monitoring Guide

## Quick Status Check

```bash
cd /home/rohith/desktop/CommandCenter/claude-rl-agent

# One-time status check
./monitor_training.sh

# Continuous monitoring (updates every 30s)
./watch_training.sh

# Live output stream (real-time)
tail -f /tmp/claude-1000/-home-rohith-desktop-CommandCenter/tasks/b4e4805.output
```

---

## What to Look For

### 1. Tokenization Phase (Current)
```
Unsloth: Tokenizing ["text"] (num_proc=68):  41%|████  | 226/554
```
- Should complete in ~5-15 minutes total
- Progress bar shows percentage and samples processed
- GPU memory will be high (95%+) but GPU utilization low

### 2. Training Phase (Next)
```
Epoch 1/3:  10%|█         | 55/554 [02:30<22:45,  2.74s/it]
  loss: 1.234
  learning_rate: 1.9e-4
```
- Will see epoch progress (1/3, 2/3, 3/3)
- Loss should decrease over time (good training)
- Each epoch takes ~45-80 minutes
- GPU utilization should be 80-100%

### 3. Saving Phase (Final)
```
Saving checkpoint to: models/sft_claude_llama_vXX/
✅ Training complete!
```
- Quick save (~1-2 minutes)
- Model ready for PPO or export

---

## Training Stages Timeline

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Model Load   │ Tokenization │   Training   │     Save     │
│   30 min     │   10-15 min  │   2-4 hours  │   1-2 min    │
│      ✅      │      🔄      │      ⏳      │      ⏳      │
└──────────────┴──────────────┴──────────────┴──────────────┘
                    You are here ↑
```

**Total Expected Time**: ~3-5 hours from start to finish

---

## GPU Monitoring

```bash
# Watch GPU usage live
watch -n 1 nvidia-smi

# GPU memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# GPU utilization over time
nvidia-smi dmon -c 60
```

**Expected GPU Metrics**:
- **Tokenization**: 0-10% utilization, 95%+ memory
- **Training**: 80-100% utilization, 95%+ memory
- **Temperature**: 50-75°C (safe range)

---

## Common Issues

### Issue: "Out of Memory"
```
CUDA out of memory. Tried to allocate 1.31 GB
```
**Solution**: Reduce batch size in `src/sft_trainer.py` line 330

### Issue: "Process Killed"
```
Killed
```
**Solution**: System OOM. Check `dmesg | tail` and reduce memory usage

### Issue: "Training Stuck"
**Check**:
```bash
# Is process running?
ps aux | grep "agent.py train"

# Is GPU active?
nvidia-smi

# Recent output?
tail /tmp/claude-1000/-home-rohith-desktop-CommandCenter/tasks/b4e4805.output
```

---

## Background Task Management

```bash
# Check if training is running
ps aux | grep "agent.py train" | grep -v grep

# Get PID
TRAINING_PID=$(ps aux | grep "agent.py train" | grep -v grep | awk '{print $2}')

# Kill training (if needed)
kill $TRAINING_PID

# Force kill (if really stuck)
kill -9 $TRAINING_PID

# View full output
less /tmp/claude-1000/-home-rohith-desktop-CommandCenter/tasks/b4e4805.output

# Search for errors
grep -i error /tmp/claude-1000/-home-rohith-desktop-CommandCenter/tasks/b4e4805.output
```

---

## Next Steps After Training

### When SFT Completes:

1. **Verify Model Saved**:
   ```bash
   ls -lh data/models/sft_claude_llama_*/
   ```

2. **Start PPO Training**:
   ```bash
   ./run.sh train --phase ppo --episodes 100
   ```

3. **Or Skip to Export**:
   ```bash
   ./run.sh export
   ```

---

## Monitoring Commands Reference

| Command | Description | Update Frequency |
|---------|-------------|------------------|
| `./monitor_training.sh` | One-time status snapshot | Manual |
| `./watch_training.sh` | Auto-refresh monitor | Every 30s |
| `tail -f /tmp/.../output` | Live output stream | Real-time |
| `nvidia-smi` | GPU snapshot | Manual |
| `watch -n 1 nvidia-smi` | Live GPU monitor | Every 1s |
| `./run.sh status` | Agent status | Manual |

---

## Estimated Completion Times

**Current Time**: 2026-02-08 05:27 AM

**Milestones**:
- ✅ Training started: 05:20 AM
- 🔄 Tokenization done: ~05:35 AM (estimated)
- ⏳ Epoch 1 done: ~06:20-07:00 AM
- ⏳ Epoch 2 done: ~07:05-07:45 AM
- ⏳ Epoch 3 done: ~07:50-08:30 AM
- ⏳ SFT complete: ~08:30-09:30 AM

**Next Phase**:
- PPO training: ~10:00-11:00 AM
- GGUF export: ~11:00-11:05 AM
- Deployment: ~11:05-11:10 AM

**Full Pipeline Complete**: ~11:00 AM (estimated)

---

## Pro Tips

1. **Keep Terminal Open**: Don't close the terminal where training was started
2. **Use `screen` or `tmux`**: For detachable sessions
3. **Monitor GPU Temperature**: Should stay under 80°C
4. **Check Disk Space**: Training generates large checkpoint files
5. **Save Output Logs**: Copy important output for debugging

```bash
# Save full training log
cp /tmp/claude-1000/-home-rohith-desktop-CommandCenter/tasks/b4e4805.output \
   /home/rohith/desktop/CommandCenter/claude-rl-agent/logs/sft_training_$(date +%Y%m%d_%H%M%S).log
```

---

**Happy Training! 🚀**
