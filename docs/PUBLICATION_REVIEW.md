# Publication review of 29 September 2026

This is a historical record of the September revision. Output counts, document
paths and validation totals below refer to that snapshot. See the repository
README for the current reproduction workflow. Publication documents are now
assembled and edited separately in Word from the audited tables and figures.

The publication set consists of four main figures, eleven supplementary figures,
three formatted main tables and Tables S1–S16 in the revised supplementary document.
The complete CSV files retain additional machine-readable diagnostic columns.

## Outputs

- Canonical figures: `figures/`, each as 600 dpi PNG, font-embedded PDF, and editable SVG.
- Superseded figures: `figures/archive/`; preserved for traceability, excluded from the current manifest.
- Revised main manuscript and SI: `manuscript/publication/`.
- Original supplied Word files: `manuscript/templates/`; preserved without edits.
- Numerical inventory and validation: `results/publication_audit.json` and
  `docs/PUBLICATION_OUTPUT_INVENTORY.md`.
- Figure 1 collision audit: `results/figure1_label_audit.json`.
- Final document layout and provenance checks: `manuscript/publication/document_qa.json`.

## Changes that affect interpretation

1. **Option-order reference.** Comparisons now require the prespecified `rep=0`
   reference to survive censoring. The former analysis substituted the first
   surviving permutation when the reference was absent. Sol has 157 valid
   comparisons rather than 175, with mean JSD 0.045 rather than 0.052.
   F120 has no valid Sol reference comparison; its former large heatmap value is
   not a valid estimate of the specified comparison.
2. **Singleton sensitivity.** One retained label assignment or prompt descriptor
   cannot establish sensitivity. Those groups now have undefined JSD rather than
   a self-comparison of zero. Summary denominators count valid comparisons and
   exclude the unconditioned target; retained counts remain available.
3. **Sample alignment.** Each model's LOCO human and entropy reference mean now
   uses that model's observed cells. Cross-model inferential contrasts remain
   paired. Cultural-map comparisons distinguish 107-country, 91-country and
   43-country samples. Sol has no default variant-wise modal map profile.
4. **Entropy interpretation.** Low mean entropy and slopes below one do not imply
   low cross-cell variance. Both GPT models have entropy SD ratios above one.
   The manuscript now reports fixed-effect results and the limitation of only
   nine item clusters. All three two-way fixed-effect slope intervals include zero.
5. **Numerical reproducibility.** Probability CSVs must be read with round-trip
   float precision when reproducing argmax choices. One Jev Belarus/F120 vector
   contains 0.351 and 0.35100000000000003; an ordinary CSV parser can collapse
   this near-tie and select a different category. The integrity audit preserves
   the archived precision and verifies every original JSD.

Primary country-item metrics, entropy regression estimates, map coordinates and
map distances, and population-specificity estimates were regenerated from the
archived inputs and are numerically unchanged. No provider API calls were made.

## Figure design

The cultural-region assignments and all eight region colours are taken from Tao
et al.'s public source lookup and plotting script; see `config/reference/README.md`.
Figure 1 uses the exact `#CC79A7` and `#0072B2` prompting colours. The label placer
checks rendered bounding boxes against all labels and point extents and fails if
it cannot place every label. All 107 countries and three models are labelled.

Main figures reserve space for statistics and legends. Heatmaps have readable
item names, valid counts, explicit unavailable cells and contrast-aware text.
Entropy scatterplots are separated by model. All boxplots show outliers and their
conventions are stated in the captions. Prior duplicate variants are archived.

## Document revision and validation

The main manuscript revises the abstract, significance statement, results,
discussion, relevant methods and data-availability text. The supplementary
template is populated with complete methods, Tables S1–S16, Figures S1–S11 and
their captions. Conditional-probability punctuation, absolute-value delimiters
and spacing in the supplied native Word equations are repaired; the equations
remain editable. The original Dropbox documents are unchanged.

All 15 canonical figures and all 66 rendered document pages (26 main, 40 SI) were
visually inspected. The document checks verify complete figure/table numbering,
repeating table headers, absence of placeholders and blank pages, page bounds,
and exact agreement between embedded images and current figure exports.
The full test suite passed 36 tests; two warnings concern singular covariance in
existing synthetic test designs. The data/output audit passed all 988 checks
across all 43 result/table CSV files. Figure 1 contains 110 labels with zero
label-to-label or label-to-point collisions.

## Reproduce without new API calls

From the repository root, using the analysis environment:

```sh
MPLCONFIGDIR=tmp/mpl .venv/bin/python scripts/04_analyze.py
.venv/bin/python scripts/09_analyze_robustness.py
MPLCONFIGDIR=tmp/mpl .venv/bin/python scripts/05_make_outputs.py
MPLCONFIGDIR=tmp/mpl .venv/bin/python scripts/11_audit_publication.py
```

The document-assembly step has been retired. Update the manuscript and
supplementary information in Word from the audited tables and figures. Changes
in the underlying results require reviewing the interpretation and prose as well
as numerical values. Inspect the final document layout after content changes;
submission figure masters are the standalone vector files in `figures/`.

## Before submission

The original bibliography and author/contribution/conflict statements are retained
from the supplied manuscript. Their factual and bibliographic accuracy, any archive
DOI, and journal-specific word limits require author review. The analysis supports
a release-updated extension, not exact replication of Tao et al.'s archived survey
release or direct-response protocol. Dataset licensing and the final public archive
should be confirmed for the version submitted.
