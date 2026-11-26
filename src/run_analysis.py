"""Command-line entry point: python -m src.run_analysis"""

from __future__ import annotations

from src.analysis import run_full_analysis


def main() -> None:
    df, outputs = run_full_analysis()
    print("\nAnalysis completed successfully.")
    print(f"Customers analysed: {len(df):,}")
    print(f"Overall churn rate: {df['churn_flag'].mean():.1%}")
    print("\nGenerated outputs:")
    for name, path in outputs.items():
        print(f"- {name}: {path}")
    print("\nOpen reports/analysis_summary.md and reports/figures/ to review the results.")


if __name__ == "__main__":
    main()
