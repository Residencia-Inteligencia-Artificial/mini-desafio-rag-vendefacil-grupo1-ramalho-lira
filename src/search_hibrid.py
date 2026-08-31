from __future__ import annotations

from src.vector_store import VectorStore
from src.query_analyzer import analyze_query
from src.search import BM25Search
from src.embeddings import embed_texto


class HybridSearch:
    """
    Busca híbrida composta por:

    - Query Analyzer
    - busca densa com FAISS
    - busca esparsa com BM25
    - combinação dos resultados utilizando RRF
    """

    def __init__(
        self,
        index_dir: str,
    ):
        print(
            "\n2. Inicializando busca híbrida..."
        )

        # ======================================================
        # VECTOR STORE
        # ======================================================

        self.vector_store = (
            VectorStore.carregar(
                index_dir
            )
        )

        # ======================================================
        # BM25
        # ======================================================

        self.bm25 = BM25Search(
            self.vector_store.textos,
            self.vector_store.metadados,
        )

    # ==========================================================
    # CHAVE DO RESULTADO
    # ==========================================================

    @staticmethod
    def _chave(
        resultado: dict,
    ) -> str:
        """
        Obtém o chunk_id usado para identificar
        unicamente cada resultado.
        """

        metadata = resultado.get(
            "metadata",
            {},
        )

        return str(
            metadata.get(
                "chunk_id",
                resultado.get(
                    "chunk_id",
                    "",
                ),
            )
        )

    # ==========================================================
    # GARANTIR METADADOS
    # ==========================================================

    @staticmethod
    def _normalizar_resultado(
        resultado: dict,
    ) -> dict:
        """
        Garante que cada resultado tenha:

        - text
        - metadata
        - filepath
        - chunk_id
        """

        resultado = resultado.copy()

        metadata = resultado.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        metadata = metadata.copy()

        # ------------------------------------------------------
        # filepath
        # ------------------------------------------------------

        if not metadata.get("filepath"):
            metadata["filepath"] = (
                metadata.get(
                    "source",
                    "desconhecido",
                )
            )

        # ------------------------------------------------------
        # chunk_id
        # ------------------------------------------------------

        if not metadata.get("chunk_id"):
            metadata["chunk_id"] = str(
                resultado.get(
                    "chunk_id",
                    "desconhecido",
                )
            )

        resultado["metadata"] = metadata

        return resultado

    # ==========================================================
    # RRF
    # ==========================================================

    def _rrf(
        self,
        dense_results: list[dict],
        sparse_results: list[dict],
        k: int = 60,
    ) -> list[dict]:
        """
        Combina busca densa e BM25 utilizando
        Reciprocal Rank Fusion.

        Fórmula:

            score = 1 / (k + rank)
        """

        scores = {}
        documentos = {}

        # ======================================================
        # BUSCA DENSA
        # ======================================================

        for rank, resultado in enumerate(
            dense_results,
            start=1,
        ):
            resultado = (
                self._normalizar_resultado(
                    resultado
                )
            )

            chunk_id = self._chave(
                resultado
            )

            if not chunk_id:
                continue

            documentos[chunk_id] = resultado

            scores[chunk_id] = (
                scores.get(
                    chunk_id,
                    0,
                )
                + 1 / (k + rank)
            )

        # ======================================================
        # BUSCA BM25
        # ======================================================

        for rank, resultado in enumerate(
            sparse_results,
            start=1,
        ):
            resultado = (
                self._normalizar_resultado(
                    resultado
                )
            )

            chunk_id = self._chave(
                resultado
            )

            if not chunk_id:
                continue

            # Se o documento já veio da busca densa,
            # mantemos a versão mais completa.
            documentos[chunk_id] = resultado

            scores[chunk_id] = (
                scores.get(
                    chunk_id,
                    0,
                )
                + 1 / (k + rank)
            )

        # ======================================================
        # ORDENAR
        # ======================================================

        ranking_final = sorted(
            scores,
            key=scores.get,
            reverse=True,
        )

        resultados = []

        for chunk_id in ranking_final:
            resultado = (
                documentos[chunk_id].copy()
            )

            resultado["rrf_score"] = (
                scores[chunk_id]
            )

            resultados.append(
                resultado
            )

        return resultados

    # ==========================================================
    # BUSCA HÍBRIDA
    # ==========================================================

    def buscar(
        self,
        pergunta: str,
        top_k: int = 5,
    ) -> dict:
        """
        Executa todo o fluxo de busca híbrida.

        1. Query Analyzer
        2. Embedding
        3. FAISS
        4. BM25
        5. RRF
        """

        # ======================================================
        # 1. QUERY ANALYZER
        # ======================================================

        analise = analyze_query(
            pergunta
        )

        filtros = analise.get(
            "filters",
            {},
        )

        consulta = analise.get(
            "normalized_query",
            pergunta,
        )

        # ======================================================
        # 2. BUSCA DENSA
        # ======================================================

        vetor = embed_texto(
            consulta
        )

        dense_results = (
            self.vector_store.buscar(
                vetor_query=vetor,
                top_k=top_k,
                filtro=filtros,
                fetch_k=100,
            )
        )

        # ======================================================
        # 3. BUSCA BM25
        # ======================================================

        sparse_results = (
            self.bm25.buscar(
                consulta,
                top_k=top_k,
                filtro=filtros,
            )
        )

        # ======================================================
        # 4. RRF
        # ======================================================

        resultados_hibridos = (
            self._rrf(
                dense_results,
                sparse_results,
            )
        )

        # ======================================================
        # 5. RETORNO
        # ======================================================

        return {
            "question": pergunta,
            "filters": filtros,
            "dense_results": dense_results,
            "bm25_results": sparse_results,
            "hybrid_results": (
                resultados_hibridos[:top_k]
            ),
        }