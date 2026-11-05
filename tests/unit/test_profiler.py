"""Testes para o perfilamento descritivo."""

import unittest
from pathlib import Path

import pandas as pd

from data_intelligence.dataset import Dataset
from data_intelligence.profiling import profile_dataset


class ProfilerTests(unittest.TestCase):
    def test_profiles_nulls_uniques_duplicates_and_frequencies(self) -> None:
        frame = pd.DataFrame({"GRUPO": ["A", "A", "A", "A", "A", None]})
        dataset = Dataset(data=frame, source=Path("synthetic.csv"), source_format="csv")

        profile = profile_dataset(dataset, top_n=2)
        column = profile.columns[0]

        self.assertEqual(profile.row_count, 6)
        self.assertEqual(profile.column_count, 1)
        self.assertEqual(column.value_count, 6)
        self.assertEqual(column.non_null_count, 5)
        self.assertEqual(column.null_count, 1)
        self.assertAlmostEqual(column.null_percentage, 100 / 6)
        self.assertEqual(column.unique_count, 1)
        self.assertEqual(column.duplicate_count, 4)
        self.assertEqual(column.most_frequent[0].value, "A")
        self.assertEqual(column.most_frequent[0].count, 5)
        self.assertTrue(column.possible_category)

    def test_counts_repeated_complete_rows_beyond_the_first(self) -> None:
        frame = pd.DataFrame({"EAN": ["0001", "0001", "0002"], "PRECO": [10, 10, 20]})
        dataset = Dataset(data=frame, source=Path("synthetic.xlsx"), source_format="excel")

        profile = profile_dataset(dataset)

        self.assertEqual(profile.duplicate_row_count, 1)

    def test_marks_named_identifier_numeric_and_date_candidates(self) -> None:
        frame = pd.DataFrame({
            "CODIGO": [1, 2, 3],
            "PRECO": [10.5, 11.0, 9.9],
            "DATA_VENDA": ["2025-01-10", "2025-01-11", "2025-01-12"],
        })
        dataset = Dataset(data=frame, source=Path("synthetic.csv"), source_format="csv")

        profile = profile_dataset(dataset)
        by_name = {column.name: column for column in profile.columns}

        self.assertTrue(by_name["CODIGO"].possible_identifier)
        self.assertTrue(by_name["PRECO"].possible_numeric)
        self.assertTrue(by_name["DATA_VENDA"].possible_date)

    def test_empty_dataset_is_profiled_without_division_by_zero(self) -> None:
        dataset = Dataset(
            data=pd.DataFrame({"PRODUTO": pd.Series(dtype="object")}),
            source=Path("empty.csv"),
            source_format="csv",
        )

        column = profile_dataset(dataset).columns[0]

        self.assertEqual(column.null_percentage, 0.0)
        self.assertEqual(column.unique_count, 0)
        self.assertIsNone(column.average_value_length)


if __name__ == "__main__":
    unittest.main()
