"""Small deterministic unit tests for cleaning and rule-based segmentation."""

import unittest

import pandas as pd

from src.analysis import assign_customer_segments, clean_and_engineer, correlation_features


class TestChurnAnalysis(unittest.TestCase):
    def setUp(self):
        self.raw = pd.DataFrame({
            "customerID": ["A", "B", "C", "D"],
            "gender": ["Female", "Male", "Female", "Male"],
            "SeniorCitizen": [0, 0, 1, 0],
            "Partner": ["No", "Yes", "No", "Yes"],
            "Dependents": ["No", "Yes", "No", "Yes"],
            "tenure": [0, 6, 60, 36],
            "PhoneService": ["Yes"] * 4,
            "MultipleLines": ["No", "Yes", "Yes", "No"],
            "InternetService": ["DSL", "Fiber optic", "DSL", "Fiber optic"],
            "OnlineSecurity": ["No", "No", "Yes", "Yes"],
            "OnlineBackup": ["No", "No", "Yes", "No"],
            "DeviceProtection": ["No", "No", "Yes", "No"],
            "TechSupport": ["No", "No", "Yes", "Yes"],
            "StreamingTV": ["No", "Yes", "No", "Yes"],
            "StreamingMovies": ["No", "Yes", "No", "Yes"],
            "Contract": ["Month-to-month", "Month-to-month", "Two year", "One year"],
            "PaperlessBilling": ["Yes"] * 4,
            "PaymentMethod": ["Electronic check"] * 4,
            "MonthlyCharges": [20.0, 95.0, 60.0, 100.0],
            "TotalCharges": ["", "570", "3600", "3600"],
            "Churn": ["No", "Yes", "No", "No"],
        })

    def test_cleaning_converts_total_charges_and_churn(self):
        clean = clean_and_engineer(self.raw)
        self.assertEqual(clean.loc[0, "TotalCharges"], 0.0)
        self.assertEqual(clean["churn_flag"].tolist(), [0, 1, 0, 0])
        self.assertEqual(clean["service_count"].dtype.kind, "i")
        corr = correlation_features(clean)
        self.assertIn("Contract_Month-to-month", corr.columns)
        self.assertIn("Contract_One year", corr.columns)
        self.assertIn("Contract_Two year", corr.columns)

    def test_segments_cover_all_customers_and_do_not_overwrite_churn(self):
        clean = clean_and_engineer(self.raw)
        segmented, threshold = assign_customer_segments(clean)
        self.assertTrue(segmented["customer_segment"].notna().all())
        self.assertGreater(threshold, 0)
        self.assertEqual(segmented["churn_flag"].tolist(), [0, 1, 0, 0])
        self.assertIn("At-risk", set(segmented["customer_segment"]))
        self.assertIn("Loyal", set(segmented["customer_segment"]))


if __name__ == "__main__":
    unittest.main()
