## Aggregate comparison

| Policy | Avg Reward | Success Rate | Error Rate | Missed Deadlines | Escalation Threads |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | -117.5 | 0.00 | 1.00 | 60 | 0 |
| Multi-agent | +102.0 | 0.94 | 0.00 | 0 | 0 |

## Scenario talking points

### `founder_launch_dynamic`

- **Why the baseline fails:** The baseline only reacts to surface urgency and simple keywords. It misses the hidden blocker in the design/export email because the message sounds like a small question.
- **Why the multi-agent policy is better:** The Inbox Analyst and Priority Planner infer that the client deck/export message can block downstream launch work, so the policy handles it before the deadline.
- **Business consequence of a miss:** Missing the hidden blocker produces delayed deadline penalties and can create follow-up pressure later in the episode.

### `ops_fire_drill_dynamic`

- **What changed in the environment:** Revenue-risk, legal-signature, and executive-review emails compete with low-value travel and personal messages.
- **Which agent role helps most:** The Supervisor Agent checks visible safety constraints while the Priority Planner promotes deadline-sensitive business emails over low-value noise.
- **What reward difference was observed:** The multi-agent policy eliminated missed deadlines in the adaptive simulation while the greedy baseline missed 60 across eight episodes.

## Slide-ready takeaway

InboxWorld keeps the same `email triage` problem statement but enriches it with partial observability, delayed consequences, stochastic arrivals, and time pressure. That turns a basic classifier idea into a measurable agent-training environment.
