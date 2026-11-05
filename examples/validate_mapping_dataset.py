"""Confere estrutura e rótulos do conjunto sintético de mapeamentos.

Execute na raiz do projeto com:
    python examples/validate_mapping_dataset.py
"""

import csv
from collections import Counter
from pathlib import Path

from data_intelligence.schema.templates import REPORT_SCHEMAS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "synthetic" / "column_mappings_demo.csv"
REQUIRED_COLUMNS = {
    "source_profile",
    "report_type",
    "source_column",
    "canonical_field",
}
MIN_PROFILES_PER_LABEL = 5
INITIAL_TARGET_FIELDS = {
    "estoque": {
        "ean",
        "descricao_produto",
        "grupo",
        "quantidade",
        "valor_total_custo",
        "unidade",
    },
    "vendas": {
        "ean",
        "descricao_produto",
        "quantidade",
        "valor_total_bruto",
        "valor_total_liquido",
        "unidade",
    },
}


def main() -> None:
    with DATA_PATH.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        headers = set(reader.fieldnames or ())
        if headers != REQUIRED_COLUMNS:
            raise ValueError(
                f"Cabeçalhos esperados: {sorted(REQUIRED_COLUMNS)}; encontrados: {sorted(headers)}"
            )
        rows = list(reader)

    problems: list[str] = []
    seen_examples: set[tuple[str, str, str]] = set()
    per_profile: Counter[str] = Counter()
    per_label: Counter[tuple[str, str]] = Counter()
    profiles_per_label: dict[tuple[str, str], set[str]] = {}
    reports_per_profile: dict[str, set[str]] = {}
    fields_per_profile_report: dict[tuple[str, str], set[str]] = {}

    for line_number, row in enumerate(rows, start=2):
        profile = row["source_profile"].strip()
        report_type = row["report_type"].strip()
        source_column = row["source_column"].strip()
        canonical_field = row["canonical_field"].strip()

        if not all((profile, report_type, source_column, canonical_field)):
            problems.append(f"linha {line_number}: há campo vazio")
            continue

        if report_type not in REPORT_SCHEMAS:
            problems.append(f"linha {line_number}: tipo de relatório desconhecido: {report_type}")
            continue

        if canonical_field not in REPORT_SCHEMAS[report_type]:
            problems.append(
                f"linha {line_number}: {canonical_field} não pertence ao esquema {report_type}"
            )

        example_key = (profile, report_type, source_column.casefold())
        if example_key in seen_examples:
            problems.append(f"linha {line_number}: exemplo repetido {example_key}")
        seen_examples.add(example_key)

        per_profile[profile] += 1
        per_label[(report_type, canonical_field)] += 1
        profiles_per_label.setdefault((report_type, canonical_field), set()).add(profile)
        reports_per_profile.setdefault(profile, set()).add(report_type)
        fields_per_profile_report.setdefault((profile, report_type), set()).add(canonical_field)

    if len(per_profile) < 5:
        problems.append("são necessários pelo menos cinco perfis sintéticos para avaliação por origem")
    if not rows:
        problems.append("o conjunto não contém exemplos")
    for profile, report_types in sorted(reports_per_profile.items()):
        missing_reports = set(REPORT_SCHEMAS) - report_types
        if missing_reports:
            problems.append(
                f"perfil {profile} não tem exemplos para: {', '.join(sorted(missing_reports))}"
            )
    for (report_type, canonical_field), profiles in sorted(profiles_per_label.items()):
        if len(profiles) < MIN_PROFILES_PER_LABEL:
            problems.append(
                f"{report_type}.{canonical_field} aparece em apenas {len(profiles)} perfil(is); "
                f"mínimo esperado: {MIN_PROFILES_PER_LABEL}"
            )
    for report_type, fields in INITIAL_TARGET_FIELDS.items():
        for canonical_field in sorted(fields):
            if (report_type, canonical_field) not in profiles_per_label:
                problems.append(f"não há exemplos para {report_type}.{canonical_field}")
    for profile in sorted(per_profile):
        for report_type, expected_fields in INITIAL_TARGET_FIELDS.items():
            actual_fields = fields_per_profile_report.get((profile, report_type), set())
            missing_fields = expected_fields - actual_fields
            if missing_fields:
                problems.append(
                    f"perfil {profile} não tem rótulos de {report_type}: "
                    f"{', '.join(sorted(missing_fields))}"
                )

    if problems:
        print(f"Conjunto inválido: {len(problems)} problema(s)")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)

    print("Conjunto sintético válido")
    print(f"Exemplos: {len(rows)}")
    print(f"Perfis fictícios: {len(per_profile)}")
    print("Exemplos por perfil: " + ", ".join(f"{name}={count}" for name, count in sorted(per_profile.items())))
    print("\nExemplos por campo e relatório:")
    for (report_type, field), count in sorted(per_label.items()):
        print(f"- {report_type}.{field}: {count}")


if __name__ == "__main__":
    main()
