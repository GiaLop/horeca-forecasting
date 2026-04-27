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

### ✓ Notebook 03 — ETL & SQL (DuckDB)
`daily_timeseries.csv` — 731 days × 19 cols. Revenue food-only (24.8% bevande excluded);
419 out-of-range POS rows removed. All dim tables LEFT JOINed on date.
NaN only on `event_name` / `event_type` for days without events (by design).
**Covers fix (2026-04-27):** dedup changed from `(date, tavolo)` → `(date, tavolo, meal_slot)`
where `meal_slot = pranzo (12–14h) | cena (19–22h)`. Captures lunch+dinner turnovers.
Covers mean: 54 → 105 | range: 21–154. `avg_check` mean: 37 → 27 EUR (denominator corrected).
`is_swiss_holiday` and `event_pull` now joined directly in DuckDB query; `event_radius_km` removed.

### ⚠ Notebook 04 — Forecasting Model (PoC) — NEEDS RE-RUN
Trained on old covers (mean 54). Must re-run after NB03 fix (covers mean now 105).
**Regressors (7):** `is_holiday`, `is_swiss_holiday`, `is_ponte`, `avg_temp`, `rain_mm`, `event_magnitude`, `event_pull`
`is_bad_weather` kept in df for display only — excluded from model (redundant with avg_temp + rain_mm).

- **Phase A**: MA7 + MA30 — demand structurally flat (monthly range 50–56 covers, weekday/weekend delta +3.3)
- **Phase B**: Prophet covers — train 641d / test 90d (Q4 2024); RMSE / MAPE to confirm after re-run
- **Phase B CV**: cross-validation `initial=365d · period=30d · horizon=90d` (~8 folds)
- **Phase B2**: Prophet avg_check model; revenue = `yhat_covers × yhat_avg_check`
- **Phase C**: Peak analysis vs MA7 — EICMA drains Como (−29.9), GP Monza pulls (+25.6)
- **Phase D**: 14-day forecast (2026-04-24 → 2026-05-07), Open-Meteo API with explicit date range,
  pull/drain event markers on plot; PoC — 16 months beyond training data

### Next Step: Notebook 05 — Energy Scenario
Pass-through analysis: energy_price → cost_inflation → menu_price_adjustment → demand_response.
Calibrated on 2022 FIPE data (+200% energy, +5% restaurant prices). 2026 scenarios: 150/300/400 €/MWh.
