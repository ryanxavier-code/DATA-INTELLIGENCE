"""Demonstra lookup por chave e agregação em exemplos sintéticos.

Execute na raiz do projeto com:
    python examples/process_synthetic_lookup_and_aggregation.py

O script não cria nem altera arquivos. O resumo é calculado em memória.
"""

from pathlib import Path

from data_intelligence.ingestion import read_excel
from data_intelligence.transforms import aggregate_table, lookup_columns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "farmacia_demo"
    / "DATASET_FORMATOS_FICTICIOS.xlsx"
)


def main() -> None:
    reference = read_excel(
        WORKBOOK_PATH,
        sheet_name="Cadastro_Produtos",
        dtype={"EAN": "string"},
    ).data

    lookup_input = read_excel(
        WORKBOOK_PATH,
        sheet_name="Lookup_PROCV",
        dtype={"EAN": "string"},
    ).data[["EAN", "Quantidade"]]
    lookup_result = lookup_columns(
        lookup_input,
        reference,
        source_key="EAN",
        reference_key="EAN",
        columns={
            "Descrição encontrada": "Descricao_Referencia",
            "Grupo encontrado": "Grupo_Referencia",
        },
    )

    print("Demonstração de lookup por EAN")
    print(f"Correspondências: {lookup_result.matched_rows}")
    print(f"Linhas sem correspondência: {lookup_result.unmatched_rows}")
    print(f"Linhas sem chave: {lookup_result.rows_without_key}")
    print(f"Chaves não encontradas: {lookup_result.unmatched_keys}")
    print(lookup_result.data.to_string(index=False))

    sales = read_excel(
        WORKBOOK_PATH,
        sheet_name="Vendas_Com_Header",
        dtype={"GTIN produto": "string"},
    ).data
    enriched_sales = lookup_columns(
        sales,
        reference,
        source_key="GTIN produto",
        reference_key="EAN",
        columns={
            "descricao_referencia": "Descricao_Referencia",
            "grupo_referencia": "Grupo_Referencia",
        },
    )
    sales_summary = aggregate_table(
        enriched_sales.data,
        group_by=[
            "GTIN produto",
            "Filial emissora",
            "descricao_referencia",
        ],
        metrics={
            "quantidade_total": ("Qtd. comercializada", "sum"),
            "valor_bruto_total": ("Valor bruto item", "sum"),
            "valor_liquido_total": ("Valor líquido item", "sum"),
        },
    )

    print("\nVendas detalhadas enriquecidas e agregadas")
    print(f"Linhas de venda lidas: {len(sales)}")
    print(f"Linhas sem correspondência de produto: {enriched_sales.unmatched_rows}")
    print(f"Grupos agregados: {len(sales_summary)}")
    print(sales_summary.to_string(index=False))


if __name__ == "__main__":
    main()
