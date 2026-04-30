# HoReCa Demand Forecasting & Energy Impact Analysis

> Proof of Concept — dati sintetici 2023-2024 | Python · DuckDB · Prophet · Tableau

---

## Cosa fa questo progetto

Un sistema di analisi predittiva per la ristorazione che risponde a due domande:

1. **Quanti coperti faremo domani?** — Pipeline A: Demand Forecasting
2. **Quanto ci costerà uno shock energetico?** — Pipeline B: Energy Pass-Through Analysis

Costruito da un data analyst con 15 anni di esperienza HoReCa. L'obiettivo è portare decisioni data-driven in un settore che ancora si affida all'istinto.

---

## Struttura del progetto

```
horeca-forecasting/
├── data/
│   ├── raw/                    # POS, fatture, inventario, ricette, benchmark
│   ├── external/               # Dim tables: calendar, weather, events, energy
│   └── processed/              # daily_timeseries.csv — output ETL
├── notebook/
│   ├── 01_data_profiling_cleaning.ipynb
│   ├── 02_dimension_tables.ipynb
│   ├── 03_etl_sql.ipynb
│   ├── 04_forecasting_model.ipynb
│   └── 05_energy_scenario.ipynb
├── src/
│   ├── utils.py                # Utility cleaning
│   └── utils_forecast.py       # Utility forecasting
└── output/
    ├── forecasts/
    └── scenarios/
```

---

## Pipeline A — Demand Forecasting

### Dati raw

| File | Righe | Periodo | Contenuto |
|------|-------|---------|-----------|
| `raw_sales_pos.csv` | 64.6K | 2023-2024 | Transazioni POS item-level |
| `supplier_invoices.csv` | 1.6K | 2023-2024 | Fatture fornitori |
| `inventory_stock.csv` | 577 | 2023-2024 | Snapshot mensili inventario |
| `recipe_book_unstandardized.csv` | 65 | Statico | Ricette con ingredienti |
| `benchmark_ingredienti_horeca.csv` | 117 | 2025-26 | Prezzi di riferimento HoReCa |

> **Scope:** food only — bevande escluse da tutto il pipeline.

### Dimension Tables (Notebook 02)

| Tabella | Fonte | Colonne chiave |
|---------|-------|---------------|
| `dim_calendar` | libreria `holidays` + logica custom | `is_holiday`, `is_ponte`, `is_swiss_holiday`, `is_high_season`, `season` |
| `dim_weather` | Open-Meteo API (Como 45.81°N 9.09°E) | `avg_temp`, `rain_mm`, `is_bad_weather` |
| `dim_events` | Fonti reali 2023-2024 (204 righe) | `event_name`, `event_type`, `event_magnitude`, `event_pull`, `radius_km` |
| `dim_energy` | GME PUN reale + indice base 2019 | `pun_eur_mwh`, `energy_cost_index` |

### Time-Series unificata (Notebook 03 — DuckDB)

```
date | covers | revenue | avg_check | avg_temp | rain_mm | is_bad_weather
     | is_holiday | is_swiss_holiday | is_ponte | is_high_season | season
     | event_magnitude | event_pull | event_radius_km
     | pun_eur_mwh | energy_cost_index
```

731 giorni × 19 colonne. Join su `date` con tutte le dim tables.

> **Nota sui coperti:** calcolati con deduplicazione per `(date, tavolo, time_slot)` per gestire i turni multipli pranzo/cena. Senza questa logica i coperti risultano sottostimati dell'87%.

### Modello di Forecasting (Notebook 04)

**Regressori Prophet:**

| Regressore | Tipo | Note |
|-----------|------|------|
| `is_holiday` | binario | Festività nazionali italiane |
| `is_swiss_holiday` | binario | Festività svizzere (TI, GR, ZH, BE) |
| `is_ponte` | binario | Giorni ponte |
| `avg_temp` | continuo | Comfort climatico |
| `rain_mm` | continuo | Deterrente pioggia |
| `event_magnitude` | ordinale 0-3 | Intensità evento |
| `event_pull` | ordinale -1/0/+1 | drain=-1, neutral=0, pull=+1 |

**Parametri scelti:**

```python
changepoint_prior_scale = 0.1      # Trend flessibile
seasonality_mode = 'additive'      # Serie piatta, variazioni assolute
holidays_prior_scale = 10          # Default
weekly_seasonality = True          # is_weekend gestito nativamente
```

**Risultati:**

| Metrica | Valore |
|---------|--------|
| RMSE single-split | 19.97 coperti |
| MAPE single-split | 19.18% |
| RMSE CV (4 fold) | 16.70 coperti |
| MAPE CV | 15.44% |

> MAPE ~15% = errore medio di ±12 coperti su 80. Accettabile per forecasting giornaliero HoReCa (letteratura: buono sotto 20-25%).

**Revenue Model:**

| Modello | MAPE Revenue |
|---------|-------------|
| Prophet B2 (covers × yhat_avg_check) | 30.88% |
| Lookup B3 (covers × mediana stagionale) | 35.97% |

Con 2 anni di dati Prophet batte il lookup. Con 3+ anni la lookup diventa più stabile ed è lo standard di settore.

### Finding chiave — Peak Analysis

| Evento | Delta vs MA7 | Interpretazione |
|--------|-------------|-----------------|
| GP Italia F1 (2023) | -47.3 (drain) | Il pubblico F1 va a Monza/Milano, Como si svuota |
| EICMA 2023 | -46.6 (drain) | Milano attrae la clientela locale |
| Milano Fashion Week | +42.9 (pull) | Fashion buyer usano Como come base |
| Salone del Mobile 2024 | +45.6 (pull) | Stessa logica Fashion Week |
| Mercatini Natale | +46 domenica / -22 giovedì | Effetto giorno sovrapposto all'evento |

> **Conclusione:** il segno dell'effetto (pull vs drain) dipende dall'evento specifico, non dalla distanza. Lo stesso tipo di evento può avere effetti opposti. È il modello che impara dai dati, non una regola a priori.

---

## Pipeline B — Energy Scenario (Notebook 05)

*In sviluppo.*

Analisi pass-through dello shock energetico 2026 (scenario Iran crisis):

```
energy_price → cost_inflation → menu_price_adjustment → demand_response
```

Scenari: 150 / 300 / 400 €/MWh (baseline 2026 già a ~120-160 €/MWh).

Calibrazione su dati FIPE 2022: +200% energia → +5% prezzi ristorazione.

---

## Stack tecnico

- **Python 3.11** — conda env `horeca_forecast`
- **DuckDB** — SQL queries ETL (Notebook 03)
- **Prophet 1.3.0** — forecasting time-series
- **Tableau** — dashboard finali (export CSV)

---

## Limiti del PoC

- Dati sintetici: la struttura del pipeline è corretta, i valori assoluti non rispecchiano un ristorante reale
- Gap temporale: modello allenato su 2023-2024, forecast al 2026 — 16 mesi di estrapolazione
- In produzione: retrain settimanale con dati aggiornati prima di ogni uso operativo
- `event_pull` del GP Monza assegnato come pull ma i dati mostrano drain nel 2023 — da rivalidare con dati reali

---

## Autore

**Giovanni Lopresti** — Data Analyst | HoReCa background 20 anni  
Progetto personale per portare decisioni data-driven nella ristorazione.
