# 2024 pilot: exposure and health context

**Project version:** v1.1.0  
**Pilot period:** 1 January–31 December 2024  
**Air-quality source:** India Air Quality Database, XKDR Forum; CPCB CAAQM network only.

## Scope

The first reproducible pilot creates one annual PM2.5 mean and one annual PM10 mean per city with eligible CPCB CAAQM stations. US Embassy/Consulate monitors are excluded so the monitoring network is consistent. City names and station metadata are taken from the XKDR station/measurement files; city-name harmonisation and city-boundary resolution are not silently inferred.

## Air-quality calculation

1. Download the 12 2024 monthly Parquet files and station metadata from XKDR.
2. Filter to `source = cpcb_caaqm` and `parameter_name IN ('PM2.5', 'PM10')`.
3. Restrict timestamps to 2024 in Indian Standard Time (IST).
4. Exclude null and negative PM values. Do not automatically trim high positive observations: XKDR publishes readings as received and does not validate or remove outliers.
5. Collapse duplicate station/pollutant/timestamp rows by taking their mean.
6. Calculate a station annual mean only when at least 75% of the 8,784 calendar hours in leap-year 2024 have valid hourly records. This is a strict full-calendar-year rule; stations commissioned part-way through 2024 may therefore be excluded.
7. Calculate each city/pollutant estimate as the unweighted arithmetic mean of eligible station annual means. This prevents stations with more records from dominating the city estimate.

The 75% threshold is a pilot quality-control choice, not a CPCB or WHO standard. Sensitivity checks should rerun the analysis at 50%, 75% and 90%. Report the number of included/excluded stations for each pollutant. The city estimate is a monitoring-network average, not a population-weighted personal exposure estimate.

## Outputs

- `city_annual_2024.csv`: one row per city/state group, with PM2.5 and PM10 annual means and station counts.
- `station_annual_2024.csv`: station-level annual means, completeness and eligibility.
- `qc_summary_2024.csv`: row counts and exclusions.

Raw files are cached under `data/raw/xkdr/2024/` and must not be committed to Git.

## Reproduce

Install the pilot dependencies:

```bash
pip install -r requirements-pilot.txt
```

Set an XKDR API key in the environment (the public demo key is restricted to 2024 bulk files; a personal key is available from XKDR):

```bash
export XKDR_API_KEY='your-key'
python -m src.exposure.xkdr_2024_pilot
```

Optional arguments:

```bash
python -m src.exposure.xkdr_2024_pilot --min-completeness 0.50
python -m src.exposure.xkdr_2024_pilot --force-download
```

## NFHS-6 health context

NFHS-6 fieldwork ran from May 2023 to December 2024. The pilot will use the national fact-sheet indicators as **descriptive health context**, not as outcomes in a city-level regression. The survey's national/state/district fact sheets are not city-level estimates, and the survey period is not exactly the 2024 calendar year.

Candidate national indicators from the official NFHS-6 fact-sheet release include:
- Women and men aged 15+: high/very high blood sugar (>140 mg/dL) or taking medicine to control blood sugar.
- Women and men aged 15+: elevated blood pressure (systolic ≥140 mmHg and/or diastolic ≥90 mmHg) or taking medicine to control blood pressure.

These are measured biomarker/medication composite indicators, not equivalent to clinically confirmed diabetes or hypertension diagnoses. The Ministry has stated that anaemia prevalence will instead be reported from a separate ICMR survey using its selected gold-standard haemoglobin method; do not use NFHS-6 as the anaemia outcome source in this pilot.

**No association or causal effect can be estimated by pairing one national air-quality estimate with one national health prevalence.** Such values can be shown side by side with separate sources and dates, but any inferential analysis requires matched spatial/temporal units, appropriate survey weights/uncertainty, confounder adjustment and a defensible study design.

## Limitations

- XKDR data are published as received; calibration, gap filling and outlier removal are not performed by XKDR.
- Station coordinates and city/state labels are based on source registry values; city labels may need manual harmonisation.
- The annual mean is conditional on monitoring coverage and the 75% completeness rule.
- Equal station weighting does not represent population exposure.
- NFHS-6 fact-sheet estimates are provisional and subject to the official release's caveats.
- No disease burden, attributable fraction or causal effect is calculated in this pilot.

## Sources and attribution

- Patnaik, A. (2026). *India Air Quality Database*. XKDR Forum. https://airquality.xkdr.org/ . CC BY 4.0. Attribute XKDR Forum and the CPCB CAAQM network.
- XKDR public API documentation: https://github.com/xKDR/Air-Quality-Database/blob/main/docs/PUBLIC_API.md
- IIPS/MoHFW, *National Family Health Survey 2023–24 (NFHS-6)*: https://www.nfhsiips.in/nfhsuser/nfhs6.php
- MoHFW/PIB update on NFHS-6 fact-sheet indicators and anaemia: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2294277
