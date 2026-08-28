from src.query_analyzer import analyze_query
from src.search import BM25Search
from src.embeddings import embed_texto

class HybridSearch:

    def __init__(self, store):
        self.store = store
        self.bm25 = BM25Search(
            store.textos,
            store.metadados
        )

    @staticmethod
    def _chave(resultado):
        return resultado["metadata"].get(
            "chunk_id"
        )

    def _rrf(
        self,
        dense_results,
        sparse_results,
        k=60
    ):

        scores = {}
        documentos = {}

        for rank, resultado in enumerate(
            dense_results,
            start=1
        ):

            chunk_id = self._chave(
                resultado
            )
            if not chunk_id:
                continue

            documentos[chunk_id] = resultado

            scores[chunk_id] = (
                scores.get(chunk_id, 0)
                + 1 / (k + rank)
            )
        for rank, resultado in enumerate(
            sparse_results,
            start=1
        ):

            chunk_id = self._chave(
                resultado
            )

            if not chunk_id:
                continue

            documentos[chunk_id] = resultado

            scores[chunk_id] = (
                scores.get(chunk_id, 0)
                + 1 / (k + rank)
            )

        ranking_final = sorted(
            scores,
            key=scores.get,
            reverse=True
        )

        resultados = []

        for chunk_id in ranking_final:

            resultado = documentos[chunk_id].copy()

            resultado["rrf_score"] = scores[
                chunk_id
            ]

            resultados.append(
                resultado
            )

        return resultados

    def buscar(
        self,
        pergunta,
        top_k=5
    ):

        # ------------------------------------------
        # 1. Query Analyzer
        # ------------------------------------------

        analise = analyze_query(
            pergunta
        )

        filtros = analise["filters"]

        consulta = analise[
            "normalized_query"
        ]

        # ------------------------------------------
        # 2. Busca densa
        # ------------------------------------------

        vetor = embed_texto(
            consulta
        )

        dense_results = self.store.buscar(
            vetor_query=vetor,
            top_k=top_k,
            filtro=filtros,
            fetch_k=100
        )

        # ------------------------------------------
        # 3. Busca BM25
        # ------------------------------------------

        sparse_results = self.bm25.buscar(
            consulta,
            top_k=top_k,
            filtro=filtros
        )

        # ------------------------------------------
        # 4. RRF
        # ------------------------------------------

        resultados = self._rrf(
            dense_results,
            sparse_results
        )

        return {
            "question": pergunta,
            "filters": filtros,
            "dense_results": dense_results,
            "bm25_results": sparse_results,
            "hybrid_results": resultados[:top_k]
        }