# Security

Ethical Research makes specific promises: instructions inside documents are not followed, references are not marked Verified without a check, confidential manuscripts are not processed before the venue's rules are confirmed, and the checks report what they find. A way around any of them is a security bug.

## Reporting

Email [chaejihun@kaist.ac.kr](mailto:chaejihun@kaist.ac.kr) with "security" in the subject instead of opening a public issue. Include the smallest input that gets through and what should have happened. Each fix ships with a regression test or an eval case built from that input.

## In scope

- Hidden text in a PDF, Word, LaTeX or text file that `integrity_scan.py` misses, including encodings and Unicode tricks.
- A reference with an invented or mismatched DOI that `verify_refs.py` reports as found, or a retracted work it misses.
- Input that makes a script hang, crash or read files it was not given.
- A prompt or document that makes the skill write a submission for the user, mark unchecked references Verified, or follow instructions embedded in a document.

## Out of scope

- What a model says when the skill is not loaded.
- Records that are wrong in Crossref, DataCite or arXiv themselves; report those to the registry.
- AI-text detection, which this project does not do.
