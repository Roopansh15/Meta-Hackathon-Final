from __future__ import annotations

import json
from pathlib import Path
import random
from typing import Protocol

from .environment import EmailEnvironment
from .types import EmailAgentAction


class SupportsAct(Protocol):
    def act(self, state: dict) -> EmailAgentAction: ...


class GreedyBaselinePolicy:
    def act(self, state: dict) -> EmailAgentAction:
        emails = state.get("emails", [])
        if not emails:
            return EmailAgentAction(email_id="none", action_type="ignore_email")
        target = emails[0]
        combined = f"{target.subject} {target.body}".lower()
        high_signal = target.visible_urgency or any(word in combined for word in ["urgent", "asap", "today"])
        low_signal = any(phrase in combined for phrase in ["no action needed", "no pressure", "dinner", "next month"])
        predicted_priority = "high" if high_signal else "low" if low_signal else "medium"
        predicted_urgency = high_signal
        action_type = "ignore_email" if predicted_priority == "low" else "classify_email"
        return EmailAgentAction(
            email_id=target.email_id,
            action_type=action_type,
            predicted_priority=predicted_priority if action_type == "classify_email" else None,
            predicted_urgency=predicted_urgency if action_type == "classify_email" else None,
            reply_tone="neutral",
        )


class RandomNaivePolicy:
    def __init__(self, seed: int = 3) -> None:
        self._rng = random.Random(seed)

    def act(self, state: dict) -> EmailAgentAction:
        emails = state.get("emails", [])
        if not emails:
            return EmailAgentAction(email_id="none", action_type="ignore_email")
        target = self._rng.choice(emails)
        action_type = self._rng.choice(
            ["classify_email", "generate_reply", "delay_email", "escalate_email", "ignore_email"]
        )
        tone = self._rng.choice(["friendly", "neutral", "professional"])
        predicted_priority = self._rng.choice(["low", "medium", "high"]) if action_type == "classify_email" else None
        predicted_urgency = self._rng.choice([True, False]) if action_type == "classify_email" else None
        return EmailAgentAction(
            email_id=target.email_id,
            action_type=action_type,
            predicted_priority=predicted_priority,
            predicted_urgency=predicted_urgency,
            reply_tone=tone,
        )


def run_simulation(
    env: EmailEnvironment,
    agent: SupportsAct,
    episodes: int = 5,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    episode_summaries = []
    reward_history = []

    for _ in range(episodes):
        state = env.reset()
        done = False
        while not done:
            action = agent.act(state)
            result = env.step(action)
            done = result.done
            if not done:
                state = env.get_state()
        summary = env.episode_summary()
        episode_summaries.append(summary)
        reward_history.append(summary["total_reward"])

    aggregate = {
        "episodes": episodes,
        "average_reward": round(sum(reward_history) / len(reward_history), 2) if reward_history else 0.0,
        "success_rate": round(
            sum(summary["success_rate"] for summary in episode_summaries) / len(episode_summaries), 2
        )
        if episode_summaries
        else 0.0,
        "error_rate": round(sum(summary["error_rate"] for summary in episode_summaries) / len(episode_summaries), 2)
        if episode_summaries
        else 0.0,
        "missed_deadlines": sum(summary.get("missed_deadlines", 0) for summary in episode_summaries),
        "escalation_count": sum(summary.get("escalation_threads", 0) for summary in episode_summaries),
        "reward_history": reward_history,
    }

    payload = {
        "aggregate": aggregate,
        "episodes": episode_summaries,
    }

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        (output_path / "simulation_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (output_path / "reward_plot.svg").write_text(_build_svg_plot(reward_history), encoding="utf-8")

    return payload


def run_learning_curve(
    env_factory,
    naive_agent: SupportsAct,
    improved_agent: SupportsAct,
    episodes: int = 12,
    switch_episode: int = 6,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    episode_rows = []
    reward_history = []

    for episode_index in range(episodes):
        agent = naive_agent if episode_index < switch_episode else improved_agent
        phase = "naive" if episode_index < switch_episode else "improved"
        env = env_factory()
        state = env.reset()
        done = False
        while not done:
            action = agent.act(state)
            result = env.step(action)
            done = result.done
            if not done:
                state = env.get_state()
        summary = env.episode_summary()
        reward_history.append(summary["total_reward"])
        episode_rows.append(
            {
                "episode": episode_index + 1,
                "phase": phase,
                "reward": summary["total_reward"],
                "error_rate": summary["error_rate"],
                "missed_deadlines": summary.get("missed_deadlines", 0),
                "escalation_threads": summary.get("escalation_threads", 0),
            }
        )

    payload = {
        "episodes": episode_rows,
        "aggregate": {
            "reward_history": reward_history,
            "naive_average_reward": round(sum(row["reward"] for row in episode_rows[:switch_episode]) / max(switch_episode, 1), 2),
            "improved_average_reward": round(
                sum(row["reward"] for row in episode_rows[switch_episode:]) / max(episodes - switch_episode, 1), 2
            ),
        },
    }

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        (output_path / "learning_curve.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (output_path / "learning_curve.svg").write_text(_build_svg_plot(reward_history), encoding="utf-8")

    return payload


def _build_svg_plot(reward_history: list[float]) -> str:
    width = 640
    height = 320
    margin = 40
    if not reward_history:
        reward_history = [0.0]

    min_reward = min(reward_history)
    max_reward = max(reward_history)
    span = max(max_reward - min_reward, 1.0)

    points = []
    for index, reward in enumerate(reward_history):
        x = margin + (index * (width - 2 * margin) / max(len(reward_history) - 1, 1))
        y = height - margin - ((reward - min_reward) / span) * (height - 2 * margin)
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)
    labels = "".join(
        f"<text x='{margin + i * (width - 2 * margin) / max(len(reward_history) - 1, 1):.1f}' y='{height - 10}' font-size='12'>E{i + 1}</text>"
        for i in range(len(reward_history))
    )

    return f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>
  <rect width='100%' height='100%' fill='#fffdf8'/>
  <line x1='{margin}' y1='{height - margin}' x2='{width - margin}' y2='{height - margin}' stroke='#1f2937' stroke-width='2'/>
  <line x1='{margin}' y1='{margin}' x2='{margin}' y2='{height - margin}' stroke='#1f2937' stroke-width='2'/>
  <polyline fill='none' stroke='#0f766e' stroke-width='3' points='{polyline}'/>
  <text x='{width / 2}' y='24' font-size='18' text-anchor='middle'>Reward vs Episode</text>
  <text x='16' y='{height / 2}' font-size='12' transform='rotate(-90 16,{height / 2})'>Reward</text>
  {labels}
</svg>"""
