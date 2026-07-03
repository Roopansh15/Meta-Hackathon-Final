from __future__ import annotations

from dataclasses import replace

from .types import EmailAgentAction, InboxEmail


EMERGENCY_KEYWORDS = [
    "heart attack",
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "stroke",
    "bleeding",
    "unconscious",
    "medical emergency",
    "emergency",
    "hospital",
    "ambulance",
    "call 911",
]


class ClassifierAgent:
    def classify(self, email: InboxEmail) -> dict[str, object]:
        combined = f"{email.subject} {email.body}".lower()
        has_emergency_signal = any(keyword in combined for keyword in EMERGENCY_KEYWORDS)

        low_signal = any(
            phrase in combined
            for phrase in [
                "no action needed",
                "not urgent",
                "no pressure",
                "dinner",
                "seat update",
                "next month",
                "review this later",
                "unless your work runs late",
            ]
        )
        critical_signal = any(
            phrase in combined
            for phrase in [
                "blocking",
                "blocked",
                "blocker",
                "client deck",
                "milestone",
                "renewal",
                "revenue",
                "contract",
                "signature",
                "board",
                "pricing",
                "approval",
                "before 4 pm",
                "before 5 pm",
                "today",
                "tonight",
                "tomorrow morning",
            ]
        )

        predicted_priority = "medium"
        if low_signal and email.sender_importance not in {"boss", "client"}:
            predicted_priority = "low"
        if email.sender_importance in {"boss", "client"} or email.visible_urgency or critical_signal:
            predicted_priority = "high"
        if email.sender_importance == "friend" and low_signal and not has_emergency_signal:
            predicted_priority = "low"
        if has_emergency_signal:
            predicted_priority = "high"
            if "emergency" not in email.tags:
                email.tags.append("emergency")
        predicted_urgency = (
            False
            if "not urgent" in combined
            else email.visible_urgency
            or has_emergency_signal
            or any(
            w in combined for w in ["today", "tonight", "immediately", "right now", "urgent", "asap", "before 4 pm", "before 5 pm"]
            )
        )
        
        if "design" in email.sender.lower() or "hero image" in combined or "client deck" in combined:
            email.tags.append("design")

        if any(phrase in combined for phrase in ["fuzzy", "possible issue", "no panic", "may affect", "details are still"]):
            email.tags.append("ambiguous")

        for keyword in ["milestone", "renewal", "revenue", "design", "contract", "board"]:
            if keyword in combined and keyword not in email.tags:
                email.tags.append(keyword)
                
        if any(tag in ["milestone", "renewal", "revenue", "contract", "board"] for tag in email.tags):
            predicted_priority = "high"
        if email.sender_importance == "friend" and low_signal and not has_emergency_signal:
            predicted_priority = "low"
            predicted_urgency = False
                
        return {
            "email_id": email.email_id,
            "predicted_priority": predicted_priority,
            "predicted_urgency": predicted_urgency,
            "features": {
                "sender_importance": email.sender_importance,
                 "tags": email.tags,
            },
        }


class PriorityAgent:
    def prioritize(self, email: InboxEmail, classification: dict[str, object]) -> dict[str, object]:
        predicted_priority = classification["predicted_priority"]
        if email.deadline_step is not None and email.deadline_step <= 2:
            predicted_priority = "high"
        if "ambiguous" in email.tags and email.sender_importance in {"boss", "client"}:
            predicted_priority = "medium"
        if bool(classification["predicted_urgency"]) and email.sender_importance in {"boss", "client"}:
            predicted_priority = "high"
        if email.sender_importance == "friend" and not bool(classification["predicted_urgency"]) and "emergency" not in email.tags:
            predicted_priority = "low"
        return {
            "email_id": email.email_id,
            "predicted_priority": predicted_priority,
            "predicted_urgency": classification["predicted_urgency"],
        }


class ResponderAgent:
    def decide(self, email: InboxEmail, priority_decision: dict[str, object]) -> EmailAgentAction:
        predicted_priority = str(priority_decision["predicted_priority"])
        predicted_urgency = bool(priority_decision["predicted_urgency"])

        if "emergency" in email.tags:
            action_type = "escalate_email"
            tone = "urgent"
        elif "ambiguous" in email.tags and predicted_priority == "medium":
            action_type = "classify_email"
            tone = "neutral"
        elif predicted_priority == "high" and (
            "milestone" in email.tags or "renewal" in email.tags or "revenue" in email.tags
        ):
            action_type = "escalate_email"
            tone = "professional"
        elif predicted_priority == "high":
            action_type = "generate_reply"
            tone = "helpful" if "design" in email.tags else "professional"
        elif predicted_priority == "medium" and email.requires_response:
            action_type = "generate_reply"
            tone = "professional" if email.sender_importance in {"boss", "client"} else "friendly"
        elif predicted_priority == "low" and not email.requires_response:
            action_type = "ignore_email"
            tone = "neutral"
        elif predicted_priority == "low":
            action_type = "delay_email"
            tone = "friendly"
        else:
            action_type = "classify_email"
            tone = "neutral"

        if "emergency" in email.tags:
            response_text = f"URGENT: {email.sender}, this sounds like a medical emergency. Please contact local emergency services immediately and alert someone nearby who can help right now."
        elif action_type == "escalate_email":
            response_text = f"Forwarding to management: The email from {email.sender} requires immediate escalation to avoid negative downstream consequences. Please review."
        elif action_type == "generate_reply" and tone == "helpful":
            response_text = f"Hi {email.sender}, I am looking into this right now! Let me gather the necessary details and get back to you shortly."
        elif action_type == "generate_reply" and tone == "professional":
            response_text = f"Hello {email.sender}, thank you for reaching out. We are actively reviewing this matter and will provide a formal update soon."
        elif action_type == "generate_reply" and tone == "friendly":
            response_text = f"Hey {email.sender}, got your message! I'll check on this and follow up with you later today."
        elif action_type == "delay_email":
            response_text = f"[Internal Note] Low priority. Delayed processing for {email.sender}. No immediate response required."
        else:
            response_text = f"[Internal Note] Archived email from {email.sender}. No action needed."

        return EmailAgentAction(
            email_id=email.email_id,
            action_type=action_type,
            predicted_priority=predicted_priority,
            predicted_urgency=predicted_urgency,
            reply_tone=tone,
            response_text=response_text,
            escalate_target="emergency_contact" if "emergency" in email.tags else "manager",
            metadata={
                "decision_trace": {
                    "email_id": email.email_id,
                    "sender_importance": email.sender_importance,
                    "visible_urgency": email.visible_urgency,
                    "known_deadline_step": email.deadline_step,
                    "requires_response": email.requires_response,
                    "age_steps": email.age_steps,
                    "derived_tags": list(email.tags),
                }
            },
        )


class SupervisorAgent:
    def review(self, email: InboxEmail, proposed_action: EmailAgentAction) -> EmailAgentAction:
        if proposed_action.action_type == "classify_email" and (
            proposed_action.predicted_priority == "high" or email.visible_urgency
        ):
            return replace(proposed_action, action_type="generate_reply", reply_tone="professional")
        if "emergency" in email.tags:
            return replace(
                proposed_action,
                action_type="escalate_email",
                predicted_priority="high",
                predicted_urgency=True,
                reply_tone="urgent",
                escalate_target="emergency_contact",
            )
        if not email.requires_response and proposed_action.predicted_priority == "low":
            return replace(proposed_action, action_type="ignore_email", reply_tone="neutral")
        if "design" in email.tags and proposed_action.action_type != "generate_reply":
            return replace(proposed_action, action_type="generate_reply", reply_tone="helpful")
        if "contract" in email.tags and proposed_action.action_type != "generate_reply":
            return replace(proposed_action, action_type="generate_reply", reply_tone="professional")
        if "milestone" in email.tags or "renewal" in email.tags:
            return replace(proposed_action, action_type="escalate_email", reply_tone="professional")
        if email.sender_importance == "boss" and proposed_action.action_type == "delay_email":
            return replace(proposed_action, action_type="generate_reply", reply_tone="professional")
        return proposed_action


class MultiAgentEmailPolicy:
    def __init__(self) -> None:
        self.classifier = ClassifierAgent()
        self.priority_agent = PriorityAgent()
        self.responder = ResponderAgent()
        self.supervisor = SupervisorAgent()

    def act(self, state: dict) -> EmailAgentAction:
        emails = state.get("emails", [])
        if not emails:
            return EmailAgentAction(email_id="none", action_type="ignore_email")

        target = self._select_target(emails)
        classification = self.classifier.classify(target)
        priority_decision = self.priority_agent.prioritize(target, classification)
        proposed_action = self.responder.decide(target, priority_decision)
        return self.supervisor.review(target, proposed_action)

    def _select_target(self, emails: list[InboxEmail]) -> InboxEmail:
        return sorted(
            emails,
            key=lambda email: (
                self._surface_priority_rank(email),
                self._surface_deadline_rank(email),
                0 if email.sender_importance == "boss" else 1 if email.sender_importance == "client" else 2,
                -email.age_steps,
            ),
        )[0]

    def _surface_priority_rank(self, email: InboxEmail) -> int:
        combined = f"{email.subject} {email.body}".lower()
        low_signal = any(
            phrase in combined
            for phrase in [
                "no action needed",
                "not urgent",
                "no pressure",
                "dinner",
                "seat update",
                "next month",
                "review this later",
                "unless your work runs late",
            ]
        )
        critical_signal = any(
            phrase in combined
            for phrase in [
                "blocking",
                "blocked",
                "client deck",
                "milestone",
                "renewal",
                "revenue",
                "contract",
                "signature",
                "board",
                "pricing",
                "approval",
                "today",
                "tonight",
                "tomorrow morning",
            ]
        )
        if email.visible_urgency or has_deadline_soon(email) or critical_signal:
            return 0
        if email.sender_importance == "friend" and low_signal:
            return 2
        if email.sender_importance in {"boss", "client"} and not low_signal:
            return 1
        return 2 if low_signal else 1

    def _surface_deadline_rank(self, email: InboxEmail) -> int:
        combined = f"{email.subject} {email.body}".lower()
        visible_deadline = email.deadline_step if email.deadline_step is not None else 999
        if any(phrase in combined for phrase in ["client deck", "hero image", "export"]):
            return min(visible_deadline, 1)
        if any(phrase in combined for phrase in ["tomorrow morning", "tomorrow's"]):
            return min(visible_deadline, 1)
        if any(phrase in combined for phrase in ["before 4 pm", "before 5 pm", "today", "tonight"]):
            return min(visible_deadline, 2)
        return visible_deadline


def has_deadline_soon(email: InboxEmail) -> bool:
    return email.deadline_step is not None and email.deadline_step <= 2
