"""Descoberta e sugestão de esquemas para colunas tabulares."""

from data_intelligence.schema.column_mapping import (
    DEFAULT_ALIASES,
    ColumnMappingSuggestion,
    MappingCandidate,
    suggest_column_mappings,
)
from data_intelligence.schema.templates import (
    REPORT_SCHEMAS,
    SALES_SCHEMA,
    STOCK_SCHEMA,
    get_report_schema,
)

__all__ = [
    "DEFAULT_ALIASES",
    "ColumnMappingSuggestion",
    "MappingCandidate",
    "suggest_column_mappings",
    "REPORT_SCHEMAS",
    "SALES_SCHEMA",
    "STOCK_SCHEMA",
    "get_report_schema",
]
