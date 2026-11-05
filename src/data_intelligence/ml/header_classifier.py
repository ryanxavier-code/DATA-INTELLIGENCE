"""Classificador experimental de cabeçalhos baseado em scikit-learn.

O modelo usa somente o tipo do relatório e o texto do cabeçalho. Ele não
interpreta valores de células nem determina regras de transformação.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline


_REQUIRED_COLUMNS = {
    "source_profile", "report_type", "source_column", "canonical_field"
}


@dataclass(frozen=True)
class HeaderCandidate:
    """Campo canônico sugerido e score bruto do classificador."""

    canonical_field: str
    score: float


@dataclass(frozen=True)
class TrainedHeaderClassifier:
    """Estimador ajustado y score mínimo aprendido por validación agrupada."""

    estimator: Pipeline
    minimum_score: float


def build_header_classifier() -> Pipeline:
    """Cria o pipeline de texto e classificação usado no experimento."""
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
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )


def train_header_classifier(training_path: str | Path) -> TrainedHeaderClassifier:
    """Treina o pipeline com exemplos rotulados de cabeçalhos.

    O arquivo precisa conter ``report_type``, ``source_column`` e
    ``canonical_field``. No aplicativo, o corpus versionado contém somente
    exemplos sintéticos.
    """
    path = Path(training_path)
    if not path.is_file():
        raise FileNotFoundError(f"Corpus de treinamento não encontrado: {path}")

    data = pd.read_csv(path)
    missing = _REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(
            "Faltam colunas obrigatórias no corpus: " + ", ".join(sorted(missing))
        )
    if data[list(_REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("O corpus contém cabeçalhos ou rótulos vazios.")

    model_input = np.asarray(
        _make_model_input(data["report_type"], data["source_column"]), dtype=object
    )
    labels = data["canonical_field"].astype(str)
    if labels.nunique() < 2:
        raise ValueError("O corpus precisa conter ao menos dois campos canônicos.")
    groups = data["source_profile"].astype(str).to_numpy()

    minimum_score = select_abstention_threshold(
        model_input,
        labels.to_numpy(),
        groups,
        n_splits=4,
    )
    estimator = build_header_classifier().fit(model_input, labels)
    return TrainedHeaderClassifier(estimator, minimum_score)


def select_abstention_threshold(
    model_input: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
    *,
    n_splits: int = 4,
) -> float:
    """Escolhe o maior uso possível sem erros nas previsões agrupadas internas.

    O threshold reduz a quantidade de sugestões pré-preenchidas quando o
    pipeline erra em validação interna. Ele não calibra as pontuações como
    probabilidades; uma avaliação externa continua necessária.
    """
    if len(set(groups)) < n_splits:
        raise ValueError(
            f"São necessários ao menos {n_splits} grupos para selecionar o corte."
        )
    splitter = GroupKFold(n_splits=n_splits)
    predictions = np.empty(len(labels), dtype=object)
    scores = np.full(len(labels), np.nan, dtype=float)

    for train_indices, valid_indices in splitter.split(model_input, labels, groups):
        if set(groups[train_indices]) & set(groups[valid_indices]):
            raise RuntimeError("Um perfil sintético apareceu em treino e validação interna.")
        model = build_header_classifier().fit(
            model_input[train_indices], labels[train_indices]
        )
        probabilities = model.predict_proba(model_input[valid_indices])
        classes = model.named_steps["classifier"].classes_
        predictions[valid_indices] = classes[probabilities.argmax(axis=1)]
        scores[valid_indices] = probabilities.max(axis=1)

    if np.isnan(scores).any():
        raise RuntimeError("Há exemplos sem previsão interna para selecionar o corte.")

    for threshold in np.unique(scores):
        accepted = scores >= threshold
        if accepted.any() and np.all(predictions[accepted] == labels[accepted]):
            return float(threshold)
    return float("inf")


def predict_header_candidates(
    model: Pipeline,
    *,
    report_type: str,
    source_column: str,
    allowed_fields: set[str] | frozenset[str],
    top_n: int = 3,
) -> tuple[HeaderCandidate, ...]:
    """Retorna candidatos ranqueados, limitados aos campos do relatório.

    ``score`` é a pontuação bruta relativa do modelo. Ela não foi calibrada
    como probabilidade de acerto e deve ser exibida como sinal para revisão.
    """
    if top_n < 1:
        raise ValueError("top_n deve ser pelo menos 1.")
    model_input = _make_model_input([report_type], [source_column])
    probabilities = model.predict_proba(model_input)[0]
    classes = model.named_steps["classifier"].classes_
    candidates = [
        HeaderCandidate(str(field), float(score))
        for field, score in zip(classes, probabilities, strict=True)
        if str(field) in allowed_fields
    ]
    candidates.sort(key=lambda candidate: (-candidate.score, candidate.canonical_field))
    return tuple(candidates[:top_n])


def _make_model_input(report_types: object, source_columns: object) -> list[str]:
    return [
        f"{str(report_type).casefold()} [SEP] {str(source_column)}"
        for report_type, source_column in zip(report_types, source_columns, strict=True)
    ]
