from __future__ import annotations

from typing import Callable, Dict, Iterable, List

from .environment import InboxWorldEnv, run_episode
from .types import Scenario


PolicyFn = Callable


def evaluate_policy_set(
    scenarios: List[Scenario],
    policies: Dict[str, PolicyFn],
) -> Dict[str, object]:
    summaries: Dict[str, object] = {}
    for policy_name, policy in policies.items():
        env = InboxWorldEnv(scenarios)
        episode_summaries = []
        for _ in scenarios:
            episode_summaries.append(run_episode(env, policy))
        summaries[policy_name] = {
            "episodes": episode_summaries,
            "aggregate": aggregate_episode_summaries(episode_summaries),
        }
    return summaries


def aggregate_episode_summaries(episode_summaries: Iterable[Dict[str, object]]) -> Dict[str, object]:
    episode_list = list(episode_summaries)
    if not episode_list:
        return {
            "average_reward": 0.0,
            "average_priority_accuracy": 0.0,
            "average_action_accuracy": 0.0,
            "missed_urgent_total": 0,
            "unnecessary_escalation_total": 0,
        }

    reward_total = 0.0
    priority_total = 0.0
    action_total = 0.0
    missed_urgent_total = 0
    unnecessary_escalation_total = 0

    for summary in episode_list:
        reward_total += float(summary["cumulative_reward"])
        priority_total += float(summary["priority_accuracy"])
        action_total += float(summary["action_accuracy"])
        missed_urgent_total += int(summary.get("missed_urgent_count", 0))
        unnecessary_escalation_total += int(summary.get("unnecessary_escalation_count", 0))

    count = len(episode_list)
    return {
        "average_reward": round(reward_total / count, 2),
        "average_priority_accuracy": round(priority_total / count, 2),
        "average_action_accuracy": round(action_total / count, 2),
        "missed_urgent_total": missed_urgent_total,
        "unnecessary_escalation_total": unnecessary_escalation_total,
        "episodes_run": count,
    }


def build_pitch_report(
    scenarios: List[Scenario],
    evaluations: Dict[str, object],
) -> Dict[str, object]:
    scenario_cards = []
    for scenario in scenarios:
        scenario_cards.append(
            {
                "scenario_id": scenario.scenario_id,
                "description": scenario.description,
                "pending_tasks": scenario.pending_tasks,
                "drift_notes": scenario.drift_notes,
                "email_count": len(scenario.emails),
            }
        )

    return {
        "project": "InboxWorld",
        "problem_statement": "Email triage environment with context-aware decision making and delayed business consequences.",
        "theme_positioning": {
            "primary": "Theme 3 - World Modeling",
            "secondary": ["Theme 1 - Multi-Agent Interactions", "Theme 2 - Long-Horizon Planning"],
        },
        "scenarios": scenario_cards,
        "evaluations": evaluations,
    }
