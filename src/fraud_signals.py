import pandas as pd


# ============================================================
# 1. LOAD CLEANED DATA
# ============================================================

INPUT_FILE = "data/cleaned/paysim_cleaned.csv"

df = pd.read_csv(INPUT_FILE)

print("===== DATA LOADED =====")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# 2. CREATE FRAUD SIGNALS
# ============================================================

# Signal 1: High transaction amount
df["high_amount_signal"] = (
    df["amount"] >= 5_000_000
).astype(int)


# Signal 2: Night-time transaction
df["night_transaction_signal"] = (
    df["transaction_period"] == "Night"
).astype(int)


# Signal 3: Risky transaction type
# PaySim fraud is concentrated in TRANSFER and CASH_OUT.
df["risky_type_signal"] = (
    df["type"].isin(["TRANSFER", "CASH_OUT"])
).astype(int)


# Signal 4: Existing system fraud flag
df["existing_flag_signal"] = (
    df["isFlaggedFraud"] == 1
).astype(int)


# Signal 5: Balance depletion
# Candidate signal: CASH_OUT that leaves originator balance at zero.
df["balance_depletion_signal"] = (
    (df["type"] == "CASH_OUT") &
    (df["newbalanceOrig"] == 0)
).astype(int)


# ============================================================
# 3. SIGNAL PERFORMANCE FUNCTION
# ============================================================

def evaluate_signal(dataframe, signal_column):

    total_flagged = dataframe[signal_column].sum()

    fraud_captured = dataframe.loc[
        dataframe[signal_column] == 1,
        "isFraud"
    ].sum()

    total_fraud = dataframe["isFraud"].sum()

    signal_fraud_rate = (
        100 * fraud_captured / total_flagged
        if total_flagged > 0
        else 0
    )

    fraud_capture_rate = (
        100 * fraud_captured / total_fraud
        if total_fraud > 0
        else 0
    )

    return {
        "signal": signal_column,
        "flagged_transactions": total_flagged,
        "fraud_captured": fraud_captured,
        "signal_fraud_rate_percent": round(signal_fraud_rate, 4),
        "fraud_capture_rate_percent": round(fraud_capture_rate, 4)
    }


# ============================================================
# 4. EVALUATE ALL SIGNALS
# ============================================================

signal_columns = [
    "high_amount_signal",
    "night_transaction_signal",
    "risky_type_signal",
    "existing_flag_signal",
    "balance_depletion_signal"
]

results = []

for signal in signal_columns:
    results.append(
        evaluate_signal(df, signal)
    )


signal_results = pd.DataFrame(results)


# ============================================================
# 5. DISPLAY RESULTS
# ============================================================

print("\n===== FRAUD SIGNAL PERFORMANCE =====")

print(
    signal_results.to_string(index=False)
)


# ============================================================
# 6. SAVE SIGNAL PERFORMANCE
# ============================================================

OUTPUT_FILE = "data/output/fraud_signal_performance.csv"

signal_results.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n===== SIGNAL ANALYSIS COMPLETE =====")
print(f"Saved to: {OUTPUT_FILE}")