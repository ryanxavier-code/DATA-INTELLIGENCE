"""Limpeza de linhas configurada explicitamente por quem executa o fluxo."""

from collections.abc import Mapping, Sequence

import pandas as pd

from data_intelligence.dataset import Dataset


def prepare_dataset(
    dataset: Dataset,
    *,
    drop_empty_rows: bool = False,
    require_value_columns: Sequence[str] = (),
    excluded_values: Mapping[str, Sequence[str]] | None = None,
    strip_text: bool = False,
) -> Dataset:
    """Retorna uma cópia com as regras de preparação solicitadas.

    A função nunca altera o arquivo de origem nem o DataFrame recebido. Valores
    excluídos são comparados como texto, sem diferenciar maiúsculas/minúsculas e
    ignorando espaços nas extremidades. Colunas configuradas que não existem
    geram ``ValueError`` para evitar filtros silenciosamente ignorados.
    """
    frame = dataset.data.copy()

    configured_columns = set(require_value_columns)
    configured_columns.update((excluded_values or {}).keys())
    missing_columns = sorted(configured_columns - set(dataset.column_names))
    if missing_columns:
        raise ValueError(
            "Colunas de preparação não encontradas: " + ", ".join(missing_columns)
        )

    if strip_text:
        for column in frame.select_dtypes(include="object").columns:
            frame[column] = frame[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
        for column in frame.select_dtypes(include="string").columns:
            frame[column] = frame[column].str.strip()

    if drop_empty_rows:
        frame = frame.dropna(how="all")

    for column in require_value_columns:
        present = frame[column].notna()
        if pd.api.types.is_string_dtype(frame[column].dtype) or frame[column].dtype == object:
            present &= frame[column].astype("string").str.strip().ne("").fillna(False)
        frame = frame.loc[present]

    for column, values in (excluded_values or {}).items():
        excluded = {str(value).strip().casefold() for value in values}
        matches = frame[column].map(
            lambda value: isinstance(value, str)
            and value.strip().casefold() in excluded
        )
        frame = frame.loc[~matches]

    return Dataset(
        data=frame,
        source=dataset.source,
        source_format=dataset.source_format,
    )
