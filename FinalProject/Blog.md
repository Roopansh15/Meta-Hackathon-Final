# InboxWorld: Teaching LLMs to Survive Corporate Triage

Are we really still building assistants that only summarize text?

InboxWorld targets a practical capability gap: email triage is a long-horizon decision problem. A message can look harmless but block a client deck, renewal, legal signature, or board update several steps later.

## Phase 1: The Environment

InboxWorld keeps our Round 1 email triage problem statement and turns it into an OpenEnv-compatible inbox environment.

The environment includes:

1. A ticking clock: every action advances `time_step`.
2. Delayed consequences: bad actions can spawn angry follow-ups, escalation threads, or missed-deadline penalties.
3. Partial observability: hidden evaluator labels are not visible to the agent.
4. Schema drift: priorities shift with new VIP contacts, revenue-risk policies, and changing escalation rules.
5. Stochastic arrivals: new emails can arrive while the agent is handling older work.

## Phase 2: The Multi-Agent Policy

The local policy uses four cooperating roles:

1. Inbox Analyst: extracts visible urgency and semantic cues.
2. Priority Planner: combines sender importance, deadlines, and message content.
3. Responder Agent: chooses the structured action and tone.
4. Supervisor Agent: checks visible safety constraints before the action is submitted.

This is designed as an agent environment and evaluation loop, not just a chatbot wrapper.

## Phase 3: The Training Scaffold

We include a minimal Hugging Face TRL scaffold using `Qwen/Qwen1.5-0.5B`, plus a transition collector that exports prompt, action, reward records from InboxWorld.

That gives us a clear onsite path: scale the examples, train with the provided compute, and use the reward curves to show improvement.

## Phase 4: Live Inference

The Gradio UI can use Hugging Face `InferenceClient` with the model configured through `HF_MODEL`, defaulting to `Qwen/Qwen2.5-7B-Instruct`. If no token is configured, it falls back to the local multi-agent policy.

## Observable Improvement

The adaptive simulation compares a greedy visible-input baseline against the multi-agent policy:

- Baseline average reward: -117.5
- Multi-agent average reward: +102.0
- Baseline missed deadlines: 60
- Multi-agent missed deadlines: 0

The important claim is not that email is solved. The claim is that InboxWorld makes email triage trainable as a long-horizon, partially observable task with measurable operational consequences.
