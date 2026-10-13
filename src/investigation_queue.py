"""Validate, sort, and summarize the compact HIGH/CRITICAL investigation queue."""

from pathlib import Path

import pandas as pd


QUEUE_COLUMNS = [
    "transaction_id", "step", "transaction_hour", "transaction_period", "type",
    "amount", "nameOrig", "nameDest", "oldbalanceOrg", "newbalanceOrig",
    "oldbalanceDest", "newbalanceDest", "isFraud", "isFlaggedFraud",
    "risk_score", "risk_category", "risk_reasons",
]


def finalize_queue(queue_frames, output_dir):
    """Write a sorted queue and compact validation summary without reading the source CSV."""
    output_dir = Path(output_dir)
    queue = pd.concat(queue_frames, ignore_index=True) if queue_frames else pd.DataFrame(columns=QUEUE_COLUMNS)
    queue = queue[QUEUE_COLUMNS]

    if not queue["risk_category"].isin(["HIGH", "CRITICAL"]).all():
        raise ValueError("Investigation queue contains a non-HIGH/CRITICAL category.")
    if queue[["risk_score", "risk_category"]].isna().any().any():
        raise ValueError("Investigation queue contains a missing risk score or category.")
    if ((queue["risk_score"] > 0) & queue["risk_reasons"].isna()).any():
        raise ValueError("Investigation queue contains a missing risk reason.")

    queue = queue.sort_values(["risk_score", "amount"], ascending=[False, False], kind="mergesort")
    queue.to_csv(output_dir / "investigation_queue.csv", index=False)

    summary = (
        queue.groupby("risk_category", observed=True)
        .agg(
            transaction_count=("transaction_id", "size"),
            total_amount=("amount", "sum"),
            average_amount=("amount", "mean"),
            fraud_count=("isFraud", "sum"),
        )
        .reindex(["CRITICAL", "HIGH"], fill_value=0)
        .reset_index()
    )
    summary["fraud_rate_percent"] = (
        100 * summary["fraud_count"] / summary["transaction_count"].where(summary["transaction_count"] != 0, 1)
    ).round(4)
    summary.to_csv(output_dir / "investigation_queue_summary.csv", index=False)

    return queue, summary


def main():
    """Allow queue-only revalidation without touching the original PaySim CSV."""
    output_dir = Path("data/output")
    queue = pd.read_csv(output_dir / "investigation_queue.csv")
    _, summary = finalize_queue([queue], output_dir)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
