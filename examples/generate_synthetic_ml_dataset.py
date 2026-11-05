"""Gera corpus sintético e rotulado para preparar ML, sem treinar modelo.

Saídas em data/synthetic/farmacia_demo/:
- column_mappings_header_ml_demo.csv: cabeçalho -> campo canônico;
- column_value_training_X_demo.csv: características das colunas;
- column_value_training_y_demo.csv: rótulos esperados separados;
- source_profile_folds_demo.csv: perfis reservados juntos nas futuras avaliações.

Execute na raiz do projeto com:
    python examples/generate_synthetic_ml_dataset.py
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

import pandas as pd

from data_intelligence.profiling import profile_frame_columns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic" / "farmacia_demo"

PROFILES = [
    "FarmaNuvem",
    "RedeCuidar",
    "PontoSaude",
    "BoticaCloud",
    "Drogaria360",
    "PharmaLink",
    "SaudeMaisERP",
    "MedGestor",
    "FarmaciaDigital",
    "VidaFarma",
    *(f"SistemaFicticio{number:02d}" for number in range(11, 21)),
]

STOCK_FIELDS = [
    "ean",
    "descricao_produto",
    "grupo",
    "quantidade",
    "valor_total_custo",
    "unidade",
]
SALES_FIELDS = [
    "mes",
    "ean",
    "descricao_produto",
    "grupo",
    "quantidade",
    "valor_total_bruto",
    "valor_total_liquido",
    "unidade",
]

# Campos usados pelos modelos sintéticos de saída. A identidade da unidade/CNPJ
# é resolvida pelo cadastro; as outras colunas podem vir das planilhas fonte.
STOCK_HEADER_FIELDS = [
    "ean", "descricao_produto", "grupo", "subgrupo", "laboratorio",
    "quantidade", "giro_mensal", "valor_total_custo", "custo_medio",
    "valor_total_liquido", "unidade",
]
SALES_HEADER_FIELDS = [
    "mes", "filial", "ean", "descricao_produto", "grupo", "subgrupo",
    "laboratorio", "quantidade", "valor_total_bruto", "valor_total_liquido",
    "valor_total_custo", "lucro_bruto", "desconto_maximo", "desconto_padrao",
    "desconto_preferencial", "unidade",
]

HEADER_VARIANTS = {
    "ean": [
        "Código de barras", "GTIN do item", "Barcode", "Identificador universal",
        "EAN produto", "Código GTIN", "GTIN-13", "Referência EAN", "Item GTIN",
        "Código universal", "EAN comercial", "Código do produto", "GTIN cadastrado",
        "Identificação EAN", "Número de barras", "Chave do produto", "Código global",
        "EAN principal", "Referência do item", "Identificador GTIN",
    ],
    "descricao_produto": [
        "Nome comercial", "Descrição do item", "Apresentação", "Medicamento",
        "Produto da venda", "Descrição resumida", "Nome de catálogo", "Item comercial",
        "Descrição produto", "Produto cadastrado", "Nome do item", "Descrição mercantil",
        "Apresentação comercial", "Item do catálogo", "Nome produto", "Produto/descrição",
        "Descrição do medicamento", "Nome reduzido", "Produto faturado", "Denominação",
    ],
    "grupo": [
        "Setor", "Categoria comercial", "Família", "Seção", "Segmento mercadológico",
        "Grupo de produtos", "Classificação", "Linha de produtos", "Categoria",
        "Grupo mercadológico", "Segmento", "Classe do item", "Família comercial",
        "Grupo de mercadorias", "Seção comercial", "Categoria de produto",
        "Agrupador", "Linha de catálogo", "Divisão", "Tipo de produto",
    ],
    "quantidade": [
        "Saldo disponível", "Quantidade em mãos", "Saldo físico", "Existência atual",
        "Saldo em unidades", "Unidades no estoque", "Estoque disponível",
        "Quantidade em saldo", "Saldo contado", "Unidades disponíveis", "Qtd. atual",
        "Itens em estoque", "Volume em saldo", "Unidades restantes", "Quantidade física",
        "Saldo do produto", "Qtd disponível", "Estoque atual", "Unidades armazenadas",
        "Quantidade registrada",
    ],
    "valor_total_custo": [
        "Custo do estoque", "Valor de aquisição total", "Montante em custo",
        "Investimento total", "Total de custo", "Custo acumulado", "Valor total de custo",
        "Custo dos itens", "Custo total atual", "Montante de aquisição", "Custo em estoque",
        "Valor de custo agregado", "Custo total dos produtos", "Valor investido",
        "Total de aquisição", "Custo contabilizado", "Custo do saldo", "Valor custo estoque",
        "Custo consolidado", "Montante de custo total",
    ],
    "unidade": [
        "Loja", "Unidade operacional", "Código da unidade", "Ponto de estoque",
        "Estabelecimento", "Unidade de negócio", "Loja emitente", "Centro de operação",
        "Unidade cadastrada", "Ponto de venda", "Local de operação", "Unidade emissora",
        "Loja de origem", "Estabelecimento comercial", "Código filial", "Unidade de venda",
        "Localidade", "Farmácia", "Identificação da loja",
    ],
    "mes": [
        "Período", "Mês de movimento", "Competência", "Mês da venda", "Referência mensal",
        "Mês de apuração", "Período da venda", "Competência venda", "Mês referência",
        "Período comercial", "Data-base mensal", "Mês comercial", "Período de referência",
        "Competência do relatório", "Mês de faturamento", "Referência da venda",
        "Período analisado", "Ano e mês", "Mês consolidado", "Data de referência",
    ],
    "valor_total_bruto": [
        "Valor vendido bruto", "Total antes de descontos", "Valor original das vendas",
        "Faturamento sem abatimentos", "Valor sem desconto", "Montante bruto",
        "Total bruto dos itens", "Bruto dos produtos", "Valor total sem deduções",
        "Total comercial bruto", "Venda antes de descontos", "Receita inicial",
        "Valor bruto faturado", "Total de vendas bruto", "Faturamento original",
        "Montante antes de abatimento", "Bruto da operação", "Receita bruta dos itens",
        "Valor de tabela vendido", "Total bruto comercializado",
    ],
    "valor_total_liquido": [
        "Venda", "Valor Vendido", "Valor líquido vendido", "Total recebido", "Valor líquido recebido",
        "Receita após abatimentos", "Valor recebido líquido", "Montante líquido",
        "Total líquido dos itens", "Líquido dos produtos", "Valor total após desconto",
        "Total comercial líquido", "Venda após descontos", "Receita final",
        "Valor líquido faturado", "Total de vendas líquido", "Faturamento recebido",
        "Montante após abatimento", "Líquido da operação", "Receita líquida dos itens",
        "Valor final vendido", "Total líquido comercializado",
    ],
    "subgrupo": [
        "Departamento", "Subcategoria", "Família detalhada", "Segmento específico", "Classe secundária",
        "Categoria filha", "Grupo secundário", "Divisão de produto", "Subgrupo mercantil",
        "Classificação detalhada", "Linha específica", "Tipo secundário", "Setor detalhado",
        "Ramo do produto", "Categoria complementar", "Nível de grupo 2",
        "Subdivisão comercial", "Família de segundo nível", "Grupo filho",
        "Segmento de catálogo", "Classificação secundária",
    ],
    "laboratorio": [
        "Fabricante do item", "Marca responsável", "Indústria fabricante", "Laboratório fornecedor",
        "Nome do fabricante", "Marca comercial", "Fornecedor fabricante", "Indústria do produto",
        "Fabricante cadastrado", "Marca do produto", "Origem laboratorial", "Empresa fabricante",
        "Produtor do item", "Laboratório responsável", "Marca registrada do produto",
        "Fabricante principal", "Indústria responsável", "Nome da indústria",
        "Fornecedor principal", "Laboratório do produto",
    ],
    "giro_mensal": [
        "Giro mensal", "Unidades vendidas no mês", "Rotação mensal", "Consumo mensal médio",
        "Saídas por mês", "Média de venda mensal", "Giro médio mensal", "Movimento mensal",
        "Unidades movimentadas no mês", "Índice de giro mensal", "Consumo médio mensal",
        "Venda média mensal", "Rotatividade mensal", "Quantidade de saída mensal",
        "Média mensal de unidades", "Giro no período mensal", "Volume mensal movimentado",
        "Vendas médias do mês", "Saída mensal média", "Rotação do estoque mensal",
    ],
    "custo_medio": [
        "Custo médio", "Preço médio de aquisição", "Valor médio de custo", "Custo unitário médio",
        "Média de custo unitário", "Custo médio por unidade", "Aquisição média unitária",
        "Valor médio por item", "Custo ponderado médio", "Preço de custo médio",
        "Média ponderada de custo", "Custo médio cadastrado", "Valor unitário médio de custo",
        "Custo médio do produto", "Custo por unidade médio", "Média de aquisição por item",
        "Valor médio de compra", "Custo padrão unitário", "Custo médio atual",
        "Aquisição média do produto",
    ],
    "filial": [
        "Código da filial", "Identificador numérico da loja", "Número da unidade de venda",
        "Código do ponto de venda", "Loja numérica", "ID da filial", "Referência da loja emissora",
        "Número do estabelecimento", "Identificação da filial de venda", "Código da loja de origem",
        "Identificador do ponto comercial", "Número da filial", "Loja responsável pela venda",
        "Código interno da loja", "Unidade numérica de venda", "ID do estabelecimento vendedor",
        "Referência numérica da filial", "Loja de faturamento", "Código da unidade emissora",
        "Identificador da loja de venda",
    ],
    "lucro_bruto": [
        "Lucro bruto", "Margem bruta em valor", "Resultado bruto da venda", "Ganho bruto por item",
        "Valor de lucro antes de despesas", "Lucro comercial bruto", "Resultado bruto comercial",
        "Margem financeira bruta", "Valor bruto de ganho", "Lucro da operação antes de despesas",
        "Ganho comercial bruto", "Resultado financeiro bruto", "Lucro bruto apurado",
        "Montante de lucro bruto", "Valor do ganho bruto", "Margem bruta calculada",
        "Lucro bruto dos produtos", "Resultado bruto por produto", "Lucro total bruto",
        "Retorno bruto da venda",
    ],
    "desconto_maximo": [
        "Desconto máximo", "Limite superior de desconto", "Percentual máximo permitido",
        "Teto de desconto", "Maior desconto autorizado", "Desconto máximo comercial",
        "Limite máximo promocional", "Percentual teto de abatimento", "Desconto máximo da loja",
        "Máximo abatimento permitido", "Maior percentual de desconto", "Limite de desconto total",
        "Desconto máximo cadastrado", "Teto percentual de redução", "Abatimento máximo autorizado",
        "Percentual máximo de redução", "Limite superior promocional", "Desconto máximo aplicável",
        "Maior redução autorizada", "Máximo comercial de desconto",
    ],
    "desconto_padrao": [
        "Desconto padrão", "Percentual habitual de desconto", "Abatimento de rotina",
        "Desconto regular", "Percentual padrão aplicado", "Desconto base da venda",
        "Redução comercial padrão", "Abatimento usual", "Desconto padrão cadastrado",
        "Percentual regular de redução", "Desconto normal", "Taxa padrão de abatimento",
        "Redução de preço habitual", "Desconto comercial base", "Percentual comum de desconto",
        "Abatimento padrão da loja", "Desconto operacional usual", "Taxa regular de desconto",
        "Percentual de redução padrão", "Desconto corrente",
    ],
    "desconto_preferencial": [
        "Desconto preferencial", "Abatimento para cliente preferencial", "Percentual de benefício especial",
        "Desconto de cliente VIP", "Redução preferencial", "Desconto para fidelidade",
        "Benefício percentual preferencial", "Abatimento de cliente especial", "Desconto de convênio",
        "Percentual de desconto fidelidade", "Desconto para cliente cadastrado",
        "Redução de preço preferencial", "Benefício comercial especial", "Desconto de relacionamento",
        "Percentual para clientes especiais", "Abatimento preferencial cadastrado",
        "Desconto de programa de benefícios", "Taxa de redução preferencial",
        "Desconto especial do cliente", "Benefício de fidelização",
    ],
}


def _ean13(base12: int) -> str:
    digits = str(base12).zfill(12)
    weighted_sum = sum(
        int(digit) * (1 if index % 2 == 0 else 3)
        for index, digit in enumerate(digits)
    )
    check_digit = (10 - weighted_sum % 10) % 10
    return digits + str(check_digit)


def _headers_for(profile_index: int, report_type: str, fields: list[str]) -> dict[str, str]:
    # 13 é coprimo com os comprimentos das listas (19–22), então cada
    # sistema percorre variantes diferentes sem repetir o mesmo cabeçalho.
    offset = profile_index * 13 + (1 if report_type == "vendas" else 0)
    return {
        field: HEADER_VARIANTS[field][(offset + field_index * 7) % len(HEADER_VARIANTS[field])]
        for field_index, field in enumerate(fields)
    }


def _synthetic_rows(profile_index: int, report_type: str) -> list[dict[str, object]]:
    rng = random.Random(20261030 + profile_index * 101 + (report_type == "vendas"))
    unit = f"UNIDADE FICTÍCIA {profile_index + 1:02d}"
    products: list[dict[str, object]] = []

    for product_index in range(48):
        quantity = rng.randint(1, 70)
        unit_cost = round(rng.uniform(1.25, 38.5), 2)
        selling_price = round(unit_cost * rng.uniform(1.35, 2.4), 2)
        products.append(
            {
                "ean": _ean13(290000000000 + profile_index * 1000 + product_index + 1),
                "descricao_produto": f"Produto fictício {profile_index + 1:02d}-{product_index + 1:03d}",
                "grupo": f"GRUPO FICTÍCIO {chr(65 + (product_index + profile_index) % 5)}",
                "quantidade": quantity,
                "valor_total_custo": round(quantity * unit_cost, 2),
                "unidade": unit,
                "mes": f"2026-{(product_index % 12) + 1:02d}",
                "valor_total_bruto": round(quantity * selling_price, 2),
                "valor_total_liquido": round(quantity * selling_price * rng.uniform(0.87, 0.99), 2),
            }
        )

    if report_type == "estoque":
        rows = products
        fields = STOCK_FIELDS
    else:
        fields = SALES_FIELDS
        rows = []
        for product_index, product in enumerate(products):
            for movement in range(2):
                quantity = (product_index + movement * 3) % 9 + 1
                gross = round(quantity * rng.uniform(4.25, 95.0), 2)
                discount_rate = rng.uniform(0.0, 0.15)
                rows.append(
                    {
                        **product,
                        "mes": f"2026-{(product_index + movement) % 12 + 1:02d}",
                        "quantidade": quantity,
                        "valor_total_bruto": gross,
                        "valor_total_liquido": round(gross * (1 - discount_rate), 2),
                    }
                )

    # Introduz valores ausentes controlados para que as características não
    # sejam idênticas em todas as colunas. Todos os dados continuam fictícios.
    for row_index, row in enumerate(rows):
        for field_index, field in enumerate(fields):
            if (row_index + profile_index * 2 + field_index * 5) % 97 == 0:
                row[field] = None
    return rows


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    feature_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, str]] = []
    header_rows: list[dict[str, str]] = []
    manifest_rows: list[dict[str, object]] = []

    for profile_index, profile in enumerate(PROFILES):
        for report_type, fields in (("estoque", STOCK_FIELDS), ("vendas", SALES_FIELDS)):
            header_fields = (
                STOCK_HEADER_FIELDS if report_type == "estoque" else SALES_HEADER_FIELDS
            )
            header_map = _headers_for(profile_index, report_type, header_fields)
            rows = _synthetic_rows(profile_index, report_type)
            shuffled_fields = list(fields)
            random.Random(profile_index * 13 + len(report_type)).shuffle(shuffled_fields)
            has_header = (
                profile_index % 2 == 0
                if report_type == "estoque"
                else profile_index % 3 != 0
            )
            headers = [header_map[field] for field in shuffled_fields] if has_header else None
            matrix = [[row[field] for field in shuffled_fields] for row in rows]
            frame = pd.DataFrame(matrix, columns=headers)
            column_features = profile_frame_columns(
                frame,
                has_header=has_header,
                headers=headers,
            )

            for position, field in enumerate(shuffled_fields):
                example_id = f"{profile}__{report_type}__col{position + 1:02d}"
                # Identificadores, origem, tipo de relatório, cabeçalho e amostras
                # são metadados ou pistas de outro experimento. Não os misturamos
                # com as características de valores da coluna.
                value_features = {
                    name: value
                    for name, value in column_features[position].items()
                    if name not in {
                        "column_position_1_based",
                        "has_header",
                        "source_header",
                        "sample_values_json",
                        "table_width",
                    }
                }
                feature_rows.append(
                    {
                        "example_id": example_id,
                        "source_profile": profile,
                        "report_type": report_type,
                        "source_sheet_id": f"{profile}__{report_type}",
                        **value_features,
                    }
                )
                label_rows.append(
                    {"example_id": example_id, "canonical_field": field}
                )
                manifest_rows.append(
                    {
                        "example_id": example_id,
                        "source_profile": profile,
                        "report_type": report_type,
                        "source_sheet_id": f"{profile}__{report_type}",
                        "column_position_1_based": position + 1,
                        "has_header": has_header,
                    }
                )
            if has_header:
                for field in header_fields:
                    header_rows.append(
                        {
                            "source_profile": profile,
                            "report_type": report_type,
                            "source_column": header_map[field],
                            "canonical_field": field,
                        }
                    )

    feature_frame = pd.DataFrame(feature_rows)
    labels_frame = pd.DataFrame(label_rows)
    header_frame = pd.DataFrame(header_rows)
    folds_frame = pd.DataFrame(
        [
            {"source_profile": profile, "fold_id": (index % 5) + 1}
            for index, profile in enumerate(PROFILES)
        ]
    )
    manifest_frame = pd.DataFrame(manifest_rows)

    feature_frame.to_csv(
        OUTPUT_DIR / "column_value_training_X_demo.csv",
        index=False,
        encoding="utf-8-sig",
    )
    labels_frame.to_csv(
        OUTPUT_DIR / "column_value_training_y_demo.csv",
        index=False,
        encoding="utf-8-sig",
    )
    header_frame.to_csv(
        OUTPUT_DIR / "column_mappings_header_ml_demo.csv",
        index=False,
        encoding="utf-8-sig",
    )
    folds_frame.to_csv(
        OUTPUT_DIR / "source_profile_folds_demo.csv",
        index=False,
        encoding="utf-8-sig",
    )
    manifest_frame.to_csv(
        OUTPUT_DIR / "column_value_manifest_demo.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Perfis fictícios: {len(PROFILES)}")
    print(f"Exemplos com cabeçalho: {len(header_frame)}")
    print(f"Exemplos por valores da coluna: {len(feature_frame)}")
    print(
        "Exemplos sem cabeçalho: "
        f"{int((~manifest_frame['has_header']).sum())}"
    )
    print(f"Campos-alvo: {labels_frame['canonical_field'].nunique()}")
    print(f"Dobras agrupadas por sistema: {folds_frame['fold_id'].nunique()}")
    print(f"Arquivos sintéticos criados em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
