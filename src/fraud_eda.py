"""Create the seven required EDA charts from compact in-memory aggregates."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _save_bar(labels, values, title, ylabel, path, color, rotation=0, currency=False):
    """Render a concise, consistently formatted bar chart."""
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([str(label) for label in labels], values, color=color)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=rotation)
    ax.grid(axis="y", alpha=0.25)
    if currency:
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda value, _: f"{value / 1_000_000:,.0f}M")
        )
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def create_eda_charts(type_agg, hour_agg, amount_band_agg, risk_agg, queue_summary, output_dir):
    """Save only the requested charts; all inputs are compact aggregate tables."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    type_agg = type_agg.copy()
    type_agg["fraud_rate_percent"] = (
        100 * type_agg["fraud_count"] / type_agg["transaction_count"]
    )
    _save_bar(
        type_agg["type"], type_agg["fraud_rate_percent"],
        "Fraud Rate by Transaction Type", "Fraud rate (%)",
        output_dir / "fraud_rate_by_transaction_type.png", "#2a6fbb", 20,
    )
    _save_bar(
        hour_agg["transaction_hour"], hour_agg["fraud_rate_percent"],
        "Fraud Rate by Transaction Hour", "Fraud rate (%)",
        output_dir / "fraud_rate_by_hour.png", "#3b8c6e",
    )
    _save_bar(
        type_agg["type"], type_agg["fraud_amount"],
        "Fraud Amount by Transaction Type", "Fraud amount (millions)",
        output_dir / "fraud_amount_by_type.png", "#9a4f2f", 20, True,
    )
    _save_bar(
        amount_band_agg["amount_band"], amount_band_agg["fraud_rate_percent"],
        "Fraud Rate by Amount Band", "Fraud rate (%)",
        output_dir / "fraud_rate_by_amount_band.png", "#7d5ba6", 20,
    )

    risk_agg = risk_agg.set_index("risk_category").reindex(RISK_ORDER).reset_index()
    _save_bar(
        risk_agg["risk_category"], risk_agg["transaction_count"],
        "Risk Category Distribution", "Transaction count",
        output_dir / "risk_category_distribution.png", "#4f86c6",
    )
    _save_bar(
        risk_agg["risk_category"], risk_agg["fraud_count"],
        "Fraud Count by Risk Category", "Fraud count",
        output_dir / "fraud_by_risk_category.png", "#c94c4c",
    )

    queue_plot = queue_summary.set_index("risk_category").reindex(["HIGH", "CRITICAL"], fill_value=0).reset_index()
    _save_bar(
        queue_plot["risk_category"], queue_plot["total_amount"],
        "Investigation Queue Amount by Risk Category", "Amount (millions)",
        output_dir / "investigation_amount_by_risk_category.png", "#d18c2d", 0, True,
    )
