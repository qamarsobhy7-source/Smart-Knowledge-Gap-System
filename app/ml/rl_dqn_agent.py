"""
DQN Agent — Deep Q-Network for Adaptive Learning Path.

Uses a small MLP (2 hidden layers) to learn a Q-function:

    Q(state, action) = expected future reward

The agent learns to pick the next concept that maximizes the
student's total mastery gain over an episode.

Reference:
    Mnih et al. (2015) — "Human-level control through deep
    reinforcement learning" (Nature)
"""

import json
import random
from collections import deque

import joblib
import numpy as np

from .config import MODELS_DIR, RANDOM_SEED


DQN_MODEL_PATH = MODELS_DIR / "rl_dqn_agent.joblib"
DQN_TORCH_PATH = MODELS_DIR / "rl_dqn_agent.pt"
DQN_METRICS_PATH = MODELS_DIR / "metrics" / "rl_dqn_metrics.json"


class ReplayBuffer:
    """Fixed-size experience replay buffer."""

    def __init__(self, capacity=50000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int64),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.float32),
        )

    def __len__(self):
        return len(self.buffer)


class DQNAgent:
    """Deep Q-Network agent."""

    def __init__(
        self,
        state_dim,
        action_dim,
        hidden_dim=128,
        lr=1e-3,
        gamma=0.95,
        epsilon_start=1.0,
        epsilon_end=0.05,
        epsilon_decay=0.995,
    ):
        import torch
        import torch.nn as nn

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay

        torch.manual_seed(RANDOM_SEED)
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)

        class _QNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(state_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Linear(hidden_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Linear(hidden_dim, action_dim),
                )

            def forward(self, x):
                return self.net(x)

        self.q_net = _QNet()
        self.target_net = _QNet()
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.target_net.eval()

        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=lr)
        self.loss_fn = nn.SmoothL1Loss()

        self.replay = ReplayBuffer()

    # ---------------------------------------------------------
    # Action selection
    # ---------------------------------------------------------
    def select_action(self, state, training=True):
        import torch

        if training and random.random() < self.epsilon:
            return random.randrange(self.action_dim)

        with torch.no_grad():
            state_t = torch.tensor([state], dtype=torch.float32)
            q_values = self.q_net(state_t)
            return int(q_values.argmax(dim=1).item())

    # ---------------------------------------------------------
    # Training step
    # ---------------------------------------------------------
    def train_step(self, batch_size=64):
        import torch

        if len(self.replay) < batch_size:
            return None

        states, actions, rewards, next_states, dones = self.replay.sample(batch_size)

        states_t = torch.tensor(states, dtype=torch.float32)
        actions_t = torch.tensor(actions, dtype=torch.int64).unsqueeze(1)
        rewards_t = torch.tensor(rewards, dtype=torch.float32)
        next_states_t = torch.tensor(next_states, dtype=torch.float32)
        dones_t = torch.tensor(dones, dtype=torch.float32)

        # Current Q
        q_values = self.q_net(states_t).gather(1, actions_t).squeeze(1)

        # Target Q
        with torch.no_grad():
            next_q = self.target_net(next_states_t).max(dim=1)[0]
            target_q = rewards_t + self.gamma * next_q * (1.0 - dones_t)

        loss = self.loss_fn(q_values, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), 1.0)
        self.optimizer.step()

        return float(loss.item())

    # ---------------------------------------------------------
    # Target network update
    # ---------------------------------------------------------
    def update_target(self):
        self.target_net.load_state_dict(self.q_net.state_dict())

    # ---------------------------------------------------------
    # Epsilon decay
    # ---------------------------------------------------------
    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)


# ============================================================
# TRAINING LOOP
# ============================================================
def train_dqn(
    env,
    n_episodes=1000,
    batch_size=64,
    target_update_every=10,
    verbose=True,
):
    """Train a DQN agent on the given environment."""
    state_dim = env.state_dim
    action_dim = env.action_dim

    agent = DQNAgent(state_dim=state_dim, action_dim=action_dim)

    episode_rewards = []
    episode_losses = []

    for ep in range(1, n_episodes + 1):
        state = env.reset()
        total_reward = 0.0
        total_loss = 0.0
        loss_count = 0

        while True:
            action = agent.select_action(state, training=True)
            next_state, reward, done, _ = env.step(action)

            agent.replay.push(state, action, reward, next_state, float(done))

            loss = agent.train_step(batch_size=batch_size)
            if loss is not None:
                total_loss += loss
                loss_count += 1

            state = next_state
            total_reward += reward

            if done:
                break

        agent.decay_epsilon()

        if ep % target_update_every == 0:
            agent.update_target()

        episode_rewards.append(total_reward)
        if loss_count > 0:
            episode_losses.append(total_loss / loss_count)

        if verbose and ep % 50 == 0:
            avg_r = np.mean(episode_rewards[-50:])
            avg_l = np.mean(episode_losses[-50:]) if episode_losses else 0.0
            print(
                f"   Episode {ep:5d}/{n_episodes} "
                f"— avg reward: {avg_r:8.2f}  "
                f"— epsilon: {agent.epsilon:.3f}  "
                f"— loss: {avg_l:.4f}"
            )

    # Evaluate the trained agent (no exploration)
    agent.epsilon = 0.0
    eval_rewards = []
    for _ in range(50):
        state = env.reset()
        total = 0.0
        while True:
            action = agent.select_action(state, training=False)
            state, reward, done, _ = env.step(action)
            total += reward
            if done:
                break
        eval_rewards.append(total)

    metrics = {
        "task": "reinforcement_learning",
        "model": "DQN",
        "purpose": "Adaptive Learning Path",
        "evaluation_type": "Development Evaluation",
        "synthetic_data": True,
        "n_episodes": n_episodes,
        "final_epsilon": float(agent.epsilon),
        "avg_reward_last_50_train": float(np.mean(episode_rewards[-50:])),
        "avg_reward_best_50_train": float(np.mean(sorted(episode_rewards)[-50:])),
        "avg_reward_eval_50": float(np.mean(eval_rewards)),
        "std_reward_eval_50": float(np.std(eval_rewards)),
    }

    return agent, metrics


# ============================================================
# SAVE / LOAD
# ============================================================
def save_dqn_agent(agent, metrics):
    import torch

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    torch.save(agent.q_net.state_dict(), DQN_TORCH_PATH)

    joblib.dump(
        {
            "state_dim": agent.state_dim,
            "action_dim": agent.action_dim,
            "gamma": agent.gamma,
        },
        DQN_MODEL_PATH,
    )

    DQN_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DQN_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n✅ DQN agent saved: {DQN_TORCH_PATH}")
    print(f"✅ DQN metadata: {DQN_MODEL_PATH}")
    print(f"✅ DQN metrics: {DQN_METRICS_PATH}")


def load_dqn_agent():
    """Load a trained DQN agent from disk."""
    import torch

    if not (DQN_TORCH_PATH.exists() and DQN_MODEL_PATH.exists()):
        return None

    metadata = joblib.load(DQN_MODEL_PATH)

    agent = DQNAgent(
        state_dim=metadata["state_dim"],
        action_dim=metadata["action_dim"],
        gamma=metadata["gamma"],
    )
    agent.q_net.load_state_dict(torch.load(DQN_TORCH_PATH))
    agent.q_net.eval()
    agent.epsilon = 0.0

    return agent


def plan_learning_path(agent, initial_mastery, n_steps=10):
    """
    Use the trained agent to plan a personalized learning path.

    Args:
        agent: trained DQNAgent
        initial_mastery: array of shape (n_concepts,) with values 0..1
        n_steps: number of concepts to recommend

    Returns:
        List of concept indices in recommended order.
    """
    import torch

    state = np.concatenate([
        initial_mastery.astype(np.float32),
        np.array([0.0], dtype=np.float32),
    ])

    path = []
    for _ in range(n_steps):
        with torch.no_grad():
            state_t = torch.tensor([state], dtype=torch.float32)
            q_values = agent.q_net(state_t)
            action = int(q_values.argmax(dim=1).item())

        path.append(action)

        # Simulate the improvement (approximate)
        max_gain = 0.1 * (1.0 - state[action])
        state[action] = min(1.0, state[action] + max_gain)
        state[-1] = (action + 1) / agent.action_dim

    return path
