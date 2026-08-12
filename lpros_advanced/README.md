# LPROS Advanced Rules & Skills Pack

Next-level refinement for mathematics, statistics, forecasting, simulations, conditioning, behavior analysis, computational rigor, and agentic orchestration.

## Structure

```
lpros_advanced/
├── .cursor/
│   ├── rules/
│   │   ├── 00-core-advanced.mdc
│   │   ├── statistics-probability.mdc
│   │   └── forecasting-standards.mdc
│   └── skills/
│       ├── forecasting/SKILL.md
│       ├── bayesian-updating/SKILL.md
│       ├── simulation-engine/SKILL.md
│       ├── behavior-analysis/SKILL.md
│       ├── conditioning-protocol/SKILL.md
│       ├── optimization/SKILL.md
│       ├── computational-math/SKILL.md
│       ├── agentic-orchestration/SKILL.md
│       ├── accuracy-audit/SKILL.md
│       ├── physics-informed/SKILL.md
│       └── ebay-listings/SKILL.md
└── README.md
```

## What This Pack Adds

| Domain | Files | Purpose |
|--------|-------|---------|
| Core rigor | `00-core-advanced.mdc` | Elevated non-negotiables |
| Statistics & Probability | `statistics-probability.mdc` | Uncertainty, sample size, Bayesian preference |
| Forecasting | `forecasting-standards.mdc` + forecasting skill | Base/adverse/severe + listings-needed discipline |
| Bayesian updating | bayesian-updating skill | Sequential belief updates from real outcomes |
| Simulation | simulation-engine skill | Monte Carlo / scenario risk distributions |
| Behavior analysis | behavior-analysis skill | Product + agent behavioral diagnostics |
| Conditioning | conditioning-protocol skill | Authoritative + Pavlovian shaping protocol |
| Optimization | optimization skill | Price, quantity, portfolio decisions |
| Computational math | computational-math skill | Fee algebra, sensitivity, numerical hygiene |
| Agentic design | agentic-orchestration skill | Brain/Soldier routing and contracts |
| Accuracy | accuracy-audit skill | Continuous calibration against reality |
| Constraint thinking | physics-informed skill | Capital conservation & irreversibility mindset |
| eBay evidence | ebay-listings skill | Sold/active comps via `ebay-sold-items` bridge |

## How to Install

1. Merge the `.cursor/rules/` files into your project’s `.cursor/rules/`
2. Merge the `.cursor/skills/` folders into your project’s `.cursor/skills/`
3. Keep the original core LPROS rules (economics, verification, agents) — this pack extends them

### Merge example

```bash
# from repo root
cp lpros_advanced/.cursor/rules/*.mdc .cursor/rules/
cp -R lpros_advanced/.cursor/skills/* .cursor/skills/
```

## Design Philosophy

- Rules stay short and hard (constraints)
- Skills carry longer procedures (only loaded when needed)
- All numerical claims remain subordinate to the deterministic Economics Engine
- Uncertainty is first-class
- Conditioning is explicit and measurable

## Suggested load order

1. Always-on: `00-core-advanced.mdc`
2. Agent pulls `statistics-probability` / `forecasting-standards` when relevant
3. Skills load by task: forecast → simulate → optimize → audit; agents → Brain/Soldier contracts
