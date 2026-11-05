"""Testes do ponto central que conecta as etapas da ferramenta."""

import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from data_intelligence.dataset import Dataset
from data_intelligence.engine import analyze_file


class EngineTests(unittest.TestCase):
    def test_connects_ingestion_profile_schema_and_canonical_mapping(self) -> None:
        frame = pd.DataFrame(
            {
                "EAN": pd.Series(["0000000000017", "0000000000017"], dtype="string"),
                "PRECO": [12.5, 12.5],
            }
        )
        dataset = Dataset(data=frame, source=Path("sample.xlsx"), source_format="excel")

        with patch("data_intelligence.engine.read_excel", return_value=dataset) as reader:
            result = analyze_file(
                "sample.xlsx",
                text_columns=("EAN",),
                approved_mapping={"EAN": "ean"},
            )

        reader.assert_called_once_with(
            Path("sample.xlsx"), sheet_name=0, dtype={"EAN": "string"}
        )
        self.assertEqual(result.profile.row_count, 2)
        self.assertEqual(result.profile.duplicate_row_count, 1)
        self.assertEqual(len(result.duplicate_rows), 2)
        self.assertEqual(result.schema_suggestions[0].candidates[0].canonical_name, "ean")
        self.assertEqual(result.canonical_dataset.column_names, ["ean", "PRECO"])


if __name__ == "__main__":
    unittest.main()
