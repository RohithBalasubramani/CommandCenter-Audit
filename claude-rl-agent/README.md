# Claude Behavioral Replication Agent

**Train a local LLaMA model to replicate Claude Code's workflow design capability through reinforcement learning.**

## 🎯 What This Does

Claude Code doesn't just answer questions—it **designs and executes complex multi-step workflows**. When you ask *"What's the difference between transformer 1 and transformer 2?"*, Claude:

1. **Designs a pipeline**: Schema → Code search → Database queries → Comparison
2. **Executes the workflow**: Runs each tool sequentially (Read → Grep → Bash → Bash)
3. **Synthesizes results**: Combines all information into a coherent answer

This agent trains a local LLaMA 3.1 8B model to **replicate this meta-capability**, so you can:

✅ Run Claude-quality workflows locally (no API costs)  
✅ Process sensitive data offline (no external API calls)  
✅ Customize for your specific codebase patterns  
✅ Scale to handle high query volumes  

---

## 🚀 Quick Start

### 1. See the Demonstration

```bash
cd /home/rohith/desktop/CommandCenter/claude-rl-agent/src
python agent.py capture --demo
```

This shows how we capture Claude's workflow when answering a transformer comparison question.

### 2. Start Capturing Workflows

```bash
python agent.py capture --interactive
```

Capture 500-1000 diverse Claude interactions over 1-2 weeks. Focus on:
- Database/data queries
- Multi-step file operations
- Complex reasoning workflows
- Tool chaining (RAG + terminal + file reads)

### 3. Check Progress

```bash
python agent.py status
```

Shows how many traces you've captured and what's next.

### 4. Build Training Dataset

```bash
python agent.py build-dataset
```

Converts Claude traces into behavioral cloning training data.

### 5. Train LLaMA (Coming in Week 2)

```bash
python agent.py train --phase sft    # Phase 1: Behavioral cloning
python agent.py train --phase ppo    # Phase 2: RL alignment
```

---

## 📂 Project Structure

```
claude-rl-agent/
├── src/
│   ├── agent.py                        # Main CLI entry point
│   ├── claude_trace_schema.py         # Data structures for workflows
│   ├── reasoning_extractor.py         # Extract behavioral patterns
│   ├── claude_capture_hook.py         # Capture system (interactive + API)
│   ├── behavioral_cloning_builder.py  # Build SFT datasets
│   ├── demo_workflow_capture.py       # Live demonstration
│   └── example_capture_claude.py      # Code examples
├── data/
│   ├── traces/                        # Captured Claude workflows (JSONL)
│   ├── datasets/                      # Training datasets
│   └── models/                        # Trained LLaMA models (GGUF)
├── config/
│   └── agent_config.yaml             # Configuration
├── tests/
│   └── test_agent.py                 # E2E tests
└── README.md                          # This file
```

---

## 🎓 How It Works

### What Makes This Different

**Standard Fine-Tuning:**
- ❌ Trains on text output only
- ❌ LLaMA learns to "sound like Claude"
- ❌ Result: Similar text, but random tool usage

**Our Behavioral Replication:**
- ✅ Trains on workflow design + execution
- ✅ LLaMA learns to "think like Claude"
- ✅ Result: Same tools, same order, same reasoning depth

### Training Pipeline

#### Phase 1: Data Collection (NOW - Week 2)

**Capture Claude's workflows** using the interactive CLI:

```bash
python agent.py capture --interactive
```

For each question, log:
- User prompt
- Tools Claude used (Read, Bash, Grep, etc.)
- WHY Claude chose each tool
- Claude's final response

**Goal**: 500-1000 diverse traces

#### Phase 2: Behavioral Cloning (Week 2)

**Supervised fine-tuning** on Claude's workflows:

```python
# Training data format
{
    "prompt": "What's the difference between transformer 1 and 2?",
    "reasoning_chain": [
        "First, read schema to understand structure",
        "Then search for transformer references",
        "Query both transformers for comparison"
    ],
    "tool_sequence": [
        {"tool": "Read", "reasoning": "Understand schema"},
        {"tool": "Grep", "reasoning": "Find references"},
        {"tool": "Bash", "reasoning": "Query transformer 1"},
        {"tool": "Bash", "reasoning": "Query transformer 2"}
    ],
    "response": "Claude's synthesized answer..."
}
```

**Result**: `llama-claude-bc-v1.gguf` (baseline model)

#### Phase 3: RL Alignment (Week 3-6)

**PPO training** with behavioral reward model:

```python
# Reward model scores LLaMA responses based on:
1. Constraint detection match (25%)
2. Tool use alignment (30%)
3. Self-correction behavior (15%)
4. Outcome equivalence (20%)
5. Reasoning depth (10%)
```

**Result**: `llama-claude-ppo-v{N}.gguf` (aligned model)

#### Phase 4: Continuous Improvement (Week 7+)

- Adversarial prompt mining (find gaps)
- Iterative retraining
- Blind A/B testing (Claude vs LLaMA)
- Gradual deployment (5% → 20% → 50% → 80%)

**Success metric**: Users can't distinguish Claude from LLaMA (indistinguishability >45%)

---

## 📊 What LLaMA Learns

After training on 500-1000 traces, LLaMA learns:

### 1. Meta-Capability: Design Workflows

**Pattern recognition, not memorization**

```
For "compare X and Y" queries:
  → Schema → Search → Query X → Query Y → Compare → Synthesize

Applies to:
  - "What's the difference between transformer 1 and 2?"
  - "Compare DG 1 vs DG 2 performance"
  - "Difference between UPS 1 and UPS 2?"
```

### 2. Tool Selection: When to Use Which Tool

- Database questions → Bash + psql
- Code questions → Read + Grep
- File modifications → Edit (not Write)
- Exploration → Read schema BEFORE querying

### 3. Reasoning Depth: Explore Before Answering

- Don't jump to conclusions
- Gather data first (Read, Grep)
- Then take action (Bash, Edit)
- Synthesize coherently

### 4. Workflow Execution: Sequential vs Parallel

- Foundation → Action (Read schema → Query DB)
- Parallel efficiency (multiple Read calls at once)

### 5. Synthesis: Combine Results

- Structure: Workflow → Findings → Comparison → Conclusion
- Use tables for clarity
- Highlight key differences

---

## 🎯 Success Timeline

| Week | Phase | Goal | Deliverable |
|------|-------|------|-------------|
| 1-2 | **Data Collection** | Capture 500-1000 traces | `traces.jsonl` |
| 2 | **Training Prep** | Build SFT dataset | `bc_dataset.jsonl` |
| 2 | **Behavioral Cloning** | Train baseline | `llama-claude-bc-v1.gguf` |
| 3-6 | **RL Training** | PPO alignment | `llama-claude-ppo-v{N}.gguf` |
| 7+ | **Deployment** | A/B testing, rollout | Indistinguishability >45% |

---

## 📚 Documentation

- **Quick Start**: This README
- **Implementation Plan**: [PLAN.md](../memory/MEMORY.md)
- **Code Examples**: [example_capture_claude.py](src/example_capture_claude.py)
- **Demonstration**: `python agent.py capture --demo`

---

## 🔧 Requirements

```bash
# Python 3.11+
pip install torch transformers trl peft bitsandbytes accelerate

# For Ollama deployment
curl -fsSL https://ollama.com/install.sh | sh

# For GGUF export (llama.cpp)
git clone https://github.com/ggerganov/llama.cpp ~/llama.cpp
cd ~/llama.cpp && cmake -B build && cmake --build build
```

---

## 💡 Key Insights

### Workflow Design Meta-Capability

When you ask:

> "What's the difference between transformer 1 and transformer 2?"

**What we DON'T capture:**
- ❌ Just the final answer text

**What we DO capture:**
- ✅ Claude's workflow design: `Read → Grep → Bash → Bash`
- ✅ WHY each tool: "Read schema to understand structure"
- ✅ Reasoning depth: Thorough (5 steps)
- ✅ Synthesis pattern: Findings → Comparison → Conclusion

**What LLaMA learns:**
- ✅ For comparison queries → Schema → Search → Query both → Compare
- ✅ NOT memorized text, but transferable workflow pattern

### Behavioral Replication vs Text Similarity

**Success is NOT measured by**:
- ❌ Text similarity to Claude's responses
- ❌ Benchmark scores
- ❌ BLEU/ROUGE metrics

**Success IS measured by**:
- ✅ Same tool sequence as Claude
- ✅ Same reasoning depth
- ✅ Users can't distinguish in blind A/B test (>45% indistinguishability)

---

## ❓ FAQ

**Q: Do I need to capture every Claude interaction?**  
A: No! Focus on quality. 500 diverse, high-quality traces is better than 5000 low-quality ones.

**Q: What if I forget to log some tool calls?**  
A: That's OK. The reasoning extractor will analyze the workflow from Claude's response text.

**Q: Can LLaMA really match Claude Code?**  
A: For YOUR specific use case (Command Center codebase), yes. We're teaching behavioral patterns, not general intelligence.

**Q: How long does training take?**  
A: Phase 1 (SFT): ~30 minutes on RTX PRO 6000. Phase 2 (PPO): ~2-4 hours per iteration.

**Q: What if LLaMA diverges from Claude?**  
A: That's what adversarial mining catches. We continuously find gaps and retrain.

---

## 🚀 Get Started Now

```bash
# 1. See the demo
cd /home/rohith/desktop/CommandCenter/claude-rl-agent/src
python agent.py capture --demo

# 2. Check current progress
python agent.py status

# 3. Start capturing
python agent.py capture --interactive

# 4. Track progress
python agent.py status
```

**Goal**: 50 traces in Week 1, 500 by Week 2. Then we train! 🚀

---

## 📝 License

MIT License - See LICENSE file

---

**Every trace brings LLaMA closer to Claude's workflow design capability!**
