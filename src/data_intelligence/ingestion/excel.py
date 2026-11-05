"""Leitura de planilhas Excel."""

from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

from data_intelligence.dataset import Dataset
from data_intelligence.ingestion.errors import IngestionError


def read_excel(
    path: str | Path,
    *,
    sheet_name: str | int = 0,
    dtype: Mapping[str, str] | None = None,
    usecols: Sequence[str] | None = None,
) -> Dataset:
    """Lê uma aba do Excel; ``dtype`` permite preservar tipos de colunas-chave."""
    source = Path(path)
    try:
        options: dict[str, object] = {"sheet_name": sheet_name}
        if dtype is not None:
            options["dtype"] = dtype
        if usecols is not None:
            options["usecols"] = list(usecols)
        frame = pd.read_excel(source, **options)
    except (OSError, ValueError, ImportError) as exc:
        raise IngestionError(f"Não foi possível ler o Excel '{source}': {exc}") from exc
    return Dataset(data=frame, source=source, source_format="excel")
