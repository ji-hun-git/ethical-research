---
name: scan-coauthor-text
description: "A co-author's paragraph with chatbot leftovers, tortured phrases, a placeholder and an overclaim: it finds them."
tags: [integrity, slop]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Bash]
---

/ethical-research:er-scan Check this paragraph from my co-author before we submit:

"Certainly, here is the revised related work. Recent advances in profound learning and counterfeit consciousness have transformed colossal information analysis [citation needed]. Our results prove that this approach is groundbreaking."
