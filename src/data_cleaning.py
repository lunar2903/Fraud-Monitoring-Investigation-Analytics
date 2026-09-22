import pandas as pd
from pathlib import Path


# ==========================================
# 1. Load raw dataset
# ==========================================

input_path = Path(
    "data/PS_20174392719_1491204439457_log.csv"
)

output_path = Path(
    "data/cleaned/paysim_cleaned.csv"
)

df = pd.read_csv(input_path)

print("Raw dataset loaded.")
print(f"Rows: {len(df):,}")


# ==========================================
# 2. Basic cleaning
# ==========================================

# Remove exact duplicate rows
df = df.drop_duplicates()

# Remove records with missing critical fields
critical_columns = [
    "step",
    "type",
    "amount",
    "nameOrig",
    "nameDest",
    "isFraud"
]

df = df.dropna(subset=critical_columns)


# ==========================================
# 3. Validate financial values
# ==========================================

financial_columns = [
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest"
]

for column in financial_columns:
    df = df[df[column] >= 0]


# ==========================================
# 4. Validate transaction types
# ==========================================

valid_types = [
    "CASH_IN",
    "CASH_OUT",
    "DEBIT",
    "PAYMENT",
    "TRANSFER"
]

df = df[df["type"].isin(valid_types)]


# ==========================================
# 5. Validate fraud labels
# ==========================================

df = df[df["isFraud"].isin([0, 1])]
df = df[df["isFlaggedFraud"].isin([0, 1])]


# ==========================================
# 6. Create time features
# ==========================================

# PaySim uses hourly time steps.
df["transaction_hour"] = (df["step"] - 1) % 24

df["transaction_day"] = ((df["step"] - 1) // 24) + 1


def classify_period(hour):
    if 0 <= hour < 6:
        return "Night"
    elif 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 18:
        return "Afternoon"
    else:
        return "Evening"


df["transaction_period"] = df["transaction_hour"].apply(
    classify_period
)


# ==========================================
# 7. Identify merchant transactions
# ==========================================

df["is_merchant_transaction"] = (
    df["nameDest"].str.startswith("M")
).astype(int)


# ==========================================
# 8. Reset index
# ==========================================

df = df.reset_index(drop=True)


# ==========================================
# 9. Save cleaned dataset
# ==========================================

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(output_path, index=False)


# ==========================================
# 10. Cleaning summary
# ==========================================

print("\n===== CLEANING SUMMARY =====")

print(f"Final rows: {len(df):,}")
print(f"Final columns: {len(df.columns)}")

print("\nMissing values:")
print(df.isnull().sum().sum())

print(f"\nDuplicate rows: {df.duplicated().sum():,}")

print("\nFraud distribution:")
print(df["isFraud"].value_counts())

print("\nNew columns:")
print([
    "transaction_hour",
    "transaction_day",
    "transaction_period",
    "is_merchant_transaction"
])

print("\n===== CLEANING COMPLETE =====")
print(f"Saved to: {output_path}")