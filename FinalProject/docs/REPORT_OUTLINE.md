# Final Year Project Report Outline: InboxWorld

**Proposed Title:** InboxWorld: Teaching Large Language Models Long-Horizon Planning in Corporate Triage via Multi-Agent Verification

## Chapter 1: Introduction
- **1.1 Background:** The rise of LLMs in natural language processing and the limitation of current systems to purely static, immediate-reward classification tasks.
- **1.2 Problem Statement:** Corporate email triage requires systemic authority recognition and long-horizon planning. Existing simple "chatbot" heuristics fail when actions have delayed consequences (e.g., delaying the CEO causes an escalation 3 days later).
- **1.3 Objectives:**
  - To develop a time-constrained physics engine representing an inbox (InboxWorld).
  - To implement a Multi-Agent architecture capable of semantic intent extraction and rigid action selection.
  - To demonstrate measurable improvement over greedy baseline heuristics.

## Chapter 2: Literature Review
- **2.1 LLMs in Task Automation:** Reviewing current paradigms (e.g., LangChain, AutoGPT) and their struggle with long-term memory and delayed consequences.
- **2.2 Reinforcement Learning with Verifiable Rewards (RLVR):** Discussing how RL is shifting from simple reward signals (like game scores) to complex, verifiable operational constraints.
- **2.3 Multi-Agent Systems:** Analyzing how distinct agent roles (Planner, Verifier, Responder) prevent reward hacking and hallucinations in LLMs.

## Chapter 3: Methodology & Environment Design
- **3.1 OpenEnv Standard Implementation:** Detailed breakdown of `src/inboxworld/environment.py`. Explain the transition dynamics and the `time_step` mechanics.
- **3.2 The Reward Matrix:** Explain `src/inboxworld/reward_calculator.py`. Detail the mathematical difference between immediate tone rewards (+5) and massive delayed penalties (-10) for missing deadlines.
- **3.3 The Agent Architecture:**
  - **Inbox Analyst:** Semantic extraction.
  - **Priority Planner:** Contextual schema drift adaptation.
  - **Responder & Supervisor:** The dual-actor system for action execution and safety verification.

## Chapter 4: Implementation
- **4.1 Production Inference Pipeline:** How `llm_inference.py` connects the local UI to a 7B-parameter serverless LLM API.
- **4.2 The User Interface:** Building an interactive visualization using Gradio to demonstrate the multi-agent decision steps in real-time.
- **4.3 Technology Stack:** Python, Hugging Face `transformers` & `TRL`, Gradio, OpenEnv.

## Chapter 5: Results & Evaluation
- **5.1 Baseline Evaluation:** Analyzing the failure of the greedy heuristic (-117.5 average reward, 60 missed deadlines).
- **5.2 Multi-Agent Policy Evaluation:** Demonstrating the success of the multi-agent system (+102.0 average reward, 0 missed deadlines).
- **5.3 Case Studies:** Break down specific email scenarios such as the hidden client-deck blocker, revenue-risk escalation, legal-signature deadline, and low-value personal/travel noise.

## Chapter 6: Conclusion & Future Work
- **6.1 Conclusion:** Summarize how enriching the environment with delayed consequences leads to better operational decision quality.
- **6.2 Future Work:** Potential integration with real IMAP/SMTP servers, or expanding the action space to calendar management.

---
*Note: Use the graphs generated in the `artifacts/adaptive_environment/` folder as your primary figures for Chapter 5.*
