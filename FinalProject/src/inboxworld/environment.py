from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import random
from typing import Callable, Dict, List

from .reward_calculator import compute_reward, delayed_reward_calculation
from .types import (
    ActionOutcome,
    BufferedRewardEvent,
    EmailAgentAction,
    EmailEnvConfig,
    InboxEmail,
    Scenario,
    StepResult,
    TriageAction,
)

try:
    from openenv import Environment  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - local fallback for environments without OpenEnv installed
    class Environment:
        """Fallback base class to keep local demo runnable without OpenEnv."""

        pass

class InboxWorldEnv(Environment):
    def __init__(self, scenarios: List[Scenario]):
        if not scenarios:
            raise ValueError("InboxWorldEnv requires at least one scenario.")
        self.scenarios = scenarios
        self._scenario_index = -1
        self.current_scenario: Scenario | None = None
        self._cursor = 0
        self._cumulative_reward = 0.0
        self._events: List[Dict[str, object]] = []

    def reset(self) -> Dict[str, object]:
        self._scenario_index = (self._scenario_index + 1) % len(self.scenarios)
        self.current_scenario = self.scenarios[self._scenario_index]
        self._cursor = 0
        self._cumulative_reward = 0.0
        self._events = []
        return self._observation()

    def step(self, action: TriageAction) -> StepResult:
        if self.current_scenario is None:
            raise RuntimeError("Call reset() before step().")

        email = self.current_scenario.emails[self._cursor]
        expected = self.current_scenario.expected_outcomes[email.email_id]
        reward, metrics = self._score_action(action, expected)
        self._cumulative_reward += reward

        self._events.append(
            {
                "email_id": email.email_id,
                "reward": reward,
                "predicted_priority": action.priority,
                "predicted_action": action.action_type,
                "expected_priority": expected["priority"],
                "expected_action": expected["action_type"],
            }
        )

        self._cursor += 1
        done = self._cursor >= len(self.current_scenario.emails)
        info = {
            "metrics": metrics,
            "cumulative_reward": round(self._cumulative_reward, 2),
            "scenario_id": self.current_scenario.scenario_id,
        }
        if done:
            info["episode_summary"] = self.episode_summary()
        return StepResult(reward=reward, done=done, info=info)

    def episode_summary(self) -> Dict[str, object]:
        total = len(self._events)
        if total == 0:
            return {
                "scenario_id": self.current_scenario.scenario_id if self.current_scenario else None,
                "cumulative_reward": 0.0,
                "priority_accuracy": 0.0,
                "action_accuracy": 0.0,
                "missed_urgent_count": 0,
                "unnecessary_escalation_count": 0,
            }

        priority_hits = sum(1 for event in self._events if event["predicted_priority"] == event["expected_priority"])
        action_hits = sum(1 for event in self._events if event["predicted_action"] == event["expected_action"])
        missed_urgent_count = sum(
            1
            for event in self._events
            if event["expected_priority"] == "high" and event["predicted_priority"] != "high"
        )
        unnecessary_escalation_count = sum(
            1
            for event in self._events
            if event["predicted_action"] == "escalate" and event["expected_action"] != "escalate"
        )
        return {
            "scenario_id": self.current_scenario.scenario_id if self.current_scenario else None,
            "cumulative_reward": round(self._cumulative_reward, 2),
            "priority_accuracy": round(priority_hits / total, 2),
            "action_accuracy": round(action_hits / total, 2),
            "missed_urgent_count": missed_urgent_count,
            "unnecessary_escalation_count": unnecessary_escalation_count,
            "events": self._events,
        }

    def _observation(self) -> Dict[str, object]:
        if self.current_scenario is None:
            raise RuntimeError("Environment has not been reset.")

        email = self.current_scenario.emails[self._cursor]
        return {
            "scenario_id": self.current_scenario.scenario_id,
            "description": self.current_scenario.description,
            "user_profile": asdict(self.current_scenario.user_profile),
            "thread_history": self.current_scenario.thread_history.get(email.thread_id, ""),
            "pending_tasks": self.current_scenario.pending_tasks,
            "email": asdict(email),
            "remaining_emails": len(self.current_scenario.emails) - self._cursor,
        }

    def _score_action(
        self,
        action: TriageAction,
        expected: Dict[str, object],
    ) -> tuple[float, Dict[str, float]]:
        reward = 0.0
        metrics = {
            "priority_correct": 0.0,
            "action_correct": 0.0,
            "deadline_correct": 0.0,
            "unnecessary_escalation": 0.0,
        }

        if action.priority == expected["priority"]:
            reward += 2.0
            metrics["priority_correct"] = 1.0
        else:
            reward -= 1.5

        if action.action_type == expected["action_type"]:
            reward += 2.5
            metrics["action_correct"] = 1.0
        else:
            reward -= 2.0

        if action.extracted_deadline_hours == expected["deadline_hours"]:
            reward += 1.0
            metrics["deadline_correct"] = 1.0
        elif expected["deadline_hours"] is not None:
            reward -= 0.5

        if action.action_type == "escalate" and expected["action_type"] != "escalate":
            reward -= 1.0
            metrics["unnecessary_escalation"] = 1.0

        if expected["priority"] == "high" and action.priority != "high":
            reward -= 2.0

        return reward, metrics


def run_episode(
    env: InboxWorldEnv,
    policy: Callable,
) -> Dict[str, object]:
    observation = env.reset()
    done = False
    while not done:
        email = env.current_scenario.emails[env._cursor]
        action = policy(email, env.current_scenario)
        result = env.step(action)
        done = result.done
        if not done:
            observation = env._observation()
    return env.episode_summary()


class EmailEnvironment(Environment):
    def __init__(self, configs: List[EmailEnvConfig] | None = None):
        if configs is None:
            from .scenarios import dynamic_environment_configs

            configs = dynamic_environment_configs()
        if not configs:
            raise ValueError("EmailEnvironment requires at least one config.")
        self.configs = configs
        self._config_index = -1
        self.current_config: EmailEnvConfig | None = None
        self._time_step = 0
        self._emails: List[InboxEmail] = []
        self._pending_arrivals: List[InboxEmail] = []
        self._history: List[Dict[str, object]] = []
        self._cumulative_reward = 0.0
        self._reward_buffer: List[BufferedRewardEvent] = []
        self._rng = random.Random(7)
        self._missed_deadlines = 0
        self._escalation_threads = 0

    def reset(self) -> Dict[str, object]:
        self._config_index = (self._config_index + 1) % len(self.configs)
        self.current_config = self.configs[self._config_index]
        self._time_step = 0
        self._emails = deepcopy(self.current_config.initial_emails)
        self._pending_arrivals = deepcopy(self.current_config.arrivals)
        self._history = []
        self._cumulative_reward = 0.0
        self._reward_buffer = []
        self._rng = random.Random(self.current_config.random_seed)
        self._missed_deadlines = 0
        self._escalation_threads = 0
        return self.get_state()

    def get_state(self) -> Dict[str, object]:
        if self.current_config is None:
            raise RuntimeError("Call reset() before requesting state.")
        return {
            "config_id": self.current_config.config_id,
            "description": self.current_config.description,
            "time_step": self._time_step,
            "user_profile": asdict(self.current_config.user_profile),
            "emails": [self._visible_email(email) for email in self._emails if not email.resolved],
            "resolved_count": sum(1 for email in self._emails if email.resolved),
            "time_budget_remaining": self.current_config.time_budget_per_step - 1,
            "pending_delayed_rewards": len(self._reward_buffer),
            "history": self._public_history(),
        }

    def step(self, action: EmailAgentAction) -> StepResult:
        if self.current_config is None:
            raise RuntimeError("Call reset() before step().")

        target = self._find_email(action.email_id)
        outcome = self._apply_action(target, action)
        reward, metrics = compute_reward(target, action, outcome, time_step=self._time_step)
        self._cumulative_reward += reward
        self._enqueue_reward_event(target, action, outcome)

        self._time_step += 1
        overdue_penalty_triggered = self._advance_unresolved_emails()
        if overdue_penalty_triggered:
            reward -= 4.0
            self._cumulative_reward -= 4.0
            metrics["deadline_penalty"] = metrics.get("deadline_penalty", 0.0) + 1.0
            outcome.overdue_penalty_triggered = True
            outcome.notes.append("A previously unresolved email crossed its deadline.")
            self._missed_deadlines += 1

        new_arrivals = self._release_new_arrivals()
        if new_arrivals:
            outcome.new_email_ids.extend(new_arrivals)
            outcome.notes.append("New emails arrived after the action.")

        delayed_reward, delayed_metrics, delayed_events = delayed_reward_calculation(
            self._time_step,
            self._reward_buffer,
            self._emails,
        )
        if delayed_reward != 0.0:
            reward += delayed_reward
            self._cumulative_reward += delayed_reward
        metrics.update(delayed_metrics)

        event = {
            "time_step": self._time_step,
            "action": asdict(action),
            "reward": round(reward, 2),
            "metrics": metrics,
            "outcome": asdict(outcome),
            "delayed_events": delayed_events,
        }
        self._history.append(event)

        done = self._is_done()
        info = {
            "cumulative_reward": round(self._cumulative_reward, 2),
            "metrics": metrics,
            "outcome": asdict(outcome),
            "remaining_emails": len([email for email in self._emails if not email.resolved]),
            "missed_deadlines": self._missed_deadlines,
            "escalation_threads": self._escalation_threads,
        }
        if done:
            info["episode_summary"] = self.episode_summary()
        return StepResult(reward=reward, done=done, info=info)

    def episode_summary(self) -> Dict[str, object]:
        total_steps = len(self._history)
        mistakes = sum(
            1
            for event in self._history
            if event["reward"] < 0 or event["outcome"]["follow_up_created"] or event["outcome"]["overdue_penalty_triggered"]
        )
        successes = sum(1 for event in self._history if event["reward"] > 0 and event["outcome"]["handled_correctly"])
        return {
            "config_id": self.current_config.config_id if self.current_config else None,
            "total_reward": round(self._cumulative_reward, 2),
            "steps": total_steps,
            "success_rate": round(successes / total_steps, 2) if total_steps else 0.0,
            "error_rate": round(mistakes / total_steps, 2) if total_steps else 0.0,
            "mistakes": mistakes,
            "missed_deadlines": self._missed_deadlines,
            "escalation_threads": self._escalation_threads,
            "history": self._history,
        }

    def _apply_action(self, email: InboxEmail | None, action: EmailAgentAction) -> ActionOutcome:
        if email is None:
            return ActionOutcome(
                email_id=action.email_id,
                handled_correctly=False,
                resolved=False,
                follow_up_created=False,
                overdue_penalty_triggered=False,
                new_email_ids=[],
                notes=["Action referenced an unknown email."],
            )

        handled_correctly = False
        resolved = False
        follow_up_created = False
        new_email_ids: List[str] = []
        notes: List[str] = []

        if action.action_type == "classify_email":
            email.classified_priority = action.predicted_priority
            email.classified_urgency = action.predicted_urgency
            handled_correctly = action.predicted_priority == email.priority
            notes.append("Email classified for later batching.")
        elif action.action_type == "generate_reply":
            resolved = True
            email.resolved = True
            handled_correctly = email.expected_action == "generate_reply"
            email.satisfaction_delta += 2 if handled_correctly else -2
            notes.append("Reply drafted and thread resolved.")
        elif action.action_type == "delay_email":
            email.age_steps += max(action.delay_steps, 1)
            handled_correctly = email.expected_action == "delay_email"
            email.satisfaction_delta -= 1 if email.urgency else 0
            notes.append("Email delayed for later handling.")
        elif action.action_type == "escalate_email":
            resolved = True
            email.resolved = True
            handled_correctly = email.expected_action == "escalate_email"
            email.satisfaction_delta += 1 if handled_correctly else -2
            notes.append(f"Email escalated to {action.escalate_target}.")
        elif action.action_type == "ignore_email":
            resolved = True
            email.resolved = True
            handled_correctly = email.expected_action == "ignore_email"
            email.satisfaction_delta -= 3 if email.priority == "high" else 0
            notes.append("Email ignored and removed from queue.")

        escalation_thread_created = False
        if not handled_correctly and email.priority == "high" and not email.angry_follow_up_generated:
            follow_up = self._build_angry_follow_up(email)
            self._emails.append(follow_up)
            email.angry_follow_up_generated = True
            follow_up_created = True
            new_email_ids.append(follow_up.email_id)
            notes.append("Wrong handling triggered an angry follow-up email.")

        if action.action_type == "generate_reply" and action.reply_tone not in {None, email.expected_tone}:
            escalation_thread = self._build_escalation_thread(email)
            self._emails.append(escalation_thread)
            new_email_ids.append(escalation_thread.email_id)
            escalation_thread_created = True
            self._escalation_threads += 1
            email.escalation_level += 1
            notes.append("Wrong tone created an escalation thread.")

        return ActionOutcome(
            email_id=email.email_id,
            handled_correctly=handled_correctly,
            resolved=resolved,
            follow_up_created=follow_up_created,
            overdue_penalty_triggered=False,
            new_email_ids=new_email_ids,
            escalation_thread_created=escalation_thread_created,
            satisfaction_delta=email.satisfaction_delta,
            notes=notes,
        )

    def _visible_email(self, email: InboxEmail) -> InboxEmail:
        visible_deadline = email.deadline_step if email.visible_urgency else None
        return InboxEmail(
            email_id=email.email_id,
            sender=email.sender,
            sender_importance=email.sender_importance,
            subject=email.subject,
            body=email.body,
            priority=email.classified_priority or "unknown",
            urgency=email.visible_urgency,
            visible_urgency=email.visible_urgency,
            deadline_step=visible_deadline,
            hidden_intent="unknown",
            expected_action="unknown",
            expected_tone="unknown",
            thread_id=email.thread_id,
            requires_response=email.requires_response,
            resolved=email.resolved,
            classified_priority=email.classified_priority,
            classified_urgency=email.classified_urgency,
            age_steps=email.age_steps,
            angry_follow_up_generated=False,
            tags=[],
            satisfaction_delta=0,
            escalation_level=0,
        )

    def _public_history(self) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for event in self._history[-5:]:
            action = event.get("action", {})
            outcome = event.get("outcome", {})
            rows.append(
                {
                    "time_step": event.get("time_step"),
                    "email_id": action.get("email_id") if isinstance(action, dict) else None,
                    "action_type": action.get("action_type") if isinstance(action, dict) else None,
                    "reward": event.get("reward"),
                    "new_email_ids": outcome.get("new_email_ids", []) if isinstance(outcome, dict) else [],
                    "notes": outcome.get("notes", []) if isinstance(outcome, dict) else [],
                }
            )
        return rows

    def _advance_unresolved_emails(self) -> bool:
        overdue_triggered = False
        for email in self._emails:
            if email.resolved:
                continue
            email.age_steps += 1
            if email.deadline_step is not None and self._time_step >= email.deadline_step and email.priority == "high":
                overdue_triggered = True
                email.satisfaction_delta -= 2
        return overdue_triggered

    def _release_new_arrivals(self) -> List[str]:
        arriving = []
        if self._pending_arrivals and self._time_step % 2 == 0:
            next_email = self._pending_arrivals.pop(0)
            self._emails.append(next_email)
            arriving.append(next_email.email_id)
        if self.current_config and self._rng.random() < self.current_config.stochastic_arrival_rate:
            stochastic_email = self._build_stochastic_email()
            self._emails.append(stochastic_email)
            arriving.append(stochastic_email.email_id)
        return arriving

    def _build_angry_follow_up(self, email: InboxEmail) -> InboxEmail:
        return InboxEmail(
            email_id=f"{email.email_id}-followup",
            sender=email.sender,
            sender_importance=email.sender_importance,
            subject=f"Following up: {email.subject}",
            body="This is now blocking work. Please respond immediately.",
            priority="high",
            urgency=True,
            visible_urgency=True,
            deadline_step=self._time_step + 1,
            hidden_intent="angry_follow_up",
            expected_action="generate_reply" if email.expected_action != "escalate_email" else "escalate_email",
            expected_tone="professional",
            thread_id=email.thread_id,
            tags=["follow_up"],
        )

    def _build_escalation_thread(self, email: InboxEmail) -> InboxEmail:
        return InboxEmail(
            email_id=f"{email.email_id}-escalation",
            sender=f"manager+{email.sender}",
            sender_importance="boss",
            subject=f"Escalation: concern about {email.subject}",
            body="The previous response created concern. Please address this immediately.",
            priority="high",
            urgency=True,
            visible_urgency=True,
            deadline_step=self._time_step + 2,
            hidden_intent="tone_escalation",
            expected_action="escalate_email",
            expected_tone="professional",
            thread_id=f"{email.thread_id}-escalation",
            tags=["escalation"],
        )

    def _build_stochastic_email(self) -> InboxEmail:
        chaotic_templates = [
            {
                "email_id": f"random-{self._time_step}-boss",
                "sender": "ceo@company.ai",
                "sender_importance": "boss",
                "subject": "Quick check before the client call",
                "body": "Can you review this today? It may impact the conversation, but the details are buried.",
                "priority": "high",
                "urgency": True,
                "visible_urgency": False,
                "deadline_step": self._time_step + 2,
                "hidden_intent": "hidden_vip_blocker",
                "expected_action": "generate_reply",
                "expected_tone": "professional",
                "thread_id": f"stochastic-{self._time_step}-1",
                "tags": ["boss", "ambiguous", "vip"],
            },
            {
                "email_id": f"random-{self._time_step}-client",
                "sender": "client-warning@northstar.com",
                "sender_importance": "client",
                "subject": "Just flagging a possible issue",
                "body": "No panic yet, but we might need a revised answer if procurement asks.",
                "priority": "medium",
                "urgency": True,
                "visible_urgency": False,
                "deadline_step": self._time_step + 3,
                "hidden_intent": "client_risk",
                "expected_action": "classify_email",
                "expected_tone": "professional",
                "thread_id": f"stochastic-{self._time_step}-2",
                "tags": ["client", "ambiguous"],
            },
            {
                "email_id": f"random-{self._time_step}-personal",
                "sender": "family@home.net",
                "sender_importance": "friend",
                "subject": "Need help with tonight's plan",
                "body": "Not urgent unless your work runs late. Let me know when you can.",
                "priority": "low",
                "urgency": False,
                "visible_urgency": False,
                "deadline_step": None,
                "hidden_intent": "personal_conflict",
                "expected_action": "delay_email",
                "expected_tone": "friendly",
                "thread_id": f"stochastic-{self._time_step}-3",
                "tags": ["personal", "conflict"],
            },
        ]
        template = self._rng.choice(chaotic_templates)
        return InboxEmail(**template)

    def _enqueue_reward_event(
        self,
        email: InboxEmail | None,
        action: EmailAgentAction,
        outcome: ActionOutcome,
    ) -> None:
        if email is None:
            return
        self._reward_buffer.append(
            BufferedRewardEvent(
                email_id=email.email_id,
                scheduled_step=self._time_step + 2,
                action_type=action.action_type,
                expected_action=email.expected_action,
                expected_tone=email.expected_tone,
                priority=email.priority,
                deadline_step=email.deadline_step,
                caused_follow_up=outcome.follow_up_created,
                caused_escalation_thread=outcome.escalation_thread_created,
                resolved=email.resolved,
            )
        )

    def _find_email(self, email_id: str) -> InboxEmail | None:
        for email in self._emails:
            if email.email_id == email_id and not email.resolved:
                return email
        return None

    def _is_done(self) -> bool:
        if self.current_config is None:
            return True
        unresolved = any(not email.resolved for email in self._emails)
        return self._time_step >= self.current_config.max_steps or (
            not unresolved and not self._pending_arrivals and not self._reward_buffer
        )
