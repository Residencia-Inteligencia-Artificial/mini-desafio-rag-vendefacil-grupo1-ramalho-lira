from __future__ import annotations

import os
from typing import Any

from src.embeddings import embed_texto
from src.query_analyzer import analyze_query
from src.search import BM25Search
from src.vector_store import VectorStore


class HybridSearch:
    """
    Busca híbrida combinando:

    - busca densa com embeddings + FAISS
    - busca esparsa com BM25
    - filtros de metadados extraídos pelo Query Analyzer
    - fusão dos resultados usando Reciprocal Rank Fusion (RRF)
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

        self.bm25 = BM25Search(
            self.vector_store.textos,
            self.vector_store.metadados
        )

    # =========================================================
    # NORMALIZAÇÃO DOS RESULTADOS
    # =========================================================

    @staticmethod
    def _normalizar_resultado(
        resultado: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Garante que os resultados tenham uma estrutura consistente.

        O pipeline de ingestão utiliza principalmente `source_file`.
        """

        resultado = dict(resultado)

        metadata = resultado.get("metadata")

        if not isinstance(metadata, dict):
            metadata = {}

        # -----------------------------------------------------
        # SOURCE FILE
        # -----------------------------------------------------

        source_file = (
            metadata.get("source_file")
            or metadata.get("filepath")
            or metadata.get("file_path")
            or metadata.get("source")
            or metadata.get("filename")
            or resultado.get("source_file")
            or resultado.get("filepath")
            or resultado.get("file_path")
            or resultado.get("source")
            or resultado.get("filename")
        )

        if not source_file:
            source_file = "desconhecido"

        metadata["source_file"] = source_file
        metadata["filepath"] = source_file

        resultado["metadata"] = metadata

        # -----------------------------------------------------
        # CHUNK ID
        # -----------------------------------------------------

        chunk_id = (
            metadata.get("chunk_id")
            or resultado.get("chunk_id")
            or metadata.get("id")
        )

        if chunk_id:
            metadata["chunk_id"] = chunk_id
            resultado["chunk_id"] = chunk_id

        # -----------------------------------------------------
        # TEXTO
        # -----------------------------------------------------

        if "text" not in resultado:
            if "page_content" in resultado:
                resultado["text"] = resultado["page_content"]

            elif "content" in resultado:
                resultado["text"] = resultado["content"]

            else:
                resultado["text"] = ""

        # -----------------------------------------------------
        # SCORE
        # -----------------------------------------------------

        if "score" not in resultado:
            resultado["score"] = 0.0

        return resultado

    # =========================================================
    # CHAVE PARA RRF
    # =========================================================

    @staticmethod
    def _chave(
        resultado: dict[str, Any]
    ) -> str:
        """
        Gera uma chave única para identificar o mesmo chunk
        entre a busca densa e a busca BM25.
        """

        metadata = resultado.get("metadata", {})

        chunk_id = (
            metadata.get("chunk_id")
            or resultado.get("chunk_id")
        )

        if chunk_id:
            return str(chunk_id)

        source_file = (
            metadata.get("source_file")
            or metadata.get("filepath")
            or resultado.get("source_file")
            or resultado.get("filepath")
            or "desconhecido"
        )

        chunk_index = (
            metadata.get("chunk_index")
            or resultado.get("chunk_index")
            or 0
        )

        return f"{source_file}|{chunk_index}"

    # =========================================================
    # RECIPROCAL RANK FUSION
    # =========================================================

    def _rrf(
        self,
        resultados_dense: list[dict[str, Any]],
        resultados_bm25: list[dict[str, Any]],
        k: int = 60,
    ) -> list[dict[str, Any]]:
        """
        Combina os resultados Dense + BM25 usando RRF.

        Fórmula:

            RRF = 1 / (k + posição)
        """

        combinados: dict[str, dict[str, Any]] = {}

        # -----------------------------------------------------
        # RESULTADOS DENSE
        # -----------------------------------------------------

        for rank, resultado in enumerate(
            resultados_dense,
            start=1
        ):
            resultado = self._normalizar_resultado(
                resultado
            )

            chave = self._chave(resultado)

            if chave not in combinados:
                combinados[chave] = dict(resultado)

                combinados[chave]["rrf_score"] = 0.0
                combinados[chave]["dense_score"] = None
                combinados[chave]["bm25_score"] = None

            combinados[chave]["rrf_score"] += (
                1.0 / (k + rank)
            )

            combinados[chave]["dense_score"] = (
                resultado.get("score")
            )

        # -----------------------------------------------------
        # RESULTADOS BM25
        # -----------------------------------------------------

        for rank, resultado in enumerate(
            resultados_bm25,
            start=1
        ):
            resultado = self._normalizar_resultado(
                resultado
            )

            chave = self._chave(resultado)

            if chave not in combinados:
                combinados[chave] = dict(resultado)

                combinados[chave]["rrf_score"] = 0.0
                combinados[chave]["dense_score"] = None
                combinados[chave]["bm25_score"] = None

            combinados[chave]["rrf_score"] += (
                1.0 / (k + rank)
            )

            combinados[chave]["bm25_score"] = (
                resultado.get("score")
            )

            if not combinados[chave].get("text"):
                combinados[chave]["text"] = (
                    resultado.get("text", "")
                )

            if not combinados[chave].get("metadata"):
                combinados[chave]["metadata"] = (
                    resultado.get("metadata", {})
                )

        # -----------------------------------------------------
        # ORDENAÇÃO
        # -----------------------------------------------------

        resultados = list(
            combinados.values()
        )

        resultados.sort(
            key=lambda x: x.get(
                "rrf_score",
                0.0
            ),
            reverse=True
        )

        return resultados

    # =========================================================
    # BUSCA HÍBRIDA
    # =========================================================

    def buscar(
        self,
        query: str,
        top_k: int = 5,
        fetch_k: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Executa:

        Query Analyzer
              ↓
        Dense Search + BM25
              ↓
             RRF
              ↓
            Top-K
        """

        if not query or not query.strip():
            return []

        # -----------------------------------------------------
        # 1. QUERY ANALYZER
        # -----------------------------------------------------

        analise = analyze_query(query)

        query_normalizada = analise.get(
            "normalized_query",
            query
        )

        filtros = analise.get(
            "filters",
            {}
        )

        # -----------------------------------------------------
        # 2. EMBEDDING DA QUERY
        # -----------------------------------------------------

        query_vector = embed_texto(
            query_normalizada
        )

        # -----------------------------------------------------
        # 3. BUSCA DENSA
        # -----------------------------------------------------

        resultados_dense = self.vector_store.buscar(
            query_vector,
            top_k=fetch_k,
            filtro=filtros,
            fetch_k=fetch_k,
        )

        # -----------------------------------------------------
        # 4. BUSCA BM25
        # -----------------------------------------------------

        resultados_bm25 = self.bm25.buscar(
            query_normalizada,
            top_k=fetch_k,
            filtro=filtros,
        )

        # -----------------------------------------------------
        # 5. NORMALIZAÇÃO
        # -----------------------------------------------------

        resultados_dense = [
            self._normalizar_resultado(resultado)
            for resultado in resultados_dense
        ]

        resultados_bm25 = [
            self._normalizar_resultado(resultado)
            for resultado in resultados_bm25
        ]

        # -----------------------------------------------------
        # 6. RRF
        # -----------------------------------------------------

        resultados = self._rrf(
            resultados_dense,
            resultados_bm25,
        )

        # -----------------------------------------------------
        # 7. TOP-K
        # -----------------------------------------------------

        return resultados[:top_k]


# =============================================================
# TESTE MANUAL
# =============================================================

if __name__ == "__main__":

    INDEX_DIR = os.getenv(
        "INDEX_DIR",
        "index_store"
    )

    print("=" * 60)
    print("TESTE DE BUSCA HÍBRIDA")
    print("=" * 60)

    print(
        f"\nCarregando índice: {INDEX_DIR}"
    )

    vector_store = VectorStore.carregar(
        INDEX_DIR
    )

    print(
        f"Índice carregado. "
        f"Total de vetores: "
        f"{len(vector_store.textos)}"
    )

    search = HybridSearch(
        vector_store
    )

    perguntas = [
        (
            "Quais tickets de clientes de Minas "
            "Gerais estão relacionados ao módulo "
            "de estoque?"
        ),
        "Quais são os planos disponíveis?",
        "Qual é o procedimento para sangria no PDV?",
    ]

    for pergunta in perguntas:

        print("\n" + "=" * 60)
        print(
            f"PERGUNTA: {pergunta}"
        )
        print("=" * 60)

        resultados = search.buscar(
            pergunta,
            top_k=5,
            fetch_k=20,
        )

        if not resultados:
            print(
                "\nNenhum resultado encontrado."
            )
            continue

        for i, resultado in enumerate(
            resultados,
            start=1
        ):
            metadata = resultado.get(
                "metadata",
                {}
            )

            print(
                f"\n--- Resultado {i} ---"
            )

            print(
                "Arquivo:",
                metadata.get(
                    "source_file",
                    "desconhecido"
                )
            )

            print(
                "Chunk:",
                metadata.get(
                    "chunk_id",
                    "desconhecido"
                )
            )

            print(
                "RRF:",
                resultado.get(
                    "rrf_score"
                )
            )

            print(
                "Dense:",
                resultado.get(
                    "dense_score"
                )
            )

            print(
                "BM25:",
                resultado.get(
                    "bm25_score"
                )
            )

            texto = resultado.get(
                "text",
                ""
            )

            print(
                "Texto:",
                texto[:500].replace(
                    "\n",
                    " "
                )
            )