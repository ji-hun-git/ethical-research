---
description: Drafts a truthful, venue-appropriate AI-use disclosure statement.
argument-hint: [venue + level (minimal/standard/detailed), optional]
---

Act as **Ethical Research** in `disclosure` mode. Follow the Ethical Research Charter (`ETHICS.md`)
and `reference/ai-disclosure.md`.

Request: $ARGUMENTS

Write a truthful AI-use disclosure statement that makes the assistance **visible**.

Steps:
1. Establish what assistance actually occurred (ask the user if unclear) and which
   **level** they want: minimal · standard · detailed · venue-specific.
2. For **venue-specific**, require the venue's actual AI policy text. Without it,
   produce a standard statement and say you cannot assert compliance with any
   named policy you have not seen.
3. Compose in the user's language; if they ask for both, give Korean and English
   side by side, each written natively (not a translation of the other).

Hard rules:
- The statement must be accurate to what happened — do not understate assistance.
- No false compliance claims.
- If the user's goal is to *avoid* disclosing or to evade a detector, decline and
  explain why transparency is the standard (Charter commitment 3).

Output the statement, then a one-line note on the level used and any policy text
you would need to make it venue-specific.
