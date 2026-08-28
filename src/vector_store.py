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

    def adicionar(
        self,
        vetores: np.ndarray,
        textos: list[str],
        metadados: list[dict]
    ) -> None:

        vetores = np.asarray(
            vetores,
            dtype="float32"
        )

        self.index.add(vetores)

        self.textos.extend(textos)
        self.metadados.extend(metadados)

    def _indices_que_passam_no_filtro(
        self,
        filtro: dict | None
    ) -> list[int]:

        # Sem filtro: todos os documentos são válidos
        if not filtro:
            return list(range(len(self.textos)))

        indices = []

        for i, meta in enumerate(self.metadados):

            passou = True

            for chave, valor in filtro.items():

                atual = str(
                    meta.get(chave, "")
                ).strip().lower()

                esperado = str(
                    valor
                ).strip().lower()

                # -----------------------------------------
                # Tratamento especial para módulo
                # -----------------------------------------
                if chave == "module":

                    # Alguns documentos possuem apenas:
                    # "estoque", "pay", "pdv" etc.
                    #
                    # Outros possuem:
                    # "VendeFácil Analytics, VendeFácil Loja,
                    #  VendeFácil Estoque"

                    modulos = [
                        item.strip().lower()
                        for item in atual.split(",")
                    ]

                    if esperado not in modulos:
                        passou = False
                        break

                # -----------------------------------------
                # Demais metadados
                # -----------------------------------------
                else:

                    if atual != esperado:
                        passou = False
                        break

            if passou:
                indices.append(i)

        return indices

    def buscar(
        self,
        vetor_query: np.ndarray,
        top_k: int = 5,
        filtro: dict | None = None,
        fetch_k: int = 100
    ) -> list[dict]:

        vetor_query = np.asarray(
            vetor_query,
            dtype="float32"
        ).reshape(1, -1)

        indices_validos = (
            self._indices_que_passam_no_filtro(
                filtro
            )
        )

        # Não existem documentos que atendem
        # aos filtros
        if not indices_validos:
            return []

        # ==================================================
        # SEM FILTRO
        # ==================================================

        if filtro is None:

            k_busca = min(
                len(self.textos),
                fetch_k
            )

            scores, indices = self.index.search(
                vetor_query,
                k_busca
            )

            resultados = []

            for score, idx in zip(
                scores[0],
                indices[0]
            ):

                if idx == -1:
                    continue

                resultados.append({
                    "text": self.textos[idx],
                    "metadata": self.metadados[idx],
                    "score": float(score),
                })

                if len(resultados) >= top_k:
                    break

            return resultados

        # ==================================================
        # COM FILTRO
        # ==================================================
        #
        # Primeiro selecionamos apenas os documentos
        # que atendem aos metadados.
        #
        # Depois calculamos a similaridade somente
        # dentro desse subconjunto.
        # ==================================================

        vetores_validos = np.array(
            [
                self.index.reconstruct(i)
                for i in indices_validos
            ],
            dtype="float32"
        )

        # Similaridade por produto interno.
        # Como os embeddings foram normalizados,
        # isso equivale à similaridade de cosseno.

        scores = (
            vetores_validos @ vetor_query[0]
        )

        ordem = np.argsort(scores)[::-1]

        resultados = []

        for pos in ordem[:top_k]:

            idx_original = indices_validos[pos]

            resultados.append({
                "text": self.textos[idx_original],
                "metadata": self.metadados[idx_original],
                "score": float(scores[pos]),
            })

        return resultados

    def salvar(
        self,
        pasta: str
    ) -> None:

        os.makedirs(
            pasta,
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            os.path.join(
                pasta,
                "index.faiss"
            )
        )

        with open(
            os.path.join(
                pasta,
                "store.json"
            ),
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                {
                    "textos": self.textos,
                    "metadados": self.metadados,
                    "dim": self.dim
                },
                f,
                ensure_ascii=False
            )

    @classmethod
    def carregar(
        cls,
        pasta: str
    ) -> "VectorStore":

        with open(
            os.path.join(
                pasta,
                "store.json"
            ),
            "r",
            encoding="utf-8"
        ) as f:

            dados = json.load(f)

        store = cls(
            dim=dados["dim"]
        )

        store.index = faiss.read_index(
            os.path.join(
                pasta,
                "index.faiss"
            )
        )

        store.textos = dados["textos"]

        store.metadados = dados["metadados"]

        return store