"""
Low-Rank Scorer — Lightweight neural reranker for widget selection.

Tier 1 of the continuous RL system. Trains in milliseconds from each
feedback event and re-ranks LLM widget outputs immediately.

Architecture:
    Input: intent embedding (768-dim) ⊕ widget one-hot (19-dim) = 787-dim
    Hidden: Low-rank factorization  W = A @ B  where A: (787, r), B: (r, 64)
    Output: score adjustment ∈ [-1, 1] via tanh

    Total parameters at rank=8: 787*8 + 8*64 + 64*1 = 6,872 (tiny)

This is NOT an LLM — it's a learned scoring adjustment that sits on top
of the LLM's widget selection, continuously adapting from user feedback.
"""

import json
import logging
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
import torch.optim as optim

logger = logging.getLogger(__name__)

# Paths
_RL_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _RL_DIR.parent.parent
SCORER_CHECKPOINT_DIR = _PROJECT_DIR / "rl_checkpoints" / "scorer"

# Get embedding dim from the model used
INTENT_EMBEDDING_DIM = 768  # BGE-base-en-v1.5 output dim
NUM_SCENARIOS = 19           # Number of widget scenarios in catalog
INPUT_DIM = INTENT_EMBEDDING_DIM + NUM_SCENARIOS  # 787


class LowRankScorer(nn.Module):
    """
    Low-rank factorized scoring network.

    Uses W = A @ B factorization to keep parameter count tiny while
    still learning meaningful adjustments to widget scores.
    """

    def __init__(self, input_dim: int = INPUT_DIM, rank: int = 8, hidden_dim: int = 64):
        super().__init__()

        self.rank = rank
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim

        # Low-rank factorized layer: W = A @ B
        # Instead of a full (input_dim, hidden_dim) matrix with 50,368 params,
        # we use A(input_dim, rank) @ B(rank, hidden_dim) with 6,808 params
        self.A = nn.Linear(input_dim, rank, bias=False)
        self.B = nn.Linear(rank, hidden_dim, bias=True)

        # Output head
        self.out = nn.Linear(hidden_dim, 1, bias=True)

        # Activation
        self.relu = nn.ReLU()
        self.tanh = nn.Tanh()

        # Initialize with small weights (start near zero = no adjustment)
        self._init_weights()

    def _init_weights(self):
        """Small initialization so scorer starts near-zero (no adjustment)."""
        nn.init.normal_(self.A.weight, std=0.01)
        nn.init.normal_(self.B.weight, std=0.01)
        nn.init.zeros_(self.B.bias)
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: (batch, input_dim) — concatenation of intent embedding + scenario one-hot

        Returns:
            (batch, 1) — score adjustment in [-1, 1]
        """
        h = self.A(x)          # (batch, rank)
        h = self.relu(h)
        h = self.B(h)          # (batch, hidden_dim)
        h = self.relu(h)
        score = self.out(h)    # (batch, 1)
        return self.tanh(score)  # Clamp to [-1, 1]

    @property
    def num_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())


@dataclass
class ScorerState:
    """Tracked state of the scorer."""
    training_steps: int = 0
    total_feedback_events: int = 0
    avg_loss: float = 0.0
    recent_losses: list = None

    def __post_init__(self):
        if self.recent_losses is None:
            self.recent_losses = []


class ContinuousLowRankTrainer:
    """
    Continuously trains the low-rank scorer from feedback.

    Each feedback event triggers an immediate gradient update.
    No batching, no epochs — pure online learning.
    """

    def __init__(
        self,
        rank: int = 8,
        lr: float = 1e-3,
        weight_decay: float = 1e-4,
        checkpoint_every: int = 50,
        device: str = "cpu",  # CPU is fine for this tiny model
    ):
        self.device = torch.device(device)
        self.scorer = LowRankScorer(rank=rank).to(self.device)
        self.optimizer = optim.AdamW(
            self.scorer.parameters(),
            lr=lr,
            weight_decay=weight_decay,
        )
        self.checkpoint_every = checkpoint_every
        self.state = ScorerState()

        # Embedding model (lazy loaded)
        self._embed_model = None
        self._embed_lock = threading.Lock()

        # Scenario name → index mapping
        self._scenario_to_idx: dict[str, int] = {}
        self._init_scenario_mapping()

        # Thread safety
        self._lock = threading.Lock()

        # Try to load existing checkpoint
        self._load_checkpoint()

        logger.info(
            f"LowRankScorer initialized: rank={rank}, params={self.scorer.num_parameters}, "
            f"device={self.device}, steps={self.state.training_steps}"
        )

    def _init_scenario_mapping(self):
        """Build scenario name to index mapping from widget catalog."""
        try:
            from layer2.widget_catalog import VALID_SCENARIOS
            for idx, name in enumerate(sorted(VALID_SCENARIOS)):
                self._scenario_to_idx[name] = idx
        except ImportError:
            # Fallback scenarios
            scenarios = [
                "alerts", "category-bar", "chatstream", "comparison",
                "composition", "distribution", "edgedevicepanel",
                "eventlogstream", "flow-sankey", "kpi", "matrix-heatmap",
                "peoplehexgrid", "peoplenetwork", "peopleview",
                "supplychainglobe", "timeline", "trend",
                "trend-multi-line", "trends-cumulative",
            ]
            for idx, name in enumerate(scenarios):
                self._scenario_to_idx[name] = idx

    def _get_embedding(self, text: str) -> torch.Tensor:
        """Get intent embedding from sentence-transformers."""
        with self._embed_lock:
            if self._embed_model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    model_name = os.getenv("RAG_EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
                    self._embed_model = SentenceTransformer(model_name)
                    logger.info(f"Loaded embedding model: {model_name}")
                except ImportError:
                    logger.warning("sentence-transformers not available, using random embeddings")
                    return torch.randn(INTENT_EMBEDDING_DIM)

            embedding = self._embed_model.encode(text, convert_to_tensor=True)
            return embedding.cpu().float()

    def _encode_input(self, transcript: str, scenario: str) -> torch.Tensor:
        """
        Encode a (transcript, scenario) pair into scorer input.

        Returns: (1, input_dim) tensor
        """
        # Intent embedding
        intent_emb = self._get_embedding(transcript)  # (768,)

        # Scenario one-hot
        scenario_vec = torch.zeros(NUM_SCENARIOS)
        idx = self._scenario_to_idx.get(scenario.lower(), -1)
        if idx >= 0:
            scenario_vec[idx] = 1.0

        # Concatenate
        x = torch.cat([intent_emb, scenario_vec], dim=0)  # (787,)
        return x.unsqueeze(0).to(self.device)  # (1, 787)

    def score_widgets(
        self,
        transcript: str,
        scenarios: list[str],
    ) -> dict[str, float]:
        """
        Score a list of widget scenarios for a given transcript.

        Args:
            transcript: User's query text
            scenarios: List of scenario names to score

        Returns:
            Dict mapping scenario → score adjustment in [-1, 1]
        """
        self.scorer.eval()
        scores = {}

        with torch.no_grad():
            for scenario in scenarios:
                x = self._encode_input(transcript, scenario)
                adjustment = self.scorer(x).item()
                scores[scenario] = adjustment

        return scores

    def train_step(
        self,
        transcript: str,
        scenario: str,
        reward: float,
    ) -> float:
        """
        Single online training step from one feedback event.

        Args:
            transcript: User's query
            scenario: Widget scenario that was selected
            reward: Reward signal (-2 to +2, from RewardSignalAggregator)

        Returns:
            Training loss
        """
        with self._lock:
            self.scorer.train()

            x = self._encode_input(transcript, scenario)
            target = torch.tensor([[max(-1.0, min(1.0, reward / 2.0))]],
                                  device=self.device)  # Normalize to [-1, 1]

            # Forward
            predicted = self.scorer(x)

            # MSE loss: predicted adjustment should match normalized reward
            loss = nn.functional.mse_loss(predicted, target)

            # Backward + update
            self.optimizer.zero_grad()
            loss.backward()

            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_(self.scorer.parameters(), max_norm=1.0)

            self.optimizer.step()

            # Track state
            loss_val = loss.item()
            self.state.training_steps += 1
            self.state.total_feedback_events += 1
            self.state.recent_losses.append(loss_val)
            if len(self.state.recent_losses) > 100:
                self.state.recent_losses = self.state.recent_losses[-100:]
            self.state.avg_loss = sum(self.state.recent_losses) / len(self.state.recent_losses)

            # Checkpoint periodically
            if self.state.training_steps % self.checkpoint_every == 0:
                self._save_checkpoint()

            return loss_val

    def train_batch(
        self,
        experiences: list[tuple[str, str, float]],
    ) -> float:
        """
        Train on a batch of (transcript, scenario, reward) tuples.

        Args:
            experiences: List of (transcript, scenario, reward)

        Returns:
            Average loss
        """
        total_loss = 0.0
        for transcript, scenario, reward in experiences:
            loss = self.train_step(transcript, scenario, reward)
            total_loss += loss

        return total_loss / max(len(experiences), 1)

    def _save_checkpoint(self):
        """Save scorer checkpoint to disk."""
        SCORER_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        path = SCORER_CHECKPOINT_DIR / "scorer_latest.pt"

        torch.save({
            "model_state_dict": self.scorer.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "state": {
                "training_steps": self.state.training_steps,
                "total_feedback_events": self.state.total_feedback_events,
                "avg_loss": self.state.avg_loss,
            },
            "scenario_mapping": self._scenario_to_idx,
        }, str(path))

        logger.info(f"Scorer checkpoint saved: step={self.state.training_steps}")

    def _load_checkpoint(self):
        """Load scorer checkpoint from disk if available."""
        path = SCORER_CHECKPOINT_DIR / "scorer_latest.pt"
        if not path.exists():
            return

        try:
            checkpoint = torch.load(str(path), map_location=self.device, weights_only=False)
            self.scorer.load_state_dict(checkpoint["model_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

            state = checkpoint.get("state", {})
            self.state.training_steps = state.get("training_steps", 0)
            self.state.total_feedback_events = state.get("total_feedback_events", 0)
            self.state.avg_loss = state.get("avg_loss", 0.0)

            logger.info(f"Scorer checkpoint loaded: step={self.state.training_steps}")
        except Exception as e:
            logger.warning(f"Failed to load scorer checkpoint: {e}")

    def get_stats(self) -> dict:
        """Get scorer statistics."""
        return {
            "type": "low_rank_scorer",
            "rank": self.scorer.rank,
            "parameters": self.scorer.num_parameters,
            "device": str(self.device),
            "training_steps": self.state.training_steps,
            "total_feedback_events": self.state.total_feedback_events,
            "avg_loss": round(self.state.avg_loss, 6),
            "recent_losses": [round(l, 6) for l in self.state.recent_losses[-10:]],
        }


# ============================================================
# Singleton
# ============================================================

_scorer: Optional[ContinuousLowRankTrainer] = None
_scorer_lock = threading.Lock()


def get_scorer() -> ContinuousLowRankTrainer:
    """Get the global low-rank scorer instance."""
    global _scorer
    if _scorer is None:
        with _scorer_lock:
            if _scorer is None:
                _scorer = ContinuousLowRankTrainer()
    return _scorer
