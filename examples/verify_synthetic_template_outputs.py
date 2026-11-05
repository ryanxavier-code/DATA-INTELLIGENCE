"""Compara as saídas do CLI com os valores sintéticos esperados.

Execute depois de gerar os arquivos padronizados pelo CLI:
    python examples/verify_synthetic_template_outputs.py
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from data_intelligence.identity import lookup_store


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic" / "farmacia_demo"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
STORE_NAME = "FARMÁCIA MODELO - UNIDADE 27"
REPORTS = {
    "estoque": {
        "source": "TESTEML_ESTOQUE.xlsx",
        "template": "modelo_estoque_demo.xlsx",
        "output": "ESTOQUE_PADRONIZADO_DEMO.xlsx",
        "mapping": {
            "EAN": "ean",
            "Produto": "descricao_produto",
            "Categoria": "grupo",
            "Departamento": "subgrupo",
            "Laboratório": "laboratorio",
            "Estoque": "quantidade",
            "Giro Mensal": "giro_mensal",
            "Custo": "valor_total_custo",
            "Custo Médio": "custo_medio",
            "Venda": "valor_total_liquido",
        },
    },
    "vendas": {
        "source": "TESTEML_VENDAS.xlsx",
        "template": "modelo_vendas_demo.xlsx",
        "output": "VENDAS_PADRONIZADAS_DEMO.xlsx",
        "mapping": {
            "Período": "mes",
            "filial": "filial",
            "EAN": "ean",
            "Produto": "descricao_produto",
            "Categoria": "grupo",
            "Departamento": "subgrupo",
            "Laboratório": "laboratorio",
            "Quantidade Vendida": "quantidade",
            "Valor Vendido": "valor_total_liquido",
            "Custo": "valor_total_custo",
            "Lucro Bruto": "lucro_bruto",
            "Desconto Máximo": "desconto_maximo",
            "Desconto Padrão": "desconto_padrao",
            "Desconto Preferencial": "desconto_preferencial",
        },
    },
}


def _same_value(actual: object, expected: object, *, text: bool) -> bool:
    actual_missing = pd.isna(actual)
    expected_missing = pd.isna(expected)
    if actual_missing or expected_missing:
        return bool(actual_missing and expected_missing)
    if text:
        return str(actual) == str(expected)
    try:
        return math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=1e-9)
    except (TypeError, ValueError):
        return str(actual) == str(expected)


def main() -> None:
    registered_name, cnpj = lookup_store(
        DATA_DIR / "cadastro_unidades_demo.xlsx", STORE_NAME
    )
    failures: list[str] = []
    total_cells = 0
    matching_cells = 0

    for report_type, config in REPORTS.items():
        source_path = DATA_DIR / config["source"]
        template_path = DATA_DIR / config["template"]
        output_path = OUTPUT_DIR / config["output"]
        if not output_path.is_file():
            raise FileNotFoundError(
                f"Saída não encontrada: {output_path}. Gere-a primeiro pelo comando do CLI."
            )

        source = pd.read_excel(source_path, dtype={"EAN": "string"})
        source["EAN"] = source["EAN"].str.strip()
        expected_source = source.loc[source["EAN"].notna() & source["EAN"].ne("")].reset_index(drop=True)
        expected_by_target = {
            target: expected_source[origin].reset_index(drop=True)
            for origin, target in config["mapping"].items()
        }
        expected_by_target["unidade"] = pd.Series(
            [registered_name] * len(expected_source), dtype="string"
        )
        expected_by_target["cnpj"] = pd.Series([cnpj] * len(expected_source), dtype="string")

        template_headers = list(pd.read_excel(template_path, nrows=0).columns)
        actual = pd.read_excel(
            output_path,
            dtype={"ean": "string", "cnpj": "string"},
        )
        if list(actual.columns) != template_headers:
            failures.append(f"{report_type}: cabeçalhos da saída diferem do modelo")
        if len(actual) != len(expected_source):
            failures.append(
                f"{report_type}: esperadas {len(expected_source)} linhas, encontradas {len(actual)}"
            )

        for column in template_headers:
            if column not in expected_by_target:
                failures.append(f"{report_type}: não há valor esperado para {column!r}")
                continue
            expected_values = expected_by_target[column]
            if len(actual) != len(expected_values):
                continue
            total_cells += len(actual)
            text_field = column in {"ean", "cnpj", "unidade", "descricao_produto", "grupo", "subgrupo", "laboratorio", "mes"}
            for row_index, (actual_value, expected_value) in enumerate(
                zip(actual[column], expected_values, strict=True), start=2
            ):
                if _same_value(actual_value, expected_value, text=text_field):
                    matching_cells += 1
                else:
                    failures.append(
                        f"{report_type}.{column}, linha {row_index}: "
                        f"esperado={expected_value!r}, encontrado={actual_value!r}"
                    )

        ean_values = actual["ean"].astype("string")
        invalid_eans = ean_values.isna() | ~ean_values.str.fullmatch(r"\d{13}").fillna(False)
        if invalid_eans.any():
            failures.append(f"{report_type}: {int(invalid_eans.sum())} EAN(s) não são texto de 13 dígitos")
        if actual["cnpj"].astype("string").map(lambda value: len(str(value)) != 14).any():
            failures.append(f"{report_type}: CNPJ sintético não foi mantido como texto de 14 dígitos")

        print(
            f"{report_type.title()}: entrada={len(source)} linhas, "
            f"retidas={len(expected_source)}, saída={len(actual)} x {len(actual.columns)}, "
            f"células vazias={int(actual.isna().sum().sum())}"
        )

    print(
        f"Correspondência com os valores esperados: {matching_cells}/{total_cells} "
        f"({matching_cells / total_cells:.1%})"
    )
    if failures:
        print(f"Verificação encontrou {len(failures)} divergência(s):")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print("Saídas conferidas: colunas, valores, unidade/CNPJ fictícios e EAN como texto.")


if __name__ == "__main__":
    main()
