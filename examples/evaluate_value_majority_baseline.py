"""Mede uma referência ingênua para mapear colunas sem usar ML.

Para cada grupo, prevê a classe mais frequente por tipo de relatório usando
somente os outros grupos de sistemas. Serve como piso de comparação futuro.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic" / "farmacia_demo"


def main() -> None:
    labels = pd.read_csv(DATA_DIR / "column_value_training_y_demo.csv")
    manifest = pd.read_csv(DATA_DIR / "column_value_manifest_demo.csv")
    folds = pd.read_csv(DATA_DIR / "source_profile_folds_demo.csv")
    data = manifest.merge(labels, on="example_id", validate="one_to_one")
    data = data.merge(folds, on="source_profile", validate="many_to_one")

    expected_profiles = set(data["source_profile"].astype(str))
    if folds["source_profile"].duplicated().any() or set(
        folds["source_profile"].astype(str)
    ) != expected_profiles:
        raise ValueError("Cada sistema precisa aparecer exatamente uma vez no arquivo de grupos")

    predictions: list[tuple[str, str, str]] = []
    for fold_id in sorted(data["fold_id"].unique()):
        train = data[data["fold_id"] != fold_id]
        held_out = data[data["fold_id"] == fold_id]
        if set(train["source_profile"]) & set(held_out["source_profile"]):
            raise ValueError(f"Vazamento de sistema na dobra {fold_id}")

        majorities = (
            train.groupby(["report_type", "canonical_field"])
            .size()
            .reset_index(name="count")
            .sort_values(["report_type", "count", "canonical_field"], ascending=[True, False, True])
            .drop_duplicates("report_type")
            .set_index("report_type")["canonical_field"]
            .to_dict()
        )
        for row in held_out.itertuples(index=False):
            predictions.append(
                (str(row.report_type), str(row.canonical_field), str(majorities[row.report_type]))
            )

    correct = sum(expected == predicted for _, expected, predicted in predictions)
    labels_by_report: dict[str, set[str]] = defaultdict(set)
    for report, expected, _ in predictions:
        labels_by_report[report].add(expected)
    f1_scores: list[float] = []
    for report, label_set in labels_by_report.items():
        for label in label_set:
            true_positive = sum(
                row_report == report and gold == label and predicted == label
                for row_report, gold, predicted in predictions
            )
            false_positive = sum(
                row_report == report and gold != label and predicted == label
                for row_report, gold, predicted in predictions
            )
            false_negative = sum(
                row_report == report and gold == label and predicted != label
                for row_report, gold, predicted in predictions
            )
            denominator = 2 * true_positive + false_positive + false_negative
            f1_scores.append(2 * true_positive / denominator if denominator else 0.0)

    print("Referência majoritária, sem treinamento de ML")
    print(f"Exemplos avaliados fora do grupo de treino: {len(predictions)}")
    print(f"Sistemas fictícios: {data['source_profile'].nunique()}")
    print(f"Grupos: {folds['fold_id'].nunique()}")
    print(f"Top-1: {correct / len(predictions):.1%} ({correct}/{len(predictions)})")
    print(f"Macro-F1: {sum(f1_scores) / len(f1_scores):.3f}")
    print("Esta é uma referência mínima; não é um modelo nem uma recomendação utilizável.")


if __name__ == "__main__":
    main()
