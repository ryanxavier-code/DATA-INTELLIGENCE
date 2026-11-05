"""Vocabulários-alvo para os formatos padronizados de estoque e vendas."""

from collections.abc import Mapping, Sequence


STOCK_SCHEMA: dict[str, tuple[str, ...]] = {
    "cnpj": ("cnpj", "cnpj estabelecimento", "documento da empresa", "tax id"),
    "unidade": ("unidade", "filial", "loja", "farmacia", "estabelecimento", "branch", "store"),
    "mes": ("mês", "mes", "competencia", "período", "periodo", "month"),
    "ean": ("ean", "gtin", "código de barras", "codigo de barras", "barcode", "bar code"),
    "descricao_produto": ("descrição produto", "descricao produto", "produto", "nome do produto", "item", "product name", "description"),
    "grupo": ("grupo", "categoria", "category", "department"),
    "subgrupo": ("subgrupo", "subcategoria", "departamento", "subcategoria de produto", "subcategory"),
    "laboratorio": ("laboratório", "laboratorio", "fabricante", "marca", "manufacturer", "brand"),
    "quantidade": ("quantidade", "qtd", "qty", "quantity", "units"),
    "valor_total_custo": ("valor total custo", "custo total", "valor de custo total", "total cost"),
    "valor_total_liquido": ("valor total liquido", "venda liquida", "valor vendido", "venda", "net sales"),
    "giro_mensal": ("giro mensal", "rotacao mensal", "consumo mensal", "venda media mensal", "monthly turnover"),
    "custo_medio": ("custo medio", "custo unitario medio", "preco medio de aquisicao", "average cost"),
    "data_cadastro": ("data cadastro", "data de cadastro", "data inclusão", "registration date"),
    "data_ultima_venda": ("data ult venda", "data última venda", "data ultima venda", "última venda", "last sale date"),
}

SALES_SCHEMA: dict[str, tuple[str, ...]] = {
    "cnpj": STOCK_SCHEMA["cnpj"],
    "unidade": ("unidade", "loja", "farmacia", "estabelecimento", "branch", "store"),
    "filial": ("codigo da filial", "id da filial", "numero da filial", "codigo da loja de origem", "store code"),
    "ean": STOCK_SCHEMA["ean"],
    "codigo_reduzido": ("cod reduzido", "código reduzido", "codigo reduzido", "código interno reduzido", "reduced code"),
    "mes": STOCK_SCHEMA["mes"],
    "descricao_produto": STOCK_SCHEMA["descricao_produto"],
    "grupo": STOCK_SCHEMA["grupo"],
    "subgrupo": STOCK_SCHEMA["subgrupo"],
    "laboratorio": STOCK_SCHEMA["laboratorio"],
    "quantidade": STOCK_SCHEMA["quantidade"],
    "valor_total_bruto": ("valor total bruto", "venda bruta", "total bruto", "gross sales", "gross amount"),
    "valor_total_liquido": ("valor total líquido", "valor total liquido", "venda líquida", "venda liquida", "total líquido", "net sales", "net amount"),
    "valor_total_custo": STOCK_SCHEMA["valor_total_custo"],
    "lucro_bruto": ("lucro bruto", "margem bruta em valor", "resultado bruto da venda", "gross profit"),
    "desconto_maximo": ("desconto maximo", "teto de desconto", "limite maximo de desconto", "maximum discount"),
    "desconto_padrao": ("desconto padrao", "desconto regular", "percentual padrao aplicado", "standard discount"),
    "desconto_preferencial": ("desconto preferencial", "desconto para cliente preferencial", "desconto de fidelidade", "preferred discount"),
}


REPORT_SCHEMAS: dict[str, Mapping[str, Sequence[str]]] = {
    "estoque": STOCK_SCHEMA,
    "vendas": SALES_SCHEMA,
}


def get_report_schema(report_type: str) -> Mapping[str, Sequence[str]]:
    """Retorna aliases do relatório ou explica os tipos aceitos."""
    try:
        return REPORT_SCHEMAS[report_type]
    except KeyError as exc:
        available = ", ".join(REPORT_SCHEMAS)
        raise ValueError(
            f"Tipo de relatório {report_type!r} desconhecido. Use: {available}."
        ) from exc
