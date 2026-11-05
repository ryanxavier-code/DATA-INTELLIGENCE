"""Executa leitura, perfilamento e padronização em um Excel totalmente fictício."""

from pathlib import Path

from data_intelligence.canonical import apply_column_mapping
from data_intelligence.ingestion import read_excel
from data_intelligence.profiling import profile_dataset
from data_intelligence.schema import suggest_column_mappings


project_root = Path(__file__).resolve().parents[1]
data_path = project_root / "data" / "synthetic" / "produtos_demo_ean.xlsx"

# EAN é identificador, não quantidade. Forçamos o tipo texto para preservar zeros.
dataset = read_excel(data_path, dtype={"EAN": "string"})
profile = profile_dataset(dataset)

print(f"Arquivo: {profile.source}")
print(f"Formato: {profile.row_count} linhas x {profile.column_count} colunas")
print(f"EAN preservado como texto: {dataset.data['EAN'].iloc[0]!r}\n")

print("Perfil das colunas:")
for column in profile.columns:
    print(
        f"{column.name}: tipo={column.apparent_type}, nulos={column.null_count}, "
        f"únicos={column.unique_count}, repetidos={column.duplicate_count}"
    )

print("\nSugestões de esquema:")
for suggestion in suggest_column_mappings(dataset.column_names):
    best = suggestion.candidates[0] if suggestion.candidates else None
    if best is None:
        print(f"{suggestion.source_column} -> sem sugestão")
    else:
        print(
            f"{suggestion.source_column} -> {best.canonical_name} "
            f"(score {best.score:.2f}; evidência: {best.matched_alias})"
        )

# Aplicamos apenas este mapeamento explícito para testar a etapa canônica.
approved_mapping = {
    "EAN": "ean",
    "DESCRICAO_PRODUTO": "descricao_produto",
    "GRUPO": "grupo",
    "PRECO": "preco",
}
canonical_dataset = apply_column_mapping(dataset, approved_mapping)
print(f"\nColunas canônicas: {canonical_dataset.column_names}")
