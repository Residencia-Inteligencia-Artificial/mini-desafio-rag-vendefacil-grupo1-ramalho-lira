from collections import Counter

from src.ingest import rodar_ingestao
from src.embeddings import embed_textos
from src.vector_store import VectorStore

DATA_DIR = "data"
INDEX_DIR = "index_store"

def main():

    print("=" * 60)
    print("ETAPA 1 - INGESTÃO E INDEXAÇÃO")
    print("=" * 60)

    chunks = rodar_ingestao(
        data_dir=DATA_DIR,
        chunk_size=800,
        chunk_overlap=100
    )

    distribuicao = Counter(
        chunk["metadata"]["doc_type"]
        for chunk in chunks
    )

    print()
    print("Distribuição por doc_type:")

    for doc_type, quantidade in sorted(
        distribuicao.items()
    ):

        print(
            f"  {doc_type}: {quantidade}"
        )

    print()
    print("Gerando embeddings...")

    textos = [
        chunk["text"]
        for chunk in chunks
    ]

    vetores = embed_textos(
        textos
    )

    print(
        f"Dimensão dos embeddings: "
        f"{vetores.shape[1]}"
    )

    print()
    print("Criando índice FAISS...")

    store = VectorStore(
        dim=vetores.shape[1]
    )

    store.adicionar(
        vetores,
        textos,
        [
            chunk["metadata"]
            for chunk in chunks
        ]
    )

    store.salvar(
        INDEX_DIR
    )

    print()
    print(
        f"Índice salvo em: "
        f"{INDEX_DIR}/"
    )

    print(
        f"Vetores indexados: "
        f"{len(chunks)}"
    )

    print()
    print("ETAPA 1 CONCLUÍDA.")


if __name__ == "__main__":
    main()