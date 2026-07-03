---
title: InboxWorld
emoji: 📬
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "5.0.0"
app_file: app.py
python_version: "3.10"
pinned: false
---

# InboxWorld: Teaching LLMs to Survive Corporate Triage

InboxWorld keeps our Round 1 problem statement, **email triage**, and turns it into an OpenEnv-compatible training environment for long-horizon, context-aware agents.

Most email triage demos stop at classification. InboxWorld instead models the inbox as a partially observable world where decisions have consequences: missed deadlines, angry follow-ups, escalation threads, and user satisfaction changes.

## Environment

The environment simulates a busy professional inbox with:

- a ticking `time_step`
- visible and hidden urgency
- stochastic email arrivals
- delayed reward events
- follow-up and escalation generation
- user profile and sender-importance context

Hidden evaluator labels such as true priority, expected action, expected tone, and hidden intent are not exposed to the policy. The agent only sees public inbox state.

## Action Space

The policy returns a structured `EmailAgentAction`:

- `classify_email`
- `generate_reply`
- `delay_email`
- `escalate_email`
- `ignore_email`

Each action can include predicted priority, predicted urgency, reply tone, response text, and metadata.

## Multi-Agent Policy

The local policy uses four cooperating roles:

1. `Inbox Analyst`: extracts visible intent and urgency cues.
2. `Priority Planner`: combines sender importance, deadlines, and semantic signals.
3. `Responder Agent`: chooses the structured action and tone.
4. `Supervisor Agent`: checks visible safety constraints before submission.

## Simulation Results

The adaptive simulation compares a greedy visible-input baseline against the multi-agent policy.

| Policy | Avg Reward | Success Rate | Error Rate | Missed Deadlines |
| --- | ---: | ---: | ---: | ---: |
| Baseline | -117.5 | 0.00 | 1.00 | 60 |
| Multi-agent | +102.0 | 0.94 | 0.00 | 0 |

Generated artifacts live under `artifacts/adaptive_environment/`.

## Training Evidence

The project includes a minimal Hugging Face TRL training scaffold and Colab proof artifacts:

- `artifacts/training/transition_buffer.json`
- `artifacts/training/loss_curve_colab.png`
- `artifacts/training/TRAINING_EVIDENCE.md`

The live demo uses hosted LLM inference for natural responses, while the training scaffold shows how InboxWorld transitions can be used to fine-tune a small model.

## Local Setup

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Optional Hugging Face token for serverless LLM inference:

```powershell
$env:HF_TOKEN="your_hf_token_here"
$env:HF_MODEL="Qwen/Qwen2.5-7B-Instruct"
```

Run the Gradio demo:

```powershell
python app.py
```

Run the adaptive simulation:

```powershell
python scripts/run_adaptive_environment.py
```

Collect training transitions:

```powershell
python scripts/rl_training_stub.py
```

Run the minimal TRL scaffold in Colab or a GPU runtime:

```powershell
python scripts/minimal_trl_train.py
```

## Repository Structure

- `src/inboxworld/environment.py`: OpenEnv-compatible environment and transition dynamics.
- `src/inboxworld/reward_calculator.py`: immediate and delayed reward logic.
- `src/inboxworld/agents.py`: multi-agent policy implementation.
- `src/inboxworld/simulator.py`: baseline, random, and multi-agent evaluation runners.
- `src/inboxworld/training.py`: prompt/action/reward transition collection.
- `scripts/run_adaptive_environment.py`: judge-facing simulation artifact generator.
- `scripts/minimal_trl_train.py`: minimal Hugging Face TRL training scaffold.
- `app.py`: Gradio demo with optional Hugging Face inference.
