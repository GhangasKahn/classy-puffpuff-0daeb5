---
name: behavior-analysis
description: Product and agent behavioral diagnostics — funnels, habit loops, failure modes, and incentive misalignment. Use when analyzing user behavior, agent drift, engagement, conversion, or why a system acts against stated goals under LPROS.
---

# Behavior Analysis Skill

## When to use

- Diagnosing drop-off, churn, non-adoption, or misuse in a product
- Auditing agent/tool behavior vs intended policy (Brain/Soldier drift)
- Incentive and feedback-loop analysis (humans or agents)
- Designing measurement for conditioning / training protocols

## Procedure

### 1. Specify the organism

- **Actor**: user segment, agent role (Brain/Soldier), or coupled system.
- **Goal**: stated objective vs revealed objective (what is actually optimized).
- **Environment**: UI affordances, tool permissions, rewards, latency, information.

### 2. Map the behavior loop

1. Cue → routine → reward (habit) **or** observe → decide → act → feedback (agent).
2. Identify friction, ambiguity, and competing rewards.
3. Separate capability failures (cannot) from motivation/incentive failures (will not).

### 3. Instrumentation

- Define events with clear identity: who, what, when, properties.
- Funnel stages with mutually exclusive counts where possible.
- For agents: log plan, tool calls, outputs, verification results, overrides.

### 4. Diagnostics checklist

| Question | Probe |
|----------|-------|
| Is the goal measurable? | Metric + window |
| Is feedback delayed/noisy? | Latency of reward |
| Are incentives misaligned? | Local reward vs global objective |
| Is the policy underspecified? | Ambiguous branching |
| Is there reward hacking? | Proxy metric inflation |
| Is sample biased? | Survivorship / selection |

### 5. Interventions

- Prefer smallest reversible change that tests the causal story.
- Pair each intervention with a success metric and kill criterion.
- For agents: tighten contracts, add verification gates, or retrain conditioning — do not only add prose prompts.

### 6. Output contract

```text
BEHAVIOR ANALYSIS
- Actor / context:
- Stated vs revealed goal:
- Loop map (cue→act→feedback):
- Failure mode classification: capability | incentive | information | policy gap
- Evidence (counts, rates, logs):
- Intervention + metric + kill criterion:
- Risks / ethics notes:
```

## Anti-patterns

- Blaming “users are dumb” or “the model is random” without instrumentation
- Optimizing vanity metrics that diverge from capital or mission outcomes
- Changing five variables at once and claiming learning
