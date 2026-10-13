# Fraud Signal Engineering

## Objective

Evaluate the four approved AND-combinations of the established fraud signals without building a risk score, queue, BI report, or model.

## Existing Signals

High Amount (amount >= 5,000,000), Night Transaction (transaction period is Night), Risky Transaction Type (TRANSFER or CASH_OUT), Existing Fraud Flag, and Balance Depletion were previously evaluated.

## Signal Performance

High Amount flagged 11,515 transactions at a 6.4611% fraud rate and captured 9.0588% of fraud. Night Transaction flagged 44,438 at a 4.6222% fraud rate and captured 25.0091%. Risky Transaction Type captured 100.0000% of fraud but flagged 2,770,409 transactions at 0.2965%. Existing Fraud Flag had 100.0000% precision but captured 0.1948%. Balance Depletion flagged 1,985,211 transactions at 0.2073%.

## Signal Combination Performance

| Combination (AND) | Flagged | Fraud captured | Fraud rate | Fraud capture |
|---|---:|---:|---:|---:|
| high_amount_signal + night_transaction_signal | 190 | 168 | 88.4211% | 2.0455% |
| high_amount_signal + risky_type_signal | 11,515 | 744 | 6.4611% | 9.0588% |
| night_transaction_signal + risky_type_signal | 10,755 | 2,054 | 19.0981% | 25.0091% |
| high_amount_signal + night_transaction_signal + risky_type_signal | 190 | 168 | 88.4211% | 2.0455% |

The highest fraud concentration is a tie between **high_amount_signal + night_transaction_signal** and **high_amount_signal + night_transaction_signal + risky_type_signal**: each flags 190 transactions, captures 168 fraud cases, has an 88.4211% fraud rate, and captures 2.0455% of all fraud. The three-signal result is identical because every high-amount night transaction is already a risky transaction type in this dataset. For broader practical coverage, Night Transaction + Risky Transaction Type captures 25.0091% of fraud at a 19.0981% fraud rate.

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
