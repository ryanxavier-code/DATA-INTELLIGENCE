"""Características de una columna para análisis o ML supervisado.

Este módulo describe los valores observados sin usar etiquetas canónicas.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence

import pandas as pd


def is_valid_ean13(value: str) -> bool:
    """Comprueba el formato de 13 dígitos y el dígito verificador EAN-13."""
    if not re.fullmatch(r"\d{13}", value):
        return False
    digits = [int(digit) for digit in value]
    weighted_sum = sum(
        digit * (1 if index % 2 == 0 else 3)
        for index, digit in enumerate(digits[:12])
    )
    return (10 - weighted_sum % 10) % 10 == digits[-1]


def profile_column_values(series: pd.Series) -> dict[str, object]:
    """Calcula características descriptivas sin cambiar la serie recibida."""
    values = series.dropna().tolist()
    strings = [str(value).strip() for value in values]
    count = len(strings)
    if not count:
        return _empty_column_features(len(series))

    numeric = pd.to_numeric(pd.Series(values), errors="coerce")
    numeric_values = numeric.dropna()
    string_series = pd.Series(strings, dtype="string")
    ean_count = sum(bool(re.fullmatch(r"\d{13}", value)) for value in strings)
    valid_ean_count = sum(is_valid_ean13(value) for value in strings)
    date_fraction = float(
        pd.to_datetime(string_series, errors="coerce", format="mixed").notna().mean()
    )

    numeric_fraction = float(numeric.notna().mean())
    if numeric_values.empty:
        numeric_stats = {
            "integer_fraction": 0.0,
            "decimal_fraction": 0.0,
            "mean_numeric_value": 0.0,
            "std_numeric_value": 0.0,
            "min_numeric_value": 0.0,
            "max_numeric_value": 0.0,
        }
    else:
        decimal_mask = (numeric_values.mod(1).abs() >= 1e-9)
        numeric_stats = {
            "integer_fraction": round(float((~decimal_mask).mean()), 4),
            "decimal_fraction": round(float(decimal_mask.mean()), 4),
            "mean_numeric_value": round(float(numeric_values.mean()), 4),
            "std_numeric_value": round(float(numeric_values.std(ddof=0)), 4),
            "min_numeric_value": round(float(numeric_values.min()), 4),
            "max_numeric_value": round(float(numeric_values.max()), 4),
        }

    alpha_fraction = sum(any(char.isalpha() for char in value) for value in strings) / count
    alphanumeric_fraction = sum(
        bool(re.search(r"[A-Za-z]", value) and re.search(r"\d", value))
        for value in strings
    ) / count
    currency_fraction = sum(
        any(marker in value.casefold() for marker in ("r$", "$", "€"))
        for value in strings
    ) / count

    return {
        "non_null_count": count,
        "null_fraction": round(1 - count / len(series), 4) if len(series) else 1.0,
        "unique_ratio": round(string_series.nunique() / count, 4),
        "numeric_fraction": round(numeric_fraction, 4),
        "digit_only_fraction": round(
            sum(bool(re.fullmatch(r"\d+", value)) for value in strings) / count,
            4,
        ),
        "ean13_fraction": round(ean_count / count, 4),
        "valid_ean13_fraction": round(valid_ean_count / count, 4),
        "date_like_fraction": round(date_fraction, 4),
        "alphabetic_fraction": round(alpha_fraction, 4),
        "alphanumeric_fraction": round(alphanumeric_fraction, 4),
        "currency_marker_fraction": round(currency_fraction, 4),
        "mean_text_length": round(sum(map(len, strings)) / count, 2),
        **numeric_stats,
        "sample_values_json": json.dumps(strings[:5], ensure_ascii=False),
    }


def profile_frame_columns(
    frame: pd.DataFrame,
    *,
    has_header: bool,
    headers: Sequence[str] | None = None,
) -> list[dict[str, object]]:
    """Perfilha colunas e acrescenta estatísticas relativas à tabela inteira.

    ``headers`` deve conter os nomes lidos da fonte quando existem. Para uma
    entrada sem cabeçalho, passe ``has_header=False`` e deixe ``headers=None``.
    A função não tenta inferir rótulos canônicos.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame deve ser um pandas.DataFrame")
    if headers is not None and len(headers) != frame.shape[1]:
        raise ValueError("A quantidade de cabeçalhos deve corresponder às colunas")
    if headers is not None and not has_header:
        raise ValueError("Não passe cabeçalhos quando has_header=False")

    features = [profile_column_values(frame.iloc[:, index]) for index in range(frame.shape[1])]
    numeric_candidates = [
        index
        for index, feature in enumerate(features)
        if feature["numeric_fraction"] >= 0.8 and feature["ean13_fraction"] < 0.5
    ]
    numeric_matrix = pd.DataFrame(
        {
            index: pd.to_numeric(frame.iloc[:, index], errors="coerce")
            for index in numeric_candidates
        }
    )
    rank_matrix = (
        numeric_matrix.rank(axis=1, method="average", pct=True)
        if not numeric_matrix.empty
        else numeric_matrix
    )

    records: list[dict[str, object]] = []
    for index, column_features in enumerate(features):
        peer_candidates = [candidate for candidate in numeric_candidates if candidate != index]
        correlations: list[float] = []
        if index in numeric_matrix.columns:
            for candidate in peer_candidates:
                correlation = numeric_matrix[index].corr(numeric_matrix[candidate])
                if pd.notna(correlation):
                    correlations.append(abs(float(correlation)))

        relative_rank = rank_matrix[index] if index in rank_matrix.columns else None
        if relative_rank is None or relative_rank.empty or len(numeric_candidates) < 2:
            relative_features = {
                "relative_numeric_rank_mean": 0.0,
                "relative_numeric_highest_fraction": 0.0,
                "relative_numeric_lowest_fraction": 0.0,
            }
        else:
            relative_features = {
                "relative_numeric_rank_mean": round(float(relative_rank.mean()), 4),
                "relative_numeric_highest_fraction": round(
                    float(relative_rank.eq(rank_matrix.max(axis=1)).mean()), 4
                ),
                "relative_numeric_lowest_fraction": round(
                    float(relative_rank.eq(rank_matrix.min(axis=1)).mean()), 4
                ),
            }

        header = headers[index] if headers is not None else ""
        records.append(
            {
                "column_position_1_based": index + 1,
                "has_header": has_header,
                "source_header": str(header),
                "table_width": frame.shape[1],
                "peer_numeric_count": len(peer_candidates),
                "peer_numeric_corr_max": round(max(correlations), 4) if correlations else 0.0,
                **relative_features,
                **column_features,
            }
        )
    return records


def _empty_column_features(total_count: int) -> dict[str, object]:
    return {
        "non_null_count": 0,
        "null_fraction": 1.0 if total_count else 0.0,
        "unique_ratio": 0.0,
        "numeric_fraction": 0.0,
        "digit_only_fraction": 0.0,
        "ean13_fraction": 0.0,
        "valid_ean13_fraction": 0.0,
        "date_like_fraction": 0.0,
        "alphabetic_fraction": 0.0,
        "alphanumeric_fraction": 0.0,
        "currency_marker_fraction": 0.0,
        "mean_text_length": 0.0,
        "integer_fraction": 0.0,
        "decimal_fraction": 0.0,
        "mean_numeric_value": 0.0,
        "std_numeric_value": 0.0,
        "min_numeric_value": 0.0,
        "max_numeric_value": 0.0,
        "sample_values_json": "[]",
    }
