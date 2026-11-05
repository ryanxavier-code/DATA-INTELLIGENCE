"""Agregações tabulares explícitas, semelhantes às de uma tabela dinâmica."""

from collections.abc import Mapping, Sequence

import pandas as pd


_SUPPORTED_OPERATIONS = {"sum", "count", "mean", "min", "max"}


def aggregate_table(
    data: pd.DataFrame,
    *,
    group_by: Sequence[str],
    metrics: Mapping[str, tuple[str, str]],
) -> pd.DataFrame:
    """Agrupa linhas e calcula métricas definidas explicitamente.

    ``metrics`` associa o nome de saída a ``(coluna_de_origem, operação)``.
    Operações aceitas: ``sum``, ``count``, ``mean``, ``min`` e ``max``.
    Todas as linhas recebidas participam da agregação: filtros de totalizadores
    ou registros inválidos precisam ser aplicados antes, de forma explícita.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data deve ser um pandas.DataFrame")
    if not group_by:
        raise ValueError("Informe ao menos uma coluna para agrupar")
    if not metrics:
        raise ValueError("Informe ao menos uma métrica para agregar")
    if data.columns.duplicated().any():
        raise ValueError("A tabela não pode ter nomes de coluna duplicados")

    group_columns = list(group_by)
    if len(group_columns) != len(set(group_columns)):
        raise ValueError("As colunas de agrupamento devem ser únicas")

    required_columns = set(group_columns)
    required_columns.update(source for source, _ in metrics.values())
    missing = sorted(required_columns - set(data.columns))
    if missing:
        raise ValueError("Colunas de agregação não encontradas: " + ", ".join(missing))

    output_names = list(metrics)
    if len(output_names) != len(set(output_names)):
        raise ValueError("Os nomes de saída das métricas devem ser únicos")
    collisions = sorted(set(output_names) & set(group_columns))
    if collisions:
        raise ValueError(
            "As métricas não podem sobrescrever colunas de agrupamento: "
            + ", ".join(collisions)
        )

    aggregations: dict[str, tuple[str, object]] = {}
    for output_name, (source_name, operation) in metrics.items():
        if operation not in _SUPPORTED_OPERATIONS:
            allowed = ", ".join(sorted(_SUPPORTED_OPERATIONS))
            raise ValueError(
                f"Operação {operation!r} não aceita. Use uma destas: {allowed}."
            )
        if operation != "count" and not pd.api.types.is_numeric_dtype(data[source_name]):
            raise TypeError(
                f"A coluna {source_name!r} precisa ser numérica para {operation!r}; "
                "conversões devem ser decididas e validadas antes da agregação."
            )
        function: object = _sum_min_count_one if operation == "sum" else operation
        aggregations[output_name] = (source_name, function)

    grouped = data.groupby(group_columns, dropna=False, sort=False)
    return grouped.agg(**aggregations).reset_index()


def _sum_min_count_one(values: pd.Series) -> object:
    """Mantém valor ausente quando o grupo não contém nenhum valor conhecido."""
    return values.sum(min_count=1)
