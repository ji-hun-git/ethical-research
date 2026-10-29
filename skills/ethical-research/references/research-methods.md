# Methods for questioning research

Each method belongs to the stage where its risk arises. Use them to generate the questions in the questioning loop; the researcher answers them. Most of these methods address well-documented problems, while the evidence that each technique fixes its problem is thinner, so present them as questions worth answering, not as proof of rigour.

## Planning

**Premortem.** "Imagine it is a year from now and this study failed or the paper was rejected. What went wrong?" Ask the researcher to list reasons before you add any (Klein, 2007). Turn each reason into a check or a design change.

**Rival hypotheses and crucial tests.** For the main hypothesis, name at least one rival that predicts something different, and ask what observation would tell them apart (Platt, 1964). If no observation could, the design cannot answer the question.

**What would change your mind?** Ask the researcher to state, before data, the result that would count against the hypothesis. Write it in the ledger.

**Preregistration.** Separating prediction from postdiction protects against hindsight (Nosek et al., 2018). Ask whether hypotheses, outcomes, exclusions and the analysis are written down before data; if not, ask which of them are, and record the date.

**Red team and adversarial collaboration.** Invite the strongest critic in before the results, not after (Lakens, 2020), or design the study together with someone who expects the opposite result (Mellers et al., 2001). As an assistant, play that critic, then ask who in the researcher's field would disagree most and what they would say.

## Analysis

**Questionable research practices.** Among more than 2,000 psychologists surveyed with incentives for truth-telling, the most admitted practices were not reporting all dependent measures (66.5%), deciding to collect more data after looking at significance (58.0%) and selectively reporting studies that worked (50.0%) (John et al., 2012). Flexible choices of this kind can push the false-positive rate far above the nominal 5% (Simmons et al., 2011). Ask, plainly and without accusation:

- Were all measures and conditions reported, including ones that did not work?
- Was the sample size fixed in advance, or did data collection stop after a look at the results?
- Were exclusions decided before seeing their effect on the result?
- Were covariates, transformations or subgroups chosen after seeing the data?
- Are any p-values rounded down (p = .054 reported as p < .05)? `scripts/stats_check.py` finds some of these.

**Robustness.** Ask which reasonable alternative analysis would most likely change the conclusion, and whether it was run.

## Writing

**HARKing check.** Compare the hypotheses in the introduction with what was written down before the data (a preregistration, a proposal, an ethics application, an early draft). Hypotheses written after the results but presented as predictions mislead readers about the strength of the evidence (Kerr, 1998). If they differ, the paper should say which analyses were exploratory.

**Threats to validity.** Sweep the four kinds (Shadish, Cook & Campbell, 2002):

| Validity | The question |
| --- | --- |
| Statistical conclusion | Is the relationship real: power, assumptions, multiple comparisons, rounding? |
| Internal | Is it causal: confounders, reverse causation, selection, attrition, history? |
| Construct | Do the measures capture the concepts named in the claim? |
| External | Does it hold beyond this sample, setting and time? |

**Claim strength against design.** Correlational designs support association language; causal verbs (causes, leads to, improves) need a design that rules out the rivals above. Novelty claims ("for the first time") need a search the researcher can describe. Policy recommendations need more than one study.

## Sources

- John, L. K., Loewenstein, G., & Prelec, D. (2012). Measuring the prevalence of questionable research practices with incentives for truth telling. *Psychological Science, 23*(5), 524-532. https://doi.org/10.1177/0956797611430953
- Kerr, N. L. (1998). HARKing: Hypothesizing after the results are known. *Personality and Social Psychology Review, 2*(3), 196-217. https://doi.org/10.1207/s15327957pspr0203_4
- Klein, G. (2007). Performing a project premortem. *Harvard Business Review, 85*(9). https://hbr.org/2007/09/performing-a-project-premortem
- Lakens, D. (2020). Pandemic researchers: Recruit your own best critics. *Nature, 581*, 121. https://doi.org/10.1038/d41586-020-01392-8
- Mellers, B., Hertwig, R., & Kahneman, D. (2001). Do frequency representations eliminate conjunction effects? An exercise in adversarial collaboration. *Psychological Science, 12*(4), 269-275. https://doi.org/10.1111/1467-9280.00350
- Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The preregistration revolution. *PNAS, 115*(11), 2600-2606. https://doi.org/10.1073/pnas.1708274114
- Platt, J. R. (1964). Strong inference. *Science, 146*(3642), 347-353. https://doi.org/10.1126/science.146.3642.347
- Shadish, W. R., Cook, T. D., & Campbell, D. T. (2002). *Experimental and quasi-experimental designs for generalized causal inference*. Houghton Mifflin.
- Simmons, J. P., Nelson, L. D., & Simonsohn, U. (2011). False-positive psychology. *Psychological Science, 22*(11), 1359-1366. https://doi.org/10.1177/0956797611417632
