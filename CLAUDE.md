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
├── CLAUDE.md
├── data/
│   ├── raw/
│   │   ├── raw_sales_pos.csv
│   │   ├── supplier_invoices.csv
│   │   ├── recipe_book_unstandardized.csv
│   │   ├── inventory_stock.csv
│   │   └── benchmark_ingredienti_horeca.csv
│   ├── external/
│   │   ├── dim_calendar.csv
│   │   ├── dim_weather.csv
│   │   ├── dim_events.csv
│   │   └── dim_energy.csv
│   └── processed/
├── notebooks/
│   ├── 01_data_profiling.ipynb
│   ├── 02_dimension_tables.ipynb
│   ├── 03_etl_sql.ipynb
│   ├── 04_forecasting_model.ipynb
│   └── 05_energy_scenario.ipynb
├── src/
│   ├── utils.py
│   └── utils_forecast.py
└── output/
    ├── forecasts/
    └── scenarios/
```

## PHASES

### Phase 1 — Dimension Tables
- **dim_calendar**: `date`, `is_weekend`, `is_holiday`, `is_ponte`, `season`
  Source: Python `holidays` library + custom bridge-day logic
- **dim_weather**: `date`, `avg_temp`, `rain_mm`, `is_bad_weather`
  Source: Open-Meteo free API (Como/Milan area)
- **dim_events**: `date`, `event_type`, `magnitude`
  Source: simulated CSV
- **dim_energy**: `date`, `pun_eur_mwh`, `gas_eur_mwh`, `energy_cost_index`
  Source: real PUN data from GME (mercatoelettrico.org) for 2022-2024 baseline;
  simulated 2026 shock scenario calibrated on FIPE reports

### Phase 2 — ETL & SQL Preparation (DuckDB)
Merge internal POS data with all dimension tables.
Target unified time-series:
`date | covers | revenue | avg_check | max_temp | rain_mm | is_holiday | is_ponte | event_flag | pun_eur_mwh | energy_cost_index`

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

New functions → `src/utils_forecast.py`

### Division of Labor
- **Claude Code**: ETL, scaffolding, mechanical code
- **Giovanni + Claude chat**: model logic, parameter decisions, business interpretation
- **Giovanni**: domain decisions, elasticity validation, scenario assumptions
