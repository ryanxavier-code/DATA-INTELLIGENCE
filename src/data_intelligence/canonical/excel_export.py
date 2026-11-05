"""Exportação explícita de um Dataset canônico para um modelo Excel."""

from copy import copy
from pathlib import Path
import unicodedata

import pandas as pd
from openpyxl import load_workbook

from data_intelligence.dataset import Dataset


class ExportError(Exception):
    """Erro ao gravar dados em um modelo de saída."""


def _column_key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip().casefold())
    return "".join(character for character in text if not unicodedata.combining(character))


def write_excel_template(
    dataset: Dataset,
    template_path: str | Path,
    output_path: str | Path,
    *,
    sheet_name: str | None = None,
    header_row: int = 1,
) -> Path:
    """Grava as colunas correspondentes em uma cópia de um modelo Excel.

    Os nomes das colunas em ``dataset`` devem estar no formato canônico e
    corresponder aos cabeçalhos do modelo, ignorando espaços externos e
    diferenças entre maiúsculas e minúsculas. Colunas do modelo sem
    correspondência ficam vazias. A linha de cabeçalho é preservada; as linhas
    abaixo dela na aba escolhida são substituídas. O arquivo do modelo nunca é
    salvo por esta função: a gravação ocorre apenas em ``output_path``.
    """
    template = Path(template_path)
    output = Path(output_path)

    if template.suffix.casefold() != ".xlsx" or output.suffix.casefold() != ".xlsx":
        raise ExportError("A exportação para modelo aceita arquivos .xlsx.")
    if not template.is_file():
        raise ExportError(f"Modelo Excel não encontrado: {template}")
    if template.resolve() == output.resolve():
        raise ExportError("O arquivo de saída não pode sobrescrever o modelo.")
    if dataset.source.resolve() == output.resolve():
        raise ExportError("O arquivo de saída não pode sobrescrever a fonte dos dados.")
    if header_row < 1:
        raise ExportError("header_row deve ser 1 ou maior.")

    try:
        workbook = load_workbook(template)
        if sheet_name is None:
            worksheet = workbook.active
        elif sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
        else:
            raise ExportError(f"Aba não encontrada no modelo: {sheet_name}")

        headers = [
            worksheet.cell(row=header_row, column=column).value
            for column in range(1, worksheet.max_column + 1)
        ]
        while headers and headers[-1] is None:
            headers.pop()
        if not headers:
            raise ExportError(f"Nenhum cabeçalho encontrado na linha {header_row}.")
        named_headers = [_column_key(header) for header in headers if header is not None]
        if len(named_headers) != len(set(named_headers)):
            raise ExportError("O modelo contém cabeçalhos repetidos na linha selecionada.")

        # Guarda os estilos de uma linha de dados do modelo para as novas linhas.
        first_data_row = header_row + 1
        style_row = min(first_data_row, worksheet.max_row)
        template_styles = [
            copy(worksheet.cell(style_row, column)._style)
            for column in range(1, len(headers) + 1)
        ] if worksheet.max_row >= first_data_row else [None] * len(headers)

        column_positions = {
            _column_key(name): index
            for index, name in enumerate(dataset.data.columns)
        }
        if len(column_positions) != len(dataset.data.columns):
            raise ExportError("A tabela contém nomes de coluna duplicados após conversão para texto.")
        if not any(
            _column_key(header) in column_positions
            for header in headers
            if header is not None
        ):
            raise ExportError("Nenhuma coluna canônica corresponde aos cabeçalhos do modelo.")

        last_existing_row = worksheet.max_row
        existing_column_count = max(len(headers), worksheet.max_column)

        # Limpa apenas células com conteúdo no modelo. Não percorre o tamanho
        # inteiro da futura exportação para atribuir None a células novas.
        if last_existing_row >= first_data_row:
            for row in worksheet.iter_rows(
                min_row=first_data_row,
                max_row=last_existing_row,
                min_col=1,
                max_col=existing_column_count,
            ):
                for cell in row:
                    if cell.value is not None:
                        cell.value = None

        write_columns = [
            (column_number, column_positions[_column_key(header)])
            for column_number, header in enumerate(headers, start=1)
            if header is not None and _column_key(header) in column_positions
        ]
        styled_columns = [
            (column_number, style)
            for column_number, style in enumerate(template_styles, start=1)
            if style is not None
        ]

        for row_offset, values in enumerate(dataset.data.itertuples(index=False, name=None)):
            row_number = first_data_row + row_offset
            for column_number, style in styled_columns:
                cell = worksheet.cell(row=row_number, column=column_number)
                if cell.has_style is False:
                    cell._style = copy(style)

            for column_number, source_position in write_columns:
                value = values[source_position]
                if value is not None and pd.isna(value):
                    value = None
                if value is None:
                    continue
                if hasattr(value, "item"):
                    value = value.item()
                cell = worksheet.cell(row=row_number, column=column_number)
                cell.value = value
                if isinstance(value, str) and value.startswith("="):
                    cell.data_type = "s"

        required_last_row = header_row + len(dataset.data.index)
        if worksheet.max_column and required_last_row >= header_row:
            worksheet.auto_filter.ref = (
                f"A{header_row}:{worksheet.cell(required_last_row, len(headers)).coordinate}"
            )

        output.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(output)
    except ExportError:
        raise
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ExportError(f"Não foi possível gravar o arquivo '{output}': {exc}") from exc

    return output
