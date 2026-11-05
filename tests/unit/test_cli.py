"""Testes da interface integrada do projeto."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from data_intelligence.cli import main
from data_intelligence.dataset import Dataset


class CliTests(unittest.TestCase):
    def test_runs_csv_profile_and_approved_mapping(self) -> None:
        csv_path = Path("produtos.csv")
        dataset = Dataset(
            data=pd.DataFrame(
                {
                    "EAN": pd.Series(["0000000000017"], dtype="string"),
                    "DESCRICAO_PRODUTO": ["Dipirona"],
                    "GRUPO": ["MEDICAMENTOS"],
                    "PRECO": [12.5],
                }
            ),
            source=csv_path,
            source_format="csv",
        )
        output = StringIO()
        with patch("data_intelligence.engine.read_csv", return_value=dataset) as read_csv:
            with redirect_stdout(output):
                exit_code = main(
                    [
                        str(csv_path),
                        "--separator",
                        ";",
                        "--text-column",
                        "EAN",
                        "--map-column",
                        "EAN=ean",
                        "--map-column",
                        "DESCRICAO_PRODUTO=descricao_produto",
                    ]
                )

        read_csv.assert_called_once_with(
            csv_path, sep=";", dtype={"EAN": "string"}
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("0000000000017", output.getvalue())
        self.assertIn("EAN -> ean", output.getvalue())
        self.assertIn("Colunas: ['ean', 'descricao_produto', 'GRUPO', 'PRECO']", output.getvalue())


if __name__ == "__main__":
    unittest.main()
