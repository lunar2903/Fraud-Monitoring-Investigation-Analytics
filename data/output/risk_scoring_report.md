# Fraud Risk Scoring

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
| LOW | 6,306,850 | 5,576 | 0.0884% |
| MEDIUM | 55,571 | 2,460 | 4.4268% |
| HIGH | 193 | 171 | 88.6010% |
| CRITICAL | 6 | 6 | 100.0000% |

## Investigation Queue

The queue contains 199 HIGH/CRITICAL transactions and is sorted by descending risk score then amount. `isFraud` is included only for retrospective validation because PaySim provides a ground-truth label.

## EDA Findings

The highest transaction-type fraud rate is TRANSFER at 0.7688%. The highest hourly fraud rate is hour 4 at 22.3035%. The highest amount-band fraud rate is 5M+ at 6.4611%.

## Limitations

PaySim is synthetic. The rule weights and category thresholds are transparent business rules rather than calibrated probabilities, and the fraud label would not be available to production investigators.
