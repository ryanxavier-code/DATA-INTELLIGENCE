"""Executa ingestão e perfilamento sobre uma base fictícia de produtos."""

from pathlib import Path

from data_intelligence.ingestion import read_csv
from data_intelligence.profiling import profile_dataset


project_root = Path(__file__).resolve().parents[1]
data_path = project_root / "data" / "synthetic" / "produtos_demo.csv"

dataset = read_csv(data_path, sep=";")
profile = profile_dataset(dataset)

print(f"Arquivo: {profile.source}")
print(f"Formato: {profile.row_count} linhas x {profile.column_count} colunas\n")
print(
    "Linhas completamente repetidas "
    f"(além da primeira ocorrência): {profile.duplicate_row_count}\n"
)

duplicate_rows = dataset.data[dataset.data.duplicated(keep=False)]
if duplicate_rows.empty:
    print("Nenhuma linha completamente duplicada foi encontrada.\n")
else:
    print("Linhas envolvidas em duplicidades completas:")
    print(duplicate_rows.to_string(index=False))
    print()

for column in profile.columns:
    print(
        f"{column.name}: tipo={column.apparent_type}, "
        f"nulos={column.null_count} ({column.null_percentage:.1f}%), "
        f"únicos={column.unique_count}, duplicidades={column.duplicate_count}"
    )
    if column.most_frequent:
        most_common = column.most_frequent[0]
        print(f"  mais frequente: {most_common.value!r} ({most_common.count} ocorrências)")
