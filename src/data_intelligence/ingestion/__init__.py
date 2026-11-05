"""Leitores para fontes de dados tabulares."""

from data_intelligence.ingestion.csv import read_csv
from data_intelligence.ingestion.excel import read_excel
from data_intelligence.ingestion.errors import IngestionError

__all__ = ["IngestionError", "read_csv", "read_excel"]
