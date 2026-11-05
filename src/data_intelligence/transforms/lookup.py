"""Junções explícitas por chave para enriquecer tabelas de referência."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class LookupResult:
    """Tabela enriquecida e resumo das correspondências da procura."""

    data: pd.DataFrame
    matched_rows: int
    unmatched_rows: int
    rows_without_key: int
    unmatched_keys: tuple[Any, ...]


def lookup_columns(
    source: pd.DataFrame,
    reference: pd.DataFrame,
    *,
    source_key: str,
    reference_key: str,
    columns: Mapping[str, str],
) -> LookupResult:
    """Acrescenta colunas de referência com uma junção exata muitos-para-um.

    ``columns`` associa o nome que será criado no resultado ao nome da coluna
    correspondente na tabela de referência. Linhas da origem sem chave ou sem
    correspondência são mantidas; os contadores e chaves não encontradas ficam
    disponíveis em ``LookupResult``. A referência precisa ter chaves não nulas
    e únicas. Os valores das chaves não são normalizados nem convertidos.
    """
    if not isinstance(source, pd.DataFrame) or not isinstance(reference, pd.DataFrame):
        raise TypeError("source e reference devem ser pandas.DataFrame")
    if not columns:
        raise ValueError("Informe ao menos uma coluna da tabela de referência")

    _require_columns(source, {source_key}, "origem")
    required_reference = {reference_key, *columns.values()}
    _require_columns(reference, required_reference, "referência")

    if source.columns.duplicated().any() or reference.columns.duplicated().any():
        raise ValueError("As tabelas não podem ter nomes de coluna duplicados")

    output_columns = list(columns)
    if len(output_columns) != len(set(output_columns)):
        raise ValueError("Os nomes das colunas de saída do lookup devem ser únicos")
    reference_value_columns = list(columns.values())
    if len(reference_value_columns) != len(set(reference_value_columns)):
        raise ValueError("As colunas da tabela de referência devem ser únicas")
    if reference_key in reference_value_columns:
        raise ValueError("A chave da referência não pode ser uma coluna enriquecida")
    collisions = sorted(set(output_columns) & set(source.columns))
    if collisions:
        raise ValueError(
            "O lookup não sobrescreve colunas da origem: " + ", ".join(collisions)
        )

    reference_keys = reference[reference_key]
    if reference_keys.isna().any():
        raise ValueError(f"A chave de referência {reference_key!r} contém valores nulos")
    duplicate_mask = reference_keys.duplicated(keep=False)
    if duplicate_mask.any():
        examples = reference_keys.loc[duplicate_mask].drop_duplicates().head(5).tolist()
        raise ValueError(
            f"A chave de referência {reference_key!r} precisa ser única; "
            f"duplicidades de exemplo: {examples!r}"
        )

    reserved_names = {
        *source.columns,
        *reference.columns,
        *output_columns,
    }
    order_column = _temporary_name(reserved_names, "__lookup_row_order")
    reserved_names.add(order_column)
    status_column = _temporary_name(reserved_names, "__lookup_status")
    reserved_names.add(status_column)
    right_key_column = _temporary_name(reserved_names, "__lookup_reference_key")

    right = reference[[reference_key, *columns.values()]].copy()
    rename_map = {reference_key: right_key_column}
    rename_map.update({reference_name: output_name for output_name, reference_name in columns.items()})
    right = right.rename(columns=rename_map)

    left = source.copy()
    left[order_column] = range(len(left))
    try:
        merged = left.merge(
            right,
            how="left",
            left_on=source_key,
            right_on=right_key_column,
            sort=False,
            validate="many_to_one",
            indicator=status_column,
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(
            "Não foi possível comparar as chaves. Confira se os tipos e formatos "
            "das duas colunas são compatíveis; nenhuma conversão automática foi feita."
        ) from exc

    matched_rows = int(merged[status_column].eq("both").sum())
    unmatched_mask = merged[status_column].eq("left_only")
    unmatched_rows = int(unmatched_mask.sum())
    rows_without_key = int(merged.loc[unmatched_mask, source_key].isna().sum())
    unmatched_keys = tuple(
        pd.unique(merged.loc[unmatched_mask, source_key].dropna()).tolist()
    )

    result = (
        merged.sort_values(order_column, kind="stable")
        .drop(columns=[order_column, status_column, right_key_column])
    )
    result.index = source.index
    return LookupResult(
        data=result,
        matched_rows=matched_rows,
        unmatched_rows=unmatched_rows,
        rows_without_key=rows_without_key,
        unmatched_keys=unmatched_keys,
    )


def _require_columns(
    frame: pd.DataFrame, required: set[str], label: str
) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(
            f"Colunas ausentes na tabela de {label}: " + ", ".join(missing)
        )


def _temporary_name(columns: Any, base: str) -> str:
    existing = set(columns)
    name = base
    suffix = 1
    while name in existing:
        name = f"{base}_{suffix}"
        suffix += 1
    return name
