# Brazilian Energy Dashboard with ML

A Streamlit dashboard for Brazilian energy market analysis with automated CSV ingestion, PostgreSQL storage, and ML forecasts for BBCE prices.

## Features
- Ingest CSVs (BSO, BBCE, PLD, CMO) into PostgreSQL
- Normalized schema with uniqueness constraints
- Prophet baseline forecasting for BBCE products
- Interactive Streamlit dashboard with indicators and charts

## Project Structure
```
project_root/
  data/
    raw_csv/
    processed/
    database/
  src/
    data_processing/
    database/
    ml_models/
    visualization/
    utils/
  config/
  docs/
  tests/
  main.py
  dashboard.py
  database_setup.sql
  requirements.txt
```

## Setup

### Option A (quick validation): SQLite (no PostgreSQL needed)
Set `DATABASE_URL` in `.env` to a local SQLite file (example in `.env.example`), then run:
```bash
source .venv/bin/activate
python main.py --setup-db --ingest
python main.py --train
python main.py --predict --product "ANU JAN/26 DEZ/26"
streamlit run dashboard.py
```

### Option B: PostgreSQL (recommended for production)

### 1) Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
If `python3 -m venv` fails on Ubuntu/Debian (missing `python3-venv`), use:
```bash
pip3 install --user --break-system-packages virtualenv
python3 -m virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment
```bash
cp .env.example .env
# edit .env with your DB credentials
```

### 3) Start PostgreSQL
Use your local PostgreSQL or run:
```bash
docker-compose up -d db
```

### 4) Apply schema
```bash
python3 main.py --setup-db
```

### 5) Ingest data
```bash
python3 main.py --ingest
```

### 6) Train models
```bash
python3 main.py --train
```

### 7) Generate predictions
```bash
python3 main.py --predict --product "ANU JAN/26 DEZ/26"
```

### 8) Run dashboard
```bash
streamlit run dashboard.py
```

## CSV Expectations
Raw CSVs must be placed in `data/raw_csv/` with the following names:
- `bso.csv`
- `bbce.csv`
- `pld.csv`
- `cmo.csv`

## Notes on Data Processing
- Itaipu generation is added to SE/CO hydro generation.
- NE interchange sign is inverted to keep balance consistent.
- Operational week label uses the `bso` column from BSO files.

## Testing
Basic validation is enforced during ingestion. Add tests under `tests/` for:
- column validation
- interchange sum equals zero
- weekly navigation
- Itaipu adjustment

## Deployment
```bash
docker-compose up --build
```

Streamlit will be available at `http://localhost:8501`.
