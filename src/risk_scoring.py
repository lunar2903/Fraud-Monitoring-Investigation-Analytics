"""One-pass, chunked rule-based fraud scoring with compact EDA aggregation."""

from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from fraud_eda import create_eda_charts
from investigation_queue import QUEUE_COLUMNS, finalize_queue


INPUT_FILE = Path("data/cleaned/paysim_cleaned.csv")
OUTPUT_DIR = Path("data/output")
CHUNK_SIZE = 100_000
TOTAL_EXPECTED_ROWS = 6_362_620
TOTAL_EXPECTED_FRAUD = 8_213
EXPECTED_FRAUD_AMOUNT = 12_056_415_427.84

WEIGHTS = {
    "High Amount": 30,
    "Night Transaction": 25,
    "Risky Transaction Type": 10,
    "Existing Fraud Flag": 35,
}
RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
AMOUNT_BANDS = ["Under 10K", "10K-100K", "100K-1M", "1M-5M", "5M+"]
USECOLS = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg", "newbalanceOrig",
    "nameDest", "oldbalanceDest", "newbalanceDest", "isFraud", "isFlaggedFraud",
    "transaction_hour", "transaction_period",
]


def _update(aggregate, keys, fraud, amount):
    """Update a low-cardinality aggregate using a per-chunk grouped reduction."""
    frame = pd.DataFrame({
        "key": keys,
        "transaction_count": 1,
        "fraud_count": fraud.astype("int64"),
        "fraud_amount": np.where(fraud, amount, 0.0),
        "total_amount": amount,
    })
    for key, row in frame.groupby("key", observed=True).sum(numeric_only=True).iterrows():
        values = aggregate[key]
        values["transaction_count"] += int(row["transaction_count"])
        values["fraud_count"] += int(row["fraud_count"])
        values["fraud_amount"] += float(row["fraud_amount"])
        values["total_amount"] += float(row["total_amount"])


def _to_frame(aggregate, key_name, order):
    rows = []
    for key in order:
        value = aggregate[key]
        rows.append({key_name: key, **value})
    return pd.DataFrame(rows)


def _risk_reasons(high, night, risky, existing):
    """Build deterministic, human-readable reasons without row-wise DataFrame apply."""
    reasons = np.full(len(high), "None", dtype=object)
    for mask, label in [
        (high, "High Amount"),
        (night, "Night Transaction"),
        (risky, "Risky Transaction Type"),
        (existing, "Existing Fraud Flag"),
    ]:
        current = reasons[mask]
        reasons[mask] = np.where(current == "None", label, current + "; " + label)
    return reasons


def _amount_band(amount):
    return np.select(
        [amount < 10_000, amount < 100_000, amount < 1_000_000, amount < 5_000_000],
        AMOUNT_BANDS[:-1],
        default=AMOUNT_BANDS[-1],
    )


def _write_report(risk_summary, queue_summary, type_agg, hour_agg, amount_band_agg, validation):
    distribution = "\n".join(
        f"| {row.risk_category} | {int(row.transaction_count):,} | {int(row.fraud_count):,} | {row.fraud_rate_percent:.4f}% |"
        for row in risk_summary.itertuples(index=False)
    )
    type_agg = type_agg.assign(fraud_rate_percent=100 * type_agg.fraud_count / type_agg.transaction_count)
    highest_type = type_agg.loc[type_agg.fraud_rate_percent.idxmax()]
    highest_hour = hour_agg.loc[hour_agg.fraud_rate_percent.idxmax()]
    highest_band = amount_band_agg.loc[amount_band_agg.fraud_rate_percent.idxmax()]
    queue_total = int(queue_summary.transaction_count.sum())
    report = f"""# Fraud Risk Scoring

## Objective

Create a deterministic, explainable 0–100 rule-based fraud score, retain only HIGH and CRITICAL cases for investigation, and generate compact EDA outputs in one chunked source-data pass.

## Scoring Methodology

No machine learning was used. Scores are transparent expert rules informed by the observed fraud-signal performance; they are not statistically optimized model coefficients.

## Signal Weights

| Signal | Points |
|---|---:|
| High Amount | 30 |
| Night Transaction | 25 |
| Risky Transaction Type | 10 |
| Existing Fraud Flag | 35 |

## Risk Categories

LOW: 0–24; MEDIUM: 25–49; HIGH: 50–74; CRITICAL: 75–100.

## Score Distribution

| Risk category | Transactions | Fraud count | Fraud rate |
|---|---:|---:|---:|
{distribution}

## Investigation Queue

The queue contains {queue_total:,} HIGH/CRITICAL transactions and is sorted by descending risk score then amount. `isFraud` is included only for retrospective validation because PaySim provides a ground-truth label.

## EDA Findings

The highest transaction-type fraud rate is {highest_type['type']} at {highest_type['fraud_rate_percent']:.4f}%. The highest hourly fraud rate is hour {int(highest_hour['transaction_hour'])} at {highest_hour['fraud_rate_percent']:.4f}%. The highest amount-band fraud rate is {highest_band['amount_band']} at {highest_band['fraud_rate_percent']:.4f}%.

## Limitations

PaySim is synthetic. The rule weights and category thresholds are transparent business rules rather than calibrated probabilities, and the fraud label would not be available to production investigators.
"""
    (OUTPUT_DIR / "risk_scoring_report.md").write_text(report, encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    type_aggregate = defaultdict(lambda: defaultdict(float))
    hour_aggregate = defaultdict(lambda: defaultdict(float))
    band_aggregate = defaultdict(lambda: defaultdict(float))
    risk_aggregate = defaultdict(lambda: defaultdict(float))
    queue_frames = []
    processed_rows = 0
    total_fraud = 0
    total_fraud_amount = 0.0
    min_score = 100
    max_score = 0

    for chunk in pd.read_csv(INPUT_FILE, usecols=USECOLS, chunksize=CHUNK_SIZE):
        size = len(chunk)
        transaction_ids = np.arange(processed_rows, processed_rows + size, dtype=np.int64)
        processed_rows += size

        high = chunk["amount"].ge(5_000_000).to_numpy()
        night = chunk["transaction_period"].eq("Night").to_numpy()
        risky = chunk["type"].isin(["TRANSFER", "CASH_OUT"]).to_numpy()
        existing = chunk["isFlaggedFraud"].eq(1).to_numpy()
        fraud = chunk["isFraud"].to_numpy(dtype=bool)
        amount = chunk["amount"].to_numpy()

        score = (high * WEIGHTS["High Amount"] + night * WEIGHTS["Night Transaction"]
                 + risky * WEIGHTS["Risky Transaction Type"] + existing * WEIGHTS["Existing Fraud Flag"]).astype(np.int16)
        category = np.select(
            [score >= 75, score >= 50, score >= 25],
            ["CRITICAL", "HIGH", "MEDIUM"],
            default="LOW",
        )
        reasons = _risk_reasons(high, night, risky, existing)

        min_score = min(min_score, int(score.min()))
        max_score = max(max_score, int(score.max()))
        total_fraud += int(fraud.sum())
        total_fraud_amount += float(amount[fraud].sum())

        _update(type_aggregate, chunk["type"].to_numpy(), fraud, amount)
        _update(hour_aggregate, chunk["transaction_hour"].to_numpy(), fraud, amount)
        _update(band_aggregate, _amount_band(amount), fraud, amount)
        _update(risk_aggregate, category, fraud, amount)

        retain = np.isin(category, ["HIGH", "CRITICAL"])
        if retain.any():
            queue_chunk = chunk.loc[retain, [column for column in QUEUE_COLUMNS if column in chunk.columns]].copy()
            queue_chunk.insert(0, "transaction_id", transaction_ids[retain])
            queue_chunk["risk_score"] = score[retain]
            queue_chunk["risk_category"] = category[retain]
            queue_chunk["risk_reasons"] = reasons[retain]
            queue_frames.append(queue_chunk[QUEUE_COLUMNS])

    type_agg = _to_frame(type_aggregate, "type", sorted(type_aggregate))
    hour_agg = _to_frame(hour_aggregate, "transaction_hour", list(range(24)))
    hour_agg["fraud_rate_percent"] = 100 * hour_agg["fraud_count"] / hour_agg["transaction_count"]
    band_agg = _to_frame(band_aggregate, "amount_band", AMOUNT_BANDS)
    band_agg["fraud_rate_percent"] = 100 * band_agg["fraud_count"] / band_agg["transaction_count"]
    risk_agg = _to_frame(risk_aggregate, "risk_category", RISK_ORDER)
    risk_summary = risk_agg[["risk_category", "transaction_count", "fraud_count", "total_amount"]].copy()
    risk_summary["transaction_count"] = risk_summary["transaction_count"].astype("int64")
    risk_summary["fraud_count"] = risk_summary["fraud_count"].astype("int64")
    risk_summary["fraud_rate_percent"] = (100 * risk_summary["fraud_count"] / risk_summary["transaction_count"]).round(4)
    risk_summary["average_amount"] = risk_summary["total_amount"] / risk_summary["transaction_count"]
    risk_summary = risk_summary[["risk_category", "transaction_count", "fraud_count", "fraud_rate_percent", "total_amount", "average_amount"]]
    risk_summary.to_csv(OUTPUT_DIR / "risk_scoring_summary.csv", index=False)

    queue, queue_summary = finalize_queue(queue_frames, OUTPUT_DIR)
    create_eda_charts(type_agg, hour_agg, band_agg, risk_agg, queue_summary, OUTPUT_DIR / "eda")

    validations = {
        "processed_rows": processed_rows == TOTAL_EXPECTED_ROWS,
        "total_fraud": total_fraud == TOTAL_EXPECTED_FRAUD,
        "fraud_aggregate_reconciliation": int(type_agg["fraud_count"].sum()) == total_fraud,
        "fraud_amount_reconciliation": abs(total_fraud_amount - EXPECTED_FRAUD_AMOUNT) < 0.01,
        "queue_categories": queue["risk_category"].isin(["HIGH", "CRITICAL"]).all(),
        "queue_scores_present": not queue["risk_score"].isna().any(),
        "queue_categories_present": not queue["risk_category"].isna().any(),
        "queue_reasons_present": not queue.loc[queue["risk_score"] > 0, "risk_reasons"].isna().any(),
    }
    if not all(validations.values()):
        failed = [name for name, passed in validations.items() if not passed]
        raise ValueError(f"Validation failed: {', '.join(failed)}")

    _write_report(risk_summary, queue_summary, type_agg, hour_agg, band_agg, validations)
    print(f"Processed rows: {processed_rows:,}")
    print(f"Fraud rows: {total_fraud:,}")
    print(f"Risk score range: {min_score}-{max_score}")
    print(risk_summary.to_string(index=False))
    print(f"Investigation queue size: {len(queue):,}")


if __name__ == "__main__":
    main()
