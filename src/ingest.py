from __future__ import annotations
import os
import argparse

from src.loaders import carregar_todas_as_fontes_vetorizaveis
from src.chunking import chunk_texto
from src.embeddings import embed_textos
from src.vector_store import VectorStore

TIPOS_QUE_NAO_SAO_DIVIDIDOS = {"ticket", "pricing_plan", "store_profile", "employee_record"}


def preparar_chunks(documentos: list[dict], chunk_size: int, chunk_overlap: int) -> list[dict]:
    chunks_finais = []

    for doc in documentos:
        texto = doc["text"]
        meta = doc["metadata"]

        if meta["doc_type"] in TIPOS_QUE_NAO_SAO_DIVIDIDOS or len(texto) <= chunk_size:
            partes = [texto]
        else:
            partes = chunk_texto(texto, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        for i, parte in enumerate(partes):
            chunk_meta = dict(meta)
            chunk_meta["chunk_index"] = i
            chunk_meta["total_chunks_do_documento"] = len(partes)
            chunks_finais.append({"text": parte, "metadata": chunk_meta})

    return chunks_finais


def rodar_ingestao(data_dir: str, saida_dir: str, chunk_size: int = 800, chunk_overlap: int = 100) -> VectorStore:
    print("1/4 -- Carregando documentos de todas as fontes...")
    documentos = carregar_todas_as_fontes_vetorizaveis(data_dir)
    print(f"   {len(documentos)} documentos carregados.")

    print("2/4 -- Dividindo em chunks...")
    chunks = preparar_chunks(documentos, chunk_size, chunk_overlap)
    print(f"   {len(chunks)} chunks gerados.")

    sensiveis = sum(1 for c in chunks if c["metadata"].get("is_sensitive"))
    print(f"   {sensiveis} chunks marcados como potencialmente sensíveis (LGPD/segredo).")

    print("3/4 -- Gerando embeddings...")
    textos = [c["text"] for c in chunks]
    vetores = embed_textos(textos)

    print("4/4 -- Indexando no FAISS...")
    store = VectorStore(dim=vetores.shape[1])
    store.adicionar(vetores, textos, [c["metadata"] for c in chunks])
    store.salvar(saida_dir)
    print(f"   Índice salvo em '{saida_dir}/' ({len(chunks)} vetores, dimensão {vetores.shape[1]}).")

    return store


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data", help="Pasta raiz dos dados do desafio")
    parser.add_argument("--saida", default="index_store", help="Pasta onde salvar o índice vetorial")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    args = parser.parse_args()

    rodar_ingestao(args.data_dir, args.saida, args.chunk_size, args.chunk_overlap)
