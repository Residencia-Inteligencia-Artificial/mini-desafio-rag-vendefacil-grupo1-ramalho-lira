from __future__ import annotations

import re
import unicodedata


VALID_DOC_TYPES = {
    "customer",
    "employee",
    "product",
    "store",
    "sale",
    "ticket",
    "log",
    "manual",
    "policy",
    "email",
    "ata",
}

VALID_STATES = {
    "BA", "CE", "DF", "ES", "GO", "MG",
    "PE", "PR", "RJ", "RS", "SC", "SP"
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
    "alta": "alta",
    "baixa": "baixa",
    "critica": "critica",
    "média": "media",
    "media": "media",
}

VALID_STATUSES = {
    "aberto": "aberto",
    "ativo": "ativo",
    "cancelado": "cancelado",
    "em andamento": "em andamento",
    "inativo": "inativo",
    "resolvido": "resolvido",
}


STATE_NAMES = {
    "bahia": "BA",
    "ceara": "CE",
    "ceará": "CE",
    "distrito federal": "DF",
    "espirito santo": "ES",
    "espírito santo": "ES",
    "goias": "GO",
    "goiás": "GO",
    "minas gerais": "MG",
    "pernambuco": "PE",
    "parana": "PR",
    "paraná": "PR",
    "rio de janeiro": "RJ",
    "rio grande do sul": "RS",
    "santa catarina": "SC",
    "sao paulo": "SP",
    "são paulo": "SP",
}


# IMPORTANTE:
# Aqui só entram palavras que realmente indicam
# o TIPO DA FONTE/documento.
#
# Não colocamos:
# cliente -> customer
# funcionário -> employee
# produto -> product
# loja -> store
#
# porque essas palavras podem representar entidades,
# e não necessariamente o tipo do documento que contém a resposta.
DOC_TYPE_SYNONYMS = {
    "ticket": [
        "ticket",
        "tickets",
        "chamado",
        "chamados",
    ],

    "log": [
        "log",
        "logs",
        "registro de log",
        "registros de log",
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
        "reuniao",
        "reunião",
        "reunioes",
        "reuniões",
    ],

    "policy": [
        "politica",
        "política",
        "politicas",
        "políticas",
    ],

    "manual": [
        "manual",
        "manuais",
    ],

    "store": [
        "filial",
        "filiais",
        "unidade",
        "unidades",
        "store",
        "stores",
    ],

    "sale": [
        "venda",
        "vendas",
    ],
}


MODULE_SYNONYMS = {
    "estoque": [
        "estoque",
        "inventario",
        "inventário",
    ],

    "pay": [
        "pay",
        "pagamento",
        "pagamentos",
    ],

    "pdv": [
        "pdv",
        "ponto de venda",
    ],

    "analytics": [
        "analytics",
    ],

    "ecommerce": [
        "ecommerce",
        "e-commerce",
    ],

    "loja": [
        "vendefacil loja",
    ],
}


def normalize(text: str) -> str:
    """
    Normaliza o texto:
    - lowercase
    - remove acentos
    - normaliza espaços
    """

    text = text.lower()

    text = unicodedata.normalize(
        "NFKD",
        text
    ).encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_customer_id(text: str):
    match = re.search(
        r"\bCUST\d+\b",
        text,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(0).upper()

    return None


def extract_ticket_id(text: str):
    match = re.search(
        r"\bTCK-\d+\b",
        text,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(0).upper()

    return None


def extract_doc_types(text: str):
    """
    Detecta os tipos de documentos explicitamente
    mencionados na pergunta.
    """

    normalized = normalize(text)

    detected = []

    for doc_type, synonyms in DOC_TYPE_SYNONYMS.items():

        for synonym in synonyms:

            synonym_normalized = normalize(synonym)

            if re.search(
                rf"\b{re.escape(synonym_normalized)}\b",
                normalized
            ):
                detected.append(doc_type)
                break

    return detected


def extract_state(text: str):
    normalized = normalize(text)

    # Primeiro tenta nomes completos
    for name, code in STATE_NAMES.items():

        name_normalized = normalize(name)

        if re.search(
            rf"\b{re.escape(name_normalized)}\b",
            normalized
        ):
            return code

    # Depois tenta siglas
    for state in VALID_STATES:

        if re.search(
            rf"\b{state.lower()}\b",
            normalized
        ):
            return state

    return None


def extract_city(text: str):
    normalized = normalize(text)

    cities = {
        "belo horizonte": "Belo Horizonte",
        "bh": "Belo Horizonte",
        "sao paulo": "São Paulo",
        "rio de janeiro": "Rio de Janeiro",
        "curitiba": "Curitiba",
        "recife": "Recife",
        "salvador": "Salvador",
    }

    for city, canonical in cities.items():

        if re.search(
            rf"\b{re.escape(city)}\b",
            normalized
        ):
            return canonical

    return None


def extract_module(text: str):
    normalized = normalize(text)

    for module, synonyms in MODULE_SYNONYMS.items():

        for synonym in synonyms:

            synonym_normalized = normalize(synonym)

            if re.search(
                rf"\b{re.escape(synonym_normalized)}\b",
                normalized
            ):
                return module

    return None


def extract_priority(text: str):
    normalized = normalize(text)

    priorities = {
        "alta": "alta",
        "baixa": "baixa",
        "critica": "critica",
        "media": "media",
    }

    for value, canonical in priorities.items():

        if re.search(
            rf"\b{re.escape(value)}\b",
            normalized
        ):
            return canonical

    return None


def extract_status(text: str):
    normalized = normalize(text)

    statuses = [
        "aberto",
        "ativo",
        "cancelado",
        "em andamento",
        "inativo",
        "resolvido",
    ]

    for status in statuses:

        if re.search(
            rf"\b{re.escape(status)}\b",
            normalized
        ):
            return status

    return None


def analyze_query(query: str):

    normalized_query = normalize(query)

    doc_types = extract_doc_types(query)

    customer_id = extract_customer_id(query)

    ticket_id = extract_ticket_id(query)

    state = extract_state(query)

    city = extract_city(query)

    module = extract_module(query)

    priority = extract_priority(query)

    status = extract_status(query)

    filters = {}

    # Só usamos doc_type como filtro quando existe
    # UM ÚNICO tipo de documento explicitamente pedido.
    #
    # Exemplo:
    # "listar os tickets..." -> ticket
    #
    # Mas:
    # "e-mails, tickets e reuniões" -> não filtra
    # porque precisamos buscar em várias fontes.
    if len(doc_types) == 1:
        filters["doc_type"] = doc_types[0]

    if customer_id:
        filters["customer_id"] = customer_id

    if ticket_id:
        filters["ticket_id"] = ticket_id

    if state:
        filters["state"] = state

    if city:
        filters["city"] = city

    if module:
        filters["module"] = module

    if priority:
        filters["priority"] = priority

    if status:
        filters["status"] = status

    return {
        "original_query": query,
        "normalized_query": normalized_query,
        "filters": filters,
        "doc_types_detected": doc_types,
    }


if __name__ == "__main__":

    test_queries = [

        "Quais tickets de clientes de Minas Gerais estão relacionados ao módulo de estoque?",

        "Quem é o responsável técnico (Tech Lead) e a gerente de produto (PM) do VendeFácil Estoque?",

        "Qual é a política de home office para os funcionários da equipe de Engenharia?",

        "Listar os logs de erro registrados para o cliente CUST008 no serviço de pagamento (pay).",

        "O cliente Supermercado Boa Compra está reclamando de falha de sincronização. Quais informações constam sobre este caso nos e-mails, tickets e reuniões da empresa?",

        "A cliente Ótica Visão Clara pediu cancelamento de contrato. Analise o e-mail enviado.",

        "Por que o PDV exibe a mensagem Timeout de confirmação TEF no cliente CUST008?",

        "Quais são as filiais cadastradas para o cliente CUST001 em Belo Horizonte?",

        "Qual é a regra de Safety Stock configurável no VendeFácil Loja?",
    ]

    for query in test_queries:

        result = analyze_query(query)

        print("=" * 70)
        print("PERGUNTA:")
        print(query)

        print("\nNORMALIZADA:")
        print(result["normalized_query"])

        print("\nTIPOS DE DOCUMENTO DETECTADOS:")
        print(result["doc_types_detected"])

        print("\nFILTROS:")
        print(result["filters"])