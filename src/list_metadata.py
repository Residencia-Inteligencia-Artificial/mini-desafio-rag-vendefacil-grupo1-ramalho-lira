from src.vector_store import VectorStore


INDEX_DIR = "index_store"


def main():

    store = VectorStore.carregar(INDEX_DIR)

    campos = [
        "doc_type",
        "state",
        "module",
        "priority",
        "status",
        "sensitivity"
    ]

    for campo in campos:

        valores = sorted({
            str(meta.get(campo))
            for meta in store.metadados
            if meta.get(campo) is not None
        })

        print(f"\n{campo}:")
        
        for valor in valores:
            print(f"  - {valor}")


if __name__ == "__main__":
    main()