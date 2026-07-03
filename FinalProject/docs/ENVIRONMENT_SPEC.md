# InboxWorld Environment Spec

## Problem statement

InboxWorld keeps the Round 1 problem statement, `email triage`, but models it as an interactive training environment instead of a static classifier benchmark.

## Observation space

Each step exposes:

- current email metadata and body
- partial thread history
- user profile and preferences
- pending tasks
- scenario description
- previous public action feedback and reward

Hidden evaluator labels such as true priority, expected action, expected tone, and hidden intent are not exposed in agent observations.

## Action space

The acting policy returns:

- `email_id`: target email
- `action_type`: `classify_email`, `generate_reply`, `delay_email`, `escalate_email`, or `ignore_email`
- `predicted_priority`: `low`, `medium`, `high`, or `None`
- `predicted_urgency`: boolean or `None`
- `reply_tone`: `professional`, `friendly`, `helpful`, `urgent`, `neutral`, or `None`
- `response_text`: generated draft or internal note

## Transition logic

- The environment maintains a mutable inbox across time steps.
- Every action advances the clock.
- New scheduled and stochastic emails can arrive after each action.
- Wrong handling can spawn angry follow-ups or escalation threads.
- Delayed reward events are buffered and resolved after future state changes.

## Reward model

Immediate components:

- positive reward for matching hidden priority and selecting an appropriate action
- positive reward for handling critical emails before deadlines
- positive reward for matching the expected reply tone
- penalty for unknown targets, missed critical emails, urgent delays, and unnecessary escalations

Delayed components:

- bonus when a previously scheduled action resolves cleanly
- penalty when a bad tone creates an escalation thread
- penalty when an unresolved critical email crosses its deadline
- satisfaction bonus for accepted replies and correct escalations

## Metrics to surface in the demo

- cumulative reward
- success rate
- error rate
- missed deadlines
- escalation threads
- reward history across baseline and multi-agent policies

## Round 2 theme mapping

- Primary: `Theme 3 - World Modeling`
- Secondary: `Theme 1 - Multi-Agent Interactions`
- Secondary: `Theme 2 - Long-Horizon Planning`

## Immediate next upgrades

1. Add mutable inbox state across multiple turns.
2. Add reply-quality scoring based on simulated user edits.
3. Add schema drift for sender importance and policy changes.
4. Replace heuristic policies with trainable model-backed policies.
