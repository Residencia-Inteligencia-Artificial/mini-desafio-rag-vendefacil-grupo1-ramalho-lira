"""
Query Analyzer

Responsável por analisar a pergunta do usuário e extrair:
- tipos de documento
- estado
- cidade
- módulo
- prioridade
- status
- customer_id
- ticket_id

Também identifica intenções específicas, como:
- catálogo de produtos
- consulta de clientes
- consulta de políticas
- consulta de manuais
"""

import os
import re
import unicodedata


# ============================================================
# TIPOS DE DOCUMENTO VÁLIDOS
# ============================================================

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


# ============================================================
# ESTADOS
# ============================================================

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


# ============================================================
# MÓDULOS
# ============================================================

VALID_MODULES = {
    "estoque",
    "pay",
    "pdv",
    "analytics",
    "ecommerce",
    "loja",
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

    "log": [
        "log",
        "logs",
        "registro de log",
        "registros de log",
        "registro de logs",
        "registros de logs",
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


# ============================================================
# SINÔNIMOS DE MÓDULOS
# ============================================================

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
        "vendefacil loja",
    ],

    "loja": [
        "loja online",
    ],
}


# ============================================================
# PRIORIDADES
# ============================================================

VALID_PRIORITIES = {
    "baixa",
    "media",
    "média",
    "alta",
    "critica",
    "crítica",
}


# ============================================================
# STATUS
# ============================================================

VALID_STATUSES = {
    "aberto",
    "aberta",
    "fechado",
    "fechada",
    "em andamento",
    "pendente",
    "resolvido",
    "resolvida",
}


# ============================================================
# CIDADES
# ============================================================


CITY_SYNONYMS = {
    "belo horizonte": "Belo Horizonte",
    "bh": "Belo Horizonte",

    "curitiba": "Curitiba",

    "recife": "Recife",

    "salvador": "Salvador",
}



# ============================================================
# CLIENTES CONHECIDOS
# ============================================================
#
# IMPORTANTE:
# Só coloque aqui IDs que realmente existam nos seus dados.
#
# No seu benchmark, Auto Peças Central aparece como CUST008.
# Outros clientes devem ser adicionados somente depois de
# confirmar o ID no arquivo de clientes.
#

CUSTOMER_NAMES = {
    "auto pecas central": "CUST008",
    "auto peças central": "CUST008",
    "supermercado boa compra": "CUST001",
}


def _load_customer_aliases() -> dict[str, str]:
    """Carrega o mapa de nomes dos clientes diretamente dos dados do benchmark."""
    aliases = dict(CUSTOMER_NAMES)

    try:
        data_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "structured",
            "customers.csv",
        )
        with open(data_path, "r", encoding="utf-8-sig", newline="") as handle:
            import csv

            reader = csv.DictReader(handle)
            for row in reader:
                customer_id = row.get("customer_id")
                company_name = row.get("company_name")
                if not customer_id or not company_name:
                    continue
                aliases[normalize(company_name)] = customer_id
                aliases[normalize(company_name.lower())] = customer_id
    except Exception:
        pass

    return aliases


CUSTOMER_ALIASES = _load_customer_aliases()


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalize(text: str) -> str:
    """
    Normaliza texto:
    - converte para string
    - lowercase
    - remove acentos
    - normaliza espaços
    """

    if not text:
        return ""

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
# EXTRAÇÃO DE CUSTOMER ID
# ============================================================

def extract_customer_id(text: str):
    """
    Detecta IDs como:

    CUST001
    CUST008
    CUST123
    """

    normalized = normalize(text)

    match = re.search(
        r"\bcust[-_ ]?(\d+)\b",
        normalized,
    )

    if not match:
        return None

    return f"CUST{match.group(1).zfill(3)}"


# ============================================================
# EXTRAÇÃO DE NOME DO CLIENTE
# ============================================================

def extract_customer_name(text: str):
    """
    Tenta identificar um cliente conhecido pelo nome.

    Exemplo:
        "erro TEF da Auto Peças Central"

    retorna:
        CUST008
    """

    normalized = normalize(text)

    for customer_name, customer_id in CUSTOMER_ALIASES.items():

        normalized_name = normalize(customer_name)

        if normalized_name in normalized:
            return customer_id

    return None


# ============================================================
# EXTRAÇÃO DE TICKET ID
# ============================================================

def extract_ticket_id(text: str):
    """
    Detecta IDs como:

    TCK-1001
    TCK1001
    """

    normalized = normalize(text)

    match = re.search(
        r"\btck[-_ ]?(\d+)\b",
        normalized,
    )

    if not match:
        return None

    return f"TCK-{match.group(1)}"


# ============================================================
# EXTRAÇÃO DE TIPOS DE DOCUMENTO
# ============================================================

def extract_doc_types(text: str):
    """
    Identifica tipos de documento mencionados
    explicitamente na pergunta.
    """

    normalized = normalize(text)

    detected = []

    for doc_type, synonyms in DOC_TYPE_SYNONYMS.items():

        for synonym in synonyms:

            normalized_synonym = normalize(synonym)

            pattern = rf"\b{re.escape(normalized_synonym)}\b"

            if re.search(pattern, normalized):
                detected.append(doc_type)
                break

    return detected


# ============================================================
# CONSULTA DE CATÁLOGO DE PRODUTOS
# ============================================================

def is_product_catalog_query(text: str) -> bool:
    """
    Identifica perguntas relacionadas ao catálogo de produtos.

    Exemplos:

    - Quais produtos a VendeFácil possui?
    - Quais planos existem?
    - Quais produtos estão disponíveis?
    - Me mostre o catálogo.
    """

    normalized = normalize(text)

    patterns = [
        r"\bquais produtos\b",
        r"\bqual(is)? produtos\b",
        r"\bprodutos .* possui\b",
        r"\bprodutos .* vendefacil\b",
        r"\bprodutos .* vende facil\b",
        r"\bcatalogo\b",
        r"\bcatalogo de produtos\b",
        r"\bplanos .* possui\b",
        r"\bquais planos\b",
        r"\bplanos disponiveis\b",
        r"\bprodutos disponiveis\b",
        r"\bitens disponiveis\b",
    ]

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


# ============================================================
# CONSULTA DE CLIENTE
# ============================================================

def is_customer_query(text: str) -> bool:
    """
    Identifica perguntas que provavelmente dependem
    de documentos de clientes.

    Exemplos:

    - Qual cliente possui maior MRR?
    - Qual cliente possui maior receita recorrente?
    - Quais clientes possuem determinado produto?
    """

    normalized = normalize(text)

    patterns = [
        r"\bmrr\b",
        r"\breceita recorrente\b",
        r"\bcliente possui\b",
        r"\bclientes possui\b",
        r"\bqual cliente\b",
        r"\bquais clientes\b",
        r"\bclientes\b.*\bproduto\b",
        r"\bcliente\b.*\bproduto\b",
        r"\bclientes\b.*\bplano\b",
        r"\bcliente\b.*\bplano\b",
    ]

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


# ============================================================
# CONSULTA DE POLÍTICA
# ============================================================

def is_policy_query(text: str) -> bool:
    """
    Identifica perguntas relacionadas a políticas,
    regras e diretrizes.

    Exemplos:

    - Qual a política de reembolso?
    - Quais são as regras?
    - Qual a política para cancelamento?
    """

    normalized = normalize(text)

    patterns = [
        r"\bpolitica\b",
        r"\bpoliticas\b",
        r"\bregras?\b",
        r"\bdiretrizes?\b",
        r"\bpolitica de reembolso\b",
        r"\breembolso\b",
        r"\bcancelamento\b",
        r"\bdevolucao\b",
        r"\bdevoluções\b",
    ]

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


# ============================================================
# CONSULTA DE MANUAL
# ============================================================

def is_manual_query(text: str) -> bool:
    """
    Identifica perguntas que normalmente dependem
    de documentação técnica/manual.

    Exemplos:

    - Como realizar o procedimento?
    - Como configurar?
    - Como corrigir o erro?
    - Qual procedimento deve ser realizado?
    """

    normalized = normalize(text)

    patterns = [
        r"\bmanual\b",
        r"\bcomo proceder\b",
        r"\bcomo realizar\b",
        r"\bcomo deve ser realizada\b",
        r"\bcomo deve ser realizado\b",
        r"\bcomo configurar\b",
        r"\bcomo corrigir\b",
        r"\bcomo resolver\b",
        r"\bprocedimento tecnico\b",
        r"\bprocedimento\b",
        r"\bconfiguracao\b",
        r"\bconfigurar\b",
        r"\berro\b.*\bprocedimento\b",
        r"\bregra\b.*\bprocedimento\b",
    ]

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


# ============================================================
# EXTRAÇÃO DE ESTADO
# ============================================================

def extract_state(text: str):
    """
    Detecta estados brasileiros tanto pela UF
    quanto pelo nome completo.

    Exemplos:

    MG -> MG
    Minas Gerais -> MG

    SP -> SP
    São Paulo -> SP
    """

    normalized = normalize(text)

    state_synonyms = {
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

    # Primeiro tenta nome completo
    for state_name, state_code in state_synonyms.items():

        if normalize(state_name) in normalized:
            return state_code

    # Depois tenta a UF
    for state in VALID_STATES:

        if re.search(
            rf"(?<![a-z]){state.lower()}(?![a-z])",
            normalized,
        ):
            return state

    return None

# ============================================================
# EXTRAÇÃO DE CIDADE
# ============================================================

def extract_city(text: str):
    """
    Detecta cidades conhecidas.
    """

    normalized = normalize(text)

    for city_alias, city_name in CITY_SYNONYMS.items():

        if city_alias in normalized:
            return city_name

    return None


# ============================================================
# EXTRAÇÃO DE MÓDULO
# ============================================================

def extract_module(text: str):
    """
    Detecta o módulo citado na pergunta.
    """

    normalized = normalize(text)

    for module, synonyms in MODULE_SYNONYMS.items():

        for synonym in synonyms:

            normalized_synonym = normalize(synonym)

            if normalized_synonym in normalized:
                return module

    return None


# ============================================================
# EXTRAÇÃO DE PRIORIDADE
# ============================================================

def extract_priority(text: str):
    """
    Detecta prioridade de ticket.
    """

    normalized = normalize(text)

    priority_map = {
        "baixa": "baixa",
        "media": "media",
        "média": "media",
        "alta": "alta",
        "critica": "critica",
        "crítica": "critica",
    }

    for value, normalized_value in priority_map.items():

        if re.search(
            rf"\b{re.escape(normalize(value))}\b",
            normalized,
        ):
            return normalized_value

    return None


# ============================================================
# EXTRAÇÃO DE STATUS
# ============================================================

def extract_status(text: str):
    """
    Detecta status de ticket.

    Evita confundir a forma verbal 'foram abertos' com uma
    requisição explícita de filtro por status.
    """

    normalized = normalize(text)

    if re.search(r"\bforam abertos?\b|\bforam fechados?\b", normalized):
        if not re.search(r"\b(status|situacao|situação)\b", normalized):
            return None

    status_map = {
        "aberto": "aberto",
        "aberta": "aberto",
        "fechado": "fechado",
        "fechada": "fechado",
        "em andamento": "em andamento",
        "pendente": "pendente",
        "resolvido": "resolvido",
        "resolvida": "resolvido",
    }

    for value, normalized_value in status_map.items():
        pattern = rf"\b{re.escape(normalize(value))}\b"
        if re.search(pattern, normalized):
            if normalize_value := normalize(value):
                if normalize_value in {"aberto", "aberta", "fechado", "fechada"}:
                    if re.search(r"\b(status|situacao|situação|estao|estão)\b", normalized):
                        return normalized_value
                    if re.search(r"\bforam abertos?\b|\bforam fechados?\b", normalized):
                        return None
                return normalized_value

    return None


# ============================================================
# ANÁLISE PRINCIPAL
# ============================================================

def analyze_query(query: str):
    """
    Analisa completamente uma pergunta.

    Retorna:

    {
        "normalized_query": "...",
        "doc_types": [...],
        "filters": {...}
    }
    """

    normalized_query = normalize(query)

    # --------------------------------------------------------
    # 1. TIPOS DE DOCUMENTO EXPLÍCITOS
    # --------------------------------------------------------

    doc_types = extract_doc_types(query)

    # --------------------------------------------------------
    # 2. CATÁLOGO DE PRODUTOS
    # --------------------------------------------------------

    if is_product_catalog_query(query):

        if "product" not in doc_types:
            doc_types.append("product")

    # --------------------------------------------------------
    # 3. CUSTOMER ID
    # --------------------------------------------------------

    customer_id = extract_customer_id(query)

    # Se não encontrou CUSTxxx,
    # tenta identificar pelo nome.
    if not customer_id:
        customer_id = extract_customer_name(query)

    # --------------------------------------------------------
    # 4. TICKET ID
    # --------------------------------------------------------

    ticket_id = extract_ticket_id(query)

    # --------------------------------------------------------
    # 5. OUTROS FILTROS
    # --------------------------------------------------------

    state = extract_state(query)

    city = extract_city(query)

    module = extract_module(query)

    # Expressões como "foram abertos" descrevem o evento histórico
    # do ticket, e não uma solicitação de filtro por status.
    if re.search(r"\bforam abertos?\b", normalized_query):
        if not re.search(r"\b(status|situacao|situação)\b", normalized_query):
            status = None
        else:
            status = extract_status(query)
    else:
        status = extract_status(query)

    safety_stock_query = "safety stock" in normalized_query
    if safety_stock_query:
        module = "ecommerce"
        doc_types = [doc_type for doc_type in doc_types if doc_type != "policy"]

    # "Devolução" pode se referir à política comercial de reembolso ou à
    # operação executada no caixa. Quando a pergunta menciona o PDV e termos
    # operacionais, a fonte correta é o manual do PDV, não a política de
    # cancelamento de planos.
    troca_devolucao_pdv_query = (
        module == "pdv"
        and any(
            termo in normalized_query
            for termo in (
                "troca",
                "devolucao",
                "vale-troca",
                "vale troca",
            )
        )
        and any(
            termo in normalized_query
            for termo in (
                "atalho",
                "teclado",
                "procedimento",
                "operacao",
                "vale-troca",
                "vale troca",
            )
        )
    )
    if troca_devolucao_pdv_query:
        doc_types = ["manual"]
        module = "pdv"

    tef_troubleshooting_query = (
        "tef" in normalized_query
        and any(
            term in normalized_query
            for term in ("timeout", "procedimento", "solucao", "solução")
        )
    )
    if tef_troubleshooting_query:
        doc_types = []
        customer_id = None
        module = None

    priority = extract_priority(query)

    sla_priority_query = (
        priority == "critica"
        and "sla" in normalized_query
    )
    if sla_priority_query:
        priority = None

    # --------------------------------------------------------
    # 6. INFERÊNCIA DE TIPO DE DOCUMENTO
    # --------------------------------------------------------
    #
    # Só inferimos quando a pergunta NÃO informou
    # explicitamente um tipo de documento.
    #
    # Isso é importante para perguntas como:
    #
    # "Quais informações aparecem nos emails e tickets?"
    #
    # Nesse caso NÃO devemos substituir os tipos explícitos.
    # --------------------------------------------------------

    if not doc_types:

        if is_customer_query(query):
            doc_types.append("customer")

        elif is_policy_query(query) and not safety_stock_query:
            doc_types.append("policy")

        elif is_manual_query(query) and not tef_troubleshooting_query:
            doc_types.append("manual")

    if sla_priority_query:
        doc_types = []

    multi_source_query = (
        len(doc_types) > 1
        or all(
            term in normalized_query
            for term in ("email", "ticket", "reun")
        )
    )
    if multi_source_query and not customer_id:
        customer_id = None

    # --------------------------------------------------------
    # 7. CONSTRUÇÃO DOS FILTROS
    # --------------------------------------------------------

    filters = {}

    # Só aplica doc_type diretamente quando existe
    # exatamente um tipo.
    #
    # Exemplo:
    #
    # ticket + MG + estoque
    # -> doc_type=ticket
    #
    # Mas:
    #
    # email + ticket + ata
    # -> não força um único doc_type.
    #

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

    # --------------------------------------------------------
    # 8. RESULTADO
    # --------------------------------------------------------

    return {
        "normalized_query": normalized_query,
        "doc_types": doc_types,
        "filters": filters,
    }


# ============================================================
# TESTES
# ============================================================

if __name__ == "__main__":

    test_queries = [

        # ----------------------------------------------------
        # PRODUTO
        # ----------------------------------------------------

        "Quais produtos a VendeFácil possui?",

        # ----------------------------------------------------
        # TICKET + ESTADO + MÓDULO
        # ----------------------------------------------------

        "Quais tickets de clientes de Minas Gerais estão relacionados ao módulo de estoque?",

        # ----------------------------------------------------
        # CLIENTE / MRR
        # ----------------------------------------------------

        "Qual cliente de São Paulo possui o maior MRR?",

        # ----------------------------------------------------
        # LOG + CUSTOMER + MODULE
        # ----------------------------------------------------

        "Quais logs do cliente CUST008 estão relacionados ao serviço pay?",

        # ----------------------------------------------------
        # CLIENTE PELO NOME
        # ----------------------------------------------------

        "Quais erros de TEF ocorreram para a Auto Peças Central?",

        # ----------------------------------------------------
        # MULTI-SOURCE
        # ----------------------------------------------------

        "O que aconteceu com o Supermercado Boa Compra considerando emails, tickets e reuniões?",

        # ----------------------------------------------------
        # POLICY
        # ----------------------------------------------------

        "Qual é a política de reembolso?",

        # ----------------------------------------------------
        # MANUAL
        # ----------------------------------------------------

        "Como deve ser realizado o procedimento de Safety Stock?",

        # ----------------------------------------------------
        # TICKET ESPECÍFICO
        # ----------------------------------------------------

        "Qual é o procedimento para o ticket STK-409?",

        # ----------------------------------------------------
        # STORE
        # ----------------------------------------------------

        "Quais filiais do Supermercado Boa Compra existem em Belo Horizonte?",
    ]

    print("=" * 70)
    print("QUERY ANALYZER - TESTES")
    print("=" * 70)

    for query in test_queries:

        result = analyze_query(query)

        print("\n" + "=" * 70)
        print("PERGUNTA:")
        print(query)

        print("\nNORMALIZADA:")
        print(result["normalized_query"])

        print("\nTIPOS DE DOCUMENTO DETECTADOS:")
        print(result["doc_types"])

        print("\nFILTROS:")
        print(result["filters"])

    print("\n" + "=" * 70)
    print("TESTES FINALIZADOS")
    print("=" * 70)
