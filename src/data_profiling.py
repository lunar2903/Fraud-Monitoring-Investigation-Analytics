import pandas as pd
from pathlib import Path

# -----------------------------
# 1. Load dataset
# -----------------------------

file_path = Path("data/PS_20174392719_1491204439457_log.csv")

df = pd.read_csv(file_path)

# -----------------------------
# 2. Basic dataset information
# -----------------------------

print("\n===== DATASET SHAPE =====")
print(f"Rows    : {df.shape[0]:,}")
print(f"Columns : {df.shape[1]}")

print("\n===== COLUMN NAMES =====")
print(df.columns.tolist())

# -----------------------------
# 3. Data types
# -----------------------------

print("\n===== DATA TYPES =====")
print(df.dtypes)

# -----------------------------
# 4. Missing values
# -----------------------------

print("\n===== MISSING VALUES =====")
missing = df.isnull().sum()

print(missing[missing > 0])

if missing.sum() == 0:
    print("No missing values found.")

# -----------------------------
# 5. Duplicate rows
# -----------------------------

print("\n===== DUPLICATES =====")
print(f"Duplicate rows: {df.duplicated().sum():,}")

# -----------------------------
# 6. Unique values
# -----------------------------

print("\n===== UNIQUE VALUES =====")

for column in df.columns:
    print(f"{column}: {df[column].nunique():,}")

# -----------------------------
# 7. Transaction types
# -----------------------------

print("\n===== TRANSACTION TYPES =====")
print(df["type"].value_counts())

# -----------------------------
# 8. Fraud distribution
# -----------------------------

print("\n===== FRAUD DISTRIBUTION =====")
print(df["isFraud"].value_counts())

print("\n===== FRAUD PERCENTAGE =====")
fraud_percentage = df["isFraud"].value_counts(normalize=True) * 100
print(fraud_percentage)

# -----------------------------
# 9. Flagged fraud distribution
# -----------------------------

print("\n===== FLAGGED FRAUD =====")
print(df["isFlaggedFraud"].value_counts())

# -----------------------------
# 10. Amount statistics
# -----------------------------

print("\n===== TRANSACTION AMOUNT =====")
print(df["amount"].describe())

# -----------------------------
# 11. Fraud by transaction type
# -----------------------------

print("\n===== FRAUD BY TRANSACTION TYPE =====")

fraud_by_type = (
    df.groupby("type")["isFraud"]
    .agg(["count", "sum", "mean"])
    .sort_values("mean", ascending=False)
)

fraud_by_type["fraud_rate_%"] = fraud_by_type["mean"] * 100

print(fraud_by_type)

# -----------------------------
# 12. Time range
# -----------------------------

print("\n===== TIME RANGE =====")
print(f"Minimum step: {df['step'].min()}")
print(f"Maximum step: {df['step'].max()}")

print("\n===== PROFILING COMPLETE =====")