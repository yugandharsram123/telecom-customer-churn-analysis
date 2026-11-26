# Customer Segmentation and Churn Analysis — Telecom

A reproducible exploratory data analysis (EDA) project using the IBM Telco Customer Churn sample. The project investigates how contract type, tenure, monthly charges, service subscriptions, and payment method relate to recorded churn. It then assigns interpretable customer segments and proposes retention actions.

## Project objectives

1. Clean and inspect the source data, documenting missing values and data types.
2. Explore churn with distributions, boxplots, crosstabs, and a numeric correlation heatmap.
3. Compare churn rates across contract, tenure, internet service, tech support, and payment method.
4. Assign customers to rule-based **At-risk**, **High-value**, **Loyal**, and **Core** segments.
5. Translate segment and EDA patterns into practical retention actions.

## Dataset

- **Name:** IBM Telco Customer Churn sample
- **Size:** 7,043 customers × 21 original columns
- **Target:** `Churn` (`Yes` / `No`)
- **Source:** [IBM's public sample-data repository](https://github.com/IBM/telco-customer-churn-on-icp4d)
- **Direct CSV:** [Telco-Customer-Churn.csv](https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv)

The CSV is downloaded automatically the first time the project is run and its SHA-256 checksum is verified. The raw file is excluded from Git; see [`data/raw/README.md`](data/raw/README.md) for details and manual download instructions. No synthetic observations are used.

## Repository structure

```text
telecom-customer-churn-analysis/
├── data/
│   └── raw/
│       └── README.md
├── notebooks/
│   └── 01_customer_segmentation_and_churn_analysis.ipynb
├── reports/
│   └── figures/              # Generated plots appear here after execution
├── src/
│   ├── __init__.py
│   ├── analysis.py           # Cleaning, segmentation, EDA, exports
│   └── run_analysis.py       # Command-line entry point
├── tests/
│   └── test_analysis.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Quick start (Windows PowerShell)

Open PowerShell in the project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m src.run_analysis
```

The first analysis run downloads the IBM CSV to `data/raw/`, validates its checksum, cleans the data, assigns segments, and creates:

- `reports/analysis_summary.md`
- `reports/figures/01_churn_distribution.png`
- `reports/figures/02_boxplots_by_churn.png`
- `reports/figures/03_correlation_heatmap.png`
- `reports/figures/04_categorical_churn_rates.png`
- `reports/figures/05_segment_summary.png`
- CSV tables in `reports/tables/`

### Run the Jupyter notebook

```powershell
jupyter notebook
```

Open `notebooks/01_customer_segmentation_and_churn_analysis.ipynb` and choose **Run All**. The notebook uses the same reusable functions as the command-line analysis.

### Run the tests

```powershell
py -m unittest discover -s tests -v
```

## Methodology

### Data preparation

- Convert `TotalCharges` from text to numeric.
- In the IBM sample, blank `TotalCharges` values for zero-tenure customers are interpreted as zero; other unresolved values remain missing and should be reviewed.
- Encode `Churn` as `churn_flag` (`No = 0`, `Yes = 1`).
- Create tenure bands and a service-count feature for exploratory comparisons.

### EDA

- Target distribution and overall churn rate.
- Boxplots of tenure, monthly charges, and total charges split by churn status.
- Correlation heatmap for numeric variables plus one-hot contract indicators (contract is nominal, not ordinal).
- Crosstabs / within-category churn rates for contract type, payment method, internet service, tech support, and tenure band.

### Rule-based segmentation

Segments are assigned in priority order. Churn is **not** used in the assignment rules, avoiding target leakage.

| Segment | Rule | Retention direction |
|---|---|---|
| At-risk | Tenure ≤ 12 months, or month-to-month contract with high monthly charges (top quartile) or no tech support | Early-life-cycle onboarding, support resolution, plan-fit review |
| Loyal | Tenure ≥ 48 months and a one- or two-year contract, provided the customer was not already tagged At-risk | Recognition, service quality, renewal and referral benefits |
| High-value | Monthly charges at or above the 75th percentile, excluding At-risk and Loyal | Proactive service, value communication, relevant bundles |
| Core | Remaining customers | Low-cost lifecycle engagement and relevant add-ons |

The exact segment counts and observed churn rates are calculated from the downloaded data and written to `reports/tables/segment_summary.csv`.

## Business recommendations

Use the results to prioritise actions, not to apply one discount to everyone:

- **At-risk:** improve first-90-day onboarding, proactively resolve technical issues, and test a plan or contract fit review.
- **High-value:** protect service quality, explain the value received for the price, and offer relevant bundles or loyalty benefits.
- **Loyal:** recognise tenure, make renewals easy, and use referral or advocacy programmes.
- **Core:** keep engagement cost-efficient and recommend add-ons only when usage indicates a relevant need.

Measure outcomes with controlled holdout tests (for example, incremental retention, offer acceptance, and margin impact) before scaling any intervention.

## Important interpretation limits

- This is a descriptive analysis of a cross-sectional sample, not a production churn prediction model.
- A higher observed churn rate is an association, not evidence that a feature causes churn.
- Rule-based segments are explainable business groupings, not statistically discovered clusters.
- The source data does not label the currency for charge fields; values are therefore treated as dataset currency units.
- Do not infer future churn timing from this snapshot or claim causal lift without an experiment.

## Author / portfolio use

Add your own name, course, date, and a short reflection before submitting. Keep the dataset attribution and interpretation limitations intact.

## Upload to GitHub

See [`GITHUB_UPLOAD_GUIDE.md`](GITHUB_UPLOAD_GUIDE.md) for step-by-step instructions using Git or GitHub Desktop.
