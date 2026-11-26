# Dataset source and download instructions

This project uses the **IBM Telco Customer Churn sample dataset** (7,043 customer records, 21 columns). It describes customers of a fictional telecommunications company.

- IBM source repository: <https://github.com/IBM/telco-customer-churn-on-icp4d>
- Direct CSV: <https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv>
- Alternative Kaggle listing: <https://www.kaggle.com/datasets/blastchar/telco-customer-churn>
- Expected SHA-256 for the IBM CSV: `16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91`

The project downloads the IBM CSV automatically on the first run and verifies its SHA-256 checksum. The raw CSV is not committed to Git, keeping the repository small and making the source and integrity check explicit.

To download manually, save the IBM CSV in this directory with the exact filename:

`Telco-Customer-Churn.csv`

If you use another mirror, verify that it is the same source version before analysis. Do not substitute generated or synthetic data and describe it as the IBM sample.
