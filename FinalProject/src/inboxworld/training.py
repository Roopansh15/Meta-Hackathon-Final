from __future__ import annotations

from dataclasses import asdict

from .agents import MultiAgentEmailPolicy
from .environment import EmailEnvironment


def state_to_prompt(state: dict) -> str:
    visible_emails = [
        {
            "email_id": email.email_id,
            "sender": email.sender,
            "sender_importance": email.sender_importance,
            "visible_urgency": email.visible_urgency,
            "known_deadline_step": email.deadline_step,
            "subject": email.subject,
            "body": email.body,
            "requires_response": email.requires_response,
            "age_steps": email.age_steps,
        }
        for email in state.get("emails", [])
    ]
    return (
        "You are acting inside the Adaptive Multi-Agent Email Decision Environment.\n"
        f"Config: {state.get('config_id')}\n"
        f"Time step: {state.get('time_step')}\n"
        f"Visible emails: {visible_emails}\n"
        "Return a structured email action with email_id, action_type, predicted_priority, "
        "predicted_urgency, and reply_tone."
    )


def collect_episode_transitions(env: EmailEnvironment, episodes: int = 3) -> list[dict]:
    policy = MultiAgentEmailPolicy()
    transitions = []

    for episode_index in range(episodes):
        state = env.reset()
        done = False
        while not done:
            prompt = state_to_prompt(state)
            action = policy.act(state)
            result = env.step(action)
            transitions.append(
                {
                    "episode": episode_index,
                    "prompt": prompt,
                    "action": asdict(action),
                    "reward": result.reward,
                    "done": result.done,
                    "info": result.info,
                }
            )
            done = result.done
            if not done:
                state = env.get_state()

    return transitions
