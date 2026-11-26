"""Reusable cleaning, segmentation, EDA, and reporting functions.

Dataset: IBM Telco Customer Churn sample (7,043 customer records).
The analysis is descriptive; it is not a causal or production churn model.
"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path
from typing import Iterable

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "Telco-Customer-Churn.csv"
DATA_URL = (
    "https://raw.githubusercontent.com/IBM/"
    "telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
)
EXPECTED_SHA256 = "16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91"

SERVICE_COLUMNS = [
    "PhoneService", "MultipleLines", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
]


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for a file, streaming it in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_dataset(destination: Path = DEFAULT_DATA_PATH) -> Path:
    """Download and verify the original IBM CSV sample."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        DATA_URL,
        headers={"User-Agent": "telco-churn-coursework-project/1.0"},
    )
    temporary_path = destination.with_suffix(destination.suffix + ".part")
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            with temporary_path.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
        actual_hash = sha256_file(temporary_path)
        if actual_hash != EXPECTED_SHA256:
            raise ValueError(
                "Downloaded CSV checksum does not match the expected IBM sample. "
                f"Expected {EXPECTED_SHA256}, received {actual_hash}. "
                "Delete the partial file and verify the source before continuing."
            )
        temporary_path.replace(destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return destination


def load_raw_data(path: Path = DEFAULT_DATA_PATH, download_if_missing: bool = True) -> pd.DataFrame:
    """Load the source CSV, downloading it if it is not present."""
    path = Path(path)
    if not path.exists():
        if not download_if_missing:
            raise FileNotFoundError(
                f"Dataset not found at {path}. See data/raw/README.md for instructions."
            )
        print("Dataset not found locally; downloading the IBM Telco Customer Churn CSV...")
        download_dataset(path)
    actual_hash = sha256_file(path)
    if actual_hash != EXPECTED_SHA256:
        raise ValueError(
            "The local CSV is not the verified IBM sample. "
            f"Expected SHA-256 {EXPECTED_SHA256}, received {actual_hash}."
        )
    return pd.read_csv(path)


def clean_and_engineer(raw: pd.DataFrame) -> pd.DataFrame:
    """Clean source fields and create interpretable analysis features."""
    required = {
        "customerID", "tenure", "Contract", "MonthlyCharges", "TotalCharges", "Churn",
        "InternetService", "TechSupport",
    }
    missing_columns = required.difference(raw.columns)
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing_columns)}")

    df = raw.copy()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    # The IBM sample has blank TotalCharges for customers with zero tenure.
    zero_tenure_blanks = df["TotalCharges"].isna() & df["tenure"].eq(0)
    df.loc[zero_tenure_blanks, "TotalCharges"] = 0.0
    df["MonthlyCharges"] = pd.to_numeric(df["MonthlyCharges"], errors="coerce")
    df["tenure"] = pd.to_numeric(df["tenure"], errors="coerce")

    churn_map = {"No": 0, "Yes": 1}
    df["churn_flag"] = df["Churn"].map(churn_map)
    if df["churn_flag"].isna().any():
        unexpected = sorted(df.loc[df["churn_flag"].isna(), "Churn"].dropna().unique())
        raise ValueError(f"Unexpected values in Churn column: {unexpected}")
    df["churn_flag"] = df["churn_flag"].astype(int)

    df["tenure_group"] = pd.cut(
        df["tenure"],
        bins=[-1, 12, 24, 48, 72],
        labels=["0–12 months", "13–24 months", "25–48 months", "49–72 months"],
        include_lowest=True,
    )
    df["service_count"] = 0
    for column in SERVICE_COLUMNS:
        if column not in df.columns:
            continue
        # For the service fields, only an explicit Yes counts as a subscribed service.
        df["service_count"] += df[column].eq("Yes").astype(int)
    return df


def assign_customer_segments(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Assign transparent rule-based segments without using the churn label.

    Rules are applied in priority order:
      1. At-risk: tenure <= 12 months OR month-to-month with high charges / no tech support.
      2. Loyal: tenure >= 48 months and a one- or two-year contract.
      3. High-value: monthly charges at or above the dataset 75th percentile.
      4. Core: all other customers.

    Churn is deliberately excluded from the rules to avoid target leakage.
    """
    result = df.copy()
    value_threshold = float(result["MonthlyCharges"].quantile(0.75))
    month_to_month = result["Contract"].eq("Month-to-month")
    no_tech_support = result["TechSupport"].eq("No")

    at_risk = result["tenure"].le(12) | (
        month_to_month & (result["MonthlyCharges"].ge(value_threshold) | no_tech_support)
    )
    loyal = (
        result["tenure"].ge(48)
        & result["Contract"].isin(["One year", "Two year"])
        & ~at_risk
    )
    high_value = result["MonthlyCharges"].ge(value_threshold) & ~at_risk & ~loyal

    result["customer_segment"] = np.select(
        [at_risk, loyal, high_value],
        ["At-risk", "Loyal", "High-value"],
        default="Core",
    )
    return result, value_threshold


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise segment size, value, tenure, and historical churn rate."""
    summary = (
        df.groupby("customer_segment", observed=True)
        .agg(
            customers=("customerID", "count"),
            share_of_customers=("customerID", lambda s: len(s) / len(df)),
            avg_monthly_charges=("MonthlyCharges", "mean"),
            median_tenure_months=("tenure", "median"),
            churned_customers=("churn_flag", "sum"),
            churn_rate=("churn_flag", "mean"),
        )
        .sort_values("customers", ascending=False)
        .reset_index()
    )
    return summary


def correlation_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build correlation-ready numeric features, one-hot encoding Contract.

    Contract is nominal, so it is represented with indicator columns rather
    than an arbitrary ordinal mapping.
    """
    numeric_columns = [
        column for column in ["SeniorCitizen", "tenure", "MonthlyCharges", "TotalCharges", "service_count", "churn_flag"]
        if column in df.columns
    ]
    result = df[numeric_columns].copy()
    if "Contract" in df.columns:
        contract_dummies = pd.get_dummies(df["Contract"], prefix="Contract", dtype=int)
        result = pd.concat([result, contract_dummies], axis=1)
    return result


def categorical_churn_table(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return category counts and the within-category churn rate."""
    table = (
        df.groupby(column, dropna=False, observed=True)
        .agg(customers=("churn_flag", "size"), churn_rate=("churn_flag", "mean"), churned=("churn_flag", "sum"))
        .reset_index()
        .sort_values("churn_rate", ascending=False)
    )
    table["churn_rate_pct"] = table["churn_rate"] * 100
    return table


def _save_figure(fig: plt.Figure, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(destination, dpi=160, bbox_inches="tight")
    plt.close(fig)


def make_eda_figures(df: pd.DataFrame, figures_dir: Path) -> list[Path]:
    """Create requested distribution, boxplot, heatmap, and segment visuals."""
    sns.set_theme(style="whitegrid", context="notebook")
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    # 1. Overall target balance.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    counts = df["Churn"].value_counts().reindex(["No", "Yes"])
    sns.barplot(x=counts.index, y=counts.values, hue=counts.index, legend=False, ax=ax)
    ax.set(title="Customer churn distribution", xlabel="Churn", ylabel="Number of customers")
    for patch, value in zip(ax.patches, counts.values):
        ax.annotate(f"{value:,}", (patch.get_x() + patch.get_width() / 2, patch.get_height()),
                    ha="center", va="bottom", xytext=(0, 4), textcoords="offset points")
    path = figures_dir / "01_churn_distribution.png"
    _save_figure(fig, path); outputs.append(path)

    # 2. Boxplots requested in the brief.
    box_features = ["tenure", "MonthlyCharges", "TotalCharges"]
    long_box = df.melt(id_vars="Churn", value_vars=box_features, var_name="metric", value_name="value")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for ax, metric in zip(axes, box_features):
        sns.boxplot(data=long_box[long_box["metric"].eq(metric)], x="Churn", y="value", hue="Churn", legend=False, ax=ax)
        ax.set_title(f"{metric} by churn")
        ax.set_xlabel("Churn")
        ax.set_ylabel(metric)
    path = figures_dir / "02_boxplots_by_churn.png"
    _save_figure(fig, path); outputs.append(path)

    # 3. Correlation heatmap for numeric/engineered numeric fields.
    corr = correlation_features(df).corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, square=True, ax=ax)
    ax.set_title("Correlation heatmap (numeric features)")
    path = figures_dir / "03_correlation_heatmap.png"
    _save_figure(fig, path); outputs.append(path)

    # 4. Churn rates by contract, payment, and internet service.
    cat_cols = ["Contract", "PaymentMethod", "InternetService", "TechSupport"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    for ax, column in zip(axes.flat, cat_cols):
        rates = categorical_churn_table(df, column).sort_values("churn_rate")
        sns.barplot(data=rates, x="churn_rate_pct", y=column, hue=column, legend=False, ax=ax)
        ax.set(title=f"Churn rate by {column}", xlabel="Churn rate (%)", ylabel="")
        ax.set_xlim(0, max(10, rates["churn_rate_pct"].max() * 1.15))
    path = figures_dir / "04_categorical_churn_rates.png"
    _save_figure(fig, path); outputs.append(path)

    # 5. Segment-level churn and customer mix.
    order = ["At-risk", "High-value", "Loyal", "Core"]
    seg = df.groupby("customer_segment", observed=True).agg(
        customers=("customerID", "size"), churn_rate=("churn_flag", "mean")
    ).reindex(order).dropna().reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    sns.barplot(data=seg, x="customer_segment", y="customers", hue="customer_segment", legend=False, ax=axes[0])
    axes[0].set(title="Customers by segment", xlabel="", ylabel="Customers")
    sns.barplot(data=seg, x="customer_segment", y="churn_rate", hue="customer_segment", legend=False, ax=axes[1])
    axes[1].set(title="Historical churn rate by segment", xlabel="", ylabel="Churn rate")
    axes[1].yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0%}"))
    path = figures_dir / "05_segment_summary.png"
    _save_figure(fig, path); outputs.append(path)

    return outputs


def retention_action(segment: str) -> str:
    """Return a practical, segment-specific retention action."""
    actions = {
        "At-risk": "Proactive 30/60/90-day onboarding; resolve setup or support friction; test a right-sized plan or a transparent term incentive before renewal.",
        "High-value": "Assign proactive service support; review price-to-value perception; offer relevant service bundles or loyalty benefits rather than a blanket discount.",
        "Loyal": "Recognise tenure with renewal benefits; protect service quality; invite referrals and targeted feedback.",
        "Core": "Use low-cost lifecycle messaging; monitor product engagement and service issues; test relevant add-ons based on actual usage.",
    }
    return actions.get(segment, "Review customer needs and contact history before choosing an intervention.")


def write_outputs(df: pd.DataFrame, value_threshold: float, reports_dir: Path) -> dict[str, Path]:
    """Write tables, figures, and a concise analysis summary to reports/."""
    reports_dir = Path(reports_dir)
    tables_dir = reports_dir / "tables"
    figures_dir = reports_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)

    overall = pd.DataFrame([{
        "customers": len(df),
        "churned_customers": int(df["churn_flag"].sum()),
        "churn_rate": float(df["churn_flag"].mean()),
        "avg_tenure_months": float(df["tenure"].mean()),
        "avg_monthly_charges": float(df["MonthlyCharges"].mean()),
        "high_value_threshold_q75": value_threshold,
    }])
    outputs: dict[str, Path] = {}
    outputs["overall"] = tables_dir / "overall_metrics.csv"
    overall.to_csv(outputs["overall"], index=False)

    seg = segment_summary(df)
    outputs["segments"] = tables_dir / "segment_summary.csv"
    seg.to_csv(outputs["segments"], index=False)

    for column in ["Contract", "PaymentMethod", "InternetService", "TechSupport", "tenure_group"]:
        path = tables_dir / f"churn_by_{column.lower()}.csv"
        categorical_churn_table(df, column).to_csv(path, index=False)
        outputs[f"{column}_crosstab"] = path

    outputs["figures"] = figures_dir
    make_eda_figures(df, figures_dir)

    actions = "\n".join(
        f"- **{row.customer_segment}:** {retention_action(row.customer_segment)}"
        for row in seg.itertuples(index=False)
    )
    highest_churn_categories = []
    for column in ["Contract", "PaymentMethod", "InternetService", "TechSupport", "tenure_group"]:
        table = categorical_churn_table(df, column)
        if not table.empty:
            row = table.iloc[0]
            highest_churn_categories.append(
                f"- **{column}:** {row[column]} has the highest observed category churn rate "
                f"({row['churn_rate_pct']:.1f}%; n={int(row['customers']):,})."
            )

    overall_rate = df["churn_flag"].mean()
    report_text = f"""# Customer churn analysis — generated results

## Dataset snapshot

- Customers: **{len(df):,}**
- Recorded churners: **{int(df['churn_flag'].sum()):,}**
- Overall recorded churn rate: **{overall_rate:.1%}**
- Average tenure: **{df['tenure'].mean():.1f} months**
- Average monthly charges: **{df['MonthlyCharges'].mean():.2f} dataset currency units**
- High-value cutoff used in segmentation (75th percentile of MonthlyCharges): **{value_threshold:.2f}**

## Category-level patterns

{chr(10).join(highest_churn_categories)}

## Rule-based customer segments

{seg.to_markdown(index=False, floatfmt='.2f')}

## Suggested retention actions

{actions}

## Interpretation notes

- Churn rates are historical proportions within this snapshot, not forecasts.
- The segments are transparent business rules, not machine-learned clusters.
- Segment rules do not use the Churn label; churn rate is used only to evaluate the resulting groups.
- Correlations and crosstabs describe association, not causation. Validate interventions with controlled tests before scaling them.
- The dataset is a sample for a fictional telecom company. Currency is not labelled in the CSV, so monetary values are intentionally shown as dataset currency units.
"""
    outputs["summary"] = reports_dir / "analysis_summary.md"
    outputs["summary"].write_text(report_text, encoding="utf-8")
    return outputs


def run_full_analysis(data_path: Path = DEFAULT_DATA_PATH, reports_dir: Path | None = None) -> tuple[pd.DataFrame, dict[str, Path]]:
    """Load, clean, segment, analyse, and export the full project outputs."""
    if reports_dir is None:
        reports_dir = PROJECT_ROOT / "reports"
    raw = load_raw_data(data_path)
    cleaned = clean_and_engineer(raw)
    segmented, threshold = assign_customer_segments(cleaned)
    outputs = write_outputs(segmented, threshold, reports_dir)
    return segmented, outputs
