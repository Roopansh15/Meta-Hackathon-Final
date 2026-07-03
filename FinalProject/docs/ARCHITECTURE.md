# InboxWorld Architecture

This document outlines the high-level architecture of the `InboxWorld` multi-agent email triage system and the environment's delayed reward mechanism.

## Multi-Agent Decision Pipeline

The core policy replaces a single monolithic LLM call with a role-based multi-agent architecture. This flow ensures safe and calculated handling of ambiguous or high-priority emails.

```mermaid
graph TD
    A[Incoming Email/Environment State] --> B[Classifier Agent]
    B -->|Extracts intent & surface priority| C[Priority Agent]
    C -->|Evaluates deadlines & hidden urgency| D[Responder Agent]
    D -->|Proposes Action & Tone| E[Supervisor Agent]
    E -->|Reviews for safety & constraints| F[Final Email Action]
```

## Environment Delayed Reward System

To simulate real-world consequences, `InboxWorld` uses a buffered reward mechanism instead of shallow, immediate textual grading. Actions have ripple effects.

```mermaid
stateDiagram-v2
    [*] --> ActionTaken
    ActionTaken --> RewardBuffer: Action is stored temporarily
    RewardBuffer --> StepPasses: 2-3 environment steps pass
    
    StepPasses --> CheckFutureState
    CheckFutureState --> PositiveReward: Resolved correctly, no escalations
    CheckFutureState --> NegativeReward: Missed deadline, angry follow-up, or bad tone escalation
```
