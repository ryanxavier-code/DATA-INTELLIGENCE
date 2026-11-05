"""Compara o primeiro classificador com os cabeçalhos dos arquivos sintéticos.

Este teste didático treina nos cabeçalhos sintéticos rotulados e avalia os dois
workbooks TESTEML. Os nomes são artificiais; várias formas de cabeçalho podem
aparecer no conjunto de treino, portanto este não é um teste de sistema real.

Execute na raiz do projeto:
    python examples/evaluate_synthetic_template_mapping.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic" / "farmacia_demo"
OUTPUT_PATH = DATA_DIR / "synthetic_template_header_predictions_demo.csv"

# Gabarito revisado para os campos de origem previstos nos modelos sintéticos.
# Unidade e CNPJ vêm de uma consulta separada ao cadastro, então não são
# previstos a partir destas planilhas fonte.
REPORTS = {
    "estoque": {
        "source_file": "TESTEML_ESTOQUE.xlsx",
        "expected": {
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
        "source_file": "TESTEML_VENDAS.xlsx",
        "expected": {
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


def _build_model() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(2, 5),
                    lowercase=True,
                    strip_accents="unicode",
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced", max_iter=2000, random_state=42
                ),
            ),
        ]
    )


def main() -> None:
    training = pd.read_csv(DATA_DIR / "column_mappings_header_ml_demo.csv")
    train_text = (
        training["report_type"].astype(str).str.lower()
        + " [SEP] "
        + training["source_column"].astype(str)
    )
    model = _build_model().fit(train_text, training["canonical_field"].astype(str))
    seen_inputs = {
        (str(row.report_type).casefold(), str(row.source_column).casefold())
        for row in training.itertuples(index=False)
    }

    prediction_rows: list[dict[str, object]] = []
    for report_type, config in REPORTS.items():
        headers = list(pd.read_excel(DATA_DIR / config["source_file"], nrows=0).columns)
        scored_headers = config["expected"]
        missing = set(scored_headers) - set(headers)
        if missing:
            raise ValueError(f"{report_type}: cabeçalhos do gabarito não encontrados: {sorted(missing)}")

        model_input = [f"{report_type} [SEP] {header}" for header in scored_headers]
        predicted = model.predict(model_input)
        probability_matrix = model.predict_proba(model_input)
        classes = model.named_steps["classifier"].classes_
        for index, (header, expected) in enumerate(scored_headers.items()):
            ranked = probability_matrix[index].argsort()[::-1][:3]
            top3 = [str(classes[class_index]) for class_index in ranked]
            prediction_rows.append(
                {
                    "report_type": report_type,
                    "source_column": header,
                    "canonical_field_expected": expected,
                    "prediction_top1": str(predicted[index]),
                    "exact_header_seen_in_training": (
                        report_type.casefold(), header.casefold()
                    ) in seen_inputs,
                    "top1_correct": bool(predicted[index] == expected),
                    "predictions_top3_json": json.dumps(top3, ensure_ascii=False),
                    "top3_correct": expected in top3,
                    "top1_confidence_uncalibrated": round(
                        float(probability_matrix[index].max()), 6
                    ),
                }
            )

    results = pd.DataFrame(prediction_rows)
    results.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    top1_count = int(results["top1_correct"].sum())
    top3_count = int(results["top3_correct"].sum())
    seen_count = int(results["exact_header_seen_in_training"].sum())
    print("Teste em workbooks totalmente sintéticos, fora do CSV de cabeçalhos:")
    print(f"Campos elegíveis para o classificador: {len(results)}")
    print(f"Top-1: {top1_count}/{len(results)} ({top1_count / len(results):.1%})")
    print(f"Top-3: {top3_count}/{len(results)} ({top3_count / len(results):.1%})")
    print(f"Cabeçalhos exatos também presentes no treino: {seen_count}/{len(results)}")
    print("Unidade/CNPJ são preenchidos pelo cadastro e não entram nesta avaliação de cabeçalhos.")
    print("Interprete como demonstração com dados sintéticos, não como validação real.")
    print(f"Detalhe por coluna: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
