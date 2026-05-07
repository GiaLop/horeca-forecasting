# HoReCa Demand Forecasting & Energy Impact Analysis

> Proof of Concept — dati sintetici 2023-2024 | Python · DuckDB · Prophet · Tableau

---

## Cosa fa questo progetto

Un sistema di analisi predittiva per la ristorazione che risponde a due domande:

1. **Quanti coperti faremo domani?** — Pipeline A: Demand Forecasting
2. **Quanto ci costerà uno shock energetico?** — Pipeline B: Energy Pass-Through Analysis

Costruito da un data analyst con 20 anni di esperienza HoReCa. L'obiettivo è portare decisioni data-driven in un settore che ancora si affida all'istinto.

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
| EICMA 2023 | −56.4 (drain) | Milano attrae la clientela locale |
| GP Italia F1 2023 | −54.4 (drain) | Il pubblico F1 va a Monza/Milano, Como si svuota |
| Milano Fashion Week | +48.6 (pull) | Fashion buyer usano Como come base |
| Mercatini di Natale Como | +46.0 (pull) | Evento locale, day-tripper diretti a Como |
| Salone del Mobile / Como 1907 | +45–47 (pull) | Stessa logica Fashion Week |

> **Conclusione:** il segno dell'effetto (pull vs drain) dipende dall'evento specifico, non dalla distanza. Lo stesso tipo di evento può avere effetti opposti. È il modello che impara dai dati, non una regola a priori.

---

## Pipeline B — Energy Scenario (Notebook 05)

Analisi pass-through dello shock energetico 2026 (scenario Iran crisis):

```
energy_price → Δ% energia vs baseline
             → Δ% prezzo menu  (pass-through rate × Δ% energia)
             → margin_compression EUR/day  (energy cost increase − quota trasferita + revenue persa)
```

**Calibrazione FIPE 2022:** +200% energia → +5% prezzi ristorazione → pass-through rate = 0.025.  
Baseline PUN 2026: 117 €/MWh. Energy share su fatturato: 12%.

**Scenari:**

| Scenario | PUN | Δ% energia |
|----------|-----|-----------|
| A — Tensione lieve | 150 €/MWh | +28.2% |
| B — Shock moderato | 250 €/MWh | +113.7% |
| C — Shock severo | 300 €/MWh | +156.4% |

**Demand Response — due segmenti di clientela:**

| Segmento | Elasticità (ε) | PT rate | Strategia |
|----------|---------------|---------|-----------|
| Turistico | −0.25 | 0.050 | Trasferisci al menu — tollera aumenti |
| Locals | −0.70 | 0.015 | Assorbi nel margine — price-sensitive |

**Compressione margine totale (EUR/day · EUR/anno):**

| Scenario | Turistico | Locals |
|----------|-----------|--------|
| A — 150 €/MWh | ~45 / ~16,400 | ~63 / ~23,000 |
| B — 250 €/MWh | ~181 / ~66,100 | ~254 / ~92,700 |
| C — 300 €/MWh | ~249 / ~90,900 | ~349 / ~127,400 |

**Leve operative per scenario** (con timeframe e KPI): ottimizzazione turni staff · menu engineering · rinegoziazione fornitori.

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
- `event_pull` del GP Monza corretto a −1 (drain) dopo analisi peak — da rivalidare con dati POS reali

---

## Autore

**Giovanni Lopresti** — Data Analyst | HoReCa background 20 anni  
Progetto personale per portare decisioni data-driven nella ristorazione.
