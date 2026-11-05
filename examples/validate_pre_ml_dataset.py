"""Valida os conjuntos sintéticos preparados antes de começar ML.

Não treina nem avalia um modelo. Confere rótulos, separação de arquivos,
cobertura por sistema e grupos reservados para uma futura avaliação.
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path

from data_intelligence.schema.templates import REPORT_SCHEMAS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic" / "farmacia_demo"
EXPECTED_FIELDS = {
    "estoque": {
        "ean", "descricao_produto", "grupo", "quantidade",
        "valor_total_custo", "unidade",
    },
    "vendas": {
        "mes", "ean", "descricao_produto", "grupo", "quantidade",
        "valor_total_bruto", "valor_total_liquido", "unidade",
    },
}
EXPECTED_HEADER_FIELDS = {
    "estoque": {
        "ean", "descricao_produto", "grupo", "subgrupo", "laboratorio",
        "quantidade", "giro_mensal", "valor_total_custo", "custo_medio",
        "valor_total_liquido", "unidade",
    },
    "vendas": {
        "mes", "filial", "ean", "descricao_produto", "grupo", "subgrupo",
        "laboratorio", "quantidade", "valor_total_bruto", "valor_total_liquido",
        "valor_total_custo", "lucro_bruto", "desconto_maximo", "desconto_padrao",
        "desconto_preferencial", "unidade",
    },
}


def main() -> None:
    features = pd.read_csv(DATA_DIR / "column_value_training_X_demo.csv")
    labels = pd.read_csv(DATA_DIR / "column_value_training_y_demo.csv")
    manifest = pd.read_csv(DATA_DIR / "column_value_manifest_demo.csv")
    header_examples = pd.read_csv(DATA_DIR / "column_mappings_header_ml_demo.csv")
    folds = pd.read_csv(DATA_DIR / "source_profile_folds_demo.csv")

    problems: list[str] = []
    for name, frame, required in (
        ("X", features, {"example_id", "source_profile", "report_type"}),
        ("y", labels, {"example_id", "canonical_field"}),
        ("manifesto", manifest, {"example_id", "source_profile", "report_type", "has_header"}),
        ("cabeçalhos", header_examples, {"source_profile", "report_type", "source_column", "canonical_field"}),
        ("dobras", folds, {"source_profile", "fold_id"}),
    ):
        missing = required - set(frame.columns)
        if missing:
            problems.append(f"{name}: faltam colunas {sorted(missing)}")
        if frame.empty:
            problems.append(f"{name}: arquivo sem exemplos")

    if problems:
        _fail(problems)

    for name, frame in (("X", features), ("y", labels), ("manifesto", manifest)):
        if frame["example_id"].duplicated().any():
            problems.append(f"{name}: example_id duplicado")

    expected_ids = list(features["example_id"])
    if list(labels["example_id"]) != expected_ids:
        problems.append("X e y não têm os mesmos example_id na mesma ordem")
    if list(manifest["example_id"]) != expected_ids:
        problems.append("X e manifesto não têm os mesmos example_id na mesma ordem")

    # Campos de identificação e informação da fonte servem para rastrear/grupar,
    # mas não devem entrar na matriz usada como preditor.
    non_predictors = {"example_id", "source_profile", "report_type", "source_sheet_id"}
    predictor_columns = set(features.columns) - non_predictors
    forbidden_predictors = {
        "canonical_field", "source_column", "source_header", "sample_values_json",
        "column_position_1_based", "has_header",
    } & predictor_columns
    if forbidden_predictors:
        problems.append(f"X contém possíveis pistas ou rótulos: {sorted(forbidden_predictors)}")
    if not predictor_columns:
        problems.append("X não contém características preditoras")
    non_numeric = [
        column for column in predictor_columns
        if not pd.api.types.is_numeric_dtype(features[column])
    ]
    if non_numeric:
        problems.append(f"X tem preditores não numéricos: {sorted(non_numeric)}")
    if features[list(predictor_columns)].isna().any().any():
        problems.append("X contém valores ausentes nas características preditoras")

    profile_set = set(features["source_profile"].astype(str))
    label_profiles: dict[tuple[str, str], set[str]] = {}
    report_fields: dict[str, set[str]] = {}
    for row in features[["source_profile", "report_type"]].itertuples(index=False):
        if row.report_type not in REPORT_SCHEMAS:
            problems.append(f"tipo de relatório inválido: {row.report_type}")
    for profile, report, field in zip(
        features["source_profile"], features["report_type"], labels["canonical_field"]
    ):
        if report not in REPORT_SCHEMAS or field not in REPORT_SCHEMAS[report]:
            problems.append(f"rótulo inválido: {report}.{field}")
            continue
        label_profiles.setdefault((report, field), set()).add(str(profile))
        report_fields.setdefault(str(report), set()).add(str(field))

    if len(profile_set) < 10:
        problems.append("esperados ao menos 10 sistemas fictícios")
    for report, expected_fields in EXPECTED_FIELDS.items():
        missing = expected_fields - report_fields.get(report, set())
        if missing:
            problems.append(f"{report}: faltam classes {sorted(missing)}")
    for key, profiles in label_profiles.items():
        if len(profiles) < 5:
            problems.append(f"{key}: classe aparece em menos de cinco sistemas")

    if set(manifest["has_header"].astype(str).str.lower()) != {"true", "false"}:
        problems.append("manifesto precisa incluir exemplos com e sem cabeçalho")
    header_profile_set = set(header_examples["source_profile"].astype(str))
    if not header_profile_set <= profile_set:
        problems.append("conjunto de cabeçalhos contém perfil fora do conjunto de valores")
    header_seen: set[tuple[str, str, str]] = set()
    for profile, report, header, field in header_examples[
        ["source_profile", "report_type", "source_column", "canonical_field"]
    ].itertuples(index=False, name=None):
        if report not in EXPECTED_HEADER_FIELDS or field not in EXPECTED_HEADER_FIELDS.get(report, set()):
            problems.append(f"rótulo de cabeçalho inválido: {report}.{field}")
        key = (str(profile), str(report), str(header).casefold())
        if key in header_seen:
            problems.append(f"cabeçalho duplicado no conjunto: {key}")
        header_seen.add(key)
    if len(header_profile_set) < 10:
        problems.append("conjunto de cabeçalhos precisa cobrir ao menos 10 sistemas")
    for report, expected_fields in EXPECTED_HEADER_FIELDS.items():
        missing_schema_fields = expected_fields - set(REPORT_SCHEMAS.get(report, {}))
        if missing_schema_fields:
            problems.append(
                f"campos de cabeçalho não definidos no esquema {report}: "
                f"{sorted(missing_schema_fields)}"
            )
        actual_fields = set(
            header_examples.loc[header_examples["report_type"] == report, "canonical_field"]
            .astype(str)
        )
        missing = expected_fields - actual_fields
        if missing:
            problems.append(f"cabeçalhos de {report}: faltam classes {sorted(missing)}")
    fold_profiles = set(folds["source_profile"].astype(str))
    if fold_profiles != profile_set or folds["source_profile"].duplicated().any():
        problems.append("cada sistema deve ter exatamente uma dobra de avaliação")
    if folds["fold_id"].nunique() < 5:
        problems.append("esperadas pelo menos cinco dobras agrupadas por sistema")
    if folds.groupby("fold_id")["source_profile"].nunique().min() < 2:
        problems.append("cada dobra precisa conter ao menos dois sistemas")

    if problems:
        _fail(problems)

    print("Conjunto sintético validado; este validador não treina modelos.")
    print(f"Sistemas fictícios: {len(profile_set)}")
    print(f"Exemplos de colunas: {len(features)}")
    print(f"Características preditoras: {len(predictor_columns)}")
    print(f"Exemplos com cabeçalho: {len(header_examples)}")
    print(f"Classes de cabeçalho: {header_examples['canonical_field'].nunique()}")
    print(f"Exemplos sem cabeçalho: {(manifest['has_header'] == False).sum()}")
    print(f"Campos canônicos: {labels['canonical_field'].nunique()}")
    print(f"Grupos de avaliação: {folds['fold_id'].nunique()} (sistemas mantidos juntos)")


def _fail(problems: list[str]) -> None:
    print(f"Preparação pré-ML inválida: {len(problems)} problema(s)")
    for problem in problems:
        print(f"- {problem}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
