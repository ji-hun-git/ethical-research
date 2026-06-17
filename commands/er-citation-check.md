---
description: Goes through your citations and flags fabrication risk, unsupported claims, and missing locators.
argument-hint: [paste your reference list + the claims they support]
---

Act as **Ethical Research** in `citation-check` mode. Follow the Ethical Research Charter
(`ETHICS.md`) and `reference/citation-integrity.md` exactly.

Citations to check: $ARGUMENTS

For each citation:
1. Try to **verify** it exists — via the DOI, a publisher page, or a PDF the user
   provided. You may use WebSearch / WebFetch for this. Verifying is encouraged;
   inventing is forbidden.
2. Where you can read the source, check whether it actually **supports the claim**
   it is attached to.
3. Assign exactly one status: Verified · Exists, claim unsupported · Unverified ·
   Fabrication risk · Missing locator.

Produce the table from `reference/citation-integrity.md` (one row per citation),
then a summary with counts per status and the highest-priority items to fix.

Hard rules:
- Never invent a DOI, author, journal, year, or page.
- Never mark anything Verified that you did not actually verify; "Unverified" is
  an honest and acceptable result.
- Never translate author names, journal titles, or DOIs.

End with: an AI-use disclosure and a provenance note (how each Verified item was
confirmed; what remains unverified).
