"""
Minimal RL-style transition collection stub for onsite work.

This file does not fully train a model yet. It demonstrates the exact objects
needed for training:
- state prompt
- structured action
- reward
- transition storage
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inboxworld import EmailEnvironment, collect_episode_transitions, dynamic_environment_configs


def main() -> None:
    env = EmailEnvironment(dynamic_environment_configs())
    transitions = collect_episode_transitions(env, episodes=3)

    output_dir = Path(__file__).resolve().parents[1] / "artifacts" / "training"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "transition_buffer.json"
    output_path.write_text(json.dumps(transitions, indent=2), encoding="utf-8")

    print(f"Collected {len(transitions)} transitions.")
    print(f"Wrote transition buffer to {output_path}")
    print("Pseudo-training loop:")
    print("for episode in episodes:")
    print("    state = env.reset()")
    print("    while not done:")
    print("        action = model(state_prompt)")
    print("        reward = env.step(action).reward")
    print("        store_transition(state, action, reward)")


if __name__ == "__main__":
    main()
