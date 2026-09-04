from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from src.query_analyzer import normalize


class BM25Search:
    """
    Busca esparsa utilizando BM25.

    Recebe os textos e metadados armazenados no VectorStore
    e permite aplicar filtros de metadados.
    """

    def __init__(
        self,
        textos: list[str],
        metadados: list[dict],
    ):
        self.textos = textos
        self.metadados = metadados

        self.tokens = [
            self._tokenizar(texto)
            for texto in textos
        ]

        self.bm25 = BM25Okapi(
            self.tokens
        )

    # ==========================================================
    # TOKENIZAÇÃO
    # ==========================================================

    @staticmethod
    def _tokenizar(texto: str) -> list[str]:
        """
        Normaliza e tokeniza o texto.

        A mesma normalização usada pelo Query Analyzer
        é aplicada aqui para evitar diferenças entre:
            São Paulo
            sao paulo
            SÃO PAULO
        """

        texto = normalize(
            texto
        )

        return re.findall(
            r"\b\w+\b",
            texto,
        )

    # ==========================================================
    # FILTRO DE METADADOS
    # ==========================================================

    @staticmethod
    def _valor_atende_filtro(
        meta: dict,
        chave: str,
        valor: object,
    ) -> bool:

        atual = str(
            meta.get(chave, "")
        ).strip().lower()

        esperado = str(
            valor
        ).strip().lower()

        # ------------------------------------------------------
        # MÓDULO
        # ------------------------------------------------------

        if chave == "module":

            modulos = [
                item.strip().lower()
                for item in atual.split(",")
            ]

            return (
                esperado in modulos
                or any(
                    esperado in modulo
                    for modulo in modulos
                )
            )

        # ------------------------------------------------------
        # DEMAIS METADADOS
        # ------------------------------------------------------

        return atual == esperado

    # ==========================================================
    # BUSCA
    # ==========================================================

    def buscar(
        self,
        consulta: str,
        top_k: int = 10,
        filtro: dict | None = None,
    ) -> list[dict]:

        # ------------------------------------------------------
        # 1. DOCUMENTOS VÁLIDOS
        # ------------------------------------------------------

        indices_validos = []

        for i, meta in enumerate(
            self.metadados
        ):

            if not filtro:
                indices_validos.append(i)
                continue

            passou = True

            for chave, valor in filtro.items():

                if not self._valor_atende_filtro(
                    meta,
                    chave,
                    valor,
                ):
                    passou = False
                    break

            if passou:
                indices_validos.append(i)

        # ------------------------------------------------------
        # NENHUM DOCUMENTO
        # ------------------------------------------------------

        if not indices_validos:
            return []

        # ------------------------------------------------------
        # 2. TOKENIZAR CONSULTA
        # ------------------------------------------------------

        consulta_tokens = self._tokenizar(
            consulta
        )

        if not consulta_tokens:
            return []

        # ------------------------------------------------------
        # 3. SCORES BM25
        # ------------------------------------------------------

        scores = self.bm25.get_scores(
            consulta_tokens
        )

        # ------------------------------------------------------
        # 4. RANKING
        # ------------------------------------------------------

        ranking = sorted(
            indices_validos,
            key=lambda i: scores[i],
            reverse=True,
        )

        # ------------------------------------------------------
        # 5. RESULTADOS
        # ------------------------------------------------------

        resultados = []

        for i in ranking[:top_k]:

            resultados.append(
                {
                    "text": self.textos[i],
                    "metadata": self.metadados[i],
                    "score": float(scores[i]),
                }
            )

        return resultados