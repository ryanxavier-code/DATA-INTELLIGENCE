"""Busca nome de unidade e CNPJ em um cadastro Excel fornecido localmente."""

import re
import unicodedata
from pathlib import Path

import pandas as pd


class StoreLookupError(Exception):
    """Erro ao resolver uma unidade no cadastro fornecido."""


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip().casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", text)


def lookup_store(
    lookup_path: str | Path,
    store_name: str,
    *,
    name_column: str = "Nome Fantasia",
    cnpj_column: str = "CNPJ",
    sheet_name: str | int = 0,
) -> tuple[str, str]:
    """Retorna ``(nome_fantasia, cnpj)`` para um nome exato normalizado.

    O nome é comparado sem diferenças de caixa, acentos, espaços ou pontuação.
    Correspondências ausentes/ambíguas e CNPJs vazios/incompletos geram erro;
    o cadastro original é aberto somente para leitura.
    """
    path = Path(lookup_path)
    if not path.is_file():
        raise StoreLookupError(f"Cadastro de unidades não encontrado: {path}")

    try:
        frame = pd.read_excel(path, sheet_name=sheet_name, dtype="string")
    except (OSError, ValueError, ImportError) as exc:
        raise StoreLookupError(f"Não foi possível ler o cadastro de unidades: {exc}") from exc

    columns_by_normalized_name = {_normalize(column): column for column in frame.columns}
    name_key = _normalize(name_column)
    cnpj_key = _normalize(cnpj_column)
    if name_key not in columns_by_normalized_name or cnpj_key not in columns_by_normalized_name:
        raise StoreLookupError(
            f"O cadastro precisa conter as colunas {name_column!r} e {cnpj_column!r}."
        )

    actual_name_column = columns_by_normalized_name[name_key]
    actual_cnpj_column = columns_by_normalized_name[cnpj_key]
    target = _normalize(store_name)
    matches = frame.loc[
        frame[actual_name_column].map(
            lambda value: pd.notna(value) and _normalize(value) == target
        )
    ]
    if len(matches) != 1:
        raise StoreLookupError(
            f"Esperava uma correspondência exata para a unidade {store_name!r}; "
            f"encontrei {len(matches)}."
        )

    registered_name = str(matches.iloc[0][actual_name_column]).strip()
    raw_cnpj = matches.iloc[0][actual_cnpj_column]
    cnpj_text = str(raw_cnpj).strip() if pd.notna(raw_cnpj) else ""
    if re.fullmatch(r"\d+\.0", cnpj_text):
        cnpj_text = cnpj_text[:-2]
    cnpj = re.sub(r"\D", "", cnpj_text)
    if len(cnpj) != 14:
        raise StoreLookupError(
            f"A correspondência de {store_name!r} não contém um CNPJ completo de 14 dígitos."
        )
    return registered_name, cnpj
