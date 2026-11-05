"""Testes dos leitores de arquivos tabulares."""

import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from data_intelligence.ingestion import IngestionError, read_csv, read_excel


class IngestionTests(unittest.TestCase):
    def test_reads_csv_and_reports_basic_structure(self) -> None:
        path = Path("produtos.csv")
        frame = pd.DataFrame({"EAN": [123, 456], "PRODUTO": ["Dipirona", "Paracetamol"]})

        with patch("data_intelligence.ingestion.csv.pd.read_csv", return_value=frame) as read:
            dataset = read_csv(path, sep=";")

        read.assert_called_once_with(path, sep=";", encoding="utf-8")
        self.assertEqual(dataset.row_count, 2)
        self.assertEqual(dataset.column_count, 2)
        self.assertEqual(dataset.column_names, ["EAN", "PRODUTO"])
        self.assertEqual(dataset.source_format, "csv")
        self.assertEqual(dataset.data.loc[0, "PRODUTO"], "Dipirona")
        self.assertIn("EAN", dataset.apparent_types)

    def test_reads_first_excel_sheet(self) -> None:
        path = Path("produtos.xlsx")
        frame = pd.DataFrame({"EAN": [123], "PRODUTO": ["Dipirona"]})

        with patch("data_intelligence.ingestion.excel.pd.read_excel", return_value=frame) as read:
            dataset = read_excel(path)

        read.assert_called_once_with(path, sheet_name=0)
        self.assertEqual(dataset.row_count, 1)
        self.assertEqual(dataset.column_names, ["EAN", "PRODUTO"])
        self.assertEqual(dataset.source_format, "excel")

    def test_passes_explicit_excel_column_types(self) -> None:
        frame = pd.DataFrame({"EAN": ["0000000000017"]})

        with patch("data_intelligence.ingestion.excel.pd.read_excel", return_value=frame) as read:
            dataset = read_excel("produtos.xlsx", dtype={"EAN": "string"})

        read.assert_called_once_with(
            Path("produtos.xlsx"), sheet_name=0, dtype={"EAN": "string"}
        )
        self.assertEqual(dataset.data.loc[0, "EAN"], "0000000000017")

    def test_missing_file_has_clear_ingestion_error(self) -> None:
        with patch("data_intelligence.ingestion.csv.pd.read_csv", side_effect=OSError("arquivo ausente")):
            with self.assertRaisesRegex(IngestionError, "Não foi possível ler o CSV"):
                read_csv(Path("inexistente.csv"))


if __name__ == "__main__":
    unittest.main()
