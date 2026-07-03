from __future__ import annotations

from .types import ActionOutcome, BufferedRewardEvent, EmailAgentAction, InboxEmail


def compute_reward(
    email: InboxEmail | None,
    action: EmailAgentAction,
    outcome: ActionOutcome,
    time_step: int = 0,
) -> tuple[float, dict[str, float]]:
    reward = 0.0
    metrics = {
        "priority_correctness": 0.0,
        "response_quality": 0.0,
        "critical_handled": 0.0,
        "tone_match": 0.0,
        "ignored_critical": 0.0,
        "urgent_delay": 0.0,
        "unnecessary_escalation": 0.0,
        "efficient_batching": 0.0,
        "follow_up_penalty": 0.0,
        "deadline_penalty": 0.0,
        "efficiency_bonus": 0.0,
        "empty_inbox_wait": 0.0,
    }

    if email is None:
        if action.email_id == "none":
            metrics["empty_inbox_wait"] = 1.0
            return reward, metrics
        reward -= 8.0
        metrics["ignored_critical"] = 1.0
        return reward, metrics

    if action.predicted_priority == email.priority:
        reward += 3.0
        metrics["priority_correctness"] = 1.0
    elif action.predicted_priority is not None:
        reward -= 2.0

    if email.priority == "high" and action.action_type in {"generate_reply", "escalate_email"}:
        reward += 4.0
        metrics["critical_handled"] = 1.0
    elif email.priority == "high" and action.action_type == "ignore_email":
        reward -= 6.0
        metrics["ignored_critical"] = 1.0

    if action.action_type == "generate_reply":
        if action.reply_tone == email.expected_tone:
            reward += 3.0
            metrics["tone_match"] = 1.0
            metrics["response_quality"] = 1.0
        elif action.reply_tone:
            reward += 1.0

    if action.action_type == "delay_email" and email.urgency:
        reward -= 4.0
        metrics["urgent_delay"] = 1.0

    if action.action_type == "escalate_email" and email.expected_action != "escalate_email":
        reward -= 3.0
        metrics["unnecessary_escalation"] = 1.0

    if action.action_type == "classify_email":
        if email.priority == "high" or email.urgency:
            reward -= 4.0
            metrics["urgent_delay"] = 1.0
        elif action.predicted_priority == email.priority:
            reward += 2.0
            metrics["efficient_batching"] = 1.0
            metrics["efficiency_bonus"] = 1.0
        else:
            reward -= 1.0

    if outcome.follow_up_created:
        reward -= 4.0
        metrics["follow_up_penalty"] = 1.0

    if outcome.overdue_penalty_triggered:
        reward -= 6.0
        metrics["deadline_penalty"] = 1.0

    if action.action_type == "delay_email" and email.deadline_step is not None and email.deadline_step <= time_step + 2:
        reward -= 4.0
        metrics["urgent_delay"] = 1.0

    if outcome.handled_correctly:
        reward += 2.0

    return reward, metrics


def delayed_reward_calculation(
    current_step: int,
    reward_buffer: list[BufferedRewardEvent],
    emails: list[InboxEmail],
) -> tuple[float, dict[str, float], list[dict[str, object]]]:
    reward = 0.0
    metrics = {
        "delayed_success": 0.0,
        "delayed_escalation_penalty": 0.0,
        "delayed_deadline_penalty": 0.0,
        "delayed_satisfaction_bonus": 0.0,
    }
    resolved_events: list[dict[str, object]] = []
    remaining: list[BufferedRewardEvent] = []

    email_lookup = {email.email_id: email for email in emails}

    for event in reward_buffer:
        if current_step < event.scheduled_step:
            remaining.append(event)
            continue

        email = email_lookup.get(event.email_id)
        if email is None:
            resolved_events.append({"email_id": event.email_id, "status": "email_missing"})
            continue

        event_reward = 0.0
        if event.action_type == event.expected_action and not event.caused_follow_up and not event.caused_escalation_thread:
            event_reward += 10.0
            metrics["delayed_success"] += 1.0
        if event.caused_escalation_thread:
            event_reward -= 15.0
            metrics["delayed_escalation_penalty"] += 1.0
        if event.deadline_step is not None and current_step >= event.deadline_step and not email.resolved:
            event_reward -= 10.0
            metrics["delayed_deadline_penalty"] += 1.0
        if email.satisfaction_delta > 0:
            event_reward += min(email.satisfaction_delta, 4)
            metrics["delayed_satisfaction_bonus"] += 1.0

        reward += event_reward
        resolved_events.append(
            {
                "email_id": event.email_id,
                "scheduled_step": event.scheduled_step,
                "reward": event_reward,
                "caused_follow_up": event.caused_follow_up,
                "caused_escalation_thread": event.caused_escalation_thread,
            }
        )

    reward_buffer[:] = remaining
    return reward, metrics, resolved_events
