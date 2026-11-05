"""Avalia a heurística atual por perfil de origem em dados sintéticos.

Execute na raiz do projeto com:
    python examples/evaluate_mapping_baseline.py

Como a heurística não é treinada, cada perfil é medido separadamente. Isso
permite enxergar se o desempenho varia entre sistemas fictícios e prepara
uma avaliação agrupada por origem para o classificador futuro.
"""

import csv
import argparse
from collections import defaultdict
from pathlib import Path
from typing import TypedDict

from data_intelligence.schema.column_mapping import suggest_column_mappings
from data_intelligence.schema.templates import get_report_schema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "synthetic" / "column_mappings_demo.csv"


class EvaluationResult(TypedDict):
    top1: int
    top3: int
    count: int
    gold: list[str]
    predicted: list[str | None]


def _empty_result() -> EvaluationResult:
    return {"top1": 0, "top3": 0, "count": 0, "gold": [], "predicted": []}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATA_PATH,
        help="CSV sintético rotulado (padrão: conjunto inicial de 120 exemplos)",
    )
    args = parser.parse_args()
    with args.dataset.open(encoding="utf-8-sig", newline="") as csv_file:
        examples = list(csv.DictReader(csv_file))

    results: defaultdict[str, EvaluationResult] = defaultdict(_empty_result)
    errors: list[tuple[str, str, str, str, str]] = []

    for example in examples:
        report_type = example["report_type"]
        expected = example["canonical_field"]
        profile = example["source_profile"]
        suggestion = suggest_column_mappings(
            [example["source_column"]],
            aliases=get_report_schema(report_type),
            top_n=3,
        )[0]
        predicted = [candidate.canonical_name for candidate in suggestion.candidates]
        top1_correct = bool(predicted and predicted[0] == expected)
        top3_correct = expected in predicted

        for group in ("TODOS", profile):
            results[group]["count"] += 1
            results[group]["top1"] += top1_correct
            results[group]["top3"] += top3_correct
            results[group]["gold"].append(expected)
            results[group]["predicted"].append(predicted[0] if predicted else None)

        if not top1_correct:
            errors.append(
                (
                    profile,
                    report_type,
                    example["source_column"],
                    expected,
                    ", ".join(predicted) if predicted else "sem sugestão",
                )
            )

    print(f"Exemplos avaliados: {len(examples)}")
    print(f"Arquivo: {args.dataset}")
    print("Somente cabeçalhos fictícios; nenhuma planilha empresarial é lida.")
    print(
        "Top-1 = rótulo correto na primeira posição; Top-3 = rótulo entre até três sugestões.\n"
        "Macro-F1 = média do F1 por campo canônico.\n"
    )

    overall = results.pop("TODOS")
    print("Resultado geral:")
    print(_format_result(overall))
    print("\nResultado por perfil (cada perfil representa um sistema fictício):")
    for profile in sorted(results):
        print(f"- {profile}: {_format_result(results[profile])}")

    print(f"\nCabeçalhos sem acerto Top-1: {len(errors)}")
    for profile, report_type, header, expected, predicted in errors:
        print(
            f"- {profile} ({report_type}): {header!r}; "
            f"esperado={expected}; sugerido={predicted}"
        )


def _format_result(result: EvaluationResult) -> str:
    count = result["count"]
    top1 = result["top1"] / count
    top3 = result["top3"] / count
    f1_by_label = []
    for label in set(result["gold"]):
        true_positive = sum(
            gold == label and predicted == label
            for gold, predicted in zip(result["gold"], result["predicted"])
        )
        false_positive = sum(
            gold != label and predicted == label
            for gold, predicted in zip(result["gold"], result["predicted"])
        )
        false_negative = sum(
            gold == label and predicted != label
            for gold, predicted in zip(result["gold"], result["predicted"])
        )
        denominator = 2 * true_positive + false_positive + false_negative
        f1_by_label.append(2 * true_positive / denominator if denominator else 0.0)
    macro_f1 = sum(f1_by_label) / len(f1_by_label)
    return (
        f"Top-1 {top1:.1%} ({result['top1']}/{count}); "
        f"Top-3 {top3:.1%} ({result['top3']}/{count}); "
        f"Macro-F1 {macro_f1:.3f}"
    )


if __name__ == "__main__":
    main()
