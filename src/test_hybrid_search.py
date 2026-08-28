from src.vector_store import VectorStore
from src.search_hibrid import HybridSearch


INDEX_DIR = "index_store"


def main():

    print("=" * 70)
    print("ETAPA 2 - BUSCA HÍBRIDA")
    print("=" * 70)

    # --------------------------------------------------
    # 1. Carregar índice existente
    # --------------------------------------------------

    print("\n1. Carregando índice FAISS...")

    store = VectorStore.carregar(
        INDEX_DIR
    )

    print(
        f"Índice carregado: {store.index.ntotal} vetores"
    )

    # --------------------------------------------------
    # 2. Criar mecanismo de busca híbrida
    # --------------------------------------------------

    print("\n2. Inicializando busca híbrida...")

    hybrid_search = HybridSearch(
        store
    )

    # --------------------------------------------------
    # 3. Pergunta de teste
    # --------------------------------------------------

    pergunta = (
        "Quais tickets de clientes de Minas Gerais "
        "estão relacionados ao módulo de estoque?"
    )

    print("\n" + "-" * 70)
    print("PERGUNTA:")
    print(pergunta)
    print("-" * 70)

    # --------------------------------------------------
    # 4. Executar busca
    # --------------------------------------------------

    resultado = hybrid_search.buscar(
        pergunta,
        top_k=5
    )

    # --------------------------------------------------
    # 5. Mostrar filtros
    # --------------------------------------------------

    print("\nFILTROS EXTRAÍDOS:")

    if resultado["filters"]:

        for chave, valor in resultado["filters"].items():

            print(
                f"  {chave}: {valor}"
            )

    else:

        print("  Nenhum filtro encontrado.")

    # --------------------------------------------------
    # 6. Mostrar resultados
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("RESULTADOS DA BUSCA HÍBRIDA")
    print("=" * 70)

    resultados = resultado[
        "hybrid_results"
    ]

    if not resultados:

        print("\nNenhum resultado encontrado.")
        return

    for i, item in enumerate(
        resultados,
        start=1
    ):

        metadata = item["metadata"]

        print(f"\n{i}.")
        print(
            f"Chunk ID: "
            f"{metadata.get('chunk_id')}"
        )

        print(
            f"Arquivo: "
            f"{metadata.get('source_file')}"
        )

        print(
            f"Doc type: "
            f"{metadata.get('doc_type')}"
        )

        print(
            f"Estado: "
            f"{metadata.get('state')}"
        )

        print(
            f"Módulo: "
            f"{metadata.get('module')}"
        )

        print(
            f"RRF Score: "
            f"{item.get('rrf_score', 0):.6f}"
        )

        print("\nTexto:")

        texto = item["text"]

        # Evita imprimir chunks gigantes
        if len(texto) > 500:

            texto = texto[:500] + "..."

        print(texto)


if __name__ == "__main__":
    main()