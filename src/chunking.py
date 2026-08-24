"""
Chunking de textos longos (políticas, atas de reunião, documentação técnica).

Usa uma estratégia recursiva simples (sem depender do LangChain, para manter
o starter enxuto): tenta cortar por parágrafo primeiro, depois por linha,
só recorrendo a corte por caractere como último recurso. Nunca corta uma
tabela markdown no meio.
"""

from __future__ import annotations
import re


def _eh_linha_de_tabela(linha: str) -> bool:
    return linha.strip().startswith("|")


def _split_preservando_tabelas(texto: str, separador: str) -> list[str]:
    """Divide o texto pelo separador, mas nunca dentro de um bloco de tabela markdown."""
    blocos = []
    atual = []
    dentro_de_tabela = False

    for linha in texto.split("\n"):
        if _eh_linha_de_tabela(linha):
            dentro_de_tabela = True
            atual.append(linha)
            continue
        if dentro_de_tabela and not _eh_linha_de_tabela(linha):
            dentro_de_tabela = False
        atual.append(linha)

    texto_reconstruido = "\n".join(atual)
    # separador aplicado fora de blocos de tabela (tabelas não têm \n\n dentro delas)
    return texto_reconstruido.split(separador)


def chunk_texto(
    texto: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[str]:
    """
    Divide um texto longo em chunks de tamanho aproximado `chunk_size`,
    tentando respeitar parágrafos e linhas antes de cortar por caractere.
    """
    texto = texto.strip()
    if len(texto) <= chunk_size:
        return [texto] if texto else []

    # 1) tenta por parágrafo
    partes = [p for p in _split_preservando_tabelas(texto, "\n\n") if p.strip()]

    chunks: list[str] = []
    buffer = ""

    for parte in partes:
        candidato = f"{buffer}\n\n{parte}".strip() if buffer else parte

        if len(candidato) <= chunk_size:
            buffer = candidato
            continue

        # a parte sozinha já é maior que o chunk_size -> corta por linha/caractere
        if buffer:
            chunks.append(buffer)
            buffer = ""

        if len(parte) <= chunk_size:
            buffer = parte
            continue

        # corte forçado por caractere, com overlap, preservando quebra de linha quando possível
        inicio = 0
        while inicio < len(parte):
            fim = min(inicio + chunk_size, len(parte))
            # tenta terminar em uma quebra de linha próxima, pra não cortar frase no meio
            corte = parte.rfind("\n", inicio, fim)
            if corte == -1 or corte <= inicio:
                corte = fim
            chunks.append(parte[inicio:corte].strip())
            inicio = max(corte - chunk_overlap, corte) if corte < fim else fim

    if buffer:
        chunks.append(buffer)

    # aplica overlap simples entre chunks vizinhos gerados por parágrafo
    if chunk_overlap > 0 and len(chunks) > 1:
        chunks_com_overlap = [chunks[0]]
        for i in range(1, len(chunks)):
            cauda_anterior = chunks[i - 1][-chunk_overlap:]
            chunks_com_overlap.append(f"{cauda_anterior}\n{chunks[i]}")
        chunks = chunks_com_overlap

    return [c.strip() for c in chunks if c.strip()]
