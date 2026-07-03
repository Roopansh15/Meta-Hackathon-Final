from __future__ import annotations

from pathlib import Path
from pprint import pprint
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inboxworld import (
    EmailEnvironment,
    GreedyBaselinePolicy,
    MultiAgentEmailPolicy,
    RandomNaivePolicy,
    dynamic_environment_configs,
    run_learning_curve,
    run_simulation,
)


def main() -> None:
    configs = dynamic_environment_configs()
    artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts" / "adaptive_environment"
    env_factory = lambda: EmailEnvironment(dynamic_environment_configs())

    baseline_results = run_simulation(
        EmailEnvironment(configs),
        GreedyBaselinePolicy(),
        episodes=8,
        output_dir=artifacts_dir / "baseline",
    )
    adaptive_results = run_simulation(
        EmailEnvironment(configs),
        MultiAgentEmailPolicy(),
        episodes=8,
        output_dir=artifacts_dir / "multi_agent",
    )
    learning_curve = run_learning_curve(
        env_factory=env_factory,
        naive_agent=RandomNaivePolicy(seed=17),
        improved_agent=MultiAgentEmailPolicy(),
        episodes=12,
        switch_episode=6,
        output_dir=artifacts_dir / "learning_curve",
    )

    print("Baseline aggregate")
    pprint(baseline_results["aggregate"])
    print()
    print("Adaptive multi-agent aggregate")
    pprint(adaptive_results["aggregate"])
    print()
    print("Learning curve aggregate")
    pprint(learning_curve["aggregate"])
    print()
    print(f"Artifacts written under {artifacts_dir}")


if __name__ == "__main__":
    main()
