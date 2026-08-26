from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

_cache = {}


def _hf_model():
    if "hf" not in _cache:
        from sentence_transformers import SentenceTransformer
        print(f"Carregando modelo de embeddings '{EMBEDDING_MODEL}' (Hugging Face, local)...")
        _cache["hf"] = SentenceTransformer(EMBEDDING_MODEL)
    return _cache["hf"]


def embed_textos(textos: list[str]):
    """Gera embeddings para uma lista de textos. Retorna np.ndarray (N, dim)."""
    if EMBEDDING_PROVIDER == "huggingface":
        modelo = _hf_model()
        return modelo.encode(textos, normalize_embeddings=True, show_progress_bar=True)

    if EMBEDDING_PROVIDER == "openai":
        from openai import OpenAI
        import numpy as np
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        vetores = []
        for texto in textos:
            resp = client.embeddings.create(input=[texto or " "], model=model_name)
            vetores.append(resp.data[0].embedding)
        return np.array(vetores, dtype="float32")

    raise ValueError(f"EMBEDDING_PROVIDER desconhecido: {EMBEDDING_PROVIDER}")


def embed_texto(texto: str):
    return embed_textos([texto])[0]
