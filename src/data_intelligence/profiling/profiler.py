"""Perfilamento descritivo de tabelas sem alterar os dados de entrada."""

from dataclasses import dataclass
import re
from typing import Any

import pandas as pd
from pandas.api import types as ptypes

from data_intelligence.dataset import Dataset


@dataclass(frozen=True)
class FrequentValue:
    """Um valor frequente e seu número de ocorrências não nulas."""

    value: Any
    count: int


@dataclass(frozen=True)
class ColumnProfile:
    """Métricas observadas e indícios heurísticos de uma coluna."""

    name: str
    apparent_type: str
    value_count: int
    non_null_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    duplicate_count: int
    average_value_length: float | None
    most_frequent: tuple[FrequentValue, ...]
    possible_identifier: bool
    possible_category: bool
    possible_numeric: bool
    possible_date: bool


@dataclass(frozen=True)
class DatasetProfile:
    """Resumo de um dataset e os perfis das suas colunas."""

    source: str
    row_count: int
    column_count: int
    duplicate_row_count: int
    columns: tuple[ColumnProfile, ...]


_IDENTIFIER_NAME_PARTS = {"ID", "COD", "CODIGO", "CNPJ", "CPF", "EAN", "SKU", "CHAVE"}


def _looks_like_identifier(name: str, non_null_count: int, unique_count: int) -> bool:
    if non_null_count == 0:
        return False
    name_parts = set(re.split(r"[^A-Z0-9]+", name.upper()))
    if name_parts & _IDENTIFIER_NAME_PARTS:
        return True
    return non_null_count >= 10 and unique_count / non_null_count >= 0.98


def _looks_like_date(series: pd.Series) -> bool:
    if ptypes.is_datetime64_any_dtype(series.dtype):
        return True
    if not (ptypes.is_object_dtype(series.dtype) or ptypes.is_string_dtype(series.dtype)):
        return False

    sample = series.dropna().head(1000)
    if sample.empty:
        return False
    parsed = pd.to_datetime(sample.astype("string"), errors="coerce", dayfirst=True, format="mixed")
    return parsed.notna().mean() >= 0.8


def _profile_column(name: str, series: pd.Series, row_count: int, top_n: int) -> ColumnProfile:
    non_null = series.dropna()
    non_null_count = len(non_null)
    unique_count = int(non_null.nunique())
    null_count = row_count - non_null_count

    lengths = non_null.astype("string").str.len()
    average_length = float(lengths.mean()) if not lengths.empty else None
    frequent = tuple(
        FrequentValue(value=value, count=int(count))
        for value, count in non_null.value_counts().head(top_n).items()
    )

    is_textual = ptypes.is_object_dtype(series.dtype) or ptypes.is_string_dtype(series.dtype)
    category_ratio = unique_count / non_null_count if non_null_count else 1.0

    return ColumnProfile(
        name=name,
        apparent_type=str(series.dtype),
        value_count=row_count,
        non_null_count=non_null_count,
        null_count=null_count,
        null_percentage=(null_count / row_count * 100) if row_count else 0.0,
        unique_count=unique_count,
        duplicate_count=non_null_count - unique_count,
        average_value_length=average_length,
        most_frequent=frequent,
        possible_identifier=_looks_like_identifier(name, non_null_count, unique_count),
        possible_category=is_textual and non_null_count > 0 and unique_count <= 20 and category_ratio <= 0.2,
        possible_numeric=ptypes.is_numeric_dtype(series.dtype),
        possible_date=_looks_like_date(series),
    )


def profile_dataset(dataset: Dataset, *, top_n: int = 5) -> DatasetProfile:
    """Calcula métricas por coluna; não modifica o DataFrame recebido.

    As classificações ``possible_*`` são pistas para investigação, não
    conclusões sobre o significado dos dados.
    """
    if top_n < 0:
        raise ValueError("top_n deve ser zero ou maior")

    frame = dataset.data
    columns = tuple(
        _profile_column(str(name), frame.iloc[:, index], len(frame.index), top_n)
        for index, name in enumerate(frame.columns)
    )
    return DatasetProfile(
        source=str(dataset.source),
        row_count=len(frame.index),
        column_count=len(frame.columns),
        duplicate_row_count=int(frame.duplicated().sum()),
        columns=columns,
    )
