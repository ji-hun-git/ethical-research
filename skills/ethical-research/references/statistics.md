# Checking reported statistics

`scripts/stats_check.py` runs two published consistency checks in the standard library. Both test whether reported numbers can be true together; neither tests whether a study was well designed or its conclusions follow.

## Recomputed p-values

For every complete APA-style result (`t(df) = x, p = y`, `F(df1, df2) = x, p = y`, `r(df) = x, p = y`, `χ2(df, N = n) = x, p = y`, `z = x, p = y`, or the same with `ns`) the script recomputes p from the statistic and degrees of freedom, allowing for rounding: any statistic that rounds to the reported one is accepted, as statcheck does (Nuijten et al., 2016).

| Status | Meaning |
| --- | --- |
| consistent | Some statistic that rounds to the reported one gives the reported p |
| inconsistent | None does; the numbers cannot all be right as reported |
| decision error | The recomputed p falls on the other side of .05 from the reported one |
| check by hand | Inconsistent, but the sentence mentions a correction (Bonferroni, Holm, Greenhouse-Geisser, Welch, adjusted p), which the recomputation ignores |

One-tailed tests are recognised when the sentence says one-tailed, one-sided or directional. The p-values come from the regularised incomplete beta and gamma functions, which agreed with SciPy to a relative error below 1e-13 on sixteen cases; the tests pin those values to seven digits.

**Limits.** statcheck-style checking has known misses and false flags: a reanalysis found many flags were not real errors (Schmidt, 2016), and formats outside APA style go undetected while corrected and one-tailed p-values are flagged wrongly (Böschen, 2024). So report an inconsistency as "inconsistent at the reported precision" and ask the author, never as an accusation. Typos, copying errors and an unstated correction are the usual causes.

## GRIM

A mean of integer responses (Likert items, counts, test scores in whole points) can only take certain values for a given sample size. GRIM asks whether any integer total divided by n × items rounds to the reported mean (Brown & Heathers, 2017). With n = 25 and one item, a mean of 3.48 is possible (87 / 25) and 3.47 is not.

GRIM says nothing once n × items reaches 10 to the power of the reported decimals (for two decimals, 100 or more responses): every mean is then possible, and the script reports "not testable". It applies only to integer data, so ask what the measure is before running it.

## How to raise a finding

> In the results paragraph, t(48) = 1.20 gives a two-tailed p of about .24, so it cannot give p < .01. Was it a different statistic, a different test, or a typo? The conclusion in the abstract depends on it.

Then let the researcher check their output. Never "correct" a number yourself: only the original analysis can say which value is right.

## Sources

- Böschen (2024). statcheck is flawed by design and no valid spell checker for statistical results. arXiv:2408.07948.
- Brown, N. J. L., & Heathers, J. A. J. (2017). The GRIM test: A simple technique detects numerous anomalies in the reporting of results in psychology. *Social Psychological and Personality Science, 8*(4), 363-369. https://doi.org/10.1177/1948550616673876
- Nuijten, M. B., Hartgerink, C. H. J., van Assen, M. A. L. M., Epskamp, S., & Wicherts, J. M. (2016). The prevalence of statistical reporting errors in psychology (1985-2013). *Behavior Research Methods, 48*, 1205-1226. https://doi.org/10.3758/s13428-015-0664-2
- Schmidt (2016). Sources of false positives and false negatives in the STATCHECK algorithm: Reply to Nuijten et al. (2016). arXiv:1610.01010.
