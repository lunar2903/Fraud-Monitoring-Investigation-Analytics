# Fraud Monitoring & Investigation Analytics

### Goal
To analyze mobile-money transactions, identify potential fraud patterns, build an explainable risk-scoring system, and prioritize suspicious transactions for investigation using Python, SQL, and Power BI.

### Code
- [Python analysis and fraud detection scripts](src/)
- [Power BI Dashboard](dashboard_original.pbix)
- [Dataset and supporting files](data/)

### Description
This project uses the PaySim synthetic mobile-money transaction dataset to demonstrate a practical fraud monitoring workflow. It combines transaction analysis, behavioural fraud signals, rule-based risk scoring, and an investigation queue to help analysts prioritize high-risk transactions.

The workflow includes data profiling, cleaning, exploratory analysis, fraud signal evaluation, risk categorization, investigation prioritization, and dashboard development.

### Skills
Fraud analytics, data cleaning, exploratory data analysis, feature engineering, rule-based risk scoring, SQL, KPI development, investigation prioritization, data visualization, and business recommendations.

### Technology
Python, Pandas, Matplotlib, SQL, Power BI, DAX, Git, GitHub, and Git LFS.

### Results
- **6.36 million transactions analyzed:** Profiled 6,362,620 transaction records from the PaySim dataset.
- **8,213 fraudulent transactions:** Evaluated fraud patterns against transaction behaviour and existing fraud labels.
- **Fraud signal analysis:** Compared high-amount, night-transaction, risky-transaction-type, and existing-flag signals.
- **Explainable risk scoring:** Implemented a rule-based score from 0–100 to categorize transactions by fraud risk.
- **Investigation queue:** Prioritized 199 high-risk and critical transactions for review.
- **Risk segmentation:** The high-risk category contained 193 transactions, while the critical category contained 6.
- **Power BI dashboard:** Developed visual reporting for fraud risk categories, signal performance, and investigation prioritization.

### Recommendations
- Prioritize critical and high-risk transactions for manual investigation.
- Combine multiple fraud signals instead of relying on a single indicator.
- Review false positives and missed fraud cases to improve detection rules.
- Monitor fraud capture rate, precision, and investigation workload as rules evolve.
- Treat automated risk scores as decision-support tools rather than definitive proof of fraud.

### Limitations
The PaySim dataset is synthetic and may not reflect real-world banking fraud patterns. The rule-based scoring system is not a production fraud detection model. Risk scores indicate suspicious behaviour, not confirmed fraud, and the results require validation before real-world deployment.

### Repository Structure

```text
Fraud-Monitoring-Investigation-Analytics/
├── dashboard_original.Report/
├── dashboard_original.SemanticModel/
├── data/
├── src/
├── .gitattributes
├── .gitignore
├── dashboard_original.pbip
├── dashboard_original.pbix
└── README.md
```

### How to Run
1. Clone the repository:
   ```bash
   git clone [<repository-url>](https://github.com/lunar2903/Fraud-Monitoring-Investigation-Analytics.git)
   ```
2. Install the Python dependencies required by the scripts.
3. Ensure Git LFS is installed to retrieve the large CSV dataset.
4. Run the data preparation and fraud analysis scripts in `src/`.
5. Open `dashboard_original.pbix` in Power BI Desktop to explore the dashboard.

---

**Project:** Fraud Monitoring & Investigation Analytics

**Dataset:** PaySim Synthetic Mobile-Money Transactions

**Tools:** Python · SQL · Power BI · Git
