"""Avalia um primeiro classificador de cabeçalhos usando sistemas separados.

O script treina modelos temporários dentro de cada dobra GroupKFold, calcula
métricas fora do treino e salva somente previsões sintéticas out-of-fold.
Não grava nem publica um modelo treinado.

Execute na raiz do projeto com:
    python examples/evaluate_header_ml_model.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold

from data_intelligence.ml import build_header_classifier


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic" / "farmacia_demo"
INPUT_PATH = DATA_DIR / "column_mappings_header_ml_demo.csv"
OUTPUT_PATH = DATA_DIR / "header_ml_oof_predictions_demo.csv"


def main() -> None:
    data = pd.read_csv(INPUT_PATH)
    required_columns = {
        "source_profile", "report_type", "source_column", "canonical_field"
    }
    missing = required_columns - set(data.columns)
    if missing:
        raise ValueError(f"Faltam colunas no conjunto: {sorted(missing)}")
    if data[list(required_columns)].isna().any().any():
        raise ValueError("O conjunto de cabeçalhos contém campos vazios")

    # O nome do sistema identifica grupos para separação, mas nunca entra no texto.
    model_input = (
        data["report_type"].astype(str).str.lower()
        + " [SEP] "
        + data["source_column"].astype(str)
    ).tolist()
    expected = data["canonical_field"].astype(str).to_numpy()
    groups = data["source_profile"].astype(str).to_numpy()
    group_count = len(set(groups))
    splitter = GroupKFold(n_splits=5)
    out_of_fold: list[dict[str, object] | None] = [None] * len(data)
    all_classes = sorted(set(expected))

    for fold_number, (train_indices, test_indices) in enumerate(
        splitter.split(model_input, expected, groups),
        start=1,
    ):
        train_groups = set(groups[train_indices])
        test_groups = set(groups[test_indices])
        if train_groups & test_groups:
            raise RuntimeError(f"Vazamento de sistema encontrado na dobra {fold_number}")
        repeated_inputs = set(model_input[index] for index in train_indices) & set(
            model_input[index] for index in test_indices
        )
        if repeated_inputs:
            raise RuntimeError(
                f"Entradas repetidas entre treino e avaliação na dobra {fold_number}: "
                f"{sorted(repeated_inputs)}"
            )

        model = build_header_classifier()
        model.fit(
            [model_input[index] for index in train_indices],
            expected[train_indices],
        )
        test_inputs = [model_input[index] for index in test_indices]
        predictions = model.predict(test_inputs)
        probabilities = model.predict_proba(test_inputs)
        classes = model.named_steps["classifier"].classes_

        print(
            f"Dobra {fold_number}: treino={len(train_indices)} colunas / "
            f"{len(train_groups)} sistemas; avaliação={len(test_indices)} colunas / "
            f"{len(test_groups)} sistemas"
        )

        for local_index, source_index in enumerate(test_indices):
            ranked_indices = probabilities[local_index].argsort()[::-1][:3]
            top3 = [str(classes[index]) for index in ranked_indices]
            out_of_fold[source_index] = {
                "example_id": (
                    f"{data.iloc[source_index]['source_profile']}__"
                    f"{data.iloc[source_index]['report_type']}__"
                    f"{data.iloc[source_index]['source_column']}"
                ),
                "source_profile": data.iloc[source_index]["source_profile"],
                "report_type": data.iloc[source_index]["report_type"],
                "source_column": data.iloc[source_index]["source_column"],
                "canonical_field_expected": expected[source_index],
                "prediction_top1": str(predictions[local_index]),
                "top1_confidence": round(float(probabilities[local_index].max()), 6),
                "predictions_top3_json": json.dumps(top3, ensure_ascii=False),
                "top1_correct": bool(predictions[local_index] == expected[source_index]),
                "top3_correct": bool(expected[source_index] in top3),
                "fold": fold_number,
            }

    if any(row is None for row in out_of_fold):
        raise RuntimeError("Alguns exemplos não receberam previsão fora do treino")
    predictions_frame = pd.DataFrame(out_of_fold)
    y_pred = predictions_frame["prediction_top1"].to_numpy()
    top1 = accuracy_score(expected, y_pred)
    top3 = predictions_frame["top3_correct"].mean()
    macro_f1 = f1_score(expected, y_pred, labels=all_classes, average="macro", zero_division=0)
    predictions_frame.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("\nPrimeiro experimento de ML: TF-IDF de caracteres + regressão logística")
    print("Somente dados sintéticos; sistemas e entradas idênticas ficaram separados entre treino e avaliação.")
    print(f"Sistemas fictícios: {group_count}; dobras agrupadas: 5")
    print(f"Exemplos avaliados: {len(data)}")
    print(f"Top-1: {top1:.1%}")
    print(f"Top-3: {top3:.1%}")
    print(f"Macro-F1: {macro_f1:.3f}")
    print(f"Previsões fora do treino: {OUTPUT_PATH}")
    print("As pontuações do classificador não estão calibradas para automação.")


if __name__ == "__main__":
    main()
