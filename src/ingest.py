from __future__ import annotations

import argparse
import hashlib

from src.loaders import (
    carregar_todas_as_fontes_vetorizaveis
)

from src.chunking import (
    chunk_texto,
    chunk_markdown,
    chunk_pdf,
    chunk_txt,
)


TIPOS_REGISTRO = {
    "customer",
    "employee",
    "product",
    "store",
    "sale",
    "ticket",
    "log",
}


def gerar_chunk_id(
    source_file: str,
    texto: str,
    indice: int
) -> str:

    valor = (
        f"{source_file}|"
        f"{indice}|"
        f"{texto}"
    )

    return hashlib.sha256(
        valor.encode("utf-8")
    ).hexdigest()[:16]


def preparar_chunks(
    documentos: list[dict],
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> list[dict]:

    chunks_finais = []

    for documento in documentos:

        texto = documento["text"]
        metadata_original = documento[
            "metadata"
        ]

        doc_type = metadata_original[
            "doc_type"
        ]

        source_file = metadata_original[
            "source_file"
        ]

        if doc_type in TIPOS_REGISTRO:

            partes = [texto]

            secoes = [None]

        elif doc_type in {
            "manual",
            "ata",
            "policy"
        }:

            partes_secoes = chunk_markdown(
                texto,
                chunk_size,
                chunk_overlap
            )

            partes = [
                item["text"]
                for item in partes_secoes
            ]

            secoes = [
                item.get("section")
                for item in partes_secoes
            ]

        elif doc_type == "email":

            partes = chunk_txt(
                texto,
                chunk_size,
                chunk_overlap
            )

            secoes = [
                None
            ] * len(partes)

        else:

            partes = chunk_texto(
                texto,
                chunk_size,
                chunk_overlap
            )

            secoes = [
                None
            ] * len(partes)

        total = len(partes)

        for i, parte in enumerate(partes):

            metadata = dict(
                metadata_original
            )

            metadata[
                "chunk_id"
            ] = gerar_chunk_id(
                source_file,
                parte,
                i
            )

            metadata[
                "chunk_index"
            ] = i

            metadata[
                "total_chunks"
            ] = total

            if secoes[i]:
                metadata[
                    "section"
                ] = secoes[i]

            # Garantias do schema
            metadata.setdefault(
                "source_file",
                source_file
            )

            metadata.setdefault(
                "doc_type",
                "unknown"
            )

            metadata.setdefault(
                "sensitivity",
                "interno"
            )

            chunks_finais.append({
                "text": parte,
                "metadata": metadata
            })

    return chunks_finais


def validar_metadados(
    chunks: list[dict]
) -> None:

    obrigatorios = {
        "source_file",
        "doc_type",
        "chunk_id",
        "sensitivity",
    }

    erros = []

    for i, chunk in enumerate(chunks):

        metadata = chunk["metadata"]

        faltando = (
            obrigatorios
            - set(metadata.keys())
        )

        if faltando:

            erros.append(
                f"Chunk {i}: "
                f"faltando {faltando}"
            )

        if metadata.get(
            "sensitivity"
        ) not in {
            "publico",
            "interno",
            "restrito"
        }:

            erros.append(
                f"Chunk {i}: "
                f"sensitivity inválido"
            )

    if erros:

        raise ValueError(
            "\n".join(erros)
        )


def rodar_ingestao(
    data_dir: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100
):

    print(
        "1/3 - Carregando documentos..."
    )

    documentos = (
        carregar_todas_as_fontes_vetorizaveis(
            data_dir
        )
    )

    print(
        f"Documentos carregados: "
        f"{len(documentos)}"
    )

    print(
        "2/3 - Aplicando chunking adaptativo..."
    )

    chunks = preparar_chunks(
        documentos,
        chunk_size,
        chunk_overlap
    )

    print(
        f"Chunks gerados: "
        f"{len(chunks)}"
    )

    print(
        "3/3 - Validando metadados..."
    )

    validar_metadados(
        chunks
    )

    print(
        "OK - Todos os chunks possuem "
        "source_file, doc_type, chunk_id "
        "e sensitivity."
    )

    return chunks


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data-dir",
        default="data"
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800
    )

    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100
    )

    args = parser.parse_args()

    chunks = rodar_ingestao(
        args.data_dir,
        args.chunk_size,
        args.chunk_overlap
    )

    print()
    print(
        f"TOTAL FINAL: {len(chunks)} chunks"
    )
