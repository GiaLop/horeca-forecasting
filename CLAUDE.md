# HoReCa Demand Forecasting & Energy Impact Analysis

## WHO
I'm a data analyst with a strong HoReCa background (20 years in high-end restaurants).
You are my senior analyst. Before writing any code:
1. Briefly explain the logic and chosen approach
2. Wait for my confirmation before proceeding
3. One task at a time — show output and wait for approval

## WHAT
Two interconnected pipelines:
- **Pipeline A**: Predict covers/revenue using POS data + external signals (weather, calendar, events)
- **Pipeline B**: Quantify energy price shocks (2026 Iran scenario) via pass-through analysis

## Repository Structure
```
horeca-forecasting/
├── data/
│   ├── raw/               ← source files (do not reload after Notebook 01)
│   ├── external/          ← dim_calendar, dim_weather, dim_events, dim_energy
│   └── processed/
│       └── daily_timeseries.csv   (731 days × 19 cols — main model input)
├── notebook/
│   ├── 01_data_profiling_cleaning.ipynb   ✓ COMPLETE
│   ├── 02_dimension_tables.ipynb          ✓ COMPLETE
│   ├── 03_etl_sql.ipynb                   ✓ COMPLETE
│   ├── 04_forecasting_model.ipynb         ✓ COMPLETE (PoC)
│   └── 05_energy_scenario.ipynb
├── src/
│   ├── utils.py           ← existing utilities (do not modify)
│   ├── utils_update.py    ← fixes to existing utilities if needed
│   └── utils_forecast.py  ← forecasting-specific functions (compute_ponte, get_season, days)
└── output/
    ├── forecasts/
    └── scenarios/
```

## HOW

### Golden Rules
1. One task at a time
2. Explain logic before writing code
3. Show output and wait for confirmation
4. Never proceed to next phase without explicit approval

### Clean Data Rule
- Always load cleaned tables from Notebook 01 — never reload from `data/raw/`
- Notebook 03+: use `data/processed/daily_timeseries.csv` as main input
- After fuzzy match: rows where `nome_standard = NaN` must NOT be dropped automatically
  → print nunique + value_counts, add `# AWAIT GIOVANNI APPROVAL`, stop

### Tech Stack
- Python 3.11 — conda env `horeca_forecast` (kernel registered in VSCode)
- DuckDB for SQL queries in Notebook 03
- Prophet 1.3.0 for forecasting
- Tableau for final dashboards (export CSVs)

### Conventions
- All code, variables, comments, markdown → English; dates → YYYY-MM-DD
- Italian column names → rename to English snake_case on first load
- Food only — exclude beverages from all source tables
- New utility functions → `src/utils_forecast.py`; import alias `ut_f`

### Division of Labor
- **Claude Code**: ETL, scaffolding, mechanical code
- **Giovanni + Claude chat**: model logic, parameter decisions, business interpretation
- **Giovanni**: domain decisions, elasticity validation, scenario assumptions

## Current Status

### ✓ Notebook 01 — Data Profiling & Cleaning
All 5 raw tables profiled and cleaned. Recipe augmented to 16 dishes with 125-ingredient benchmark.

### ✓ Notebook 02 — Dimension Tables
| Table | Shape | Notes |
|-------|-------|-------|
| `dim_calendar` | 731×7 | Italian + Swiss holidays, custom ponte logic, meteorological seasons |
| `dim_weather` | 731×4 | Open-Meteo API, Como (45.81°N 9.09°E), `is_bad_weather = rain_mm>10 OR temp<5` |
| `dim_events` | 226×8 | 2023-2024 real events + 6 events 2026 (ids 59–64); `event_pull` {−1,0,+1} added |
| `dim_energy` | 731×3 | Real GME PUN 2023-2024, base 100 = 2019 mean (52.33 €/MWh) |

### ⚠ Notebook 03 — ETL & SQL (DuckDB)
`daily_timeseries.csv` — 731 days × 19 cols. Revenue food-only (24.8% bevande excluded);
419 out-of-range POS rows removed. All dim tables LEFT JOINed on date.
NaN only on `event_name` / `event_type` for days without events (by design).
**Covers fix (2026-04-27):** dedup changed from `(date, tavolo)` → `(date, tavolo, meal_slot)`
where `meal_slot = pranzo (12–14h) | cena (19–22h)`. Captures lunch+dinner turnovers.
**Scontrino filter (2026-04-27):** dropped 4.452 scontrini — `>1000€` (25 outlier) +
`<20€ on normal tables` (3.969 incomplete registrations; bar/asporto <20€ kept).
Covers mean: 54 → 86 | range: 17–146. Revenue mean: 2004 → 2731 EUR. `avg_check` mean: 37 → 31 EUR.
`is_swiss_holiday` and `event_pull` now joined directly in DuckDB query; `event_radius_km` removed.
**GP F1 event_pull correction (2026-04-28):** `dim_events.csv` updated — GP Italia F1 `event_pull` −1 (was +1).
Peak analysis confirmed GP F1 drains Como (−54.4 vs MA7); re-run NB03 + NB04 to propagate correction.

### ✓ Notebook 04 — Forecasting Model (PoC) — re-run 2026-04-27
Data: covers mean 86, revenue mean 2731 EUR (post-scontrino filter).
**Regressors (7):** `is_holiday`, `is_swiss_holiday`, `is_ponte`, `avg_temp`, `rain_mm`, `event_magnitude`, `event_pull`
`is_bad_weather` kept in df for display only — excluded from model (redundant with avg_temp + rain_mm).

- **Phase A**: MA7 + MA30 — demand structurally flat (monthly range 50–56 covers, weekday/weekend delta +3.3)
- **Phase B**: Prophet covers — train 641d / test 90d (Q4 2024); RMSE 19.97 / MAPE 19.18%
- **Phase B CV**: cross-validation `initial=456d · period=30d · horizon=90d` (4 folds); RMSE CV 16.70 / MAPE CV 15.44%
- **Phase B2**: Prophet avg_check — RMSE 7.64 EUR / MAPE 21.59%; revenue estimate MAPE 30.88% — kept as technical benchmark
- **Phase B3**: Lookup revenue (median avg_check by season × is_weekend) — MAPE 35.97%; lost vs B2.
  Root cause: 2-year window too short for stable winter median (+8.5/+11.6 EUR mismatch on test). Revisit with ≥3 years real data.
  Operational recommendation: use Lookup B3 in production with ≥3 years; use Prophet B2 until then.
- **Phase C**: Peak analysis vs MA7 — EICMA drains (−56.4), GP F1 drains (−54.4); Fashion Week pulls (+48.6), Mercatini pulls (+46.0). 7–8/10 peaks unexplained by any regressor.
- **Phase D**: 14-day forecast (2026-04-24 → 2026-05-07), Open-Meteo API, pull/drain markers on plot.
  PoC warning explicit in printed output and plot annotation; gap ~16 months beyond training data.

### ✓ Notebook 05 — Energy Scenario (Pass-Through Analysis)
Calibration: FIPE 2022 (+200% energy → +5% menu → pass-through rate 0.025). Baseline PUN: 117 €/MWh.
Scenarios: A=150 / B=250 / C=300 €/MWh. Energy share of revenue: 12%.

- **Phase A**: Historical calibration — pass-through rate 0.025 validated
- **Phase B**: Scenario computation — Δ% energia, Δ% menu, margin_compression EUR/day and EUR/year
- **Phase C**: Historical PUN chart (GME 2023-2024) + three scenario threshold lines
- **Phase D**: Demand response — two segments (Turistico ε=−0.25 PT=0.050 / Locals ε=−0.70 PT=0.015);
  extended chain: margin_comp_total = energy_cost_increase − quota_trasferita + revenue_loss_demand.
  Operational levers per scenario (staff / menu engineering / supplier renegotiation) with timeframe + KPI.
  Model limitations documented: elasticity estimates, labour cost excluded, price transition management,
  non-linear elasticity.

**Margin compression summary (EUR/day · EUR/year):**
| Scenario | Turistico | Locals |
|----------|-----------|--------|
| A — 150 €/MWh | ~45 / ~16,400 | ~63 / ~23,000 |
| B — 250 €/MWh | ~181 / ~66,100 | ~254 / ~92,700 |
| C — 300 €/MWh | ~249 / ~90,900 | ~349 / ~127,400 |

### Project Status: COMPLETE (PoC)
All 5 notebooks delivered. Next steps if continuing with real data:
- Re-run NB03 + NB04 after GP F1 event_pull correction (dim_events already updated)
- Calibrate demand elasticity on real POS data (covers ~ delta_menu_pct)
- Add labour cost to pass-through chain (NB05 Phase D v2)
- Retrain Prophet weekly on rolling data for production forecasting
