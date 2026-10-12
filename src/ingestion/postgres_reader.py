import csv
import logging
import os
import sys
import time
from pathlib import Path
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values

# Change from relative (..quality) to absolute (src.quality)
from src.quality.expectations import validate_transaction_batch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | [%(name)s] | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("FinSight.Ingestion")

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5433"))
DB_NAME = os.getenv("POSTGRES_DB", "finsight_db")
DB_USER = os.getenv("POSTGRES_USER", "finsight_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "finsight_password")

CSV_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "sample" / "transactions.csv"
)


class PostgresIngestionEngine:

    def __init__(self):
        self.connection_pool = None
        self._init_pool()

    def _init_pool(self, retries: int = 3, backoff_sec: int = 2):
        for attempt in range(1, retries + 1):
            try:
                self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=DB_HOST,
                    port=DB_PORT,
                    dbname=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD,
                )
                logger.info(
                    "Connection pool initialized successfully [Port: %s].",
                    DB_PORT,
                )
                return
            except psycopg2.OperationalError as e:
                logger.warning(
                    "Connection attempt %d failed: %s. Retrying...",
                    attempt,
                    e,
                )
                time.sleep(backoff_sec)
                backoff_sec *= 2
        sys.exit(1)

    def ingest_batch(self):
        if not CSV_PATH.exists():
            logger.error("Ingestion source path not found: %s", CSV_PATH)
            return

        raw_records = []
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["amount"] = float(row["amount"])
                raw_records.append(row)

        valid_records, quarantined_records = validate_transaction_batch(
            raw_records
        )

        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS raw_transactions (
                        transaction_id VARCHAR(50) PRIMARY KEY,
                        account_id VARCHAR(50) NOT NULL,
                        amount NUMERIC(12, 2) NOT NULL,
                        currency VARCHAR(10) NOT NULL,
                        transaction_type VARCHAR(30) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                        ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """
                )

                if valid_records:
                    insert_payload = [
                        (
                            r["transaction_id"],
                            r["account_id"],
                            r["amount"],
                            r["currency"],
                            r["transaction_type"],
                            r["status"],
                            r["timestamp"],
                        )
                        for r in valid_records
                    ]

                    upsert_query = """
                        INSERT INTO raw_transactions (
                            transaction_id, account_id, amount, currency, transaction_type, status, timestamp
                        ) VALUES %s
                        ON CONFLICT (transaction_id) 
                        DO UPDATE SET status = EXCLUDED.status, ingested_at = CURRENT_TIMESTAMP;
                    """
                    execute_values(cursor, upsert_query, insert_payload)

                conn.commit()
                logger.info(
                    "Batch execution completed. Validated & committed %d records.",
                    len(valid_records),
                )

        except Exception as e:
            conn.rollback()
            logger.error("Pipeline failure: %s", e)
            raise e
        finally:
            self.connection_pool.putconn(conn)
            self.connection_pool.closeall()


if __name__ == "__main__":
    engine = PostgresIngestionEngine()
    engine.ingest_batch()