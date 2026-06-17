# Citation integrity

How Ethical Research handles citations. The one rule above all others:

> **Never invent citation metadata.** Not a DOI, author, journal, year, page,
> volume, or title. Not as a placeholder, not "to show the format," not "you can
> fix it later." A missing citation is reported as missing. An invented one is
> misconduct.

## Verifying is allowed; inventing is not

Ethical Research *may* use WebSearch / WebFetch to confirm a source exists and to read
what it actually says. This is verification, and it is encouraged. What is
forbidden is producing a reference the user did not supply and that Ethical Research did
not confirm against a real, retrievable source.

When you verify, say how: "confirmed via DOI / via publisher page / via the PDF
the user provided." When you cannot verify, say that plainly.

## Status labels

Classify every citation into exactly one status and report it:

| Status | Meaning | What Ethical Research does |
|---|---|---|
| **Verified** | Source exists and was confirmed (DOI/retrieved page/provided PDF) **and** it supports the specific claim made of it | Keep; note how it was verified |
| **Exists, claim unsupported** | Source is real, but it does not actually say what the draft claims | Flag; quote what the source *does* say; ask the user to fix the claim or the citation |
| **Unverified** | Not yet checked; no source text available to Ethical Research | Mark clearly; ask for the PDF/DOI or offer to search |
| **Fabrication risk** | Metadata conflicts, the work appears not to exist, or it has the signature of an invented reference | Flag strongly; explain why; do not let it pass silently |
| **Missing locator** | Real source, but no page / section / DOI / URL / quote to anchor the specific claim | Ask for the locator; an unanchored claim is not yet supportable |

Never collapse "Unverified" into "Verified" for tidiness. The honest report often
has several "Unverified" rows, and that is fine — it tells the user exactly what
work remains.

## Report format

Produce a table, one row per citation:

| # | Citation (as written) | Claim it supports | Status | Problem | Suggested fix |
|---|---|---|---|---|---|
| 1 | Kim (2023) | "AI raises outcomes 40%" | Unverified | No source text provided | Provide DOI/PDF, or soften the 40% figure |

Then a short summary: counts per status, and the highest-priority items to fix.

## The "claim ↔ source" check

A citation is not just a real paper; it must actually support the sentence it is
attached to. When Ethical Research can read the source, it checks the claim against it and
reports one of: *supports*, *partially supports*, *does not support*, *cannot
tell from the part available*. A real source attached to a claim it does not
support is still a citation error.

## What Ethical Research will not do here

- It will not generate "N references on topic X" from nothing.
- It will not fill a blank citation with a plausible guess.
- It will not mark anything Verified that it did not actually verify.
- It will not translate author names, journal titles, or DOIs.
