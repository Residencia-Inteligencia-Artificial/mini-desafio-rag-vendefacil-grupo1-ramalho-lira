from __future__ import annotations
import os
import json
import numpy as np
import faiss


class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim) 
        self.textos: list[str] = []
        self.metadados: list[dict] = []

    def adicionar(self, vetores: np.ndarray, textos: list[str], metadados: list[dict]) -> None:
        vetores = np.asarray(vetores, dtype="float32")
        self.index.add(vetores)
        self.textos.extend(textos)
        self.metadados.extend(metadados)

    def _indices_que_passam_no_filtro(self, filtro: dict | None) -> set[int] | None:
        if not filtro:
            return None
        indices = set()
        for i, meta in enumerate(self.metadados):
            if all(meta.get(chave) == valor for chave, valor in filtro.items()):
                indices.add(i)
        return indices

    def buscar(self, vetor_query: np.ndarray, top_k: int = 5, filtro: dict | None = None) -> list[dict]:
        vetor_query = np.asarray(vetor_query, dtype="float32").reshape(1, -1)

        indices_validos = self._indices_que_passam_no_filtro(filtro)

        k_busca = min(len(self.textos), top_k * 20 if indices_validos is not None else top_k)
        if k_busca == 0:
            return []

        scores, indices = self.index.search(vetor_query, k_busca)

        resultados = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            if indices_validos is not None and idx not in indices_validos:
                continue
            resultados.append({
                "text": self.textos[idx],
                "metadata": self.metadados[idx],
                "score": float(score),
            })
            if len(resultados) >= top_k:
                break

        return resultados

    def salvar(self, pasta: str) -> None:
        os.makedirs(pasta, exist_ok=True)
        faiss.write_index(self.index, os.path.join(pasta, "index.faiss"))
        with open(os.path.join(pasta, "store.json"), "w", encoding="utf-8") as f:
            json.dump({"textos": self.textos, "metadados": self.metadados, "dim": self.dim}, f, ensure_ascii=False)

    @classmethod
    def carregar(cls, pasta: str) -> "VectorStore":
        with open(os.path.join(pasta, "store.json"), "r", encoding="utf-8") as f:
            dados = json.load(f)
        store = cls(dim=dados["dim"])
        store.index = faiss.read_index(os.path.join(pasta, "index.faiss"))
        store.textos = dados["textos"]
        store.metadados = dados["metadados"]
        return store
