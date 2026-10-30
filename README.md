# India Air Quality & Health

**Version:** v1.0.0  
**Status:** Initial scaffold  
**Scope:** India-wide national-level analysis; no state- or district-wise mapping in the primary output.

## Aim

Develop a reproducible analysis of population exposure to particulate air pollution in India and the evidence linking exposure to selected health outcomes. The initial focus is **PM2.5 and PM10**.

The planned communication output is one national-level graphic combining exposure estimates with a transparent summary of evidence for outcomes such as cardiovascular disease, respiratory disease, diabetes, hypertension, dermatological conditions, iron deficiency anaemia (IDA), and other outcomes only where sufficiently credible evidence is identified.

## Scientific safeguards

1. **Association is not causation.** Do not describe an association as causal unless the study design and evidence support that interpretation.
2. **No invented national estimates.** Every numerical exposure, prevalence, risk, or attributable-burden value must have a traceable source, year, population, and unit.
3. **Separate association from burden.** An epidemiological association is not the same as an India-specific attributable disease burden.
4. **Analyse PM2.5 and PM10 separately.** Evidence for one particle fraction must not automatically be applied to the other.
5. **Avoid ecological inference.** National aggregate comparisons cannot establish individual-level risk or explain geographic variation.
6. **Document uncertainty and confounding.** Record exposure measurement, outcome definitions, adjustment variables, limitations, and evidence strength.

## Planned workflow

1. **Exposure:** assemble and harmonise national PM2.5 and PM10 estimates, documenting source, temporal coverage, spatial resolution, units, and uncertainty.
2. **Health evidence:** extract India-relevant epidemiological studies and authoritative burden estimates. Record exposure contrast, outcome, effect measure, adjustment, population, and limitations.
3. **Synthesis:** distinguish measured burden, modelled attributable burden, and epidemiological association. Do not combine incompatible measures.
4. **Visualisation:** create one national-level figure with explicit units, time period, source citations, and evidence-strength annotations.
5. **Reproducibility:** keep raw data out of Git; version code, metadata, references, and lightweight derived outputs.

## Directory architecture

    data/
      raw/                 Original downloaded data (not committed)
      interim/             Intermediate harmonised data (not committed)
      processed/           Derived analysis-ready data (large files ignored)
      metadata/            Data dictionaries, source register, provenance
    references/
      literature/          Study extraction sheets and literature notes
      reports/             Authoritative report notes and source records
    src/
      exposure/             PM2.5 / PM10 ingestion and harmonisation
      epidemiology/         Study extraction and effect-measure handling
      statistics/           National summaries and uncertainty analysis
      synthesis/             Evidence grading and integration
      visualization/        Final national graphic
    notebooks/               Exploratory notebooks; reusable logic belongs in src/
    outputs/
      figures/               Generated figures
      tables/                Generated summary tables
      reports/               Reproducible report outputs
    tests/                   Data and analytical validation tests
    docs/                    Methods, decisions, and project documentation

## Data governance

- Maintain a source register with publisher, title, URL/DOI, version, access date, years covered, units, population, and licence.
- Preserve source values; perform unit conversions in documented processing steps.
- Retain denominators and uncertainty intervals wherever available.
- Do not commit credentials, personal data, large raw datasets, or restricted source files.
- Check dataset licences and redistribution terms before publishing derived data.

## Project status

This repository contains the initial project scaffold only. No final national exposure estimate or disease association has yet been calculated in this project.

## Versioning

Visible project version: **v1.0.0**. Increment the version for every user-visible project update and record material changes in the changelog.

## License

To be selected after reviewing source-data licences and intended project use.