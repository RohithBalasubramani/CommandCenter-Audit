"""Configuration for Claude RL Agent."""

from pathlib import Path

# Base paths
AGENT_ROOT = Path(__file__).parent.parent
DATA_DIR = AGENT_ROOT / "data"
TRAINING_DATA_DIR = DATA_DIR / "traces"
DATASETS_DIR = DATA_DIR / "datasets"
MODELS_DIR = DATA_DIR / "models"
CHECKPOINTS_DIR = AGENT_ROOT / "checkpoints"

# Create directories
for dir_path in [DATA_DIR, TRAINING_DATA_DIR, DATASETS_DIR, MODELS_DIR, CHECKPOINTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Model configuration
MODEL_CONFIG = {
    "base_model": "unsloth/Meta-Llama-3.1-8B-Instruct",
    "output_model_name": "llama-claude-bc",
}

# SFT Configuration
SFT_CONFIG = {
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "learning_rate": 5e-5,
    "batch_size": 4,
    "gradient_accumulation_steps": 4,
    "num_epochs": 3,
    "max_length": 4096,
}

# PPO Configuration
PPO_CONFIG = {
    "learning_rate": 1e-5,
    "batch_size": 8,
    "mini_batch_size": 2,
    "ppo_epochs": 4,
    "init_kl_coef": 0.2,
    "target_kl": 0.1,
}

# Reward weights
REWARD_WEIGHTS = {
    "constraint_detection": 0.25,
    "tool_use_alignment": 0.30,
    "self_correction": 0.15,
    "outcome_equivalence": 0.20,
    "reasoning_depth": 0.10,
}
