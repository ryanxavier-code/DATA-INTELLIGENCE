"""Testes das sugestões de esquema e aplicação de nomes canônicos."""

import unittest
from pathlib import Path

import pandas as pd

from data_intelligence.canonical import apply_column_mapping
from data_intelligence.dataset import Dataset
from data_intelligence.schema import suggest_column_mappings


class SchemaTests(unittest.TestCase):
    def test_ean_is_suggested_as_ean_not_internal_code(self) -> None:
        suggestion = suggest_column_mappings(["EAN"])[0]

        self.assertEqual(suggestion.candidates[0].canonical_name, "ean")
        self.assertEqual(suggestion.candidates[0].score, 1.0)

    def test_similar_sales_value_name_suggests_price(self) -> None:
        suggestion = suggest_column_mappings(["VALOR_VENDA"])[0]

        self.assertEqual(suggestion.candidates[0].canonical_name, "preco")
        self.assertGreaterEqual(suggestion.candidates[0].score, 0.55)

    def test_mapping_returns_new_dataset_and_preserves_source(self) -> None:
        original = Dataset(
            data=pd.DataFrame({"EAN": ["0000000000017"], "PRECO": [10.0]}),
            source=Path("synthetic.xlsx"),
            source_format="excel",
        )

        canonical = apply_column_mapping(original, {"EAN": "ean"})

        self.assertEqual(original.column_names, ["EAN", "PRECO"])
        self.assertEqual(canonical.column_names, ["ean", "PRECO"])
        self.assertEqual(canonical.data.loc[0, "ean"], "0000000000017")

    def test_mapping_rejects_colliding_names(self) -> None:
        dataset = Dataset(
            data=pd.DataFrame({"EAN": ["0000000000017"], "PRECO": [10.0]}),
            source=Path("synthetic.xlsx"),
            source_format="excel",
        )

        with self.assertRaisesRegex(ValueError, "nomes de coluna repetidos"):
            apply_column_mapping(dataset, {"EAN": "PRECO"})


if __name__ == "__main__":
    unittest.main()
