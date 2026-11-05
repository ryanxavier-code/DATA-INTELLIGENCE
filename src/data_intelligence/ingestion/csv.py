"""Leitura de arquivos CSV."""

from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

from data_intelligence.dataset import Dataset
from data_intelligence.ingestion.errors import IngestionError


def read_csv(
    path: str | Path,
    *,
    sep: str = ",",
    encoding: str = "utf-8",
    dtype: Mapping[str, str] | None = None,
    usecols: Sequence[str] | None = None,
) -> Dataset:
    """Lê um CSV e devolve uma representação interna padronizada.

    Passe `sep=";"` para arquivos separados por ponto e vírgula, comuns
    em exportações configuradas para uso no Brasil.
    """
    source = Path(path)
    try:
        options: dict[str, object] = {"sep": sep, "encoding": encoding}
        if dtype is not None:
            options["dtype"] = dtype
        if usecols is not None:
            options["usecols"] = list(usecols)
        frame = pd.read_csv(source, **options)
    except (OSError, UnicodeError, pd.errors.ParserError, ValueError) as exc:
        raise IngestionError(f"Não foi possível ler o CSV '{source}': {exc}") from exc
    return Dataset(data=frame, source=source, source_format="csv")
