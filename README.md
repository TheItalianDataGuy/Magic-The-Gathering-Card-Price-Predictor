# Magic: The Gathering Price Forecasting Pipeline

An end-to-end **time series data pipeline** for collecting, processing, forecasting, and monitoring Magic: The Gathering card prices.

This project is designed as a **portfolio-grade data engineering / analytics engineering project**, with a strong emphasis on:
- reproducibility
- scalability
- robustness
- clear separation of pipeline stages

rather than on a single complex model.

---

## Project Overview

The pipeline ingests MTG card price data from public APIs, processes it into a clean daily time series, generates **7-day forecasts for all cards**, and records run-level metadata and data quality metrics for traceability.

The system is designed to run:
- locally (Python)
- in containers (Docker)
- under orchestration (Apache Airflow)

---

## Pipeline Stages

### 1. Data Ingestion
**Source:** Scryfall bulk data API  

- Downloads the latest card data snapshot
- Extracts cards with available USD prices
- Appends records to an append-only raw dataset

**Output**
```
data/raw/scryfall_data.csv
```

Each record includes:
- timestamp of ingestion
- card id, name, set, rarity
- USD price

This layer preserves a full audit trail of price snapshots over time.

---

### 2. Data Processing (Daily Aggregation)

Raw price snapshots are transformed into a clean daily dataset suitable for time series forecasting.

Processing logic:
- parse timestamps
- normalise to daily frequency
- group by `(date, card_id)`
- keep the latest observation per day

**Output**
```
data/processed/daily_prices.csv
```

Result:
- one row per card per day
- stable schema
- reproducible inputs for forecasting

---

### 3. Forecasting (Baseline Models)

The pipeline generates **7-day forecasts for every card** using robust statistical baselines.

Forecasting strategy (per card):
- **< 7 observations** → naive last-value forecast  
- **7–13 observations** → 7-day moving average  
- **≥ 14 observations** → EWMA (exponentially weighted moving average)

This tiered approach ensures:
- the pipeline never crashes on short histories
- all cards receive a forecast
- results scale to large numbers of time series

**Output**
```
data/predictions/forecast_7d.csv
```

---

### 4. Run Tracking

Each forecasting run is tracked with a unique run ID.

For every run, the pipeline records:
- input and output paths
- forecast horizon
- number of cards processed
- method breakdown
- timestamp of execution

**Outputs**
```
models/runs/<run_id>/run.json
models/runs/<run_id>/metrics.json
```

This provides full traceability and reproducibility without heavy external tooling.

---

### 5. Data Quality Monitoring (Basic)

Basic **data quality monitoring** is integrated into the forecasting stage.

Checks include:
- expected row counts (cards × forecast horizon)
- missing predictions
- non-positive forecast values
- forecast value ranges
- method distribution

These checks are logged per run and stored alongside tracking metrics.

This monitoring focuses on **pipeline and data integrity**, not model performance or drift (which are planned extensions).

---

## Project Structure

```
.
├── src/
│   ├── data_ingestion/
│   │   ├── fetch_scryfall_prices.py
│   │   └── run_data_pipeline.py
│   ├── processing/
│   │   └── build_daily_dataset.py
│   ├── forecasting/
│   │   └── forecast_all_cards.py
│   ├── monitoring/
│   │   └── data_quality.py
│   └── utils/
│       └── tracking.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── predictions/
│
├── models/
│   └── runs/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## How to Run

### Local execution

```bash
python -m src.processing.build_daily_dataset
python -m src.forecasting.forecast_all_cards
```

### Docker / Airflow
The pipeline is containerised and designed to be orchestrated via Apache Airflow with separate tasks for:
- ingestion
- processing
- forecasting

---

## Design Principles

- **Baseline-first forecasting:** establish robust statistical baselines before introducing complex models  
- **Fail-safe pipeline:** all cards receive forecasts regardless of history length  
- **Clear stage ownership:** each pipeline step is responsible for its own outputs  
- **Traceability:** every run produces metadata and metrics  
- **Extensibility:** advanced models (e.g. ARIMA), backtesting, and drift monitoring can be added without refactoring the core pipeline  

---

## Planned Extensions

- Advanced forecasting models for selected cards (e.g. ARIMA)
- Backtesting and model performance metrics
- Data quality checks on processed inputs
- Alerting and orchestration-level monitoring
- API-based inference services

---

## ARIMA Models (Offline Evaluation)

The repository includes an ARIMA training and evaluation module under `src/training/`.

ARIMA models are **not part of the default forecasting pipeline**. They are evaluated
offline using walk-forward backtesting on a selected subset of cards with sufficient
historical data.

At present, the dataset contains only a single daily observation per card
(due to limited time-series history), therefore **no cards currently meet the
minimum data requirements for ARIMA training**.

The ARIMA evaluation pipeline is fully implemented and will become active
automatically once sufficient multi-day price history is collected.
