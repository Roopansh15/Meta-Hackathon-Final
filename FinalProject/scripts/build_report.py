from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inboxworld import (
    EmailEnvironment,
    GreedyBaselinePolicy,
    MultiAgentEmailPolicy,
    dynamic_environment_configs,
    run_simulation,
)


def main() -> None:
    configs = dynamic_environment_configs()
    baseline_results = run_simulation(
        EmailEnvironment(configs),
        GreedyBaselinePolicy(),
        episodes=8,
    )
    multi_agent_results = run_simulation(
        EmailEnvironment(configs),
        MultiAgentEmailPolicy(),
        episodes=8,
    )

    report = {
        "project": "InboxWorld",
        "problem_statement": "Email triage environment with context-aware decisions and delayed business consequences.",
        "theme_positioning": {
            "primary": "Theme 3 - World Modeling",
            "secondary": ["Theme 1 - Multi-Agent Interactions", "Theme 2 - Long-Horizon Planning"],
        },
        "environment_properties": [
            "partial observability",
            "visible-only agent observations",
            "stochastic arrivals",
            "delayed reward buffer",
            "follow-up and escalation generation",
            "time-step pressure",
        ],
        "configs": [
            {
                "config_id": config.config_id,
                "description": config.description,
                "initial_email_count": len(config.initial_emails),
                "scheduled_arrival_count": len(config.arrivals),
                "max_steps": config.max_steps,
            }
            for config in configs
        ],
        "evaluations": {
            "baseline": baseline_results["aggregate"],
            "multi_agent": multi_agent_results["aggregate"],
        },
    }

    output_dir = Path(__file__).resolve().parents[1] / "artifacts"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "pitch_report.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote report to {output_path}")


if __name__ == "__main__":
    main()
