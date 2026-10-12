import logging
from typing import Dict, List, Tuple
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("FinSight.DataQuality")


class TransactionContract(BaseModel):
    """Data Contract for raw financial transaction records."""

    transaction_id: str = Field(..., min_length=5)
    account_id: str = Field(..., min_length=4)
    amount: float = Field(..., gt=0.0)  # Rule: Amount must be strictly > 0
    currency: str = Field(..., min_length=3, max_length=3)
    transaction_type: str
    status: str
    timestamp: str


def validate_transaction_batch(
    records: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """Validates records against schema contracts.

    Returns (valid_records, quarantined_records).
    """
    valid = []
    quarantined = []

    for record in records:
        try:
            validated_record = TransactionContract(**record)
            valid.append(validated_record.model_dump())
        except ValidationError as e:
            logger.warning(
                "Data Quality Violation | ID: %s | Error: %s",
                record.get("transaction_id", "UNKNOWN"),
                e.errors()[0]["msg"],
            )
            quarantined.append(record)

    logger.info(
        "Data Quality Gate Passed | Valid: %d | Quarantined: %d",
        len(valid),
        len(quarantined),
    )
    return valid, quarantined