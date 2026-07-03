from __future__ import annotations

from .types import EmailMessage, Scenario, TriageAction


def baseline_policy(email: EmailMessage, scenario: Scenario) -> TriageAction:
    priority = "medium"
    action_type = "reply"

    combined = f"{email.subject} {email.body}".lower()
    if "urgent" in combined or email.explicit_urgency == "high" or email.vip_sender:
        priority = "high"
    elif email.explicit_urgency == "low":
        priority = "low"

    if "question" in combined:
        action_type = "reply"
    elif email.vip_sender:
        action_type = "draft"
    elif "following up" in combined:
        action_type = "defer"

    return TriageAction(
        email_id=email.email_id,
        priority=priority,
        action_type=action_type,
        extracted_deadline_hours=email.hidden_deadline_hours if email.explicit_urgency == "high" else None,
        rationale="Single-pass heuristic using explicit urgency, sender status, and keywords.",
    )


def multi_agent_policy(email: EmailMessage, scenario: Scenario) -> TriageAction:
    analyst = _inbox_analyst(email)
    memory = _memory_agent(email, scenario)
    planner = _priority_planner(email, scenario, analyst, memory)
    action_type = _response_agent(email, scenario, planner, memory)
    rationale = (
        "InboxAnalyst extracted blockers and deadline clues; "
        "MemoryAgent merged user preferences and thread context; "
        "PriorityPlanner set the triage level; "
        "ResponseAgent selected the next action."
    )
    return TriageAction(
        email_id=email.email_id,
        priority=planner["priority"],
        action_type=action_type,
        extracted_deadline_hours=analyst["deadline_hours"],
        rationale=rationale,
    )


def _inbox_analyst(email: EmailMessage) -> dict[str, object]:
    combined = f"{email.subject} {email.body}".lower()
    deadline_hours = email.hidden_deadline_hours
    mentions_blocker = (
        email.blocks_deliverable
        or "slip" in combined
        or "blocked" in combined
        or "renewal call" in combined
        or "pricing confirmation" in combined
    )
    return {
        "mentions_blocker": mentions_blocker,
        "deadline_hours": deadline_hours,
        "asks_confirmation": "confirm" in combined or "confirmation" in combined,
    }


def _memory_agent(email: EmailMessage, scenario: Scenario) -> dict[str, object]:
    thread_context = scenario.thread_history.get(email.thread_id, "")
    is_vip = email.sender in scenario.user_profile.vip_senders or email.vip_sender
    return {
        "thread_context": thread_context.lower(),
        "is_vip": is_vip,
        "clarify_before_escalation": scenario.user_profile.prefers_clarify_before_escalation,
    }


def _priority_planner(
    email: EmailMessage,
    scenario: Scenario,
    analyst: dict[str, object],
    memory: dict[str, object],
) -> dict[str, str]:
    combined = f"{email.subject} {email.body}".lower()
    thread_context = str(memory["thread_context"])

    if "following up" in combined and "not business critical" in thread_context:
        return {"priority": "low"}
    if email.blocks_deliverable or analyst["mentions_blocker"]:
        return {"priority": "high"}
    if "no rush" in combined:
        return {"priority": "medium" if memory["is_vip"] else "low"}
    if analyst["deadline_hours"] is not None and analyst["deadline_hours"] <= scenario.user_profile.same_day_threshold_hours:
        return {"priority": "medium" if not memory["is_vip"] else "high"}
    if memory["is_vip"]:
        return {"priority": "medium"}
    return {"priority": "low" if email.explicit_urgency == "low" else "medium"}


def _response_agent(
    email: EmailMessage,
    scenario: Scenario,
    planner: dict[str, str],
    memory: dict[str, object],
) -> str:
    combined = f"{email.subject} {email.body}".lower()
    if planner["priority"] == "high" and ("milestone" in combined or "commit" in combined):
        return "escalate"
    if "renewal call" in combined or "pricing confirmation" in combined:
        return "escalate"
    if "no rush" in combined and planner["priority"] != "high":
        return "draft"
    if "following up" in combined and planner["priority"] == "low":
        return "defer"
    if "question" in combined or "confirm" in combined:
        return "reply"
    if memory["clarify_before_escalation"]:
        return "reply"
    return "draft"
