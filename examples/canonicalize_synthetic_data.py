"""Demonstra uma conversão canônica aprovada manualmente, sem salvar arquivos."""

from pathlib import Path

from data_intelligence.canonical import apply_column_mapping
from data_intelligence.ingestion import read_csv


project_root = Path(__file__).resolve().parents[1]
data_path = project_root / "data" / "synthetic" / "produtos_demo.csv"
dataset = read_csv(data_path, sep=";")

# Este mapeamento é uma decisão explícita de quem revisou o esquema.
approved_mapping = {
    "COD_INTERNO": "codigo_interno",
    "DESCRICAO_PRODUTO": "descricao_produto",
    "GRUPO": "grupo",
    "PRECO": "preco",
}
canonical_dataset = apply_column_mapping(dataset, approved_mapping)

print(f"Colunas originais: {dataset.column_names}")
print(f"Colunas canônicas: {canonical_dataset.column_names}")
print("\nPrévia dos dados convertidos (em memória):")
print(canonical_dataset.data.head().to_string(index=False))
