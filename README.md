# InboxWorld: Teaching LLMs to Survive Corporate Triage

[![OpenEnv Compliant](https://img.shields.io/badge/OpenEnv-Compliant-brightgreen.svg)](https://openenv.ai/)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/RoopanshSaxena/InboxWorld)

---

## The Story: Why We Built InboxWorld

### 1. The Problem (Why it matters)
We are all drowning in emails. But more importantly, the AI industry is currently obsessed with building simple "Chatbots" that only grade immediate text output. **InboxWorld** targets a critical capability gap: **Long-Horizon Planning in Corporate Triage.** An AI needs to know that delaying an email from the CEO today will cause a catastrophic escalation tomorrow. This is an underexplored domain in RL: teaching an AI to survive a high-stakes, time-sensitive environment.

### 2. The Environment (What the agent sees and does)
Instead of a boring grid-world, we built a chaotic inbox physics engine strictly following the OpenEnv standard. 
* **The Ticking Clock:** Every action advances the `time_step`. You cannot stall.
* **The Action Space:** The agent chooses from a structured `EmailAgentAction` space (Delay, Escalate, Reply, Ignore) rather than just writing free-form text.
* **The Delayed Reward Buffer:** The agent gets immediate lightweight points (+5) for matching the correct tone, but faces massive **Delayed Penalties (-10)** 3 turns later if it misses a deadline or angers a VIP. 

### 3. The Architecture (How it survives)
To beat this environment, we replaced the monolithic prompt with a **Four-Role Multi-Agent System**:
1.  **Inbox Analyst:** Extracts intent using keywords.
2.  **Priority Planner:** Re-evaluates urgency based on context.
3.  **Responder Agent:** Chooses the action.
4.  **Supervisor Agent:** Acts as an intermediate step-level verifier. It intercepts dangerous logic (e.g., overriding an attempt to ignore the CEO) to prevent reward-hacking.

---

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
