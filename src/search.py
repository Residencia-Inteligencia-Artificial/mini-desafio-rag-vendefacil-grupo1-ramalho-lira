from __future__ import annotations

import re

from rank_bm25 import BM25Okapi


class BM25Search:
    """
    Busca esparsa utilizando BM25.

    Recebe os textos e metadados que já estão armazenados
    no VectorStore.

    Permite aplicar filtros de metadados antes de retornar
    os resultados.
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

        self.bm25 = BM25Okapi(self.tokens)

    # ==========================================================
    # TOKENIZAÇÃO
    # ==========================================================

    @staticmethod
    def _tokenizar(texto: str) -> list[str]:
        """
        Divide o texto em tokens simples para o BM25.
        """

        return re.findall(
            r"\b\w+\b",
            texto.lower(),
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
        """
        Verifica se um documento atende a um filtro.

        O comportamento é semelhante ao VectorStore.

        Para 'module', aceita situações como:

            estoque

        ou:

            VendeFácil Estoque

        ou:

            VendeFácil Analytics, VendeFácil Loja,
            VendeFácil Estoque
        """

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
        """
        Executa busca BM25.

        Args:
            consulta:
                Texto da pergunta.

            top_k:
                Quantidade máxima de resultados.

            filtro:
                Filtros de metadados extraídos pelo Query Analyzer.

        Returns:
            Lista de resultados contendo:

                text
                metadata
                score
        """

        # ------------------------------------------------------
        # 1. IDENTIFICAR DOCUMENTOS VÁLIDOS
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
        # Nenhum documento atende aos filtros
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
        # 3. CALCULAR SCORES BM25
        # ------------------------------------------------------

        scores = self.bm25.get_scores(
            consulta_tokens
        )

        # ------------------------------------------------------
        # 4. ORDENAR SOMENTE DOCUMENTOS VÁLIDOS
        # ------------------------------------------------------

        ranking = sorted(
            indices_validos,
            key=lambda i: scores[i],
            reverse=True,
        )

        # ------------------------------------------------------
        # 5. MONTAR RESULTADOS
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