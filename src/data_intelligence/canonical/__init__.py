"""Representação canônica para dados tabulares."""

from data_intelligence.canonical.mapping import apply_column_mapping
from data_intelligence.canonical.excel_export import ExportError, write_excel_template

__all__ = ["ExportError", "apply_column_mapping", "write_excel_template"]
