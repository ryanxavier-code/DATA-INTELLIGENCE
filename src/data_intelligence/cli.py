"""Interface de linha de comando que coordena os módulos do projeto."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from data_intelligence.canonical import ExportError, write_excel_template
from data_intelligence.engine import AnalysisResult, analyze_file
from data_intelligence.ingestion import IngestionError


def _parse_mapping(values: Sequence[str], parser: argparse.ArgumentParser) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for value in values:
        source, separator, canonical = value.partition("=")
        source = source.strip()
        canonical = canonical.strip()
        if not separator or not source or not canonical:
            parser.error(
                f"Mapeamento inválido: {value!r}. Use --map-column ORIGEM=CANONICO."
            )
        if source in mapping:
            parser.error(f"A coluna de origem {source!r} foi mapeada mais de uma vez.")
        mapping[source] = canonical
    return mapping


def _parse_excluded_values(
    values: Sequence[str], parser: argparse.ArgumentParser
) -> dict[str, list[str]]:
    excluded: dict[str, list[str]] = {}
    for value in values:
        column, separator, excluded_value = value.partition("=")
        column = column.strip()
        excluded_value = excluded_value.strip()
        if not separator or not column or not excluded_value:
            parser.error(
                f"Filtro inválido: {value!r}. Use --exclude-value COLUNA=VALOR."
            )
        excluded.setdefault(column, []).append(excluded_value)
    return excluded


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data-intelligence",
        description=(
            "Lê um CSV ou Excel, resume a qualidade dos dados, sugere nomes "
            "canônicos e pode exportar para um modelo Excel após mapeamento revisado."
        ),
    )
    parser.add_argument("arquivo", type=Path, help="Caminho para um arquivo CSV ou Excel")
    parser.add_argument(
        "--separator",
        default=",",
        help="Separador do CSV (padrão: vírgula; use ';' em CSVs comuns no Brasil)",
    )
    parser.add_argument(
        "--sheet",
        default="0",
        help="Índice começando em zero ou nome da aba do Excel (padrão: primeira aba)",
    )
    parser.add_argument(
        "--text-column",
        action="append",
        default=[],
        metavar="COLUNA",
        help="Força uma coluna a texto, útil para EANs e outros identificadores; repita se necessário",
    )
    parser.add_argument(
        "--map-column",
        action="append",
        default=[],
        metavar="ORIGEM=CANONICO",
        help="Aplica um mapeamento revisado; repita para mapear várias colunas",
    )
    parser.add_argument(
        "--required-column",
        action="append",
        default=[],
        metavar="COLUNA",
        help="Exige valores preenchidos na coluna; repita para várias colunas",
    )
    parser.add_argument(
        "--unique-column",
        action="append",
        default=[],
        metavar="COLUNA",
        help="Exige valores únicos não vazios na coluna; repita se necessário",
    )
    parser.add_argument(
        "--drop-empty-rows",
        action="store_true",
        help="Remove linhas em que todas as células estão vazias",
    )
    parser.add_argument(
        "--require-value-column",
        action="append",
        default=[],
        metavar="COLUNA",
        help="Remove linhas sem valor nesta coluna; pode ser repetido",
    )
    parser.add_argument(
        "--exclude-value",
        action="append",
        default=[],
        metavar="COLUNA=VALOR",
        help="Remove linhas cujo valor na coluna corresponda ao texto; pode ser repetido",
    )
    parser.add_argument(
        "--strip-text",
        action="store_true",
        help="Remove espaços extras no início/fim de valores textuais",
    )
    parser.add_argument(
        "--report-type",
        choices=("estoque", "vendas"),
        help="Usa o vocabulário-alvo do relatório de estoque ou de vendas",
    )
    parser.add_argument(
        "--template",
        type=Path,
        help="Modelo .xlsx para preencher após aprovar um mapeamento",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Caminho do novo arquivo .xlsx de saída; exige --template e --map-column",
    )
    parser.add_argument(
        "--store-name",
        help="Nome da unidade a localizar no cadastro externo para preencher unidade e CNPJ",
    )
    parser.add_argument(
        "--store-lookup",
        type=Path,
        help="Planilha local de cadastro com colunas Nome Fantasia e CNPJ",
    )
    return parser


def _print_report(result: AnalysisResult) -> None:
    dataset = result.dataset
    profile = result.profile
    print(f"\nArquivo: {profile.source}")
    print(f"Formato: {profile.row_count} linhas x {profile.column_count} colunas")
    print(
        "Linhas completamente repetidas "
        f"(além da primeira ocorrência): {profile.duplicate_row_count}\n"
    )
    removed_rows = result.input_row_count - profile.row_count
    if removed_rows:
        print(f"Linhas removidas pelas regras de preparação: {removed_rows}\n")

    duplicate_rows = result.duplicate_rows
    if duplicate_rows.empty:
        print("Nenhuma linha completamente duplicada foi encontrada.\n")
    else:
        print("Linhas envolvidas em duplicidades completas:")
        print(duplicate_rows.to_string(index=False))
        print()

    print("Verificações de qualidade:")
    if not result.quality_issues:
        print("Nenhuma ocorrência encontrada pelas regras configuradas.\n")
    else:
        for issue in result.quality_issues:
            location = f" [{issue.column}]" if issue.column else ""
            print(
                f"  {issue.severity} {issue.rule_id}{location}: "
                f"{issue.message}"
            )
        print()

    print("Perfil das colunas:")
    for column in profile.columns:
        print(
            f"{column.name}: tipo={column.apparent_type}, "
            f"nulos={column.null_count} ({column.null_percentage:.1f}%), "
            f"únicos={column.unique_count}, duplicidades={column.duplicate_count}"
        )
        if column.most_frequent:
            most_common = column.most_frequent[0]
            print(f"  mais frequente: {most_common.value!r} ({most_common.count} ocorrências)")

    print("\nSugestões de esquema (revise antes de aplicar):")
    for suggestion in result.schema_suggestions:
        if not suggestion.candidates:
            print(f"  {suggestion.source_column}: sem sugestão")
            continue
        best = suggestion.candidates[0]
        print(
            f"  {suggestion.source_column} -> {best.canonical_name} "
            f"(score {best.score:.2f}; evidência: {best.matched_alias!r})"
        )
    if result.expected_schema_fields:
        print("\nCampos do modelo sem sugestão de cabeçalho correspondente:")
        if result.fields_without_suggestion:
            for field in result.fields_without_suggestion:
                print(f"  {field}")
        else:
            print("  Nenhum campo ficou sem sugestão.")
        print("  Revise as sugestões; ausência de sugestão não confirma ausência do dado.")


def main(argv: Sequence[str] | None = None) -> int:
    """Executa a análise integrada e retorna um código de saída."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    mapping = _parse_mapping(args.map_column, parser)
    excluded_values = _parse_excluded_values(args.exclude_value, parser)
    if bool(args.template) != bool(args.output):
        parser.error("Use --template e --output juntos para exportar um Excel.")
    if args.template and not mapping:
        parser.error("A exportação exige pelo menos um --map-column revisado.")
    if bool(args.store_name) != bool(args.store_lookup):
        parser.error("Use --store-name e --store-lookup juntos para preencher unidade/CNPJ.")
    if args.store_name and not mapping:
        parser.error("A consulta de unidade/CNPJ exige pelo menos um --map-column.")

    try:
        result = analyze_file(
            args.arquivo,
            separator=args.separator,
            sheet_name=int(args.sheet) if args.sheet.isdecimal() else args.sheet,
            text_columns=args.text_column,
            required_columns=args.required_column,
            unique_columns=args.unique_column,
            report_type=args.report_type,
            approved_mapping=mapping,
            drop_empty_rows=args.drop_empty_rows,
            require_value_columns=args.require_value_column,
            excluded_values=excluded_values,
            strip_text=args.strip_text,
            store_name=args.store_name,
            store_lookup_path=args.store_lookup,
        )
        _print_report(result)
        if result.canonical_dataset is not None:
            print("\nPrévia do conjunto canônico em memória:")
            print(f"Colunas: {result.canonical_dataset.column_names}")
            preview = result.canonical_dataset.data.head().copy()
            if "cnpj" in preview.columns:
                preview["cnpj"] = "[oculto na prévia do terminal]"
            print(preview.to_string(index=False))
            if args.template and args.output:
                output_path = write_excel_template(
                    result.canonical_dataset,
                    template_path=args.template,
                    output_path=args.output,
                )
                print(f"\nArquivo padronizado salvo em: {output_path}")
            else:
                print("Nenhum arquivo de saída foi gravado.")
        else:
            print(
                "\nNenhum mapeamento foi aplicado. Para aplicar sugestões revisadas, "
                "use --map-column ORIGEM=CANONICO."
            )
    except (IngestionError, ExportError, ValueError) as exc:
        parser.error(str(exc))

    return 0
