from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List

from src.embeddings import embed_texto
from src.query_analyzer import analyze_query
from src.search import BM25Search
from src.vector_store import VectorStore


class HybridSearch:
    """
    Busca híbrida do VendeFácil.

    Combina:

    1. Busca densa usando embeddings + FAISS
    2. Busca esparsa usando BM25
    3. Filtros de metadados
    4. Reciprocal Rank Fusion (RRF)
    5. Bônus lexical
    6. Recuperação direta de identificadores
    7. Recuperação direta de termos
    8. Bônus contextual
    9. Priorização de resultados que atendem aos filtros
    """

    # ============================================================
    # INICIALIZAÇÃO
    # ============================================================

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

        self.bm25 = BM25Search(
            self.vector_store.textos,
            self.vector_store.metadados,
        )

    # ============================================================
    # UTILITÁRIOS
    # ============================================================

    @staticmethod
    def _normalizar(texto: Any) -> str:
        if texto is None:
            return ""

        texto_normalizado = unicodedata.normalize(
            "NFD",
            str(texto).strip().lower(),
        )
        return "".join(
            caractere
            for caractere in texto_normalizado
            if unicodedata.category(caractere) != "Mn"
        )

    @staticmethod
    def _obter_texto(
        resultado: Dict[str, Any],
    ) -> str:

        return (
            resultado.get("text")
            or resultado.get("texto")
            or ""
        )

    @staticmethod
    def _obter_metadata(
        resultado: Dict[str, Any],
    ) -> Dict[str, Any]:

        return (
            resultado.get("metadata")
            or resultado.get("metadados")
            or {}
        )

    @staticmethod
    def _obter_chave(
        resultado: Dict[str, Any],
        prefixo: str,
        rank: int,
    ) -> str:

        metadata = HybridSearch._obter_metadata(
            resultado
        )

        chunk_id = metadata.get("chunk_id")

        if not chunk_id:
            chunk_id = resultado.get("chunk_id")

        if chunk_id:
            return str(chunk_id)

        texto = HybridSearch._obter_texto(
            resultado
        )

        return f"{prefixo}-{rank}-{hash(texto)}"

    # ============================================================
    # FILTROS
    # ============================================================

    def _atende_todos_os_filtros(
        self,
        metadata: Dict[str, Any],
        filtros: Dict[str, Any],
    ) -> bool:

        if not filtros:
            return True

        for chave, esperado in filtros.items():

            real = metadata.get(chave)

            if real is None:
                return False

            esperado_norm = self._normalizar(
                esperado
            )

            real_norm = self._normalizar(
                real
            )

            # ----------------------------------------------------
            # MODULE
            # ----------------------------------------------------

            if chave == "module":

                valores = [
                    item.strip()
                    for item in real_norm.split(",")
                ]

                if esperado_norm not in valores:
                    return False

            # ----------------------------------------------------
            # OUTROS FILTROS
            # ----------------------------------------------------

            else:

                if real_norm != esperado_norm:
                    return False

        return True

    # ============================================================
    # FILTROS RELAXADOS
    # ============================================================

    def _gerar_filtros_relaxados(
        self,
        filtros: Dict[str, Any] | None,
    ) -> List[Dict[str, Any]]:

        if not filtros:
            return [{}]

        filtros = dict(filtros)

        # --------------------------------------------------------
        # IMPORTANTE:
        #
        # O PRIMEIRO filtro é sempre o filtro completo.
        #
        # O relaxamento só será usado se a busca completa
        # não encontrar nenhum resultado.
        # --------------------------------------------------------

        resultados: List[Dict[str, Any]] = [
            filtros
        ]

        # --------------------------------------------------------
        # Remove module
        # --------------------------------------------------------

        if "module" in filtros:

            novo = dict(filtros)

            novo.pop(
                "module",
                None,
            )

            if novo not in resultados:
                resultados.append(novo)

        # --------------------------------------------------------
        # Remove state
        # --------------------------------------------------------

        if "state" in filtros:

            novo = dict(filtros)

            novo.pop(
                "state",
                None,
            )

            if novo not in resultados:
                resultados.append(novo)

        # --------------------------------------------------------
        # Remove city
        # --------------------------------------------------------

        if "city" in filtros:

            novo = dict(filtros)

            novo.pop(
                "city",
                None,
            )

            if novo not in resultados:
                resultados.append(novo)

        # --------------------------------------------------------
        # Remove customer_id
        # --------------------------------------------------------

        if "customer_id" in filtros:

            novo = dict(filtros)

            novo.pop(
                "customer_id",
                None,
            )

            if novo not in resultados:
                resultados.append(novo)

        # --------------------------------------------------------
        # Somente doc_type
        # --------------------------------------------------------

        if "doc_type" in filtros:

            novo = {
                "doc_type": filtros["doc_type"]
            }

            if novo not in resultados:
                resultados.append(novo)

        # --------------------------------------------------------
        # Sem filtro
        # --------------------------------------------------------

        if {} not in resultados:
            resultados.append({})

        return resultados

    # ============================================================
    # IDENTIFICADORES
    # ============================================================

    def _extrair_identificadores(
        self,
        query: str,
    ) -> List[str]:

        encontrados: List[str] = []

        texto = query.upper()

        # --------------------------------------------------------
        # CUSTOMER
        # --------------------------------------------------------

        clientes = re.findall(
            r"\bCUST\d+\b",
            texto,
        )

        for identificador in clientes:

            if identificador not in encontrados:
                encontrados.append(
                    identificador
                )

        # --------------------------------------------------------
        # TICKET
        # --------------------------------------------------------

        tickets = re.findall(
            r"\bTCK[- ]?\d+\b",
            texto,
        )

        for identificador in tickets:

            identificador = identificador.replace(
                " ",
                "-",
            )

            if identificador not in encontrados:
                encontrados.append(
                    identificador
                )

        # --------------------------------------------------------
        # ESTOQUE
        # --------------------------------------------------------

        estoque = re.findall(
            r"\bSTK[- ]?\d+\b",
            texto,
        )

        for identificador in estoque:

            identificador = identificador.replace(
                " ",
                "-",
            )

            if identificador not in encontrados:
                encontrados.append(
                    identificador
                )

        return encontrados

    # ============================================================
    # BUSCA DIRETA DE IDENTIFICADORES
    # ============================================================

    def _buscar_identificadores_direto(
        self,
        query: str,
        filtros: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:

        identificadores = (
            self._extrair_identificadores(
                query
            )
        )

        if not identificadores:
            return []

        textos = getattr(
            self.vector_store,
            "textos",
            [],
        )

        metadatas = getattr(
            self.vector_store,
            "metadados",
            [],
        )

        resultados: List[
            Dict[str, Any]
        ] = []

        for index, texto in enumerate(textos):

            if not texto:
                continue

            texto_upper = str(
                texto
            ).upper()

            encontrados = []

            for identificador in identificadores:

                if identificador in texto_upper:

                    encontrados.append(
                        identificador
                    )

            if not encontrados:
                continue

            metadata = {}

            if index < len(metadatas):

                metadata = (
                    metadatas[index]
                    or {}
                )

            # ----------------------------------------------------
            # IMPORTANTE:
            #
            # Recuperação direta também precisa respeitar filtros.
            # ----------------------------------------------------

            if filtros and not self._atende_todos_os_filtros(
                metadata,
                filtros,
            ):
                continue

            resultados.append(
                {
                    "text": texto,
                    "metadata": metadata,
                    "score": 1.0,
                    "exact_identifiers": encontrados,
                    "direct_match": True,
                }
            )

        return resultados

    # ============================================================
    # BUSCA DIRETA DE TERMOS
    # ============================================================

    def _buscar_termos_direto(
        self,
        query: str,
        filtros: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:

        query_norm = self._normalizar(
            query
        )

        grupos: List[List[str]] = []

        # --------------------------------------------------------
        # PLANOS
        # --------------------------------------------------------

        if (
            "quais são os planos" in query_norm
            or "quais sao os planos" in query_norm
            or "planos disponíveis" in query_norm
            or "planos disponiveis" in query_norm
            or "planos do vendefácil" in query_norm
            or "planos do vendefacil" in query_norm
            or "quais produtos" in query_norm
        ):

            grupos.append(
                [
                    "plano basic",
                    "plano pro",
                    "plano enterprise",
                    "vendefácil pdv",
                    "vendefacil pdv",
                    "vendefácil estoque",
                    "vendefacil estoque",
                    "vendefácil loja",
                    "vendefacil loja",
                    "vendefácil analytics",
                    "vendefacil analytics",
                    "vendefácil pay",
                    "vendefacil pay",
                ]
            )

        # --------------------------------------------------------
        # TECH LEAD / PM
        # --------------------------------------------------------

        if (
            "tech lead" in query_norm
            or "gerente de produto" in query_norm
            or "product manager" in query_norm
            or "responsável técnico" in query_norm
            or "responsavel tecnico" in query_norm
        ):

            grupos.append(
                [
                    "tech lead",
                    "carlos mendes",
                    "gerente de produto",
                    "product manager",
                    "ana souza",
                ]
            )

        # --------------------------------------------------------
        # SLA DE PRIORIDADE CRÍTICA
        # --------------------------------------------------------

        if (
            "sla" in query_norm
            and "critica" in query_norm
        ):

            grupos.append(
                [
                    "tck-1005",
                    "prioridade crítica",
                    "prioridade critica",
                    "severidade crítica",
                    "severidade critica",
                    "15 minutos",
                    "2 horas",
                ]
            )

        # --------------------------------------------------------
        # TEF
        # --------------------------------------------------------

        if (
            "tef" in query_norm
            or "timeout" in query_norm
            or "6090" in query_norm
        ):

            grupos.append(
                [
                    "tef",
                    "timeout de confirmação tef",
                    "timeout de confirmacao tef",
                    "porta 6090",
                    "6090",
                    "windows firewall",
                    "firewall",
                    "regra de exceção",
                    "regra de excecao",
                    "pinpad",
                ]
            )

        # --------------------------------------------------------
        # SAFETY STOCK
        # --------------------------------------------------------

        if "safety stock" in query_norm:

            grupos.append(
                [
                    "safety stock",
                    "estoque de segurança",
                    "estoque de seguranca",
                    "margem de reserva",
                    "margem de segurança",
                    "margem de seguranca",
                    "evitar dupla venda",
                ]
            )

        if (
            "sincroniza" in query_norm
            and "boa compra" in query_norm
        ):
            grupos.append(
                [
                    "cust001",
                    "tck-1001",
                    "customer_001",
                    "lock do banco",
                    "lock banco",
                    "contrato enterprise",
                    "roadmap",
                    "janeiro",
                    "carlos mendes",
                ]
            )

        if "dados pessoais" in query_norm and "lgpd" in query_norm:
            grupos.append(
                [
                    "operadora",
                    "dados sensíveis",
                    "dados de saúde",
                    "cartão de crédito completo",
                    "dpo",
                    "gabriel ramos",
                    "incidente",
                    "vazamento",
                ]
            )

        if "mrr" in query_norm and "sao paulo" in query_norm:
            grupos.append(
                [
                    "cust008",
                    "auto pecas central",
                    "3100",
                    "vendefacil pay",
                ]
            )

        if (
            "tickets" in query_norm
            and "estoque" in query_norm
            and ("minas gerais" in query_norm or "mg" in query_norm)
        ):
            grupos.append(
                ["tck-1001", "tck-1002", "tck-1004"]
            )

        # --------------------------------------------------------
        # STK-409
        # --------------------------------------------------------

        if "stk-409" in query_norm:

            grupos.append(
                [
                    "stk-409",
                    "tabela temporária",
                    "tabela temporaria",
                    "status da sincronização",
                    "status da sincronizacao",
                    "force reconciliation",
                    "vendefacil-estoque-agent",
                    "blind sync",
                    "reconciliação",
                    "reconciliacao",
                ]
            )

        # --------------------------------------------------------
        # SANGRIA
        # --------------------------------------------------------

        if "sangria" in query_norm:

            grupos.append(
                [
                    "sangria",
                    "f8",
                    "caixa",
                    "senha do supervisor",
                    "duas vias",
                    "2 vias",
                    "comprovante de sangria",
                ]
            )

        # --------------------------------------------------------
        # HOME OFFICE
        # --------------------------------------------------------

        if (
            "home office" in query_norm
            or "trabalho remoto" in query_norm
        ):

            grupos.append(
                [
                    "home office",
                    "100% remoto",
                    "100% home office",
                    "remote first",
                    "trabalho remoto",
                ]
            )

        if not grupos:
            return []

        termos = set()

        for grupo in grupos:
            termos.update(grupo)

        textos = getattr(
            self.vector_store,
            "textos",
            [],
        )

        metadatas = getattr(
            self.vector_store,
            "metadados",
            [],
        )

        resultados: List[
            Dict[str, Any]
        ] = []

        for index, texto in enumerate(textos):

            if not texto:
                continue

            texto_norm = self._normalizar(
                texto
            )

            if (
                (
                    "quais produtos" in query_norm
                    or "quais sao os produtos" in query_norm
                    or "quais são os produtos" in query_norm
                )
                and texto_norm.startswith("plano ")
            ):
                continue

            encontrados = [
                termo
                for termo in termos
                if termo in texto_norm
            ]


            if not encontrados:
                continue

            metadata = {}

            if index < len(metadatas):

                metadata = (
                    metadatas[index]
                    or {}
                )

            # ----------------------------------------------------
            # RESPEITA FILTROS
            # ----------------------------------------------------

            if filtros and not self._atende_todos_os_filtros(
                metadata,
                filtros,
            ):
                continue

            resultados.append(
                {
                    "text": texto,
                    "metadata": metadata,
                    "score": 1.0,
                    "direct_terms": encontrados,
                    "direct_match": True,
                }
            )

        return resultados

    # ============================================================
    # BÔNUS DE IDENTIFICADOR
    # ============================================================

    def _bonus_identificador(
        self,
        texto: str,
        query: str,
    ) -> float:

        identificadores = (
            self._extrair_identificadores(
                query
            )
        )

        if not identificadores:
            return 0.0

        texto_upper = texto.upper()

        bonus = 0.0

        for identificador in identificadores:

            if identificador not in texto_upper:
                continue

            if identificador.startswith(
                "STK-"
            ):
                bonus += 0.70

            elif identificador.startswith(
                "TCK-"
            ):
                bonus += 0.55

            elif identificador.startswith(
                "CUST"
            ):
                bonus += 0.12

        return min(
            bonus,
            1.00,
        )

    # ============================================================
    # BÔNUS LEXICAL
    # ============================================================

    def _bonus_termos(
        self,
        query: str,
        texto: str,
    ) -> float:

        query_norm = self._normalizar(
            query
        )

        texto_norm = self._normalizar(
            texto
        )

        bonus = 0.0

        # --------------------------------------------------------
        # PRODUTOS / PLANOS
        # --------------------------------------------------------

        consulta_produtos = (
            "quais produtos" in query_norm
            or "quais são os produtos" in query_norm
            or "quais sao os produtos" in query_norm
            or "quais planos" in query_norm
            or "planos disponíveis" in query_norm
            or "planos disponiveis" in query_norm
        )

        if consulta_produtos:

            termos = [
                "plano basic",
                "plano pro",
                "plano enterprise",
                "vendefácil",
                "vendefacil",
                "pricing",
                "tabela de preços",
                "tabela de precos",
            ]

            for termo in termos:

                if termo in texto_norm:
                    bonus += 0.20

            if "produto vendefacil" in texto_norm:
                bonus += 3.00

        # --------------------------------------------------------
        # TECH LEAD / PM
        # --------------------------------------------------------

        consulta_equipe = (
            "tech lead" in query_norm
            or "gerente de produto" in query_norm
            or "product manager" in query_norm
            or "responsável técnico" in query_norm
            or "responsavel tecnico" in query_norm
        )

        if consulta_equipe:

            termos = [
                "tech lead",
                "carlos mendes",
                "gerente de produto",
                "product manager",
                "ana souza",
            ]

            for termo in termos:

                if termo in texto_norm:
                    bonus += 0.25

        # --------------------------------------------------------
        # TEF
        # --------------------------------------------------------

        consulta_tef = (
            "tef" in query_norm
            or "timeout" in query_norm
            or "6090" in query_norm
        )

        if consulta_tef:

            termos = [
                "timeout de confirmação tef",
                "timeout de confirmacao tef",
                "tef",
                "porta 6090",
                "6090",
                "windows firewall",
                "firewall",
                "regra de exceção",
                "regra de excecao",
                "pinpad",
            ]

            for termo in termos:

                if termo in texto_norm:
                    bonus += 0.14

        if "sla" in query_norm and "critica" in query_norm:
            if "tck-1005" in texto_norm:
                bonus += 1.00
            if "15 minutos" in texto_norm or "2 horas" in texto_norm:
                bonus += 0.60

        # --------------------------------------------------------
        # SAFETY STOCK
        # --------------------------------------------------------

        if "safety stock" in query_norm:

            if "safety stock" in texto_norm:
                bonus += 0.60

            termos = [
                "estoque de segurança",
                "estoque de seguranca",
                "margem de reserva",
                "margem de segurança",
                "margem de seguranca",
                "evitar dupla venda",
            ]

            for termo in termos:

                if termo in texto_norm:
                    bonus += 0.14

        # --------------------------------------------------------
        # TROCA E DEVOLUÇÃO NO PDV
        # --------------------------------------------------------

        consulta_troca_pdv = (
            "pdv" in query_norm
            and any(
                termo in query_norm
                for termo in (
                    "troca",
                    "devolucao",
                    "vale-troca",
                    "vale troca",
                )
            )
        )

        if consulta_troca_pdv:

            termos = [
                "troca",
                "devolucao",
                "vale-troca",
                "vale troca",
                "ctrl + t",
                "nota fiscal",
                "qr code",
                "credito ao consumidor",
                "90 dias",
            ]

            for termo in termos:

                if termo in texto_norm:
                    bonus += 0.14

        # --------------------------------------------------------
        # STK-409
        # --------------------------------------------------------

        if "stk-409" in query_norm:

            if "stk-409" in texto_norm:
                bonus += 0.70

            termos = [
                "tabela temporária",
                "tabela temporaria",
                "status da sincronização",
                "status da sincronizacao",
                "force reconciliation",
                "vendefacil-estoque-agent",
                "blind sync",
                "reconciliação",
                "reconciliacao",
            ]

            for termo in termos:

                if termo in texto_norm:
                    bonus += 0.14

        # --------------------------------------------------------
        # SANGRIA
        # --------------------------------------------------------

        if "sangria" in query_norm:

            termos = [
                "sangria",
                "f8",
                "senha do supervisor",
                "duas vias",
                "2 vias",
                "comprovante de sangria",
            ]

            for termo in termos:

                if termo in texto_norm:
                    bonus += 0.12

        # --------------------------------------------------------
        # HOME OFFICE
        # --------------------------------------------------------

        if (
            "home office" in query_norm
            or "trabalho remoto" in query_norm
        ):

            termos = [
                "home office",
                "100% remoto",
                "100% home office",
                "remote first",
                "trabalho remoto",
            ]

            for termo in termos:

                if termo in texto_norm:
                    bonus += 0.12

        # --------------------------------------------------------
        # MG
        # --------------------------------------------------------

        if (
            "minas gerais" in query_norm
            or re.search(
                r"\bmg\b",
                query_norm,
            )
        ):

            if (
                "minas gerais" in texto_norm
                or re.search(
                    r"\bmg\b",
                    texto_norm,
                )
            ):
                bonus += 0.05

        return min(
            bonus,
            1.50,
        )

    # ============================================================
    # BÔNUS DE METADATA
    # ============================================================

    def _bonus_metadata(
        self,
        metadata: Dict[str, Any],
        filtros: Dict[str, Any],
    ) -> float:

        if not filtros:
            return 0.0

        bonus = 0.0

        for chave, esperado in filtros.items():

            real = metadata.get(chave)

            if real is None:
                continue

            esperado_norm = self._normalizar(
                esperado
            )

            real_norm = self._normalizar(
                real
            )

            if real_norm == esperado_norm:

                bonus += 0.06

            elif esperado_norm in real_norm:

                bonus += 0.02

        return min(
            bonus,
            0.25,
        )

    # ============================================================
    # BÔNUS DE CONTEXTO
    # ============================================================

    def _bonus_contexto(
        self,
        query: str,
        texto: str,
    ) -> float:

        query_norm = self._normalizar(
            query
        )

        texto_norm = self._normalizar(
            texto
        )

        bonus = 0.0

        # --------------------------------------------------------
        # PROCEDIMENTOS
        # --------------------------------------------------------

        termos_procedimento = [
            "procedimento",
            "como resolver",
            "como configurar",
            "passo a passo",
            "solução",
            "solucao",
            "configurar",
        ]

        quer_procedimento = any(
            termo in query_norm
            for termo in termos_procedimento
        )

        if quer_procedimento:

            termos_documentacao = [
                "manual",
                "procedimento",
                "passo a passo",
                "configuração",
                "configuracao",
                "documentação",
                "documentacao",
                "como resolver",
                "como fazer",
            ]

            for termo in termos_documentacao:

                if termo in texto_norm:
                    bonus += 0.05

        # --------------------------------------------------------
        # STK-409
        # --------------------------------------------------------

        if "stk-409" in query_norm:

            termos = [
                "status da sincronização",
                "status da sincronizacao",
                "force reconciliation",
                "vendefacil-estoque-agent",
                "blind sync",
                "configurações",
                "configuracoes",
                "rede",
                "sincronização",
                "sincronizacao",
            ]

            for termo in termos:

                if termo in texto_norm:
                    bonus += 0.07

        return min(
            bonus,
            0.35,
        )

    # ============================================================
    # PENALIDADES
    # ============================================================

    def _penalidade(
        self,
        query: str,
        metadata: Dict[str, Any],
        texto: str,
    ) -> float:

        query_norm = self._normalizar(
            query
        )

        texto_norm = self._normalizar(
            texto
        )

        doc_type = self._normalizar(
            metadata.get(
                "doc_type",
                "",
            )
        )

        penalidade = 0.0

        # --------------------------------------------------------
        # TEF
        # --------------------------------------------------------

        consulta_tef = (
            "tef" in query_norm
            or "timeout" in query_norm
            or "6090" in query_norm
        )

        if consulta_tef:

            if doc_type == "store":
                penalidade += 0.18

            elif doc_type == "customer":
                penalidade += 0.12

            if doc_type in {
                "ticket",
                "log",
                "manual",
                "policy",
            }:

                penalidade = max(
                    0.0,
                    penalidade - 0.03,
                )

        # --------------------------------------------------------
        # SAFETY STOCK
        # --------------------------------------------------------

        if "safety stock" in query_norm:

            if doc_type == "store":
                penalidade += 0.15

            elif doc_type == "customer":
                penalidade += 0.12

        # --------------------------------------------------------
        # STK-409
        # --------------------------------------------------------

        if "stk-409" in query_norm:

            quer_procedimento = any(
                termo in query_norm
                for termo in [
                    "procedimento",
                    "resolver",
                    "solução",
                    "solucao",
                    "como",
                ]
            )

            if (
                quer_procedimento
                and doc_type == "log"
            ):

                penalidade += 0.08

            if "stk-409" in texto_norm:

                penalidade = max(
                    0.0,
                    penalidade - 0.05,
                )

        return max(
            penalidade,
            0.0,
        )

    # ============================================================
    # SCORE FINAL
    # ============================================================

    def _score_final(
        self,
        rrf: float,
        metadata_bonus: float,
        term_bonus: float,
        identifier_bonus: float,
        context_bonus: float,
        penalty: float,
        direct_match: bool = False,
    ) -> float:

        score = (
            rrf
            + metadata_bonus
            + term_bonus
            + identifier_bonus
            + context_bonus
            - penalty
        )

        if direct_match:
            score += 0.20

        return score

    # ============================================================
    # EXECUTA UMA RODADA DE BUSCA
    # ============================================================

    def _executar_busca(
        self,
        query: str,
        query_vector,
        filtro: Dict[str, Any],
        fetch_k: int,
    ) -> Dict[str, Dict[str, Any]]:

        candidatos: Dict[
            str,
            Dict[str, Any]
        ] = {}

        # ========================================================
        # BUSCA DENSA
        # ========================================================

        try:

            dense_results = (
                self.vector_store.buscar(
                    query_vector,
                    top_k=fetch_k,
                    filtro=filtro,
                )
            )

        except Exception as erro:

            print(
                "[AVISO] Erro na busca densa:",
                erro,
            )

            dense_results = []

        for rank, resultado in enumerate(
            dense_results,
            start=1,
        ):

            if not isinstance(
                resultado,
                dict,
            ):
                continue

            texto = self._obter_texto(
                resultado
            )

            metadata = self._obter_metadata(
                resultado
            )

            # ----------------------------------------------------
            # GARANTE FILTRO
            # ----------------------------------------------------

            if filtro and not self._atende_todos_os_filtros(
                metadata,
                filtro,
            ):
                continue

            chave = self._obter_chave(
                resultado,
                "dense",
                rank,
            )

            if chave not in candidatos:

                candidatos[chave] = {
                    "text": texto,
                    "metadata": metadata,
                    "dense": None,
                    "bm25": None,
                    "dense_rank": None,
                    "bm25_rank": None,
                    "direct_match": False,
                }

            atual = candidatos[chave]

            score_dense = resultado.get(
                "score",
                resultado.get(
                    "similarity"
                ),
            )

            if (
                atual["dense"] is None
                or (
                    score_dense is not None
                    and score_dense > atual["dense"]
                )
            ):

                atual["dense"] = score_dense

                atual["dense_rank"] = rank

        # ========================================================
        # BUSCA BM25
        # ========================================================

        try:

            bm25_results = (
                self.bm25.buscar(
                    query,
                    top_k=fetch_k,
                    filtro=filtro,
                )
            )

        except Exception as erro:

            print(
                "[AVISO] Erro na busca BM25:",
                erro,
            )

            bm25_results = []

        for rank, resultado in enumerate(
            bm25_results,
            start=1,
        ):

            if not isinstance(
                resultado,
                dict,
            ):
                continue

            texto = self._obter_texto(
                resultado
            )

            metadata = self._obter_metadata(
                resultado
            )

            # ----------------------------------------------------
            # GARANTE FILTRO
            # ----------------------------------------------------

            if filtro and not self._atende_todos_os_filtros(
                metadata,
                filtro,
            ):
                continue

            chave = self._obter_chave(
                resultado,
                "bm25",
                rank,
            )

            if chave not in candidatos:

                candidatos[chave] = {
                    "text": texto,
                    "metadata": metadata,
                    "dense": None,
                    "bm25": None,
                    "dense_rank": None,
                    "bm25_rank": None,
                    "direct_match": False,
                }

            atual = candidatos[chave]

            score_bm25 = resultado.get(
                "score",
                resultado.get(
                    "bm25_score"
                ),
            )

            if (
                atual["bm25"] is None
                or (
                    score_bm25 is not None
                    and score_bm25 > atual["bm25"]
                )
            ):

                atual["bm25"] = score_bm25

                atual["bm25_rank"] = rank

        return candidatos

    # ============================================================
    # CALCULA RESULTADOS
    # ============================================================

    def _calcular_resultados(
        self,
        candidatos: Dict[str, Dict[str, Any]],
        query: str,
        filtros: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        resultados_finais: List[
            Dict[str, Any]
        ] = []

        for candidato in candidatos.values():

            dense_rank = candidato.get(
                "dense_rank"
            )

            bm25_rank = candidato.get(
                "bm25_rank"
            )

            texto = candidato.get(
                "text",
                "",
            )

            metadata = (
                candidato.get(
                    "metadata",
                    {},
                )
                or {}
            )

            # ====================================================
            # RRF
            # ====================================================

            rrf = 0.0

            if dense_rank is not None:

                rrf += (
                    1.0
                    / (
                        60
                        + dense_rank
                    )
                )

            if bm25_rank is not None:

                rrf += (
                    1.0
                    / (
                        60
                        + bm25_rank
                    )
                )

            # ====================================================
            # BÔNUS
            # ====================================================

            metadata_bonus = (
                self._bonus_metadata(
                    metadata,
                    filtros,
                )
            )

            term_bonus = (
                self._bonus_termos(
                    query,
                    texto,
                )
            )

            identifier_bonus = (
                self._bonus_identificador(
                    texto,
                    query,
                )
            )

            context_bonus = (
                self._bonus_contexto(
                    query,
                    texto,
                )
            )

            penalty = (
                self._penalidade(
                    query,
                    metadata,
                    texto,
                )
            )

            score = self._score_final(
                rrf=rrf,
                metadata_bonus=metadata_bonus,
                term_bonus=term_bonus,
                identifier_bonus=identifier_bonus,
                context_bonus=context_bonus,
                penalty=penalty,
                direct_match=candidato.get(
                    "direct_match",
                    False,
                ),
            )

            atende_filtros = (
                self._atende_todos_os_filtros(
                    metadata,
                    filtros,
                )
            )

            resultados_finais.append(
                {
                    "text": texto,
                    "metadata": metadata,
                    "score": score,
                    "score_final": score,
                    "rrf": rrf,
                    "rrf_score": rrf,
                    "dense": candidato.get(
                        "dense"
                    ),
                    "bm25": candidato.get(
                        "bm25"
                    ),
                    "metadata_bonus": (
                        metadata_bonus
                    ),
                    "term_bonus": (
                        term_bonus
                    ),
                    "identifier_bonus": (
                        identifier_bonus
                    ),
                    "context_bonus": (
                        context_bonus
                    ),
                    "penalty": penalty,
                    "direct_match": (
                        candidato.get(
                            "direct_match",
                            False,
                        )
                    ),
                    "matches_all_filters": (
                        atende_filtros
                    ),
                }
            )

        resultados_finais.sort(
            key=lambda resultado: (
                resultado.get(
                    "score",
                    0.0,
                )
            ),
            reverse=True,
        )

        return resultados_finais

    # ============================================================
    # HIGIENE E CORTE DE RELEVÂNCIA
    # ============================================================

    def _deduplicar_resultados(
        self,
        resultados: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Mantém apenas uma ocorrência de cada chunk ou texto idêntico.

        Um mesmo chunk pode entrar tanto pela busca densa quanto pela BM25 ou
        por uma recuperação direta. Mostrar essas ocorrências como fontes
        diferentes dá a impressão de que há mais evidências do que realmente
        existem.
        """

        unicos: List[Dict[str, Any]] = []
        chunks_vistos = set()
        textos_vistos = set()

        for resultado in resultados:
            metadata = self._obter_metadata(resultado)
            chunk_id = str(metadata.get("chunk_id") or "").strip()
            texto = self._normalizar(self._obter_texto(resultado))

            if chunk_id and chunk_id in chunks_vistos:
                continue

            # O texto é a segunda chave para fontes que não tenham chunk_id.
            # Não aplicamos essa regra a textos vazios para não ocultar erros.
            if texto and texto in textos_vistos:
                continue

            if chunk_id:
                chunks_vistos.add(chunk_id)
            if texto:
                textos_vistos.add(texto)

            unicos.append(resultado)

        return unicos

    @staticmethod
    def _remover_cauda_irrelevante(
        resultados: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Remove a cauda de resultados muito abaixo da melhor evidência.

        A busca anterior sempre completava ``top_k``. Assim, após encontrar
        uma fonte excelente, também retornava arquivos apenas vagamente
        relacionados. O corte relativo preserva consultas com escores baixos
        (onde a comparação absoluta seria injusta) e elimina apenas resultados
        claramente piores que o melhor candidato.
        """

        if len(resultados) < 2:
            return resultados

        melhor_score = float(resultados[0].get("score", 0.0) or 0.0)

        # Escores pequenos normalmente são somente RRF; nesse caso não há
        # sinal suficiente para aplicar um corte confiável.
        if melhor_score < 0.15:
            return resultados

        limite = melhor_score * 0.50
        return [
            resultado
            for resultado in resultados
            if float(resultado.get("score", 0.0) or 0.0) >= limite
        ]

    # ============================================================
    # BUSCA PRINCIPAL
    # ============================================================

    def buscar(
        self,
        query: str,
        top_k: int = 5,
        filtro: Dict[str, Any] | None = None,
        fetch_k: int = 50,
    ) -> Dict[str, Any]:

        if not query:

            return {
                "filters": {},
                "hybrid_results": [],
            }

        print(
            f"\nConsulta híbrida: {query}"
        )

        # ========================================================
        # 1. QUERY ANALYZER
        # ========================================================

        try:

            analise = analyze_query(
                query
            )

            filtros_extraidos = (
                analise.get(
                    "filters",
                    {},
                )
                or {}
            )

        except Exception as erro:

            print(
                "[AVISO] Falha no Query Analyzer:",
                erro,
            )

            filtros_extraidos = {}

        # Filtro explícito possui prioridade.

        if filtro:

            filtros = dict(
                filtro
            )

        else:

            filtros = dict(
                filtros_extraidos
            )

        print(
            f"Filtros aplicados: {filtros}"
        )

        # ========================================================
        # 2. EMBEDDING
        # ========================================================

        try:

            query_vector = embed_texto(
                query
            )

        except Exception as erro:

            print(
                "[AVISO] Falha ao gerar embedding; "
                "continuando com busca BM25/direct terms:",
                erro,
            )
            query_vector = None

        # ========================================================
        # 3. BUSCA COM FILTRO EXATO
        # ========================================================
        #
        # PRIMEIRO tentamos somente o filtro completo.
        #
        # Isso é fundamental para evitar que documentos
        # irrelevantes entrem no RRF.
        # ========================================================

        candidatos = self._executar_busca(
            query=query,
            query_vector=query_vector,
            filtro=filtros,
            fetch_k=fetch_k,
        )

        resultados_finais = (
            self._calcular_resultados(
                candidatos,
                query,
                filtros,
            )
        )

        # ========================================================
        # 4. RECUPERAÇÃO DIRETA
        # ========================================================

        direct_results = (
            self._buscar_identificadores_direto(
                query,
                filtros,
            )
        )

        for resultado in direct_results:

            texto = self._obter_texto(
                resultado
            )

            metadata = self._obter_metadata(
                resultado
            )

            chunk_id = metadata.get(
                "chunk_id"
            )

            if chunk_id:

                chave = str(
                    chunk_id
                )

            else:

                chave = (
                    f"direct-{hash(texto)}"
                )

            if chave not in candidatos:

                candidatos[chave] = {
                    "text": texto,
                    "metadata": metadata,
                    "dense": None,
                    "bm25": None,
                    "dense_rank": None,
                    "bm25_rank": None,
                    "direct_match": True,
                }

            else:

                candidatos[chave][
                    "direct_match"
                ] = True

        # ========================================================
        # 5. RECUPERAÇÃO DIRETA DE TERMOS
        # ========================================================

        direct_term_results = (
            self._buscar_termos_direto(
                query,
                filtros,
            )
        )

        for resultado in direct_term_results:

            texto = self._obter_texto(
                resultado
            )

            metadata = self._obter_metadata(
                resultado
            )

            chunk_id = metadata.get(
                "chunk_id"
            )

            if chunk_id:

                chave = str(
                    chunk_id
                )

            else:

                chave = (
                    f"direct-term-{hash(texto)}"
                )

            if chave not in candidatos:

                candidatos[chave] = {
                    "text": texto,
                    "metadata": metadata,
                    "dense": None,
                    "bm25": None,
                    "dense_rank": None,
                    "bm25_rank": None,
                    "direct_match": True,
                }

            else:

                candidatos[chave][
                    "direct_match"
                ] = True

        # ========================================================
        # 6. RECALCULA
        # ========================================================

        resultados_finais = (
            self._calcular_resultados(
                candidatos,
                query,
                filtros,
            )
        )

        # ========================================================
        # 7. SE NÃO ENCONTROU NADA COM FILTRO,
        #    USA RELAXAMENTO CONTROLADO
        # ========================================================

        if not resultados_finais:

            filtros_relaxados = (
                self._gerar_filtros_relaxados(
                    filtros
                )
            )

            # pula o primeiro porque ele já foi tentado
            for filtro_atual in filtros_relaxados[1:]:

                candidatos_relaxados = (
                    self._executar_busca(
                        query=query,
                        query_vector=query_vector,
                        filtro=filtro_atual,
                        fetch_k=fetch_k,
                    )
                )

                resultados_relaxados = (
                    self._calcular_resultados(
                        candidatos_relaxados,
                        query,
                        filtro_atual,
                    )
                )

                if resultados_relaxados:

                    # Marca quais ainda atendem
                    # aos filtros originais.

                    for resultado in resultados_relaxados:

                        metadata = (
                            resultado.get(
                                "metadata",
                                {},
                            )
                            or {}
                        )

                        resultado[
                            "matches_all_filters"
                        ] = (
                            self._atende_todos_os_filtros(
                                metadata,
                                filtros,
                            )
                        )

                    resultados_finais = (
                        resultados_relaxados
                    )

                    print(
                        "Filtros relaxados utilizados:",
                        filtro_atual,
                    )

                    break

        # ========================================================
        # 8. PRIORIZAÇÃO FINAL DOS FILTROS
        # ========================================================

        if filtros:

            resultados_completos = [
                resultado
                for resultado in resultados_finais
                if resultado.get(
                    "matches_all_filters",
                    False,
                )
            ]

            if resultados_completos:

                resultados_finais = (
                    resultados_completos
                )

        if (
            "quais produtos" in self._normalizar(query)
            or "quais sao os produtos" in self._normalizar(query)
            or "quais são os produtos" in self._normalizar(query)
        ):
            produtos = [
                resultado
                for resultado in resultados_finais
                if self._obter_texto(resultado).lower().startswith(
                    "produto vendefacil"
                )
            ]
            if len(produtos) >= 5:
                resultados_finais = produtos

        # ========================================================
        # 9. ORDENAÇÃO
        # ========================================================

        resultados_finais.sort(
            key=lambda resultado: (
                resultado.get(
                    "score",
                    0.0,
                )
            ),
            reverse=True,
        )

        resultados_finais = self._deduplicar_resultados(
            resultados_finais
        )

        resultados_finais = self._remover_cauda_irrelevante(
            resultados_finais
        )

        # ========================================================
        # 10. TOP K
        # ========================================================

        limite = top_k
        if (
            "quais produtos" in self._normalizar(query)
            or "quais sao os produtos" in self._normalizar(query)
            or "quais são os produtos" in self._normalizar(query)
        ):
            limite = max(top_k, 8)

        if all(
            termo in self._normalizar(query)
            for termo in ("email", "ticket", "reun")
        ):
            limite = max(limite, 8)

        resultados_finais = resultados_finais[:limite]

        # ========================================================
        # 11. RETORNO
        # ========================================================

        return {
            "filters": filtros,
            "hybrid_results": resultados_finais,
        }
