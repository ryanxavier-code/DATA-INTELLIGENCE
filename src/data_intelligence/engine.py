"""Ponto central que conecta as etapas reutilizáveis da ferramenta."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from data_intelligence.canonical import apply_column_mapping
from data_intelligence.dataset import Dataset
from data_intelligence.identity import StoreLookupError, lookup_store
from data_intelligence.ingestion import read_csv, read_excel
from data_intelligence.profiling import DatasetProfile, profile_dataset
from data_intelligence.quality import QualityIssue, run_quality_checks
from data_intelligence.schema import (
    ColumnMappingSuggestion,
    get_report_schema,
    suggest_column_mappings,
)
from data_intelligence.transforms import prepare_dataset


@dataclass(frozen=True)
class AnalysisResult:
    """Resultados de uma execução completa, prontos para CLI, app ou API."""

    dataset: Dataset
    profile: DatasetProfile
    duplicate_rows: pd.DataFrame
    quality_issues: tuple[QualityIssue, ...]
    schema_suggestions: tuple[ColumnMappingSuggestion, ...]
    expected_schema_fields: tuple[str, ...]
    fields_without_suggestion: tuple[str, ...]
    canonical_dataset: Dataset | None
    input_row_count: int


def analyze_file(
    path: str | Path,
    *,
    separator: str = ",",
    sheet_name: str | int = 0,
    text_columns: Sequence[str] = (),
    required_columns: Sequence[str] = (),
    unique_columns: Sequence[str] = (),
    report_type: str | None = None,
    approved_mapping: Mapping[str, str] | None = None,
    drop_empty_rows: bool = False,
    require_value_columns: Sequence[str] = (),
    excluded_values: Mapping[str, Sequence[str]] | None = None,
    strip_text: bool = False,
    store_name: str | None = None,
    store_lookup_path: str | Path | None = None,
) -> AnalysisResult:
    """Lê e analisa um arquivo, conectando as funções existentes do projeto.

    O arquivo de origem não é alterado. A conversão canônica só ocorre quando
    ``approved_mapping`` é fornecido explicitamente. Ao mapear uma coluna para
    ``ean``, linhas sem esse valor são removidas da preparação padrão. Uma
    consulta de unidade/CNPJ pode ser ativada com ``store_name`` e
    ``store_lookup_path`` em conjunto.
    """
    source = Path(path)
    dtype = {column: "string" for column in text_columns} or None
    suffix = source.suffix.casefold()

    if suffix == ".csv":
        dataset = read_csv(source, sep=separator, dtype=dtype)
    elif suffix in {".xlsx", ".xlsm", ".xls"}:
        dataset = read_excel(source, sheet_name=sheet_name, dtype=dtype)
    else:
        raise ValueError(
            f"Formato {suffix or '(sem extensão)'} não suportado. Use CSV ou Excel."
        )

    input_row_count = dataset.row_count
    required_value_columns = list(require_value_columns)
    if approved_mapping:
        # EAN é a chave de produto obrigatória no conjunto canônico.
        # O cabeçalho de origem pode variar (por exemplo, EAN ou GTIN).
        ean_source_columns = [
            source_column
            for source_column, canonical_name in approved_mapping.items()
            if canonical_name.strip().casefold() == "ean"
        ]
        required_value_columns.extend(ean_source_columns)

    dataset = prepare_dataset(
        dataset,
        drop_empty_rows=drop_empty_rows,
        require_value_columns=tuple(dict.fromkeys(required_value_columns)),
        excluded_values=excluded_values,
        strip_text=strip_text,
    )
    profile = profile_dataset(dataset)
    duplicate_rows = dataset.data.loc[dataset.data.duplicated(keep=False)].copy()
    quality_issues = run_quality_checks(
        dataset,
        required_columns=required_columns,
        unique_columns=unique_columns,
    )
    aliases = get_report_schema(report_type) if report_type else None
    suggestions = (
        suggest_column_mappings(dataset.column_names, aliases=aliases)
        if aliases is not None
        else suggest_column_mappings(dataset.column_names)
    )
    expected_fields = tuple(aliases) if aliases is not None else ()
    suggested_fields = {
        candidate.canonical_name
        for suggestion in suggestions
        for candidate in suggestion.candidates
    }
    fields_without_suggestion = tuple(
        field for field in expected_fields if field not in suggested_fields
    )
    canonical_dataset = (
        apply_column_mapping(dataset, approved_mapping)
        if approved_mapping
        else None
    )
    if bool(store_name) != bool(store_lookup_path):
        raise ValueError("Informe store_name e store_lookup_path juntos.")
    if store_name and store_lookup_path:
        if canonical_dataset is None:
            raise ValueError("A consulta de unidade exige um mapeamento aprovado.")
        try:
            registered_name, cnpj = lookup_store(store_lookup_path, store_name)
        except StoreLookupError as exc:
            raise ValueError(str(exc)) from exc
        identified_data = canonical_dataset.data.copy()
        identified_data["unidade"] = registered_name
        identified_data["cnpj"] = cnpj
        canonical_dataset = Dataset(
            data=identified_data,
            source=canonical_dataset.source,
            source_format=canonical_dataset.source_format,
        )
        fields_without_suggestion = tuple(
            field
            for field in fields_without_suggestion
            if field not in {"unidade", "cnpj"}
        )

    return AnalysisResult(
        dataset=dataset,
        profile=profile,
        duplicate_rows=duplicate_rows,
        quality_issues=quality_issues,
        schema_suggestions=suggestions,
        expected_schema_fields=expected_fields,
        fields_without_suggestion=fields_without_suggestion,
        canonical_dataset=canonical_dataset,
        input_row_count=input_row_count,
    )
