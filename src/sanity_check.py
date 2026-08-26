from collections import Counter

from src.embeddings import embed_textos
from src.load_index import carregar_indice


PERGUNTAS = [
    "Quais clientes estão localizados em Minas Gerais?",
    "Quais são os problemas mais comuns relatados pelos clientes nos tickets?",
    "Quais são as regras e políticas de segurança da VendeFácil?",
]


def mostrar_estatisticas(store):

    print("=" * 60)
    print("SANITY CHECK")
    print("=" * 60)

    total = len(
        store.textos
    )

    print()
    print(
        f"Total de chunks: {total}"
    )

    distribuicao = Counter(
        meta.get(
            "doc_type",
            "SEM_DOC_TYPE"
        )
        for meta in store.metadados
    )

    print()
    print(
        "Distribuição por doc_type:"
    )

    for tipo, quantidade in sorted(
        distribuicao.items()
    ):

        print(
            f"  {tipo}: {quantidade}"
        )


def executar_busca(
    store,
    pergunta,
    top_k=5
):

    print()
    print("-" * 60)
    print(
        f"PERGUNTA: {pergunta}"
    )
    print("-" * 60)

    vetor = embed_textos(
        [pergunta]
    )

    resultados = store.buscar(
        vetor[0],
        top_k=top_k
    )

    for posicao, resultado in enumerate(
        resultados,
        start=1
    ):

        metadata = resultado[
            "metadata"
        ]

        print()
        print(
            f"{posicao}. "
            f"Score: "
            f"{resultado['score']:.4f}"
        )

        print(
            f"   chunk_id: "
            f"{metadata.get('chunk_id')}"
        )

        print(
            f"   source_file: "
            f"{metadata.get('source_file')}"
        )

        print(
            f"   doc_type: "
            f"{metadata.get('doc_type')}"
        )

        print(
            f"   sensitivity: "
            f"{metadata.get('sensitivity')}"
        )

        print()
        print(
            f"   {resultado['text'][:500]}"
        )


def main():

    store = carregar_indice()

    mostrar_estatisticas(
        store
    )

    for pergunta in PERGUNTAS:

        executar_busca(
            store,
            pergunta,
            top_k=5
        )


if __name__ == "__main__":

    main()