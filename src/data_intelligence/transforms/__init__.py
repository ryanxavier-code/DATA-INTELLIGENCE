"""Transformações explícitas aplicáveis aos conjuntos tabulares."""

from data_intelligence.transforms.aggregation import aggregate_table
from data_intelligence.transforms.cleaning import prepare_dataset
from data_intelligence.transforms.lookup import LookupResult, lookup_columns

__all__ = ["LookupResult", "aggregate_table", "lookup_columns", "prepare_dataset"]
