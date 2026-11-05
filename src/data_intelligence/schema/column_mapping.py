"""Sugestões explicáveis de equivalência entre nomes de colunas."""

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence


DEFAULT_ALIASES: dict[str, tuple[str, ...]] = {
    "codigo_interno": (
        "código interno",
        "codigo",
        "cod",
        "id",
        "sku",
        "internal code",
        "product code",
    ),
    "ean": (
        "ean",
        "gtin",
        "código de barras",
        "codigo de barras",
        "barcode",
        "bar code",
    ),
    "descricao_produto": (
        "descrição",
        "descricao",
        "produto",
        "nome do produto",
        "nome produto",
        "item",
        "product name",
        "description",
    ),
    "grupo": ("grupo", "categoria", "departamento", "category", "department"),
    "preco": ("preço", "valor", "valor de venda", "price", "sale price", "cost"),
}


@dataclass(frozen=True)
class MappingCandidate:
    """Uma possível coluna canônica e a evidência que sustenta a sugestão."""

    canonical_name: str
    score: float
    matched_alias: str
    method: str


@dataclass(frozen=True)
class ColumnMappingSuggestion:
    """Sugestões ordenadas para uma coluna de origem."""

    source_column: str
    candidates: tuple[MappingCandidate, ...]


def _normalize_name(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value)
    ascii_name = without_accents.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_name.casefold())


def suggest_column_mappings(
    column_names: Iterable[str],
    *,
    aliases: Mapping[str, Sequence[str]] = DEFAULT_ALIASES,
    min_score: float = 0.55,
    top_n: int = 3,
) -> tuple[ColumnMappingSuggestion, ...]:
    """Sugere campos canônicos por aliases normalizados e similaridade textual.

    A função não renomeia colunas nem altera dados. Uma pontuação é uma pista
    para revisão humana, não uma probabilidade de acerto.
    """
    if not 0.0 <= min_score <= 1.0:
        raise ValueError("min_score deve estar entre 0.0 e 1.0")
    if top_n < 1:
        raise ValueError("top_n deve ser pelo menos 1")

    normalized_schema = {
        canonical_name: tuple(
            (alias, _normalize_name(alias))
            for alias in (canonical_name, *field_aliases)
            if _normalize_name(alias)
        )
        for canonical_name, field_aliases in aliases.items()
    }

    suggestions: list[ColumnMappingSuggestion] = []
    for source_column in column_names:
        normalized_source = _normalize_name(str(source_column))
        candidates: list[MappingCandidate] = []
        if normalized_source:
            for canonical_name, normalized_aliases in normalized_schema.items():
                best_alias = ""
                best_score = 0.0
                for alias, normalized_alias in normalized_aliases:
                    score = SequenceMatcher(
                        None, normalized_source, normalized_alias
                    ).ratio()
                    if score > best_score:
                        best_alias = alias
                        best_score = score

                if best_score >= min_score:
                    candidates.append(
                        MappingCandidate(
                            canonical_name=canonical_name,
                            score=best_score,
                            matched_alias=best_alias,
                            method="alias" if best_score == 1.0 else "similaridade",
                        )
                    )

        candidates.sort(key=lambda candidate: (-candidate.score, candidate.canonical_name))
        suggestions.append(
            ColumnMappingSuggestion(
                source_column=str(source_column),
                candidates=tuple(candidates[:top_n]),
            )
        )

    return tuple(suggestions)
