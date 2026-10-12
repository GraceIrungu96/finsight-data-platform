import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Paths
OUTPUT_DIR = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_DIR / "transactions.csv"
JSON_PATH = OUTPUT_DIR / "transactions.json"

# Seed data configurations
TRANSACTION_TYPES = ["SETTLEMENT", "WIRE", "ACH", "CARD_PAYMENT", "FEE"]
STATUSES = ["COMPLETED", "PENDING", "FAILED"]
CURRENCIES = ["USD", "EUR", "GBP"]


def generate_transactions(count=100):
    transactions = []
    base_time = datetime.utcnow() - timedelta(days=7)

    for i in range(1, count + 1):
        txn_time = base_time + timedelta(
            minutes=random.randint(1, 10000), seconds=random.randint(0, 59)
        )
        record = {
            "transaction_id": f"TXN-{100000 + i}",
            "account_id": f"ACC-{random.randint(1000, 1050)}",
            "amount": round(random.uniform(5.00, 15000.00), 2),
            "currency": random.choice(CURRENCIES),
            "transaction_type": random.choice(TRANSACTION_TYPES),
            "status": random.choice(STATUSES),
            "timestamp": txn_time.isoformat(),
        }
        transactions.append(record)
    return transactions


def save_csv(transactions):
    keys = transactions[0].keys()
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(transactions)
    print(
        f"[INFO] Generated {len(transactions)} mock transactions -> {CSV_PATH}"
    )


def save_json(transactions):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2)
    print(
        f"[INFO] Generated {len(transactions)} mock transactions -> {JSON_PATH}"
    )


if __name__ == "__main__":
    data = generate_transactions(100)
    save_csv(data)
    save_json(data)