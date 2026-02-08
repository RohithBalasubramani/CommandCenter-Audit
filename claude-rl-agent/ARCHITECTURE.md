# Claude Behavioral Replication Agent - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION WITH CLAUDE CODE                     │
│   "What's the difference between transformer 1 and transformer 2?"      │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  CLAUDE'S WORKFLOW DESIGN & EXECUTION                    │
│                                                                          │
│  Planning:   "Need to compare two DB entities"                          │
│              "Design: Schema → Search → Query → Compare"                │
│                                                                          │
│  Execution:  Read("schema.py") → "Understand structure"                 │
│              Grep("transformer") → "Find references"                     │
│              Bash("psql trf_1") → "Query transformer 1"                  │
│              Bash("psql trf_2") → "Query transformer 2"                  │
│                                                                          │
│  Synthesis:  Compare → Analyze → Generate answer                        │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ CAPTURE
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              REASONING SIGNAL EXTRACTOR (reasoning_extractor.py)         │
│                                                                          │
│  Extracts:                                                               │
│    ✓ Tool sequence: [Read, Grep, Bash, Bash]                           │
│    ✓ Reasoning chain: ["First...", "Then...", "Next..."]               │
│    ✓ Constraint detection: What limitations Claude identified           │
│    ✓ Pruning decisions: What approaches Claude rejected                 │
│    ✓ Self-corrections: How Claude adapted mid-workflow                  │
│    ✓ Exploration depth: Minimal | Moderate | Thorough | Exhaustive     │
│                                                                          │
│  Output: ClaudeTrace with ReasoningSignals                              │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ STORE
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  TRACE STORAGE (claude_trace_schema.py)                  │
│                                                                          │
│  File: data/traces/traces.jsonl                                         │
│                                                                          │
│  Format (per line):                                                     │
│  {                                                                      │
│    "trace_id": "uuid",                                                  │
│    "user_prompt": "What's the difference...",                           │
│    "tool_calls": [                                                      │
│      {"tool": "Read", "reasoning": "...", "output": "..."},            │
│      {"tool": "Grep", "reasoning": "...", "output": "..."},            │
│      ...                                                                 │
│    ],                                                                    │
│    "reasoning_signals": {                                               │
│      "tool_sequence": ["Read", "Grep", "Bash", "Bash"],                │
│      "reasoning_steps": 5,                                              │
│      "exploration_depth": "thorough",                                   │
│      "multi_step_reasoning": true,                                      │
│      ...                                                                 │
│    },                                                                    │
│    "claude_response": "...",                                            │
│    ...                                                                   │
│  }                                                                      │
│                                                                          │
│  Goal: 500-1000 traces                                                  │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ BUILD DATASET
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│       BEHAVIORAL CLONING DATASET (behavioral_cloning_builder.py)         │
│                                                                          │
│  Converts traces into SFT training samples:                             │
│                                                                          │
│  {                                                                      │
│    "prompt": "What's the difference...",                                │
│    "reasoning_chain": [                                                 │
│      "First, read schema to understand structure",                      │
│      "Then search for transformer references",                          │
│      ...                                                                 │
│    ],                                                                    │
│    "tool_sequence": [                                                   │
│      {"tool": "Read", "reasoning": "Understand schema"},                │
│      {"tool": "Grep", "reasoning": "Find references"},                  │
│      ...                                                                 │
│    ],                                                                    │
│    "response": "Claude's synthesized answer",                           │
│    "workflow_type": "exploratory",                                      │
│    "exploration_depth": "thorough"                                      │
│  }                                                                      │
│                                                                          │
│  File: data/datasets/bc_dataset.jsonl                                   │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ TRAIN (Phase 1)
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                SFT TRAINER (Coming in Week 2)                            │
│                                                                          │
│  Supervised Fine-Tuning on Claude's workflows:                          │
│                                                                          │
│  Base: unsloth/Meta-Llama-3.1-8B-Instruct                              │
│  Method: QLoRA (4-bit quantization)                                     │
│  LoRA config: rank=16, alpha=32                                         │
│  Training: 3 epochs, 4096 max length                                    │
│                                                                          │
│  Teaches LLaMA:                                                         │
│    ✓ Basic tool usage patterns                                         │
│    ✓ Step-by-step reasoning                                            │
│    ✓ Workflow design fundamentals                                      │
│                                                                          │
│  Output: models/llama-claude-bc-v1.gguf                                 │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ REFINE (Phase 2)
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│           BEHAVIORAL REWARD MODEL (Coming in Week 3)                     │
│                                                                          │
│  Scores LLaMA responses vs Claude traces:                               │
│                                                                          │
│  Reward Components:                                                     │
│    1. Constraint detection match (25%)                                  │
│       → Did LLaMA catch same limitations?                               │
│                                                                          │
│    2. Tool use alignment (30%)                                          │
│       → Same tools in similar order?                                    │
│       → Levenshtein distance of sequences                               │
│                                                                          │
│    3. Self-correction behavior (15%)                                    │
│       → Did LLaMA recover like Claude?                                  │
│                                                                          │
│    4. Outcome equivalence (20%)                                         │
│       → Same final result?                                              │
│       → Diff comparison for code edits                                  │
│                                                                          │
│    5. Reasoning depth (10%)                                             │
│       → Explored enough before answering?                               │
│                                                                          │
│  Total reward: [-1.0, 1.0]                                              │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ TRAIN (Phase 2)
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                PPO TRAINER (Coming in Weeks 3-6)                         │
│                                                                          │
│  Proximal Policy Optimization:                                          │
│                                                                          │
│  Training loop:                                                         │
│    1. LLaMA generates response for prompt                               │
│    2. Extract LLaMA's reasoning signals                                 │
│    3. Compare with Claude's trace (behavioral reward)                   │
│    4. PPO update (with KL penalty to stay close to Claude)              │
│                                                                          │
│  Iterative improvement:                                                 │
│    - Adversarial prompt mining (find divergent cases)                   │
│    - Prioritize retraining on gaps                                      │
│    - Checkpoint every 50 steps                                          │
│    - Quality gate: reward >0.80                                         │
│                                                                          │
│  Output: models/llama-claude-ppo-v{N}.gguf                              │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │ DEPLOY
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              DEPLOYMENT & TESTING (Week 7+)                              │
│                                                                          │
│  Export Pipeline:                                                       │
│    1. Merge LoRA adapters with base model                               │
│    2. Convert to GGUF format (f16)                                      │
│    3. Quantize to q4_k_m (balanced quality/size)                        │
│    4. Register with Ollama: cc-claude-agent:latest                      │
│                                                                          │
│  Testing:                                                                │
│    - Blind A/B test (50 samples)                                        │
│    - Users rate Claude vs LLaMA responses                               │
│    - Success: Indistinguishability >45%                                 │
│                                                                          │
│  Gradual Rollout:                                                       │
│    Week 1: 5% traffic → LLaMA                                           │
│    Week 2: 20% traffic → LLaMA                                          │
│    Week 3: 50% traffic → LLaMA                                          │
│    Week 4+: 80% traffic → LLaMA                                         │
│                                                                          │
│  Goal: Replace Claude entirely when indistinguishability >48%           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Question
    ↓
Claude Code (workflow design + execution)
    ↓
Capture System (claude_capture_hook.py)
    ↓
Reasoning Extraction (reasoning_extractor.py)
    ↓
Trace Storage (traces.jsonl)
    ↓
Dataset Builder (behavioral_cloning_builder.py)
    ↓
SFT Training (sft_trainer.py)
    ↓
Baseline Model (llama-claude-bc-v1.gguf)
    ↓
Behavioral Reward Model (behavioral_reward_model.py)
    ↓
PPO Training (ppo_trainer.py)
    ↓
Aligned Model (llama-claude-ppo-vN.gguf)
    ↓
GGUF Export & Ollama Deployment
    ↓
Local Claude-Quality Workflows 🎉
```

## Component Interactions

### Phase 1: Capture (Week 1-2)
```
User → ClaudeCapturer → TraceStorage → traces.jsonl
              ↑
              └─── ReasoningSignalExtractor
```

### Phase 2: Dataset (Week 2)
```
traces.jsonl → BehavioralCloningDatasetBuilder → bc_dataset.jsonl
```

### Phase 3: SFT (Week 2)
```
bc_dataset.jsonl → SFTTrainer → llama-claude-bc-v1.gguf
```

### Phase 4: PPO (Week 3-6)
```
llama-claude-bc-v1.gguf → PPOTrainer ←→ BehavioralRewardModel
                               ↓
                    llama-claude-ppo-vN.gguf
                               ↓
                    AdversarialPromptMiner
                               ↓
                    (find gaps, retrain)
```

### Phase 5: Deploy (Week 7+)
```
llama-claude-ppo-vN.gguf → GGUFExporter → OllamaDeployer
                                              ↓
                                    cc-claude-agent:latest
                                              ↓
                                    IndistinguishabilityTest
                                              ↓
                                    (if >45%, deploy)
```

## Key Design Decisions

### 1. Why JSONL for Traces?
- Append-only (no file locking issues)
- Easy streaming (process one line at a time)
- Human-readable (can inspect with `tail -f`)
- Git-friendly (line-based diffs)

### 2. Why Separate Reasoning Extraction?
- Modular (can improve extraction without changing capture)
- Testable (can validate extraction on known traces)
- Extensible (can add new signal types)

### 3. Why Two-Phase Training (SFT + PPO)?
- SFT: Bootstrap basic patterns quickly
- PPO: Fine-tune for behavioral alignment
- Safer than pure RL (starts from supervised baseline)

### 4. Why Behavioral Rewards (not text similarity)?
- Text similarity doesn't capture workflow logic
- Same answer, different workflow = failure
- Behavioral alignment = same tools, same order, same depth

### 5. Why Adversarial Mining?
- Prevents overfitting to captured traces
- Finds edge cases proactively
- Ensures robustness

### 6. Why Gradual Rollout?
- Safety (can rollback if issues)
- A/B testing (measure real impact)
- User confidence (gradual transition)

---

## Success Criteria by Phase

### Phase 1: Capture
- ✅ 500+ diverse traces collected
- ✅ Traces cover: DB queries, file ops, complex reasoning, tool chains
- ✅ Reasoning signals extracted automatically
- ✅ Storage validated (can load all traces)

### Phase 2: Dataset
- ✅ Training samples built from traces
- ✅ Reasoning chains complete
- ✅ Tool sequences valid
- ✅ Dataset statistics look good (avg 4+ tools per sample)

### Phase 3: SFT
- ✅ Model converges (loss decreases)
- ✅ Can generate valid tool sequences
- ✅ Basic reasoning present
- ✅ No catastrophic failures (e.g., wrong file edits)

### Phase 4: PPO
- ✅ Behavioral reward >0.80 (on held-out set)
- ✅ Tool use alignment >85%
- ✅ Constraint detection >75%
- ✅ No regressions (new failure modes)

### Phase 5: Deploy
- ✅ Indistinguishability >45% (blind A/B)
- ✅ Zero production issues
- ✅ User satisfaction maintained
- ✅ **Goal: Remove Claude entirely** 🎉

---

**This architecture enables local, Claude-quality workflows without API costs or external dependencies!**
