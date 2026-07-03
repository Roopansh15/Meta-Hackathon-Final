---
title: "InboxWorld: Teaching LLMs to Survive Corporate Triage"
emoji: "mailbox"
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.0.0
app_file: app.py
pinned: false
---

# InboxWorld: Teaching LLMs to Survive Corporate Triage

Email triage is not just classification. In a real inbox, a message can sound casual but still block a deadline, affect a customer renewal, or create an escalation several steps later.

InboxWorld keeps our Round 1 problem statement, email triage, and turns it into an OpenEnv-compatible training environment for context-aware agents.

## The Environment

InboxWorld simulates a busy professional inbox with:

1. A ticking clock: every action advances the environment.
2. Delayed consequences: wrong actions can spawn angry follow-ups, missed-deadline penalties, or escalation threads.
3. Partial observability: hidden evaluator labels are not visible to the agent.
4. Stochastic arrivals: new emails can appear while the agent is still handling older work.

The agent sees only public inbox state: sender, sender importance, visible urgency, subject, body, known deadlines, profile context, and recent public feedback.

## The Multi-Agent Policy

The local policy uses four cooperating roles:

1. Inbox Analyst: extracts surface intent and urgency signals.
2. Priority Planner: combines sender importance, deadlines, and message semantics.
3. Responder Agent: chooses the structured action and tone.
4. Supervisor Agent: checks visible safety constraints before the action is submitted.

This is intentionally designed as an environment and evaluation loop, not just a chatbot wrapper.

## Reward Design

The reward model gives immediate credit for correct priority, critical handling, and tone match. It also applies delayed rewards or penalties when future state reveals whether the decision was actually safe.

Examples:

- Missing a high-priority blocker can create a follow-up email.
- A wrong tone can create an escalation thread.
- Leaving a critical email unresolved past its deadline triggers delayed penalties.

## Training Scaffold

We include a minimal Hugging Face TRL script using `Qwen/Qwen1.5-0.5B` and a transition collector that exports prompt, action, reward records from the environment. This satisfies the required training-pipeline scaffold and gives us a clear onsite path for scaling with the provided compute.

## Observable Improvement

The adaptive simulation compares a greedy visible-input baseline against the multi-agent policy:

- Baseline average reward: -117.5
- Multi-agent average reward: +102.0
- Baseline missed deadlines: 60
- Multi-agent missed deadlines: 0

The important claim is not that email is solved. The claim is that InboxWorld makes email triage trainable as a long-horizon, partially observable agent task with measurable operational consequences.
