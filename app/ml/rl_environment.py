"""
RL Environment — Simulated Student Learning Environment.

The RL agent acts as a "tutor" that picks the next concept a student
should study. The environment simulates how the student's mastery
changes when they study a concept.

State: (mastery vector over N concepts, last studied concept index)
Action: pick concept index to study next (0..N-1)
Reward: improvement in mastery on the studied concept
Episode: fixed number of steps (default 30)
"""

import numpy as np


class LearningEnvironment:
    """Gym-like environment for adaptive learning path."""

    def __init__(
        self,
        n_concepts=45,
        max_steps=30,
        seed=42,
    ):
        self.n_concepts = n_concepts
        self.max_steps = max_steps
        self.rng = np.random.default_rng(seed)

        # Per-concept base difficulty (will be set externally if needed)
        self.difficulty = np.full(n_concepts, 0.3, dtype=np.float32)

        # State
        self.mastery = None
        self.step_count = 0
        self.last_action = -1

    # ---------------------------------------------------------
    # Reset
    # ---------------------------------------------------------
    def reset(self):
        """Reset the environment to a new random student."""
        # Initial mastery: random low values
        self.mastery = self.rng.uniform(0.1, 0.5, size=self.n_concepts).astype(np.float32)

        # Some concepts are already strong
        n_strong = self.rng.integers(0, 5)
        if n_strong > 0:
            strong_idx = self.rng.choice(self.n_concepts, size=n_strong, replace=False)
            self.mastery[strong_idx] = self.rng.uniform(0.7, 0.9, size=n_strong)

        self.step_count = 0
        self.last_action = -1

        return self._get_state()

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------
    def _get_state(self):
        """Return current state as a flat vector."""
        # Normalize last_action to [0, 1]
        last_action_norm = (self.last_action + 1) / self.n_concepts
        return np.concatenate([
            self.mastery,
            np.array([last_action_norm], dtype=np.float32),
        ])

    # ---------------------------------------------------------
    # Step
    # ---------------------------------------------------------
    def step(self, action):
        """
        Apply an action (pick a concept to study).

        Returns:
            next_state, reward, done, info
        """
        action = int(action)
        if action < 0 or action >= self.n_concepts:
            # Invalid action → big penalty
            return self._get_state(), -1.0, True, {"invalid": True}

        old_mastery = float(self.mastery[action])

        # Learning gain depends on:
        #   - current mastery (diminishing returns as mastery approaches 1)
        #   - difficulty of the concept
        #   - a small random factor
        max_gain = 0.15 * (1.0 - old_mastery)  # higher gain when mastery is low
        base_gain = max_gain * (1.0 - self.difficulty[action] * 0.5)
        actual_gain = float(
            np.clip(base_gain * self.rng.uniform(0.6, 1.2), 0.0, max_gain)
        )

        # Apply the gain
        new_mastery = float(np.clip(old_mastery + actual_gain, 0.0, 1.0))
        self.mastery[action] = new_mastery

        # Reward: improvement + small bonus for reaching mastery
        reward = actual_gain * 10.0
        if new_mastery > 0.8 and old_mastery <= 0.8:
            reward += 1.0  # reached mastery threshold

        # Small penalty for repeatedly studying the same concept
        if action == self.last_action:
            reward -= 0.05

        self.last_action = action
        self.step_count += 1
        done = self.step_count >= self.max_steps

        info = {
            "concept": action,
            "old_mastery": old_mastery,
            "new_mastery": new_mastery,
            "gain": actual_gain,
        }

        return self._get_state(), reward, done, info

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    @property
    def state_dim(self):
        return self.n_concepts + 1

    @property
    def action_dim(self):
        return self.n_concepts

    def set_difficulty(self, difficulty_array):
        """Set per-concept difficulty (values 0..1)."""
        d = np.asarray(difficulty_array, dtype=np.float32)
        if d.shape[0] != self.n_concepts:
            raise ValueError("Difficulty array size mismatch.")
        self.difficulty = d
