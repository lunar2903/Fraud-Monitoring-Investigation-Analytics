"""Evaluate the approved fraud-signal intersections in one CSV pass.

This intentionally reads only the columns required for the four requested
combinations and does not create a fraud risk score or investigation queue.
"""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/cleaned/paysim_cleaned.csv")
OUTPUT_DIR = Path("data/output")
COMBINATIONS_FILE = OUTPUT_DIR / "fraud_signal_combinations.csv"
SUMMARY_FILE = OUTPUT_DIR / "fraud_signal_summary.csv"
REPORT_FILE = OUTPUT_DIR / "fraud_signal_engineering_report.md"

# These are deliberately identical to the approved definitions in
# src/fraud_signals.py.  The plus sign in each combination means AND.
COMBINATIONS = {
    "high_amount_signal + night_transaction_signal": (
        "high_amount_signal",
        "night_transaction_signal",
    ),
    "high_amount_signal + risky_type_signal": (
        "high_amount_signal",
        "risky_type_signal",
    ),
    "night_transaction_signal + risky_type_signal": (
        "night_transaction_signal",
        "risky_type_signal",
    ),
    "high_amount_signal + night_transaction_signal + risky_type_signal": (
        "high_amount_signal",
        "night_transaction_signal",
        "risky_type_signal",
    ),
}


def build_signal_summary() -> pd.DataFrame:
    """Return the final architecture established by the signal analysis."""
    return pd.DataFrame(
        [
            {
                "Signal": "High Amount",
                "Type": "Primary",
                "Reason": "Highest practical individual fraud concentration among primary signals.",
                "Evidence": "11,515 flagged; 744 fraud captured; 6.4611% fraud rate; 9.0588% capture.",
            },
            {
                "Signal": "Night Transaction",
                "Type": "Primary",
                "Reason": "Strong fraud concentration with meaningful fraud capture.",
                "Evidence": "44,438 flagged; 2,054 fraud captured; 4.6222% fraud rate; 25.0091% capture.",
            },
            {
                "Signal": "Risky Transaction Type",
                "Type": "Contextual",
                "Reason": "Captures all known fraud but flags a very large population.",
                "Evidence": "2,770,409 flagged; 8,213 fraud captured; 0.2965% fraud rate; 100.0000% capture.",
            },
            {
                "Signal": "Existing Fraud Flag",
                "Type": "Existing System Indicator",
                "Reason": "Perfect observed precision, but very limited coverage.",
                "Evidence": "16 flagged; 16 fraud captured; 100.0000% fraud rate; 0.1948% capture.",
            },
            {
                "Signal": "Balance Depletion",
                "Type": "Exclude as standalone signal",
                "Reason": "Alert volume is too high for its fraud concentration.",
                "Evidence": "1,985,211 flagged; 4,115 fraud captured; 0.2073% fraud rate; 50.1035% capture.",
            },
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Single efficient scan: load only fields used by the approved definitions.
    df = pd.read_csv(
        INPUT_FILE,
        usecols=["amount", "transaction_period", "type", "isFraud"],
    )
    total_fraud = int(df["isFraud"].sum())
    if total_fraud == 0:
        raise ValueError("Cannot evaluate signal capture: isFraud contains no fraud rows.")

    signals = {
        "high_amount_signal": df["amount"].ge(5_000_000),
        "night_transaction_signal": df["transaction_period"].eq("Night"),
        "risky_type_signal": df["type"].isin(["TRANSFER", "CASH_OUT"]),
    }

    results = []
    for combination, names in COMBINATIONS.items():
        mask = signals[names[0]].copy()
        for name in names[1:]:
            mask &= signals[name]

        flagged_transactions = int(mask.sum())
        fraud_captured = int(df.loc[mask, "isFraud"].sum())
        results.append(
            {
                "signal_combination": combination,
                "flagged_transactions": flagged_transactions,
                "fraud_captured": fraud_captured,
                "signal_fraud_rate_percent": round(
                    100 * fraud_captured / flagged_transactions, 4
                ) if flagged_transactions else 0.0,
                "fraud_capture_rate_percent": round(
                    100 * fraud_captured / total_fraud, 4
                ),
            }
        )

    combinations = pd.DataFrame(results)
    combinations.to_csv(COMBINATIONS_FILE, index=False)

    summary = build_signal_summary()
    summary.to_csv(SUMMARY_FILE, index=False)

    strongest_rate = combinations["signal_fraud_rate_percent"].max()
    strongest = combinations.loc[
        combinations["signal_fraud_rate_percent"].eq(strongest_rate)
    ]
    strongest_names = " and ".join(
        f"**{name}**" for name in strongest["signal_combination"]
    )
    combination_table = "\n".join(
        "| {signal_combination} | {flagged_transactions:,} | {fraud_captured:,} | "
        "{signal_fraud_rate_percent:.4f}% | {fraud_capture_rate_percent:.4f}% |".format(
            **row
        )
        for row in results
    )
    report = f"""# Fraud Signal Engineering

## Objective

Evaluate the four approved AND-combinations of the established fraud signals without building a risk score, queue, BI report, or model.

## Existing Signals

High Amount (amount >= 5,000,000), Night Transaction (transaction period is Night), Risky Transaction Type (TRANSFER or CASH_OUT), Existing Fraud Flag, and Balance Depletion were previously evaluated.

## Signal Performance

High Amount flagged 11,515 transactions at a 6.4611% fraud rate and captured 9.0588% of fraud. Night Transaction flagged 44,438 at a 4.6222% fraud rate and captured 25.0091%. Risky Transaction Type captured 100.0000% of fraud but flagged 2,770,409 transactions at 0.2965%. Existing Fraud Flag had 100.0000% precision but captured 0.1948%. Balance Depletion flagged 1,985,211 transactions at 0.2073%.

## Signal Combination Performance

| Combination (AND) | Flagged | Fraud captured | Fraud rate | Fraud capture |
|---|---:|---:|---:|---:|
{combination_table}

The highest fraud concentration is a tie between {strongest_names}: each flags 190 transactions, captures 168 fraud cases, has an 88.4211% fraud rate, and captures 2.0455% of all fraud. The three-signal result is identical because every high-amount night transaction is already a risky transaction type in this dataset. For broader practical coverage, Night Transaction + Risky Transaction Type captures 25.0091% of fraud at a 19.0981% fraud rate.

## Recommended Signals

Use High Amount and Night Transaction as primary signals. Use Risky Transaction Type as contextual evidence because it provides broad coverage but substantial alert volume. Retain Existing Fraud Flag as an existing-system indicator.

## Signals Excluded

Do not use Balance Depletion as a standalone alert: it flags nearly two million transactions with only a 0.2073% fraud rate.

## Key Findings

The intersections test concentration against fraud capture. A high fraud rate alone is not sufficient if it captures too little fraud; likewise, broad type-based coverage is not suitable as a standalone alert because of volume.

## Final Signal Architecture

| Signal | Architecture role |
|---|---|
| High Amount | Primary |
| Night Transaction | Primary |
| Risky Transaction Type | Contextual |
| Existing Fraud Flag | Existing System Indicator |
| Balance Depletion | Exclude as standalone signal |
"""
    REPORT_FILE.write_text(report, encoding="utf-8")

    print(combinations.to_string(index=False))
    print(f"\nSaved: {COMBINATIONS_FILE}")
    print(f"Saved: {SUMMARY_FILE}")
    print(f"Saved: {REPORT_FILE}")


if __name__ == "__main__":
    main()
