"""Representação interna comum para dados recebidos de diferentes fontes."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class Dataset:
    """Tabela carregada e metadados básicos da fonte de origem.

    A tabela é mantida em memória; esta classe não altera nem sobrescreve
    o arquivo original.
    """

    data: pd.DataFrame
    source: Path
    source_format: str

    @property
    def row_count(self) -> int:
        """Quantidade de registros, sem contar o cabeçalho."""
        return len(self.data.index)

    @property
    def column_count(self) -> int:
        """Quantidade de colunas."""
        return len(self.data.columns)

    @property
    def column_names(self) -> list[str]:
        """Nomes das colunas na ordem original."""
        return [str(name) for name in self.data.columns]

    @property
    def apparent_types(self) -> dict[str, str]:
        """Tipos inferidos pelo pandas, úteis para inspeção inicial."""
        return {str(name): str(dtype) for name, dtype in self.data.dtypes.items()}
