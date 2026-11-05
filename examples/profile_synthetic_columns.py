"""Extrai características e rótulos separados do workbook sintético pequeno.

Este exemplo não treina um modelo. As características não incluem o campo
canônico; os rótulos esperados são gravados em um arquivo separado.

Execute na raiz do projeto com:
    python examples/profile_synthetic_columns.py
"""

from pathlib import Path

import pandas as pd

from data_intelligence.profiling import profile_frame_columns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "farmacia_demo"
    / "DATASET_FORMATOS_FICTICIOS.xlsx"
)
FEATURES_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "farmacia_demo"
    / "column_value_features_demo.csv"
)
LABELS_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "farmacia_demo"
    / "column_value_labels_demo.csv"
)
HEADERLESS_SHEETS = {"Estoque_Sem_Header", "Vendas_Sem_Header"}


def main() -> None:
    workbook = pd.ExcelFile(WORKBOOK_PATH)
    gold = pd.read_excel(workbook, sheet_name="Gabarito_Colunas")
    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, str]] = []

    for sheet_name in gold["Planilha"].drop_duplicates():
        sheet_gold = gold[gold["Planilha"] == sheet_name]
        has_header = sheet_name not in HEADERLESS_SHEETS
        frame = pd.read_excel(
            workbook,
            sheet_name=sheet_name,
            header=0 if has_header else None,
        )
        headers = (
            [str(value) for value in sheet_gold["Cabecalho_Se_Houver"].tolist()]
            if has_header
            else None
        )
        column_features = profile_frame_columns(
            frame,
            has_header=has_header,
            headers=headers,
        )

        for _, mapping in sheet_gold.iterrows():
            position = int(mapping["Posicao_Coluna"]) - 1
            if position < 0 or position >= frame.shape[1]:
                raise ValueError(
                    f"Posição inválida no gabarito: {sheet_name}, coluna {position + 1}"
                )
            example_id = f"{sheet_name}__col{position + 1}"
            feature_rows.append(
                {
                    "example_id": example_id,
                    "source_profile": str(mapping["Perfil_Ficticio"]),
                    "report_type": str(mapping["Tipo_Relatorio"]),
                    "sheet_name": str(sheet_name),
                    **column_features[position],
                }
            )
            label_rows.append(
                {
                    "example_id": example_id,
                    "canonical_field": str(mapping["Campo_Canonico"]),
                }
            )

    pd.DataFrame(feature_rows).to_csv(FEATURES_PATH, index=False, encoding="utf-8-sig")
    pd.DataFrame(label_rows).to_csv(LABELS_PATH, index=False, encoding="utf-8-sig")
    print(f"Colunas perfiladas: {len(feature_rows)}")
    print(f"Entradas sem cabeçalho: {sum(not row['has_header'] for row in feature_rows)}")
    print(f"Características (sem rótulos): {FEATURES_PATH}")
    print(f"Rótulos separados: {LABELS_PATH}")


if __name__ == "__main__":
    main()
