# Reading an investigation result

The four-screen wireframe organizes **where to investigate**. This report defines
**how to read the evidence** from an implemented descriptive component.

```text
QUESTION                 What are we investigating?
OBSERVATION              What did the supplied results show?
WHY THESE MEASURES       What job does each displayed metric do?
EVIDENCE                 Values + usable/excluded counts + method
MEANING | NEXT STEP      Interpretation | decision or further investigation
LIMITS                   What cannot be concluded; missing prerequisites
[Inspect calculations]  Full tables, settings and downloadable evidence file
```

`InvestigationSection` requires explicit question, result, observation,
metric_purpose, interpretation, next_step and limitations. `write_investigation`
accepts descriptive `Exploration` and `GroupedProportions` results and writes an
offline `review.html` plus `evidence.json` in a **new** directory. Existing output
directories are refused. It does not accept OLS/profile results or replace the
legacy renderer. See [the artificial example](../examples/report_investigation.py).

The renderer formats supplied statistics; it does not choose methods or calculate
new estimates. Explanations are investigator-authored, not automatically verified
conclusions. Result tables are editable: saved evidence reflects the supplied
table, while its input fingerprint and choices describe creation time. A
fingerprint does not certify later edits. Keep source data and transformation
records separately. JSON preserves numeric values without display rounding;
missing numeric results become null. Unsupported values fail before output is
created. Evidence may contain flagged measurements and row positions: review it
before sharing. No source dataset or generated report belongs in the repository.

## Metric purpose, rather than a pile of numbers

| Measure | Investigation purpose | Decision boundary |
| --- | --- | --- |
| Eligible, missing and used counts | Identify the denominator and exclusions | Large counts alone do not establish representativeness |
| Event percentage | Describe how common an explicitly coded event is | Weighted percentages use weights; displayed event counts are unweighted |
| Median and quartiles | Describe typical values and the middle half | Not fitted distributions or acceptable-value thresholds |
| IQR review flags | Locate observations worth checking | Not errors and not a deletion recommendation |
| Correlation | Describe selected linear or monotonic association | Not causation, predictive performance or a model prescription |
| Calculation status | Explain whether a result was computed | Not a confidence or reliability score |

Put uncertainty beside the finding. If intervals or survey-design adjustments
are not implemented, say so explicitly; do not invent a confidence badge.
Next steps can be “verify coding”, “compare chosen subgroups” or “obtain sampling
design information”. A decision need not mean deploying a model.

## Review of the new composition helpers

`team_workbench.py` composes existing functions, independently of the prototype.
Its CSV reader preserves string IDs/literal categories and rejects duplicate or
blank source headers before pandas can rename them. Overview supports composite
keys. Group descriptions expose weights, eligibility and missing policy;
relationship composition exposes missing policy. Notebook metadata detaches
counts from caller-owned dictionaries. These helpers do not connect the browser
prototype or implement the twenty-category roadmap.

Distribution shape hints use pandas sample skewness/kurtosis with heuristic
thresholds, not hypothesis tests. They require investigator review and do not
identify a correct distribution family. Missing exclusion defaults in recipes
must be understood before reuse. No general inference engine is implemented.

## Design references

The reading order follows the emphasis on clear communication in the
[ONS visualisation principles](https://service-manual.ons.gov.uk/data-visualisation/guidance/principles)
and makes absent uncertainty explicit, following
[ONS uncertainty guidance](https://service-manual.ons.gov.uk/data-visualisation/guidance/showing-uncertainty-in-charts).
These references guide presentation; they do not validate an analysis.
