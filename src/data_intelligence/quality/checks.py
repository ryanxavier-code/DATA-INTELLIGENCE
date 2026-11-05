"""Verificações de qualidade configuradas explicitamente pelo usuário."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from data_intelligence.dataset import Dataset


@dataclass(frozen=True)
class QualityIssue:
    """Uma ocorrência encontrada por uma regra de qualidade."""

    rule_id: str
    severity: str
    column: str | None
    count: int
    message: str


def _populated_values(series: pd.Series) -> pd.Series:
    """Retorna valores presentes, tratando texto vazio como ausente."""
    populated = series.notna()
    if pd.api.types.is_object_dtype(series.dtype) or pd.api.types.is_string_dtype(series.dtype):
        populated &= series.astype("string").str.strip().ne("").fillna(False)
    return series.loc[populated]


def run_quality_checks(
    dataset: Dataset,
    *,
    required_columns: Sequence[str] = (),
    unique_columns: Sequence[str] = (),
) -> tuple[QualityIssue, ...]:
    """Executa regras configuradas e uma verificação de linhas idênticas.

    Colunas obrigatórias geram erro quando têm nulos ou texto vazio. Colunas
    únicas geram erro para valores não vazios repetidos além da primeira
    ocorrência. Linhas completamente repetidas geram aviso. Nada é corrigido
    ou removido.
    """
    frame = dataset.data
    known_columns = {str(name) for name in frame.columns}
    configured_columns = set(required_columns) | set(unique_columns)
    missing_columns = sorted(configured_columns - known_columns)
    if missing_columns:
        names = ", ".join(missing_columns)
        raise ValueError(f"Coluna(s) configurada(s) não encontrada(s): {names}")

    issues: list[QualityIssue] = []

    for column in dict.fromkeys(required_columns):
        values = frame[column]
        missing = values.isna()
        if pd.api.types.is_object_dtype(values.dtype) or pd.api.types.is_string_dtype(values.dtype):
            missing |= values.astype("string").str.strip().eq("").fillna(False)
        count = int(missing.sum())
        if count:
            issues.append(
                QualityIssue(
                    rule_id="required_value",
                    severity="ERROR",
                    column=column,
                    count=count,
                    message=f"{count} valor(es) ausente(s) em coluna obrigatória.",
                )
            )

    for column in dict.fromkeys(unique_columns):
        values = _populated_values(frame[column])
        count = int(values.duplicated(keep="first").sum())
        if count:
            issues.append(
                QualityIssue(
                    rule_id="unique_value",
                    severity="ERROR",
                    column=column,
                    count=count,
                    message=f"{count} ocorrência(s) repetida(s) além da primeira.",
                )
            )

    duplicate_row_count = int(frame.duplicated().sum())
    if duplicate_row_count:
        issues.append(
            QualityIssue(
                rule_id="duplicate_row",
                severity="WARNING",
                column=None,
                count=duplicate_row_count,
                message=(
                    f"{duplicate_row_count} linha(s) completamente repetida(s) "
                    "além da primeira ocorrência."
                ),
            )
        )

    return tuple(issues)
