---
name: inconsistent-statistics
description: "A results paragraph whose test statistic cannot give its p-value: it catches the error rather than calling the paragraph ready."
tags: [questioning, statistics]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/ethical-research:er-review Is this results paragraph ready to submit?

"Students in the AI condition scored higher on the critical-thinking test (M = 3.47, SD = 0.61, n = 25) than controls (M = 3.12, SD = 0.70, n = 25), t(48) = 1.20, p < .01, d = 0.53."
