from __future__ import annotations

import re
import unicodedata


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalize(text: str) -> str:
    """
    Normaliza o texto para facilitar a comparação.

    - Converte para minúsculas
    - Remove acentos
    - Remove espaços duplicados
    - Remove espaços no início e no final
    """

    text = str(text).lower().strip()

    text = unicodedata.normalize("NFD", text)

    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Mn"
    )

    text = re.sub(r"\s+", " ", text)

    return text


# ============================================================
# VALORES VÁLIDOS ENCONTRADOS NO ÍNDICE
# ============================================================

VALID_DOC_TYPES = {
    "ata",
    "customer",
    "email",
    "employee",
    "log",
    "manual",
    "policy",
    "product",
    "sale",
    "store",
    "ticket",
}


VALID_STATES = {
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MG",
    "PE",
    "PR",
    "RJ",
    "RS",
    "SC",
    "SP",
}


VALID_MODULES = {
    "estoque",
    "pay",
    "pdv",
    "analytics",
    "ecommerce",
    "loja",
}


VALID_PRIORITIES = {
    "Alta": "alta",
    "Baixa": "baixa",
    "Crítica": "critica",
    "Média": "media",
}


VALID_STATUSES = {
    "Aberto": "aberto",
    "Ativo": "ativo",
    "Cancelado": "cancelado",
    "Em Andamento": "em andamento",
    "Inativo": "inativo",
    "Resolvido": "resolvido",
}


# ============================================================
# SINÔNIMOS DE TIPOS DE DOCUMENTO
# ============================================================

DOC_TYPE_SYNONYMS = {

    "ticket": [
        "ticket",
        "tickets",
        "chamado",
        "chamados",
    ],

    "customer": [
        "customer",
        "customers",
        "cliente",
        "clientes",
    ],

    "employee": [
        "employee",
        "employees",
        "funcionario",
        "funcionarios",
        "colaborador",
        "colaboradores",
    ],

    "product": [
        "product",
        "products",
        "produto",
        "produtos",
    ],

    "store": [
        "store",
        "stores",
        "loja",
        "lojas",
    ],

    "sale": [
        "sale",
        "sales",
        "venda",
        "vendas",
    ],

    "log": [
        "log",
        "logs",
    ],

    "manual": [
        "manual",
        "manuais",
    ],

    "policy": [
        "policy",
        "policies",
        "politica",
        "politicas",
    ],

    "email": [
        "email",
        "emails",
        "e-mail",
        "e-mails",
    ],

    "ata": [
        "ata",
        "atas",
    ],
}


# ============================================================
# SINÔNIMOS DE ESTADO
# ============================================================

STATE_SYNONYMS = {

    "bahia": "BA",

    "ceara": "CE",

    "distrito federal": "DF",

    "espirito santo": "ES",

    "goias": "GO",

    "minas gerais": "MG",

    "pernambuco": "PE",

    "parana": "PR",

    "rio de janeiro": "RJ",

    "rio grande do sul": "RS",

    "santa catarina": "SC",

    "sao paulo": "SP",
}


# ============================================================
# SINÔNIMOS DE MÓDULO
# ============================================================

MODULE_SYNONYMS = {

    "estoque": "estoque",
    "estoques": "estoque",

    "vende facil estoque": "estoque",

    "pay": "pay",
    "pagamento": "pay",
    "pagamentos": "pay",

    "vende facil pay": "pay",

    "pdv": "pdv",

    "ponto de venda": "pdv",

    "pontos de venda": "pdv",

    "vende facil pdv": "pdv",

    "analytics": "analytics",

    "analise": "analytics",

    "analises": "analytics",

    "vende facil analytics": "analytics",

    "ecommerce": "ecommerce",

    "e commerce": "ecommerce",

    "loja": "loja",

    "lojas": "loja",

    "vende facil loja": "loja",
}


# ============================================================
# QUERY ANALYZER
# ============================================================

def analyze_query(query: str) -> dict:

    normalized_query = normalize(query)

    filters = {}

    # ========================================================
    # 1. TIPO DE DOCUMENTO
    # ========================================================

    for doc_type, synonyms in DOC_TYPE_SYNONYMS.items():

        for synonym in synonyms:

            if re.search(
                rf"\b{re.escape(synonym)}\b",
                normalized_query
            ):

                # Garante que o valor extraído
                # existe no índice.
                if doc_type in VALID_DOC_TYPES:

                    filters["doc_type"] = doc_type

                break

        if "doc_type" in filters:
            break

    # ========================================================
    # 2. ESTADO
    # ========================================================

    # Primeiro procura nomes completos.
    # Exemplo:
    # "Minas Gerais" -> "MG"

    for state_name, state_code in STATE_SYNONYMS.items():

        if state_name in normalized_query:

            if state_code in VALID_STATES:

                filters["state"] = state_code

            break

    # Caso não tenha encontrado o nome,
    # procura diretamente pela sigla.

    if "state" not in filters:

        for state_code in VALID_STATES:

            if re.search(
                rf"\b{state_code.lower()}\b",
                normalized_query
            ):

                filters["state"] = state_code

                break

    # ========================================================
    # 3. MÓDULO
    # ========================================================

    # Ordenamos pelo tamanho para testar primeiro
    # expressões maiores.
    #
    # Exemplo:
    # "vende facil estoque"
    # antes de simplesmente "estoque".

    module_names = sorted(
        MODULE_SYNONYMS.keys(),
        key=len,
        reverse=True
    )

    for module_name in module_names:

        if re.search(
            rf"\b{re.escape(module_name)}\b",
            normalized_query
        ):

            module = MODULE_SYNONYMS[
                module_name
            ]

            # Valida contra os valores permitidos.
            if module in VALID_MODULES:

                filters["module"] = module

            break

    # ========================================================
    # 4. PRIORIDADE
    # ========================================================

    for priority, normalized_priority in VALID_PRIORITIES.items():

        normalized_priority = normalize(
            normalized_priority
        )

        if re.search(
            rf"\b{re.escape(normalized_priority)}\b",
            normalized_query
        ):

            # Recupera a capitalização usada
            # no índice.
            filters["priority"] = priority

            break

    # ========================================================
    # 5. STATUS
    # ========================================================

    status_items = sorted(
        VALID_STATUSES.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for status, normalized_status in status_items:

        normalized_status = normalize(
            normalized_status
        )

        if re.search(
            rf"\b{re.escape(normalized_status)}\b",
            normalized_query
        ):

            filters["status"] = status

            break

    # ========================================================
    # RESULTADO
    # ========================================================

    return {
        "original_query": query,
        "normalized_query": normalized_query,
        "filters": filters,
    }


# ============================================================
# TESTES
# ============================================================

if __name__ == "__main__":

    perguntas = [

        # Teste principal do desafio
        "Quais tickets de clientes de Minas Gerais estão relacionados ao módulo de estoque?",

        # Estado por sigla
        "Quais clientes estão localizados em MG?",

        # Status
        "Quais tickets de clientes de São Paulo estão abertos?",

        # Prioridade + módulo
        "Quais tickets de prioridade alta estão relacionados ao VendeFácil Pay?",

        # Venda
        "Quais vendas foram realizadas em Minas Gerais?",

        # Produto
        "Quais produtos estão relacionados ao PDV?",
    ]

    for pergunta in perguntas:

        resultado = analyze_query(
            pergunta
        )

        print("\n" + "=" * 70)

        print("PERGUNTA:")
        print(pergunta)

        print("\nPERGUNTA NORMALIZADA:")
        print(
            resultado["normalized_query"]
        )

        print("\nFILTROS EXTRAÍDOS:")

        print(
            resultado["filters"]
        )