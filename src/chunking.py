from __future__ import annotations

import re

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
def chunk_texto(
    texto: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> list[str]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    return splitter.split_text(
        texto.strip()
    )

def chunk_markdown(
    texto: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> list[dict]:

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "section"),
            ("##", "section"),
            ("###", "section"),
        ],
        strip_headers=False
    )

    secoes = splitter.split_text(
        texto
    )

    resultado = []

    fallback = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    for secao in secoes:

        conteudo = secao.page_content

        if len(conteudo) <= chunk_size:

            resultado.append({
                "text": conteudo,
                "section": secao.metadata.get(
                    "section"
                )
            })

        else:

            partes = fallback.split_text(
                conteudo
            )

            for parte in partes:

                resultado.append({
                    "text": parte,
                    "section": secao.metadata.get(
                        "section"
                    )
                })

    return resultado

def chunk_pdf(
    texto: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> list[str]:

    paragrafos = [
        p.strip()
        for p in re.split(
            r"\n\s*\n",
            texto
        )
        if p.strip()
    ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    resultado = []

    for paragrafo in paragrafos:

        if len(paragrafo) <= chunk_size:

            resultado.append(
                paragrafo
            )

        else:

            resultado.extend(
                splitter.split_text(
                    paragrafo
                )
            )

    return resultado

def chunk_txt(
    texto: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> list[str]:

    mensagens = re.split(
        r"\n(?:---+|={3,})\n",
        texto
    )

    mensagens = [
        m.strip()
        for m in mensagens
        if m.strip()
    ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    resultado = []

    for mensagem in mensagens:

        if len(mensagem) <= chunk_size:

            resultado.append(
                mensagem
            )

        else:

            resultado.extend(
                splitter.split_text(
                    mensagem
                )
            )

    return resultado