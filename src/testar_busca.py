"""
Script de teste rápido -- roda algumas buscas de exemplo no índice já
gerado, para conferir visualmente se a ingestão fez sentido.

Uso:
    python -m src.testar_busca
"""

from __future__ import annotations
from src.vector_store import VectorStore
from src.embeddings import embed_texto

PERGUNTAS_DE_TESTE = [
    ("Erro de sincronização de estoque entre filiais", {"doc_type": "ticket"}),
    ("Qual o SLA para incidentes críticos?", {"doc_type": "policy"}),
    ("Como funciona o PIX dinâmico no VendeFácil Pay?", None),
    ("Chamados do módulo de estoque em Minas Gerais", {"doc_type": "ticket", "state": "MG"}),
]


def main():
    store = VectorStore.carregar("index_store")
    print(f"Índice carregado: {len(store.textos)} chunks.\n")

    for pergunta, filtro in PERGUNTAS_DE_TESTE:
        print("=" * 70)
        print(f"Pergunta: {pergunta}")
        print(f"Filtro: {filtro}")
        print("=" * 70)

        vetor = embed_texto(pergunta)
        resultados = store.buscar(vetor, top_k=3, filtro=filtro)

        if not resultados:
            print("  (nenhum resultado)")
        for r in resultados:
            sensivel = " [SENSÍVEL]" if r["metadata"].get("is_sensitive") else ""
            print(f"  score={r['score']:.3f} [{r['metadata']['doc_type']}]{sensivel}")
            print(f"    {r['text'][:150].strip()}...")
        print()


if __name__ == "__main__":
    main()
