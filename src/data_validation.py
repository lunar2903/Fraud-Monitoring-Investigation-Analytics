import pandas as pd
from pathlib import Path


# ==========================================
# 1. Load raw dataset
# ==========================================

file_path = Path(
    "data/PS_20174392719_1491204439457_log.csv"
)

df = pd.read_csv(file_path)


# ==========================================
# 2. Zero-value transactions
# ==========================================

print("\n===== ZERO-VALUE TRANSACTIONS =====")

zero_amount = df[df["amount"] == 0]

print(f"Zero-value transactions: {len(zero_amount):,}")

print("\nZero-value transactions by type:")
print(zero_amount["type"].value_counts())

print("\nZero-value transactions by fraud status:")
print(zero_amount["isFraud"].value_counts())


# ==========================================
# 3. Negative values
# ==========================================

print("\n===== NEGATIVE VALUES =====")

numeric_columns = [
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest"
]

for column in numeric_columns:
    count = (df[column] < 0).sum()
    print(f"{column}: {count:,} negative values")


# ==========================================
# 4. Invalid fraud values
# ==========================================

print("\n===== FRAUD FLAG VALIDATION =====")

print("isFraud unique values:")
print(sorted(df["isFraud"].unique()))

print("\nisFlaggedFraud unique values:")
print(sorted(df["isFlaggedFraud"].unique()))


# ==========================================
# 5. Invalid transaction types
# ==========================================

print("\n===== TRANSACTION TYPE VALIDATION =====")

valid_types = {
    "CASH_IN",
    "CASH_OUT",
    "DEBIT",
    "PAYMENT",
    "TRANSFER"
}

invalid_types = df.loc[
    ~df["type"].isin(valid_types),
    "type"
]

print(f"Invalid transaction types: {len(invalid_types):,}")

if len(invalid_types) > 0:
    print(invalid_types.value_counts())


# ==========================================
# 6. Step validation
# ==========================================

print("\n===== STEP VALIDATION =====")

print(f"Minimum step: {df['step'].min()}")
print(f"Maximum step: {df['step'].max()}")

invalid_steps = (df["step"] <= 0).sum()

print(f"Invalid steps (<= 0): {invalid_steps:,}")


# ==========================================
# 7. Balance consistency
# ==========================================

print("\n===== BALANCE CONSISTENCY =====")

# For the originator:
# old balance - transaction amount
# should generally relate to new balance.

originator_difference = (
    df["oldbalanceOrg"]
    - df["amount"]
    - df["newbalanceOrig"]
)

print(
    "Originator balance difference statistics:"
)

print(originator_difference.describe())


# ==========================================
# 8. Destination balance consistency
# ==========================================

destination_difference = (
    df["oldbalanceDest"]
    + df["amount"]
    - df["newbalanceDest"]
)

print(
    "\nDestination balance difference statistics:"
)

print(destination_difference.describe())


# ==========================================
# 9. Suspicious balance relationships
# ==========================================

print("\n===== BALANCE ANOMALIES =====")

originator_anomaly = (
    originator_difference.abs() > 0.01
).sum()

destination_anomaly = (
    destination_difference.abs() > 0.01
).sum()

print(
    f"Originator balance inconsistencies: "
    f"{originator_anomaly:,}"
)

print(
    f"Destination balance inconsistencies: "
    f"{destination_anomaly:,}"
)


# ==========================================
# 10. Final validation summary
# ==========================================

print("\n===== VALIDATION COMPLETE =====")

# ==========================================
# 11. Balance consistency by transaction type
# ==========================================

print("\n===== BALANCE DIFFERENCE BY TRANSACTION TYPE =====")

balance_analysis = (
    df.groupby("type")
    .agg(
        transactions=("type", "size"),
        avg_originator_diff=("originator_difference", "mean")
        if "originator_difference" in df.columns
        else ("amount", "mean")
    )
)

# Recalculate differences directly
df["originator_difference"] = (
    df["oldbalanceOrg"]
    - df["amount"]
    - df["newbalanceOrig"]
)

df["destination_difference"] = (
    df["oldbalanceDest"]
    + df["amount"]
    - df["newbalanceDest"]
)

balance_analysis = (
    df.groupby("type")
    .agg(
        transactions=("type", "size"),
        avg_originator_difference=("originator_difference", "mean"),
        avg_destination_difference=("destination_difference", "mean")
    )
)

print(balance_analysis)


# ==========================================
# 12. Merchant destination analysis
# ==========================================

print("\n===== DESTINATION ACCOUNT PATTERNS =====")

merchant_accounts = df["nameDest"].str.startswith("M")

print(
    f"Transactions going to merchant accounts: "
    f"{merchant_accounts.sum():,}"
)

print(
    f"Transactions going to non-merchant accounts: "
    f"{(~merchant_accounts).sum():,}"
)


# ==========================================
# 13. Fraud balance analysis
# ==========================================

print("\n===== FRAUD BALANCE ANALYSIS =====")

fraud_balance = (
    df[df["isFraud"] == 1]
    .groupby("type")
    .agg(
        fraud_transactions=("isFraud", "size"),
        avg_amount=("amount", "mean"),
        avg_oldbalance_org=("oldbalanceOrg", "mean"),
        avg_newbalance_org=("newbalanceOrig", "mean"),
        avg_oldbalance_dest=("oldbalanceDest", "mean"),
        avg_newbalance_dest=("newbalanceDest", "mean")
    )
)

print(fraud_balance)