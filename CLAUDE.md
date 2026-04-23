# HoReCa Demand Forecasting & Energy Impact Analysis

## WHO
I'm a data analyst with a strong HoReCa background (20 years in high-end 
restaurants). My goal is to bring data-driven decision-making to an industry 
that still relies on gut feeling.

You are my senior analyst. Before writing any code:
1. Briefly explain the logic and chosen approach
2. Wait for my confirmation before proceeding
3. One task at a time — show output and wait for approval

## WHAT
We are building two interconnected pipelines:

**Pipeline A — Demand Forecasting**
Predict future revenue and covers using internal POS data enriched with 
external signals (weather, calendar, events).

**Pipeline B — Energy Cost Impact Analysis**
Quantify how energy price shocks (2026 Iran crisis scenario) affect restaurant 
operations through a pass-through analysis:
energy_price → cost_inflation → menu_price_adjustment → demand_response

## Repository Structure
```
horeca-forecasting/
├── ROADMAP.ipynb                          ← project plan and progress tracker
├── data/
│   ├── raw/
│   │   ├── raw_sales_pos.csv              (64.6K rows, 2023-2024)
│   │   ├── supplier_invoices.csv          (1.6K rows, 2023-2024)
│   │   ├── recipe_book_unstandardized.csv (65 rows — 10 original recipes)
│   │   ├── inventory_stock.csv            (577 rows, monthly snapshots)
│   │   └── benchmark_ingredienti_horeca.csv (125 ingredients with min/max prices)
│   ├── external/                          ← built in Notebook 02
│   │   ├── dim_calendar.csv
│   │   ├── dim_weather.csv
│   │   ├── dim_events.csv
│   │   └── dim_energy.csv
│   └── processed/                         ← ETL output (Notebook 03)
│       └── daily_timeseries.csv           (731 days × 18 cols — main model input)
├── notebook/                              ← singular, not "notebooks"
│   ├── 01_data_profiling_cleaning.ipynb   ✓ COMPLETE
│   ├── 02_dimension_tables.ipynb          ✓ COMPLETE
│   ├── 03_etl_sql.ipynb                   ✓ COMPLETE
│   ├── 04_forecasting_model.ipynb
│   └── 05_energy_scenario.ipynb
├── src/
│   ├── utils.py                           ← existing utilities (do not modify)
│   ├── utils_update.py                    ← if an existing utility needs fixing
│   └── utils_forecast.py                  ← new functions specific to forecasting
├── output/
│   ├── forecasts/
│   └── scenarios/
└── _extra/                                ← local only, not versioned on Git
    ├── CLAUDE.md                          ← this file
    ├── ROADMAP.ipynb
    └── ebitda_pipeline.ipynb              ← previous project, source of calibrated parameters
```

## PHASES

### Phase 1 — Dimension Tables
- **dim_calendar**: `date`, `is_weekend`, `is_holiday`, `is_ponte`, `season`
  Source: Python `holidays` library + custom bridge-day logic
- **dim_weather**: `date`, `avg_temp`, `rain_mm`, `is_bad_weather`
  Source: Open-Meteo free API (Como/Milan area)
- **dim_events**: `date`, `event_type`, `magnitude`
  Source: real events CSV
- **dim_energy**: `date`, `pun_eur_mwh`, `energy_cost_index`
  Source: real PUN data from GME (mercatoelettrico.org) for 2023-2024;
  2026 shock scenarios at 150/300/400 €/MWh calibrated on FIPE reports

### Phase 2 — ETL & SQL Preparation (DuckDB)
Merge internal POS data with all dimension tables.
Target unified time-series:
`date | covers | revenue | avg_check | avg_temp | rain_mm | is_holiday | is_ponte | event_magnitude | event_radius_km | pun_eur_mwh | energy_cost_index`

### Phase 3 — Demand Forecasting Model
- **Baseline**: weighted moving average (last 3 same weekdays + same day previous year)
- **Advanced A**: Prophet with exogenous regressors + `add_country_holidays()`
- **Advanced B**: XGBoost/LightGBM for heterogeneous feature mixing
- Model selection criteria: to be discussed before implementation

### Phase 4 — Business Forecast Output
Actionable output for restaurant managers:
> "Next week: forecast 60 covers on Friday (+15% vs baseline).
> Driver: good weather + local event.
> Recommended burrata order: 4.2kg by Tuesday."

Export CSVs → Tableau dashboard.

### Phase 5 — Energy Stress Scenario (Pass-Through Analysis)
Methodology: estimate elasticities from 2022 historical shock, project to 2026.

**Calibration (2022 observed data from FIPE reports):**
- Energy bills: +200%
- Restaurant price inflation: +5% (vs +8.1% general — sector absorbed ~3 points)
- 71% of restaurants took emergency measures
- Net business closures: -10,600 units

**Pass-through chain:**
1. `energy_price` (GME PUN data) → `cost_inflation` (energy as % of opex)
2. `cost_inflation` → `menu_price_adjustment` (how much passed to consumer vs absorbed)
3. `menu_price_adjustment` → `demand_response` (elasticity: covers drop per % price increase)

**Scenario projection (2026 Iran crisis):**
Apply calibrated elasticities to new energy price inputs.

**Output format:**
> "At 150 €/MWh energy price:
> - Demand drop: -8% covers
> - Margin compression: -3.2 points
> - Recommended action: reprice bistecca +€2, promote high-margin pasta dishes"

### Data Sources for Phase 5
- **GME** (mercatoelettrico.org): PUN Index daily prices
- **Portale Offerte** (ilportaleofferte.it): historical energy price indices
- **FIPE Rapporto Ristorazione 2023/2024**: sector-level impact data
- **ISTAT**: general and food inflation indices

## HOW

### Golden Rules
1. One task at a time
2. Explain logic before writing code
3. Show output and wait for confirmation
4. Never proceed to next phase without explicit approval

### NaN Handling Rule (nome_standard)
After every fuzzy match step, rows where nome_standard = NaN must NOT be
dropped automatically. Workflow:
1. Print nunique and value_counts('categoria') for NaN rows
2. Add comment # AWAIT GIOVANNI APPROVAL and stop
3. Giovanni decides: drop, manual map, or keep
Apply to: inventory, invoices, sales_pos, recipes — any table with fuzzy match.

### Clean Data Rule
In every notebook, always load the cleaned tables produced by Notebook 01.
Never reload raw files from data/raw/.
Clean tables: sales_pos_cleaned, invoices_cleaned_std,
inventory_cleaned_std, recipes_cleaned_aug, benchmark_cleaned.
For Notebook 03+: load data/processed/daily_timeseries.csv as the main input.

### Tech Stack
- Python + Jupyter Notebooks in VSCode
- DuckDB for SQL queries
- Prophet / XGBoost for modeling
- Tableau for final dashboards (export CSVs)

### Conventions
- Language: all code, variables, comments, markdown cells → English
- Italian column names from raw CSVs → rename to English snake_case first
- Dates: YYYY-MM-DD
- Prices: EUR, 2 decimal places
- Ingredient names: normalized lowercase singular

### Scope
- Food only: exclude beverages from all source tables

### Existing Code
`src/utils.py`: `dupli_nan_count`, `date_accuracy`, `outliers_auto_detection`,
`basic_cleaning`, `fix_unit_errors`, `standardize_quantities`,
`quantity_exception_manage`, `get_best_match`, `imputing_benchmark_price`,
`prices_delta_flag`

`src/utils_forecast.py`: `compute_ponte`, `get_season`, `days`

New functions → `src/utils_forecast.py`

### Division of Labor
- **Claude Code**: ETL, scaffolding, mechanical code
- **Giovanni + Claude chat**: model logic, parameter decisions, business interpretation
- **Giovanni**: domain decisions, elasticity validation, scenario assumptions

## Current Status

- **Notebook 01 ✓ COMPLETE**: data profiling (all 5 tables), cleaning, outlier fixing
  (inventory + invoices), recipe augmentation (16 dishes, 125-ingredient benchmark),
  sales_pos coverage check vs recipe book

- **Notebook 02 ✓ COMPLETE — Dimension Tables:**
  - `dim_calendar` ✓ — 731×7, Italian + Swiss holidays (TI/GR/ZH/BE), custom ponte
    logic (weekday-only holidays), meteorological seasons, `is_high_season` Jun–Sep
    (placeholder, to be revised after POS join in Notebook 03)
  - `dim_weather` ✓ — 731×4, Open-Meteo API, Como coords (45.81°N 9.09°E),
    `is_bad_weather = rain_mm > 10 OR avg_temp < 5`
  - `dim_events` ✓ — 204×7, real 2023-2024 events, one row per day per event,
    coverage: Como / Milano / Cernobbio / Monza; Orticolario + Proposte Cernobbio
    included; `event_id` unique per event (event_name + year key)
  - `dim_energy` ✓ — 731×3, real GME PUN data 2023-2024, base 100 = 2019 mean
    (52.33 €/MWh); 2026 scenarios: 150/300/400 €/MWh
  - Refactor: custom functions (`compute_ponte`, `get_season`, `days`) moved to
    `src/utils_forecast.py` with docstrings; notebook imports as `ut_f`

- **Notebook 03 ✓ COMPLETE — ETL & SQL (DuckDB):**
  - `data/processed/daily_timeseries.csv` — 731 days × 18 columns
  - Phase A: POS aggregated via `basic_cleaning` + `date_accuracy` (419 out-of-range
    rows removed); covers deduped by (date, tavolo); revenue food-only (24.8% bevande
    excluded)
  - Phase B: DuckDB LEFT JOINs on date — calendar, weather, events, energy all clean
  - `event_id` unique per event (not per day); `event_magnitude` and `event_radius_km`
    both set to 0 on days without events
  - NaN only on `event_name` and `event_type` for days without events (by design)

- **Next step**: Notebook 04 — Forecasting Model
