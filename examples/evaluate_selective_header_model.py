"""Avalia um corte de abstenção para sugestões ML sem reutilizar a dobra de teste.

Cada dobra externa fica fora do ajuste do classificador e da escolha do corte.
Dentro do treino externo, previsões agrupadas por sistema escolhem o menor
score que não erra nos exemplos aceitos. O corte é então medido na dobra
externa, que permanece intocada até a avaliação.

Execute na raiz do projeto:
    python examples/evaluate_selective_header_model.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GroupKFold

from data_intelligence.ml import build_header_classifier, select_abstention_threshold


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "farmacia_demo"
    / "column_mappings_header_ml_demo.csv"
)


def _model_input(data: pd.DataFrame) -> np.ndarray:
    return (
        data["report_type"].astype(str).str.casefold()
        + " [SEP] "
        + data["source_column"].astype(str)
    ).to_numpy()


def main() -> None:
    data = pd.read_csv(DATA_PATH)
    required = {"source_profile", "report_type", "source_column", "canonical_field"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError("Faltam colunas no conjunto: " + ", ".join(sorted(missing)))

    model_inputs = _model_input(data)
    labels = data["canonical_field"].astype(str).to_numpy()
    groups = data["source_profile"].astype(str).to_numpy()
    top1_predictions = np.empty(len(data), dtype=object)
    top3_correct = np.zeros(len(data), dtype=bool)
    selective_predictions: list[bool] = []
    accepted_count = 0

    outer_splitter = GroupKFold(n_splits=5)
    for fold, (train_indices, test_indices) in enumerate(
        outer_splitter.split(model_inputs, labels, groups), start=1
    ):
        train_groups = set(groups[train_indices])
        test_groups = set(groups[test_indices])
        if train_groups & test_groups:
            raise RuntimeError(f"Vazamento de perfil encontrado na dobra externa {fold}.")

        threshold = select_abstention_threshold(
            model_inputs[train_indices],
            labels[train_indices],
            groups[train_indices],
            n_splits=4,
        )
        model = build_header_classifier().fit(
            model_inputs[train_indices], labels[train_indices]
        )
        probabilities = model.predict_proba(model_inputs[test_indices])
        classes = model.named_steps["classifier"].classes_
        ranked = probabilities.argsort(axis=1)[:, ::-1]
        predictions = classes[ranked[:, 0]]
        top3 = classes[ranked[:, :3]]
        scores = probabilities.max(axis=1)
        top1_predictions[test_indices] = predictions
        top3_correct[test_indices] = np.any(top3 == labels[test_indices, None], axis=1)

        accepted = scores >= threshold
        accepted_count += int(accepted.sum())
        selective_predictions.extend(
            (predictions[accepted] == labels[test_indices][accepted]).tolist()
        )
        print(
            f"Dobra {fold}: score mínimo={threshold:.3f}; "
            f"sugestões avaliadas={int(accepted.sum())}/{len(test_indices)}"
        )

    total = len(data)
    selective_precision = (
        float(np.mean(selective_predictions)) if selective_predictions else float("nan")
    )
    print("\nAvaliação aninhada com somente cabeçalhos sintéticos:")
    print(f"Sistemas agrupados: {len(set(groups))}; dobras externas: 5; internas: 4")
    print(f"Top-1 global: {accuracy_score(labels, top1_predictions):.1%}")
    print(f"Top-3 global: {top3_correct.mean():.1%}")
    print(
        f"Precisão das sugestões aceitas: {selective_precision:.1%} "
        f"({int(sum(selective_predictions))}/{accepted_count})"
    )
    print(f"Cobertura: {accepted_count}/{total} ({accepted_count / total:.1%})")
    print("Scores não são probabilidades calibradas; resultados não validam fontes reais.")


if __name__ == "__main__":
    main()
