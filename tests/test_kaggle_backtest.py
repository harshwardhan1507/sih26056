"""
Unit tests for the 50-day Kaggle back-test pipeline (scripts/run_kaggle_backtest.py).
"""

from pathlib import Path
import csv
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.run_kaggle_backtest import run_kaggle_backtest, generate_synthetic_50day_panel


def test_generate_synthetic_panel(tmp_path: Path):
    panel_csv = tmp_path / "test_panel.csv"
    generate_synthetic_50day_panel(panel_csv)
    assert panel_csv.exists()

    with open(panel_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 50 days * 12 routes * 5 windows * 5 carriers = 15,000 rows
    assert len(rows) == 15000
    first = rows[0]
    assert "airline" in first
    assert "source_city" in first
    assert "destination_city" in first
    assert "days_left" in first
    assert "price" in first
    assert int(first["price"]) > 0


def test_run_kaggle_backtest_execution(tmp_path: Path):
    panel_csv = tmp_path / "panel.csv"
    output_series_csv = tmp_path / "output_series.csv"

    generate_synthetic_50day_panel(panel_csv)
    results = run_kaggle_backtest(dataset_path=panel_csv, output_csv=output_series_csv)

    assert results["series_length"] == 50
    assert results["base_value"] == 100.0
    assert results["min_value"] > 50.0
    assert results["max_value"] < 200.0
    assert output_series_csv.exists()

    with open(output_series_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        series_rows = list(reader)

    assert len(series_rows) == 50
    # Day 0 should be 100.0
    assert float(series_rows[0]["aggregate_index_value"]) == 100.0
    # Values should all be positive and reasonable
    for row in series_rows:
        val = float(row["aggregate_index_value"])
        assert 50.0 < val < 200.0
        assert int(row["routes_quoted"]) == 12
        assert int(row["advance_windows"]) == 5


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        test_generate_synthetic_panel(p)
        test_run_kaggle_backtest_execution(p)
    print("All Kaggle back-test unit tests passed successfully!")
