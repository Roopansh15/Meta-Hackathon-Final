from __future__ import annotations

from pprint import pprint
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from inboxworld import (
    InboxWorldEnv,
    baseline_policy,
    default_scenarios,
    evaluate_policy_set,
    multi_agent_policy,
    run_episode,
)


def main() -> None:
    scenarios = default_scenarios()

    baseline_env = InboxWorldEnv(scenarios)
    multi_agent_env = InboxWorldEnv(scenarios)

    baseline_summary = run_episode(baseline_env, baseline_policy)
    multi_agent_summary = run_episode(multi_agent_env, multi_agent_policy)

    print("Baseline summary")
    pprint(baseline_summary)
    print()
    print("Multi-agent summary")
    pprint(multi_agent_summary)
    print()

    benchmark = evaluate_policy_set(
        scenarios,
        {
            "baseline": baseline_policy,
            "multi_agent": multi_agent_policy,
        },
    )
    print("Aggregate comparison")
    pprint({name: result["aggregate"] for name, result in benchmark.items()})


if __name__ == "__main__":
    main()
