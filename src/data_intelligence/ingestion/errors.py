"""Erros claros para falhas ocorridas durante a ingestão."""


class IngestionError(Exception):
    """Indica que um arquivo não pôde ser carregado como uma tabela."""
