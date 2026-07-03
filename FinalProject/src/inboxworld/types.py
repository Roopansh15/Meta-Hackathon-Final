from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class EmailMessage:
    email_id: str
    sender: str
    sender_role: str
    subject: str
    body: str
    thread_id: str
    explicit_urgency: str
    hidden_priority: str
    hidden_action: str
    hidden_deadline_hours: Optional[int]
    blocks_deliverable: bool
    vip_sender: bool


@dataclass(frozen=True)
class UserProfile:
    role: str
    prefers_clarify_before_escalation: bool
    vip_senders: List[str] = field(default_factory=list)
    same_day_threshold_hours: int = 24


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    description: str
    user_profile: UserProfile
    emails: List[EmailMessage]
    thread_history: Dict[str, str]
    pending_tasks: List[str]
    expected_outcomes: Dict[str, Dict[str, object]]
    drift_notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TriageAction:
    email_id: str
    priority: str
    action_type: str
    extracted_deadline_hours: Optional[int]
    rationale: str


@dataclass
class StepResult:
    reward: float
    done: bool
    info: Dict[str, object]


@dataclass
class InboxEmail:
    email_id: str
    sender: str
    sender_importance: str
    subject: str
    body: str
    priority: str
    urgency: bool
    visible_urgency: bool
    deadline_step: Optional[int]
    hidden_intent: str
    expected_action: str
    expected_tone: str
    thread_id: str
    requires_response: bool = True
    resolved: bool = False
    classified_priority: Optional[str] = None
    classified_urgency: Optional[bool] = None
    age_steps: int = 0
    angry_follow_up_generated: bool = False
    tags: List[str] = field(default_factory=list)
    satisfaction_delta: int = 0
    escalation_level: int = 0


@dataclass(frozen=True)
class EmailEnvConfig:
    config_id: str
    description: str
    user_profile: UserProfile
    initial_emails: List[InboxEmail]
    arrivals: List[InboxEmail] = field(default_factory=list)
    max_steps: int = 8
    stochastic_arrival_rate: float = 0.35
    time_budget_per_step: int = 1
    random_seed: int = 7


@dataclass(frozen=True)
class EmailAgentAction:
    email_id: str
    action_type: str
    predicted_priority: Optional[str] = None
    predicted_urgency: Optional[bool] = None
    reply_tone: Optional[str] = None
    response_text: str = ""
    delay_steps: int = 1
    escalate_target: str = "manager"
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class ActionOutcome:
    email_id: str
    handled_correctly: bool
    resolved: bool
    follow_up_created: bool
    overdue_penalty_triggered: bool
    new_email_ids: List[str]
    escalation_thread_created: bool = False
    satisfaction_delta: int = 0
    notes: List[str] = field(default_factory=list)


@dataclass
class BufferedRewardEvent:
    email_id: str
    scheduled_step: int
    action_type: str
    expected_action: str
    expected_tone: str
    priority: str
    deadline_step: Optional[int]
    caused_follow_up: bool = False
    caused_escalation_thread: bool = False
    resolved: bool = False
