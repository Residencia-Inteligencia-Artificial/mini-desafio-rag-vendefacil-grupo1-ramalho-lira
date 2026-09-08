from __future__ import annotations

import os
from typing import List

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# ============================================================
# CONFIGURAÇÃO
# ============================================================

EMBEDDING_PROVIDER = os.getenv(
    "EMBEDDING_PROVIDER",
    "openrouter",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-minilm-l6-v2",
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)

# OpenRouter aceita múltiplos textos por requisição.
# 500 mantém uma margem segura em relação ao limite de 1024
# que encontramos no seu erro anterior.
EMBEDDING_BATCH_SIZE = int(
    os.getenv(
        "EMBEDDING_BATCH_SIZE",
        "500",
    )
)


# ============================================================
# CACHE
# ============================================================

_cache = {}


# ============================================================
# CLIENTE OPENROUTER
# ============================================================

def _openrouter_client() -> OpenAI:
    """
    Cria e mantém em cache o cliente OpenRouter.
    """

    if "openrouter" not in _cache:

        if not OPENROUTER_API_KEY:
            raise RuntimeError(
                "OPENROUTER_API_KEY não foi encontrada no arquivo .env"
            )

        print(
            "Inicializando cliente de embeddings via OpenRouter..."
        )

        _cache["openrouter"] = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )

    return _cache["openrouter"]


# ============================================================
# LIMPEZA DOS TEXTOS
# ============================================================

def _limpar_textos(
    textos: List[str],
) -> List[str]:
    """
    Garante que todos os textos sejam strings válidas.
    """

    textos_limpos = []

    for texto in textos:

        if texto is None:
            textos_limpos.append(" ")

        else:
            texto = str(texto).strip()

            if not texto:
                textos_limpos.append(" ")

            else:
                textos_limpos.append(texto)

    return textos_limpos


# ============================================================
# EMBEDDINGS VIA OPENROUTER
# ============================================================

def _embed_textos_openrouter(
    textos: List[str],
) -> np.ndarray:
    """
    Gera embeddings usando OpenRouter.

    Os textos são enviados em lotes para evitar
    ultrapassar o limite de itens por requisição.
    """

    if not textos:
        return np.empty(
            (0, 0),
            dtype="float32",
        )

    client = _openrouter_client()

    textos_limpos = _limpar_textos(textos)

    todos_vetores = []

    total = len(textos_limpos)

    total_lotes = (
        (total + EMBEDDING_BATCH_SIZE - 1)
        // EMBEDDING_BATCH_SIZE
    )

    print(
        f"Gerando embeddings de {total} textos..."
    )

    for inicio in range(
        0,
        total,
        EMBEDDING_BATCH_SIZE,
    ):

        fim = min(
            inicio + EMBEDDING_BATCH_SIZE,
            total,
        )

        lote = textos_limpos[inicio:fim]

        numero_lote = (
            inicio // EMBEDDING_BATCH_SIZE
        ) + 1

        print(
            f"  Lote {numero_lote}/{total_lotes} "
            f"({inicio + 1}-{fim}/{total})..."
        )

        try:

            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=lote,
            )

        except Exception as erro:

            raise RuntimeError(
                "Erro ao gerar embeddings via OpenRouter: "
                f"{erro}"
            ) from erro

        # ----------------------------------------------------
        # A API retorna índice para cada embedding.
        # Ordenamos para garantir que cada vetor continue
        # correspondendo ao texto correto.
        # ----------------------------------------------------

        dados = sorted(
            response.data,
            key=lambda item: item.index,
        )

        vetores_lote = [
            item.embedding
            for item in dados
        ]

        todos_vetores.extend(
            vetores_lote
        )

    vetores = np.asarray(
        todos_vetores,
        dtype="float32",
    )

    print(
        f"OK - Embeddings gerados: {vetores.shape}"
    )

    return vetores


# ============================================================
# HUGGING FACE LOCAL - OPCIONAL
# ============================================================

def _embed_textos_huggingface(
    textos: List[str],
) -> np.ndarray:
    """
    Gera embeddings localmente usando SentenceTransformer.

    Essa opção não usa API nem OPENROUTER.
    """

    from sentence_transformers import SentenceTransformer

    if "hf" not in _cache:

        print(
            f"Carregando modelo de embeddings "
            f"'{EMBEDDING_MODEL}' "
            f"(Hugging Face, local)..."
        )

        _cache["hf"] = SentenceTransformer(
            EMBEDDING_MODEL
        )

    modelo = _cache["hf"]

    textos_limpos = _limpar_textos(textos)

    vetores = modelo.encode(
        textos_limpos,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    return np.asarray(
        vetores,
        dtype="float32",
    )


# ============================================================
# OPENAI DIRETO - OPCIONAL
# ============================================================

def _embed_textos_openai(
    textos: List[str],
) -> np.ndarray:
    """
    Gera embeddings usando diretamente a API da OpenAI.
    """

    openai_api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY não foi encontrada."
        )

    client = OpenAI(
        api_key=openai_api_key
    )

    model_name = os.getenv(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small",
    )

    textos_limpos = _limpar_textos(
        textos
    )

    todos_vetores = []

    total = len(textos_limpos)

    for inicio in range(
        0,
        total,
        EMBEDDING_BATCH_SIZE,
    ):

        fim = min(
            inicio + EMBEDDING_BATCH_SIZE,
            total,
        )

        lote = textos_limpos[
            inicio:fim
        ]

        response = client.embeddings.create(
            input=lote,
            model=model_name,
        )

        dados = sorted(
            response.data,
            key=lambda item: item.index,
        )

        todos_vetores.extend(
            item.embedding
            for item in dados
        )

    return np.asarray(
        todos_vetores,
        dtype="float32",
    )


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def embed_textos(
    textos: List[str],
):
    """
    Gera embeddings para uma lista de textos.

    Retorna:
        np.ndarray com formato:

        (quantidade_de_textos, dimensao_embedding)
    """

    if EMBEDDING_PROVIDER == "openrouter":

        return _embed_textos_openrouter(
            textos
        )

    if EMBEDDING_PROVIDER == "huggingface":

        return _embed_textos_huggingface(
            textos
        )

    if EMBEDDING_PROVIDER == "openai":

        return _embed_textos_openai(
            textos
        )

    raise ValueError(
        "EMBEDDING_PROVIDER desconhecido: "
        f"{EMBEDDING_PROVIDER}"
    )


# ============================================================
# EMBEDDING DE UM ÚNICO TEXTO
# ============================================================

def embed_texto(
    texto: str,
):
    """
    Gera o embedding de um único texto.
    """

    vetores = embed_textos(
        [texto]
    )

    return vetores[0]