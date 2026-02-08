# 🧠 Deep Behavioral Comparison System

## What Gets Captured & Compared

When running automated comparisons, the system extracts and compares **EVERYTHING** about how Claude and LLaMA think:

### 1. Tool Sequence (Workflow Design)
**What it captures:**
- Exact sequence of tools used
- Order matters: `Bash → Read → Bash` ≠ `Read → Bash`
- Parallelism detection

**Comparison:**
```
Claude:  Bash → Read → Grep → Bash → Edit
LLaMA:   Bash → Read → Bash

Status: DIFFERENT ❌
Reason: LLaMA missing Grep step and Edit step
Training: YES - teach LLaMA the full workflow
```

### 2. Reasoning Depth (Thinking Steps)
**What it captures:**
- Number of intermediate reasoning steps
- "First...", "Then...", "Next...", "Finally..."
- Step-by-step thinking chain

**Comparison:**
```
Claude: 5 reasoning steps
LLaMA:  2 reasoning steps

Status: SHALLOW ❌
Reason: LLaMA skipped intermediate thinking
Training: YES - teach LLaMA to think deeper
```

### 3. Constraint Detection
**What it captures:**
- Limitations identified ("Can't modify without breaking...")
- Requirements recognized ("Must check X before Y...")
- Constraints that shaped the approach

**Comparison:**
```
Claude: 3 constraints detected
  • "Must verify table exists before query"
  • "Need to handle NULL values"
  • "Query must finish in <5s for real-time dashboard"

LLaMA: 0 constraints detected

Status: MISSING ❌
Reason: LLaMA didn't identify constraints
Training: YES - teach constraint awareness
```

### 4. Self-Correction
**What it captures:**
- Mistakes caught and fixed
- "Actually, let me...", "Wait, that won't work..."
- Approach revisions mid-execution

**Comparison:**
```
Claude: 1 self-correction
  • "Actually, I need to check the schema first"
  • Changed approach from direct query to schema check

LLaMA: 0 self-corrections

Status: MISSING ❌
Reason: LLaMA didn't catch potential issues
Training: YES - teach self-awareness
```

### 5. Exploration Depth
**What it captures:**
- How thoroughly the problem was explored
- minimal / moderate / thorough / exhaustive
- Appropriateness for task complexity

**Comparison:**
```
Claude: thorough (6+ steps for complex query)
LLaMA:  minimal (1-2 steps)

Status: DIFFERENT ❌
Reason: LLaMA underexplored complex problem
Training: YES - teach appropriate exploration
```

### 6. Tool Pruning (Approaches Considered but Rejected)
**What it captures:**
- Tools considered but not used
- "I could use X, but Y is better because..."
- Decision-making process

**Comparison:**
```
Claude: Considered 3 approaches, chose best
  • Grep (rejected: too slow for 357 tables)
  • Python script (rejected: overkill)
  • Direct SQL (chosen: fastest for this case)

LLaMA: No pruning detected

Status: MISSING ❌
Reason: LLaMA didn't show decision process
Training: YES - teach deliberation
```

### 7. Text Similarity (Reference Only)
**What it captures:**
- Word overlap (Jaccard similarity)
- Length similarity
- Surface-level comparison

**Note:** This is SECONDARY - behavioral patterns matter more!

---

## Example Full Comparison

**Prompt:**
> "What's the average power consumption of chiller_001 in June 2024?"

### Claude's Execution:

```
🧠 Reasoning Chain:
1. First, I'll query the schema to confirm column names
2. Then I'll filter data for June 2024 timeframe
3. Next, I'll calculate average using AVG() aggregate
4. Finally, I'll format the result with units

🔧 Tool Sequence:
Bash → Read → Bash

🚧 Constraints Detected:
• Must handle timezone (IST) correctly
• June 2024 data might be large (43,200 rows)
• Need to use efficient aggregation

🔍 Exploration: moderate

📝 Response:
[Claude's detailed answer with context]
```

### LLaMA's Execution:

```
🧠 Reasoning Chain:
1. Query the database for average

🔧 Tool Sequence:
Bash

🚧 Constraints Detected: (none)

🔍 Exploration: minimal

📝 Response:
[LLaMA's brief answer]
```

### Comparison Result:

```
╔════════════════════════════════════════════════════════════╗
║ BEHAVIORAL COMPARISON RESULTS                              ║
╚════════════════════════════════════════════════════════════╝

⏱  Execution Time:
  Claude: 3.2s | LLaMA: 1.1s

🔧 Tool Sequence:
  Claude: Bash → Read → Bash
  LLaMA:  Bash
  Match:  DIFFERENT ❌

🧠 Reasoning Depth:
  Claude: 4 steps
  LLaMA:  1 step
  Status: DIFFERENT ❌

🚧 Constraint Detection:
  Claude: 3 constraints
  LLaMA:  0 constraints
  Status: MISSING ❌

🔄 Self-Correction:
  Claude: 0 corrections
  LLaMA:  0 corrections

🔍 Exploration Depth:
  Claude: moderate
  LLaMA:  minimal
  Status: DIFFERENT ❌

────────────────────────────────────────────────────────────
📊 Overall Behavioral Similarity: 35%
📝 Text Overlap: 67%

🎯 TRAINING NEEDED
   Reasons:
   • Tool sequence mismatch (missing Read step)
   • Reasoning depth differs (75% shallower)
   • Exploration depth mismatch (minimal vs moderate)
   • LLaMA missing constraint detection
────────────────────────────────────────────────────────────
```

### DPO Training Pair Created:

```json
{
  "prompt": "What's the average power consumption of chiller_001 in June 2024?",
  "chosen": "[Claude's full response with all reasoning]",
  "rejected": "[LLaMA's shallow response]",
  "behavioral_differences": {
    "tool_sequence": "Missing Read step",
    "reasoning_depth": "4 steps vs 1 step",
    "constraints": "Missing 3 constraint detections",
    "exploration": "minimal vs moderate"
  }
}
```

---

## Why This Matters

**Text-only comparison:**
- "Both mentioned chiller_001" ✓
- "Both gave a number" ✓
- **RESULT:** 67% similar → might not train

**Deep behavioral comparison:**
- LLaMA missing Read step (didn't verify schema) ❌
- LLaMA didn't identify timezone constraint ❌
- LLaMA explored minimally (should be moderate) ❌
- LLaMA's reasoning is 75% shallower ❌
- **RESULT:** 35% similar → MUST train!

**The deep comparison catches problems that text similarity misses!**

---

## Run It Now

```bash
cd /home/rohith/desktop/CommandCenter/claude-rl-agent/src

# Run automated deep comparison (50 prompts)
python automated_runner.py --batch 50

# This will:
# 1. Generate 50 Command Center prompts
# 2. Run each through Claude CLI (captures EVERYTHING)
# 3. Run each through LLaMA (captures EVERYTHING)
# 4. Deep compare ALL behavioral patterns
# 5. Create DPO pairs for behavioral differences
# 6. Save for training
```

---

## Training on Behavioral Differences

Once you have DPO pairs from deep comparison:

```bash
# Train LLaMA to match Claude's behavioral patterns
./run.sh train --phase ppo

# This trains LLaMA to:
# ✓ Use the same tool sequences as Claude
# ✓ Reason with the same depth as Claude
# ✓ Detect constraints like Claude
# ✓ Self-correct like Claude
# ✓ Explore appropriately like Claude
```

---

## The Complete Loop

```
1. Automated Runner generates prompt
   ↓
2. Claude executes (captures ALL reasoning)
   ↓
3. LLaMA executes (captures ALL reasoning)
   ↓
4. Deep Behavioral Comparison
   • Tool sequences
   • Reasoning chains
   • Constraints
   • Self-corrections
   • Exploration depth
   • Everything
   ↓
5. Identify Differences
   ↓
6. Create DPO Training Pairs
   ↓
7. Train LLaMA to Match Claude
   ↓
8. Repeat (continuous improvement)
```

---

**This is TRUE behavioral cloning - not just text similarity!** 🧠
