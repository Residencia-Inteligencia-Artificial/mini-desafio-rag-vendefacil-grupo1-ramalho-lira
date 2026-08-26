from src.vector_store import VectorStore

INDEX_DIR = "index_store"

def carregar_indice():

    store = VectorStore.carregar(
        INDEX_DIR
    )

    print(
        "Índice carregado com sucesso."
    )

    print(
        f"Total de vetores: "
        f"{store.index.ntotal}"
    )

    return store


if __name__ == "__main__":
    carregar_indice()