# MTG Price Forecasting Pipeline

End-to-end data pipeline for collecting and analysing **Magic: The Gathering card prices**, with a focus on data ingestion, orchestration, and future forecasting.

This project is designed as a **portfolio-grade data engineering / MLOps project**, emphasising clean architecture, reproducibility, and extensibility rather than ad-hoc scripts.

---

## Project Goals

- Collect up-to-date MTG card prices from public APIs  
- Store raw price data in a reproducible and auditable way  
- Orchestrate ingestion using **Apache Airflow**  
- Prepare the ground for **price forecasting and monitoring**  
- Demonstrate production-oriented Python practices  

---

## Current Status

### Implemented
- Scryfall bulk data ingestion (USD prices)
- CSV-based raw data storage
- Dockerised environment
- Apache Airflow orchestration
- Logging and error handling
- Environment-variable based configuration

### Planned
- Daily price aggregation
- Baseline forecasting models (moving average / ARIMA)
- Optional market comparison (TCGPlayer, eBay)
- Monitoring and anomaly detection

---

## Project Structure

```
.
├── airflow/
│   ├── dags/                # Airflow DAG definitions
│   ├── logs/
│   ├── data/
│   └── airflow.cfg
│
├── src/
│   ├── data_ingestion/
│   │   ├── fetch_scryfall_prices.py   # Main ingestion source (active)
│   │   ├── fetch_tcgplayer_prices.py  # Optional / future source
│   │   ├── run_data_pipeline.py       # Pipeline entry point
│   │   └── __init__.py
│   │
│   ├── forecasting/          # Planned forecasting module
│   ├── training/             # Planned training module
│   └── monitoring/           # Planned monitoring module
│
├── data/
│   └── raw/                  # Generated raw datasets (gitignored)
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── variables.json            # Airflow variables
└── README.md
```

---

## Data Ingestion

### Scryfall (active)

- Uses the Scryfall bulk data API
- Extracts cards with available USD prices
- Stores records with:
  - timestamp  
  - card name  
  - card ID  
  - set  
  - rarity  
  - USD price  

Example output:

```
data/raw/scryfall_data.csv
```

The ingestion pipeline can be executed:
- locally via Python
- inside Docker
- on a schedule via Airflow

---

## Orchestration (Airflow)

The project includes an Airflow DAG that:
- runs the Scryfall ingestion task
- logs execution details
- is designed to be extended with downstream tasks

Airflow runs using:
- LocalExecutor
- PostgreSQL metadata database
- Docker Compose for reproducibility

---

# Monitoring (planned)

Future work:
- data quality checks (nulls, negative prices, schema drift)
- anomaly detection on price jumps
- Airflow alerts via email

Not implemented yet.

---

# Training (planned)

Future work:
- backtesting utilities
- model selection/benchmarking
- saving artefacts under models/

Not implemented yet.

---

## Configuration

Configuration is handled via environment variables:
- API keys (where required)
- Output paths
- SMTP settings for future alerting

Sensitive data is **not committed** to the repository.

---

## How to Run

### Local (without Airflow)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python src/data_ingestion/fetch_scryfall_prices.py
```

---

### Docker + Airflow

```bash
docker compose up -d
```

Then open the Airflow UI:

```
http://localhost:8080
```

(Login credentials are created during the Airflow init step.)

---

## Why This Project

This project is intentionally scoped to:
- demonstrate **realistic data engineering patterns**
- avoid unnecessary over-engineering
- remain extensible for forecasting and monitoring

It complements model-heavy projects by focusing on **data reliability, orchestration, and maintainability**.

---

## Next Steps

- Aggregate daily prices per card
- Implement simple baseline forecasts
- Add data quality and anomaly checks
- Extend ingestion to additional marketplaces (optional)
