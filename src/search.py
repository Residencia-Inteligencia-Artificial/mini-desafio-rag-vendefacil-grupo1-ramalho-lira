from rank_bm25 import BM25Okapi
import re


class BM25Search:

    def __init__(
        self,
        textos,
        metadados
    ):

        self.textos = textos
        self.metadados = metadados

        self.tokens = [
            self._tokenizar(texto)
            for texto in textos
        ]

        self.bm25 = BM25Okapi(
            self.tokens
        )

    @staticmethod
    def _tokenizar(texto):

        return re.findall(
            r"\b\w+\b",
            texto.lower()
        )

    def buscar(
        self,
        consulta,
        top_k=10,
        filtro=None
    ):

        indices_validos = []

        for i, meta in enumerate(
            self.metadados
        ):

            if not filtro:

                indices_validos.append(i)
                continue

            passou = all(
                str(meta.get(chave, "")).strip().lower()
                ==
                str(valor).strip().lower()
                for chave, valor in filtro.items()
            )

            if passou:
                indices_validos.append(i)

        if not indices_validos:
            return []

        consulta_tokens = self._tokenizar(
            consulta
        )

        scores = self.bm25.get_scores(
            consulta_tokens
        )

        ranking = sorted(
            indices_validos,
            key=lambda i: scores[i],
            reverse=True
        )

        resultados = []

        for i in ranking[:top_k]:

            resultados.append({
                "text": self.textos[i],
                "metadata": self.metadados[i],
                "score": float(scores[i])
            })

        return resultados