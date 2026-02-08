# Training LLaMA to Replicate Claude Code's Reasoning Behavior

## Overview

This system trains a local LLaMA 3.1 8B model to **behaviorally replicate Claude Code** - not just match text output, but replicate the **entire problem-solving workflow** that Claude uses.

When you ask Claude: *"What's the difference between transformer 1 and transformer 2?"*

Claude doesn't just answer - it **designs and executes a workflow**:
1. Reads schema to understand data structure
2. Searches for relevant code/docs
3. Queries the database
4. Compares results
5. Synthesizes a comprehensive answer

**Goal**: Train LLaMA to learn this meta-capability - to design and execute the same kind of multi-step workflows Claude does.

---

## What We've Built (Week 1 Complete)

### ✅ Core Infrastructure

1. **Data Schemas** ([claude_trace_schema.py](claude_trace_schema.py))
   - `ClaudeTrace`: Complete capture of Claude's interaction
   - `ReasoningSignals`: Latent patterns (constraints, pruning, self-correction)
   - `ToolCall`: Tool usage with reasoning
   - `TraceStorage`: JSONL persistence

2. **Reasoning Extractor** ([reasoning_extractor.py](reasoning_extractor.py))
   - Extracts **constraint detection**: What limitations did Claude identify?
   - Extracts **pruning decisions**: What approaches did Claude reject?
   - Extracts **self-correction**: How did Claude adapt its approach?
   - Analyzes **tool workflows**: What pipeline did Claude design?
   - Measures **exploration depth**: How thoroughly did Claude explore?

3. **Capture System** ([claude_capture_hook.py](claude_capture_hook.py))
   - Manual capture of Claude interactions
   - Interactive CLI for guided capture
   - Quick one-liner capture for simple cases
   - Automatic reasoning extraction on save

4. **Storage Structure**
   ```
   /home/rohith/desktop/CommandCenter/
   ├── rl_training_data/
   │   ├── claude_traces/        # Captured Claude workflows (JSONL)
   │   └── eval_results/          # Evaluation metrics
   └── rl_checkpoints/
       ├── claude_sft_v1/         # SFT checkpoints
       ├── claude_dpo_v1/         # DPO checkpoints
       └── export/                # GGUF models for Ollama
   ```

---

## How to Capture Claude's Workflow

### Method 1: Interactive Capture Session (Recommended)

```bash
cd /home/rohith/desktop/CommandCenter/backend/rl
python -m claude_capture_hook
```

This starts an interactive session that guides you through:
1. Enter your prompt to Claude
2. Ask Claude the question (in separate Claude Code window)
3. Log each tool Claude uses (Read, Bash, Grep, etc.)
4. Paste Claude's final response
5. Rate the response (optional)

**The extractor automatically analyzes the workflow and extracts reasoning signals.**

### Method 2: Quick Manual Capture

```python
from claude_capture_hook import quick_capture

# After you get a response from Claude, quickly log it
quick_capture(
    prompt="What's the difference between transformer 1 and 2?",
    claude_response="[Claude's full response here]",
    tool_calls=[
        ("Read", {"file_path": "schema.py"}, "...file contents..."),
        ("Bash", {"command": "psql -c 'SELECT...'"}, "...query results..."),
    ]
)
```

### Method 3: Programmatic Capture

```python
from claude_capture_hook import ClaudeCapturer

capturer = ClaudeCapturer()

# Before asking Claude
capturer.start_trace("What's the difference between transformer 1 and 2?")

# Log each tool Claude uses
capturer.add_tool_call(
    tool="Read",
    args={"file_path": "/path/to/schema.py"},
    output="... file contents ...",
    reasoning="I'll read the schema to understand the data structure"
)

capturer.add_tool_call(
    tool="Bash",
    args={"command": "psql -U postgres -d command_center_data -c 'SELECT...'"},
    output="... query results ...",
    reasoning="Querying transformer 1 data"
)

# After Claude responds
trace = capturer.finish_trace(claude_response="[Claude's full response]")
capturer.save(trace)
```

---

## Example: Capturing a Real Interaction

### Your Question to Claude:
> "What's the difference between transformer 1 and transformer 2 in the factory data?"

### What Claude Does:
1. **Read** `generate_schema.py` → Understands transformer table structure
2. **Grep** for "transformer" → Finds relevant code
3. **Bash**: `psql ... SELECT * FROM trf_substation_main_1 LIMIT 5` → Gets transformer 1 data
4. **Bash**: `psql ... SELECT * FROM trf_substation_main_2 LIMIT 5` → Gets transformer 2 data
5. **Responds** with comparison

### What Gets Captured:
```json
{
  "user_prompt": "What's the difference between...",
  "tool_calls": [
    {"tool": "Read", "args": {...}, "output": "...", "reasoning": "..."},
    {"tool": "Grep", ...},
    {"tool": "Bash", ...},
    {"tool": "Bash", ...}
  ],
  "claude_response": "Based on the database queries...",
  "reasoning_signals": {
    "tool_sequence": ["Read", "Grep", "Bash", "Bash"],
    "reasoning_steps": 5,
    "exploration_depth": "thorough",
    "used_terminal": true,
    "multi_step_reasoning": true,
    "constraints_detected": [...],
    "explicit_plan": "First I'll read the schema..."
  }
}
```

### What LLaMA Learns:
- **Workflow pattern**: Read schema → Search code → Query database → Compare → Synthesize
- **Tool selection**: When to use Read vs Bash vs Grep
- **Reasoning depth**: Explore before answering (don't jump to conclusions)
- **Multi-step planning**: Design a pipeline, execute it sequentially

---

## Captured Reasoning Signals

The extractor automatically identifies these patterns:

### 1. Constraint Detection
**What**: Limitations Claude identified that affected its approach

**Examples**:
- "Can't modify this file without breaking backward compatibility"
- "Need to preserve existing test coverage"
- "Must avoid changing the public API"

**Why it matters**: LLaMA needs to learn to identify the same constraints

### 2. Pruning Decisions
**What**: Approaches Claude considered but rejected

**Examples**:
- "Could use Write, but Edit is safer for preserving file structure"
- "Considered rewriting from scratch, but refactoring is better"

**Why it matters**: LLaMA needs to learn the same decision-making process

### 3. Self-Correction
**What**: Moments where Claude adjusted its approach

**Examples**:
- "Actually, let me read the file first before editing"
- "That query didn't work, let me try a different pattern"

**Why it matters**: LLaMA needs to learn to adapt when things don't work

### 4. Tool Workflow
**What**: The sequence and logic of tool usage

**Examples**:
- Linear: Read → Grep → Edit
- Exploratory: Read → Read → Read → Grep → Edit (explores first)
- Parallel: Multiple Read calls simultaneously

**Why it matters**: This IS the workflow Claude designed - LLaMA must replicate it

### 5. Reasoning Depth
**What**: How thoroughly Claude explored before answering

**Categories**:
- **Minimal** (1-2 steps): Quick answers
- **Moderate** (3-5 steps): Some exploration
- **Thorough** (6+ steps): Deep exploration
- **Exhaustive** (10+ steps): Very comprehensive

**Why it matters**: LLaMA should match Claude's exploration patterns

---

## Data Collection Goals

### Week 1-2: Bootstrap Dataset
- **Goal**: 500-1000 diverse traces
- **Focus**: Wide variety of query types
- **Quality**: High-quality interactions only (thumbs up)

### Categories to capture:
1. **Database queries** (like transformer example)
2. **Code refactoring** (multi-step edits)
3. **Debugging** (error investigation)
4. **File exploration** (understanding codebases)
5. **System commands** (terminal operations)
6. **Multi-tool workflows** (Read + Grep + Edit chains)
7. **Complex reasoning** (planning before execution)

### Quality Gates:
✅ **Include**:
- Clear problem-solving workflows
- Multi-step reasoning
- Tool chaining
- Claude's explicit planning

❌ **Exclude**:
- Simple one-word answers
- Errors or incomplete responses
- Ambiguous interactions
- Very short responses (<50 words)

---

## Next Steps (Week 2+)

Once you have 500-1000 traces captured:

### Week 2: Behavioral Cloning (SFT)
1. Run `behavioral_cloning_builder.py` to create SFT dataset
2. Train LLaMA with `sft_trainer.py` (supervised fine-tuning)
3. Export to GGUF: `llama-claude-bc-v1.gguf`
4. Manual testing: Does LLaMA use tools correctly?

### Week 3-6: PPO Behavioral Alignment
1. Implement `behavioral_reward_model.py` (reward based on workflow alignment)
2. Implement `ppo_trainer.py` (PPO training loop)
3. Train iteratively: Generate LLaMA response → Compare to Claude → Compute reward → PPO update
4. Quality gate: Behavioral reward >0.80

### Week 7+: Continuous Improvement
1. Deploy LLaMA (5% traffic initially)
2. Collect feedback
3. Mine adversarial prompts (find gaps)
4. Retrain on divergent cases
5. Gradual rollout: 5% → 20% → 50% → 80%

---

## Checking Your Progress

```bash
# Check how many traces you've captured
cd /home/rohith/desktop/CommandCenter/backend/rl
python3 << EOF
from claude_capture_hook import ClaudeCapturer
capturer = ClaudeCapturer()
print(f"Total traces captured: {capturer.get_trace_count()}")
EOF
```

```python
# Inspect a captured trace
from claude_trace_schema import TraceStorage

storage = TraceStorage()
traces = storage.load_traces("traces.jsonl")

# Show first trace
trace = traces[0]
print(f"Prompt: {trace.user_prompt}")
print(f"Tools used: {trace.reasoning_signals.tool_sequence}")
print(f"Reasoning steps: {trace.reasoning_signals.reasoning_steps}")
print(f"Exploration: {trace.reasoning_signals.exploration_depth.value}")
```

---

## FAQ

### Q: Why capture tool calls and not just responses?
**A**: Because we want LLaMA to learn **HOW Claude solves problems**, not just WHAT it says. The workflow is the key behavioral pattern.

### Q: Do I need to capture every interaction with Claude?
**A**: No. Focus on **high-quality, diverse interactions** that show Claude's problem-solving process. 500-1000 good traces is enough to start.

### Q: What if Claude uses a tool I didn't capture?
**A**: That's fine. The extractor will still analyze the workflow from the response text. Just try to capture what you can.

### Q: How is this different from standard fine-tuning?
**A**: Standard fine-tuning optimizes for text similarity. We're optimizing for **behavioral alignment** - did LLaMA design the same workflow as Claude? Did it use the same tools in the same order? Did it catch the same constraints?

### Q: Can LLaMA really match Claude's intelligence?
**A**: The goal is **behavioral replication within a specific domain** (your Command Center codebase). LLaMA won't become "smarter" than Claude in general, but it can learn to replicate Claude's workflow patterns for YOUR specific use case.

---

## File Reference

| File | Purpose |
|------|---------|
| `claude_trace_schema.py` | Data structures for traces and reasoning signals |
| `reasoning_extractor.py` | Extracts latent patterns from Claude's workflow |
| `claude_capture_hook.py` | Manual capture system (interactive + API) |
| `example_capture_claude.py` | Examples and demos |
| `CLAUDE_TRAINING_README.md` | This file |

---

## Support & Troubleshooting

### Captured traces not saving?
Check that the storage directory exists:
```bash
ls -la /home/rohith/desktop/CommandCenter/rl_training_data/claude_traces/
```

### Extractor not finding patterns?
The extractor uses regex patterns. If Claude's response format changes, you may need to adjust the patterns in `reasoning_extractor.py`.

### Want to see what was extracted?
```python
from claude_trace_schema import TraceStorage
storage = TraceStorage()
traces = storage.load_traces()
trace = traces[-1]  # Last trace
print(trace.reasoning_signals.to_dict())
```

---

## Key Insight

> **The goal is to make LLaMA THINK like Claude, not just SOUND like Claude.**

This requires:
1. Capturing Claude's **workflow design** (not just answers)
2. Training LLaMA to **design similar workflows** (behavioral cloning)
3. Using RL to **close behavioral gaps** (PPO alignment)
4. Testing with **human indistinguishability** (blind A/B)

Success = Claude can be removed without users noticing a quality drop.

---

**Start capturing now**: `python -m claude_capture_hook`

Goal: 500 traces in Week 1, 1000 by Week 2. Then we train! 🚀
