"""Demonstra sugestões de nomes canônicos usando apenas nomes fictícios."""

from data_intelligence.schema import suggest_column_mappings


source_columns = [
    "SKU",
    "NOME_PRODUTO",
    "CATEGORIA",
    "VALOR_VENDA",
    "OBSERVACAO_LIVRE",
]

suggestions = suggest_column_mappings(source_columns, min_score=0.55)

print("Sugestões de esquema (revise antes de aplicar):\n")
for suggestion in suggestions:
    print(f"Coluna de origem: {suggestion.source_column}")
    if not suggestion.candidates:
        print("  Nenhuma sugestão acima do limite.\n")
        continue

    for candidate in suggestion.candidates:
        print(
            f"  {candidate.canonical_name}: score={candidate.score:.2f}, "
            f"evidência={candidate.method} ({candidate.matched_alias!r})"
        )
    print()
