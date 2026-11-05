"""Aplicação explícita e segura de um mapeamento de colunas aprovado."""

from collections.abc import Mapping

from data_intelligence.dataset import Dataset


def apply_column_mapping(dataset: Dataset, mapping: Mapping[str, str]) -> Dataset:
    """Devolve uma cópia com nomes aprovados, preservando o Dataset recebido.

    ``mapping`` associa nomes de origem a nomes canônicos. Colunas sem entrada
    no mapeamento são mantidas. A função rejeita origens ausentes e nomes finais
    repetidos para evitar perda ou ambiguidade de informação.
    """
    source_names = dataset.column_names
    if len(source_names) != len(set(source_names)):
        raise ValueError("O conjunto de dados tem nomes de coluna repetidos")

    missing_sources = sorted(set(mapping) - set(source_names))
    if missing_sources:
        raise ValueError(
            "Colunas de origem não encontradas: " + ", ".join(missing_sources)
        )

    final_names = [str(mapping.get(name, name)).strip() for name in source_names]
    if any(not name for name in final_names):
        raise ValueError("Nomes canônicos não podem estar vazios")

    normalized_names = [name.casefold() for name in final_names]
    if len(normalized_names) != len(set(normalized_names)):
        raise ValueError("O mapeamento produziria nomes de coluna repetidos")

    renamed_data = dataset.data.rename(
        columns=dict(zip(dataset.data.columns, final_names, strict=True))
    )
    return Dataset(
        data=renamed_data,
        source=dataset.source,
        source_format=dataset.source_format,
    )
