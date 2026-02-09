from __future__ import annotations

import argparse
from pathlib import Path

from src.data_processing.pipeline import run_ingestion
from src.database.setup import run_schema
from src.ml_models.predict import forecast_product, write_predictions
from src.ml_models.train import train_all_products_from_year, train_latest_products


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Energy Dashboard pipeline")
    parser.add_argument("--setup-db", action="store_true", help="Apply database schema")
    parser.add_argument("--ingest", action="store_true", help="Ingest CSV data into database")
    parser.add_argument("--train", action="store_true", help="Train Prophet models")
    parser.add_argument("--train-all", action="store_true", help="Train models for all products from a given year")
    parser.add_argument("--min-year", type=int, default=2026, help="Min ano_referencia when using --train-all")
    parser.add_argument("--predict", action="store_true", help="Generate forecasts and store predictions")
    parser.add_argument("--product", type=str, default=None, help="Product name for predictions")
    args = parser.parse_args()

    if args.setup_db:
        run_schema(ROOT / "database_setup.sql")
        print("Schema applied.")

    if args.ingest:
        counts = run_ingestion()
        print(f"Ingestion complete: {counts}")

    if args.train:
        model_dir = ROOT / "data" / "models"
        if args.train_all:
            ids = train_all_products_from_year(model_dir, min_year=args.min_year)
        else:
            ids = train_latest_products(model_dir)
        print(f"Trained models: {ids}")

    if args.predict:
        if not args.product:
            raise SystemExit("--product is required to generate predictions")
        preds = forecast_product(args.product, [1, 4, 12])
        rows = write_predictions(preds)
        print(f"Stored {rows} predictions")


if __name__ == "__main__":
    main()
