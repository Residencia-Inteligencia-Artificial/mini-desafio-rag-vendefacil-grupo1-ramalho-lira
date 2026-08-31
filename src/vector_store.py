from __future__ import annotations

import json
import os

import faiss
import numpy as np


class VectorStore:
    """
    Armazena embeddings no índice FAISS junto com os textos
    e respectivos metadados.

    Estrutura esperada:

        index_store/
            index.faiss
            store.json
    """

    def __init__(self, dim: int):
        self.dim = dim

        # Produto interno.
        # Como os embeddings são normalizados,
        # equivale à similaridade de cosseno.
        self.index = faiss.IndexFlatIP(dim)

        self.textos: list[str] = []
        self.metadados: list[dict] = []

    # ==========================================================
    # ADICIONAR DOCUMENTOS
    # ==========================================================

    def adicionar(
        self,
        vetores: np.ndarray,
        textos: list[str],
        metadados: list[dict],
    ) -> None:

        vetores = np.asarray(
            vetores,
            dtype="float32",
        )

        # Garante matriz 2D
        if vetores.ndim == 1:
            vetores = vetores.reshape(1, -1)

        if vetores.ndim != 2:
            raise ValueError(
                "Os vetores precisam possuir formato 2D."
            )

        if vetores.shape[1] != self.dim:
            raise ValueError(
                f"Dimensão dos vetores ({vetores.shape[1]}) "
                f"é diferente da dimensão do índice ({self.dim})."
            )

        if len(textos) != len(vetores):
            raise ValueError(
                "A quantidade de textos deve ser igual "
                "à quantidade de vetores."
            )

        if len(metadados) != len(vetores):
            raise ValueError(
                "A quantidade de metadados deve ser igual "
                "à quantidade de vetores."
            )

        self.index.add(vetores)

        self.textos.extend(textos)

        self.metadados.extend(metadados)

    # ==========================================================
    # NORMALIZAÇÃO DE VALORES
    # ==========================================================

    @staticmethod
    def _normalizar_valor(valor) -> str:
        """
        Converte valores para comparação consistente.
        """

        if valor is None:
            return ""

        return str(valor).strip().lower()

    # ==========================================================
    # VERIFICAÇÃO DE FILTRO
    # ==========================================================

    @classmethod
    def _valor_atende_filtro(
        cls,
        atual,
        esperado,
        chave: str,
    ) -> bool:

        atual = cls._normalizar_valor(atual)
        esperado = cls._normalizar_valor(esperado)

        # ------------------------------------------------------
        # Filtro por módulo
        # ------------------------------------------------------

        if chave == "module":

            # Alguns documentos podem possuir:
            #
            # estoque
            #
            # ou:
            #
            # VendeFácil Analytics,
            # VendeFácil Loja,
            # VendeFácil Estoque

            valores = [
                item.strip()
                for item in atual.split(",")
            ]

            for valor in valores:

                if valor == esperado:
                    return True

                if esperado in valor:
                    return True

            return False

        # ------------------------------------------------------
        # Filtro por doc_type
        # ------------------------------------------------------

        if chave == "doc_type":

            return atual == esperado

        # ------------------------------------------------------
        # Demais campos
        # ------------------------------------------------------

        return atual == esperado

    # ==========================================================
    # ÍNDICES QUE PASSAM NO FILTRO
    # ==========================================================

    def _indices_que_passam_no_filtro(
        self,
        filtro: dict | None,
    ) -> list[int]:

        # Sem filtro:
        # todos os documentos podem ser utilizados.

        if not filtro:
            return list(
                range(len(self.textos))
            )

        indices = []

        for i, metadata in enumerate(
            self.metadados
        ):

            passou = True

            for chave, valor_esperado in filtro.items():

                valor_atual = metadata.get(
                    chave,
                    ""
                )

                if not self._valor_atende_filtro(
                    valor_atual,
                    valor_esperado,
                    chave,
                ):
                    passou = False
                    break

            if passou:
                indices.append(i)

        return indices

    # ==========================================================
    # BUSCA
    # ==========================================================

    def buscar(
        self,
        vetor_query: np.ndarray,
        top_k: int = 5,
        filtro: dict | None = None,
        fetch_k: int = 100,
    ) -> list[dict]:

        vetor_query = np.asarray(
            vetor_query,
            dtype="float32",
        )

        # ------------------------------------------------------
        # Normaliza formato da query
        # ------------------------------------------------------

        if vetor_query.ndim == 1:
            vetor_query = vetor_query.reshape(1, -1)

        if vetor_query.ndim != 2:
            raise ValueError(
                "O vetor da query precisa possuir formato 2D."
            )

        if vetor_query.shape[1] != self.dim:
            raise ValueError(
                f"Dimensão da query ({vetor_query.shape[1]}) "
                f"é diferente da dimensão do índice ({self.dim})."
            )

        # ------------------------------------------------------
        # Verifica filtro
        # ------------------------------------------------------

        indices_validos = (
            self._indices_que_passam_no_filtro(
                filtro
            )
        )

        # Nenhum documento atende ao filtro.

        if not indices_validos:
            return []

        # ======================================================
        # SEM FILTRO
        # ======================================================

        if not filtro:

            k_busca = min(
                len(self.textos),
                max(top_k, fetch_k),
            )

            scores, indices = self.index.search(
                vetor_query,
                k_busca,
            )

            resultados = []

            for score, idx in zip(
                scores[0],
                indices[0],
            ):

                if idx == -1:
                    continue

                resultados.append(
                    {
                        "text": self.textos[idx],
                        "metadata": self.metadados[idx],
                        "score": float(score),
                    }
                )

                if len(resultados) >= top_k:
                    break

            return resultados

        # ======================================================
        # COM FILTRO
        # ======================================================

        # Reconstrói apenas os vetores que passaram
        # pelos filtros.

        vetores_validos = np.array(
            [
                self.index.reconstruct(i)
                for i in indices_validos
            ],
            dtype="float32",
        )

        # Similaridade por produto interno.

        scores = (
            vetores_validos @ vetor_query[0]
        )

        # Ordena do maior para o menor.

        ordem = np.argsort(
            scores
        )[::-1]

        resultados = []

        for pos in ordem[:top_k]:

            idx_original = indices_validos[pos]

            resultados.append(
                {
                    "text": self.textos[idx_original],
                    "metadata": self.metadados[idx_original],
                    "score": float(scores[pos]),
                }
            )

        return resultados

    # ==========================================================
    # SALVAR
    # ==========================================================

    def salvar(
        self,
        pasta: str,
    ) -> None:

        if not isinstance(
            pasta,
            (str, os.PathLike),
        ):
            raise TypeError(
                "O parâmetro 'pasta' precisa ser um caminho "
                "para uma pasta, e não um objeto VectorStore."
            )

        os.makedirs(
            pasta,
            exist_ok=True,
        )

        caminho_index = os.path.join(
            pasta,
            "index.faiss",
        )

        caminho_store = os.path.join(
            pasta,
            "store.json",
        )

        # ------------------------------------------------------
        # Salva FAISS
        # ------------------------------------------------------

        faiss.write_index(
            self.index,
            caminho_index,
        )

        # ------------------------------------------------------
        # Salva textos e metadados
        # ------------------------------------------------------

        with open(
            caminho_store,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                {
                    "textos": self.textos,
                    "metadados": self.metadados,
                    "dim": self.dim,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    # ==========================================================
    # CARREGAR
    # ==========================================================

    @classmethod
    def carregar(
        cls,
        pasta: str,
    ) -> "VectorStore":

        # ------------------------------------------------------
        # Validação do caminho
        # ------------------------------------------------------

        if not isinstance(
            pasta,
            (str, os.PathLike),
        ):
            raise TypeError(
                "VectorStore.carregar() espera o caminho "
                "da pasta onde estão 'store.json' e "
                "'index.faiss'. "
                f"Foi recebido: {type(pasta).__name__}"
            )

        pasta = os.fspath(pasta)

        caminho_store = os.path.join(
            pasta,
            "store.json",
        )

        caminho_index = os.path.join(
            pasta,
            "index.faiss",
        )

        # ------------------------------------------------------
        # Verifica arquivos
        # ------------------------------------------------------

        if not os.path.exists(
            caminho_store
        ):
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho_store}"
            )

        if not os.path.exists(
            caminho_index
        ):
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho_index}"
            )

        # ------------------------------------------------------
        # Carrega store.json
        # ------------------------------------------------------

        with open(
            caminho_store,
            "r",
            encoding="utf-8",
        ) as f:

            dados = json.load(f)

        # ------------------------------------------------------
        # Valida dimensão
        # ------------------------------------------------------

        if "dim" not in dados:
            raise ValueError(
                "O arquivo store.json não possui "
                "o campo 'dim'."
            )

        # ------------------------------------------------------
        # Cria VectorStore
        # ------------------------------------------------------

        store = cls(
            dim=int(
                dados["dim"]
            )
        )

        # ------------------------------------------------------
        # Carrega FAISS
        # ------------------------------------------------------

        store.index = faiss.read_index(
            caminho_index
        )

        # ------------------------------------------------------
        # Carrega textos
        # ------------------------------------------------------

        store.textos = dados.get(
            "textos",
            [],
        )

        # ------------------------------------------------------
        # Carrega metadados
        # ------------------------------------------------------

        store.metadados = dados.get(
            "metadados",
            [],
        )

        # ------------------------------------------------------
        # Valida consistência
        # ------------------------------------------------------

        if store.index.ntotal != len(
            store.textos
        ):

            raise ValueError(
                "O índice FAISS e o store.json "
                "estão inconsistentes: "
                f"FAISS possui {store.index.ntotal} vetores, "
                f"mas existem {len(store.textos)} textos."
            )

        if len(
            store.textos
        ) != len(
            store.metadados
        ):

            raise ValueError(
                "Quantidade de textos e metadados é diferente: "
                f"{len(store.textos)} textos e "
                f"{len(store.metadados)} metadados."
            )

        # ------------------------------------------------------
        # Atualiza dimensão real do índice
        # ------------------------------------------------------

        store.dim = store.index.d

        print(
            f"Índice carregado: "
            f"{store.index.ntotal} vetores"
        )

        return store