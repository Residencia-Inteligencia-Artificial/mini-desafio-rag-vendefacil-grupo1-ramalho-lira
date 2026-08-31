from __future__ import annotations

import csv
import glob
import json
import os
import re

from pypdf import PdfReader


# ============================================================
# CLASSIFICAÇÃO DE SENSIBILIDADE
# ============================================================

PADROES_RESTRITOS = [
    re.compile(r"\bsenha\b", re.IGNORECASE),
    re.compile(r"\bapi[_ -]?key\b", re.IGNORECASE),
    re.compile(r"\bchave de api\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
    re.compile(r"\btoken\b", re.IGNORECASE),
]

PADROES_SENSIVEIS = [
    re.compile(r"\bsal[aá]rio\b", re.IGNORECASE),
    re.compile(r"\bcpf\b", re.IGNORECASE),
    re.compile(r"\bcredencia(is|l)\b", re.IGNORECASE),
]


def classificar_sensitivity(texto: str) -> str:
    if any(p.search(texto) for p in PADROES_RESTRITOS):
        return "restrito"

    if any(p.search(texto) for p in PADROES_SENSIVEIS):
        return "interno"

    return "publico"


# ============================================================
# CSV GENÉRICO
# ============================================================

def carregar_csv(caminho: str) -> list[dict]:
    documentos = []

    with open(
        caminho,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for linha in reader:

            texto = ". ".join(
                f"{chave.replace('_', ' ')}: {valor}"
                for chave, valor in linha.items()
                if valor not in (None, "")
            )

            documentos.append({
                "text": texto,
                "metadata": {
                    "source_file": os.path.basename(caminho),
                    "row": linha,
                }
            })

    return documentos


# ============================================================
# CUSTOMERS
# ============================================================

def carregar_customers(caminho: str) -> list[dict]:
    documentos = []

    with open(
        caminho,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for linha in reader:

            customer_id = linha.get("customer_id")
            nome = linha.get("name")
            estado = linha.get("state")
            modulo = linha.get("module")
            data = linha.get("date")
            status = linha.get("status")

            # Compatibilidade com diferentes nomes de colunas
            email = (
                linha.get("email")
                or linha.get("e_mail")
                or linha.get("email_address")
                or ""
            )

            telefone = (
                linha.get("phone")
                or linha.get("telefone")
                or linha.get("telephone")
                or linha.get("phone_number")
                or ""
            )

            texto = (
                f"Cliente {customer_id}: "
                f"{nome}, "
                f"estado {estado}, "
                f"módulo contratado {modulo}, "
                f"cliente desde {data}, "
                f"situação {status}."
            )

            # IMPORTANTE:
            # Mantemos e-mail e telefone no documento para que
            # possam ser recuperados pela busca e posteriormente
            # mascarados pela camada LGPD.
            if email:
                texto += f" E-mail: {email}."

            if telefone:
                texto += f" Telefone: {telefone}."

            documentos.append({
                "text": texto,
                "metadata": {
                    "source_file": os.path.basename(caminho),
                    "doc_type": "customer",
                    "customer_id": customer_id,
                    "name": nome,
                    "state": estado,
                    "module": modulo,
                    "date": data,
                    "status": status,

                    # Dados pessoais ficam disponíveis para
                    # processamento da camada LGPD.
                    "email": email if email else None,
                    "phone": telefone if telefone else None,

                    "sensitivity": classificar_sensitivity(texto),
                }
            })

    return documentos


# ============================================================
# EMPLOYEES
# ============================================================

def carregar_employees(caminho: str) -> list[dict]:
    documentos = []

    with open(
        caminho,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for linha in reader:

            texto = (
                f"Funcionário {linha.get('name')} "
                f"({linha.get('id')}), "
                f"cargo {linha.get('role')}, "
                f"departamento {linha.get('department')}, "
                f"admitido em {linha.get('hire_date')}, "
                f"status {linha.get('status')}, "
                f"salário {linha.get('salary')}."
            )

            documentos.append({
                "text": texto,
                "metadata": {
                    "source_file": os.path.basename(caminho),
                    "doc_type": "employee",
                    "department": linha.get("department"),
                    "sensitivity": "interno",
                }
            })

    return documentos


# ============================================================
# SALES
# ============================================================

def carregar_sales(caminho: str) -> list[dict]:
    documentos = []

    with open(
        caminho,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for linha in reader:

            texto = ". ".join(
                f"{chave.replace('_', ' ')}: {valor}"
                for chave, valor in linha.items()
                if valor not in (None, "")
            )

            documentos.append({
                "text": texto,
                "metadata": {
                    "source_file": os.path.basename(caminho),
                    "doc_type": "sale",
                    "date": linha.get("date"),
                    "sensitivity": "interno",
                }
            })

    return documentos


# ============================================================
# SYSTEM LOGS
# ============================================================

def carregar_system_logs(caminho: str) -> list[dict]:
    documentos = []

    with open(
        caminho,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for linha in reader:

            texto = ". ".join(
                f"{chave.replace('_', ' ')}: {valor}"
                for chave, valor in linha.items()
                if valor not in (None, "")
            )

            documentos.append({
                "text": texto,
                "metadata": {
                    "source_file": os.path.basename(caminho),
                    "doc_type": "log",
                    "sensitivity": classificar_sensitivity(texto),
                }
            })

    return documentos


# ============================================================
# PRODUCTS
# ============================================================

def carregar_products(caminho: str) -> list[dict]:

    with open(
        caminho,
        "r",
        encoding="utf-8"
    ) as f:

        dados = json.load(f)

    documentos = []

    for nome_plano, info in dados.get(
        "pricing_plans",
        {}
    ).items():

        texto = (
            f"Plano {nome_plano} da VendeFácil. "
            f"Mensalidade: R$ "
            f"{info.get('monthly_fee_brl')}. "
            f"Terminais inclusos: "
            f"{info.get('included_terminals')}. "
            f"Terminal extra: R$ "
            f"{info.get('extra_terminal_fee_brl')}. "
            f"{info.get('description', '')}"
        )

        documentos.append({
            "text": texto,
            "metadata": {
                "source_file": os.path.basename(caminho),
                "doc_type": "product",
                "sensitivity": "publico",
                "product": nome_plano,
            }
        })

    return documentos


# ============================================================
# STORES
# ============================================================

def carregar_stores(caminho: str) -> list[dict]:

    with open(
        caminho,
        "r",
        encoding="utf-8"
    ) as f:

        dados = json.load(f)

    documentos = []

    for loja in dados.get(
        "network_stores",
        []
    ):

        modulos = ", ".join(
            loja.get("active_modules", [])
        )

        texto = (
            f"Loja {loja.get('store_name')} "
            f"({loja.get('store_id')}), "
            f"cliente {loja.get('company_name')} "
            f"({loja.get('customer_id')}), "
            f"localizada em "
            f"{loja.get('city')}/"
            f"{loja.get('state')}. "
            f"Terminais de PDV: "
            f"{loja.get('pos_terminals_count')}. "
            f"Módulos ativos: {modulos}."
        )

        documentos.append({
            "text": texto,
            "metadata": {
                "source_file": os.path.basename(caminho),
                "doc_type": "store",
                "customer_id": loja.get("customer_id"),
                "state": loja.get("state"),
                "module": modulos,
                "sensitivity": "publico",
            }
        })

    return documentos


# ============================================================
# TICKETS
# ============================================================

def carregar_tickets(caminho: str) -> list[dict]:
    documentos = []

    with open(
        caminho,
        "r",
        encoding="utf-8"
    ) as f:

        for linha in f:

            linha = linha.strip()

            if not linha:
                continue

            ticket = json.loads(linha)

            texto = (
                f"Chamado {ticket.get('ticket_id')} - "
                f"{ticket.get('title')}. "
                f"Cliente: "
                f"{ticket.get('customer_name', '')} "
                f"({ticket.get('customer_id', '')}). "
                f"Categoria: "
                f"{ticket.get('category', '')}. "
                f"Prioridade: "
                f"{ticket.get('priority', '')}. "
                f"Status: "
                f"{ticket.get('status', '')}. "
                f"Descrição: "
                f"{ticket.get('description', '')}."
            )

            if ticket.get("resolution"):
                texto += (
                    f" Resolução: "
                    f"{ticket['resolution']}."
                )

            documentos.append({
                "text": texto,
                "metadata": {
                    "source_file": os.path.basename(caminho),
                    "doc_type": "ticket",
                    "customer_id": ticket.get("customer_id"),
                    "state": ticket.get("state"),
                    "module": ticket.get("module"),
                    "priority": ticket.get("priority"),
                    "status": ticket.get("status"),
                    "date": ticket.get("date"),
                    "ticket_id": ticket.get("ticket_id"),
                    "sensitivity": classificar_sensitivity(texto),
                }
            })

    return documentos


# ============================================================
# MARKDOWN
# ============================================================

def carregar_markdown(
    caminho: str,
    doc_type: str,
    modulo: str | None = None
) -> list[dict]:

    with open(
        caminho,
        "r",
        encoding="utf-8"
    ) as f:

        texto = f.read()

    return [{
        "text": texto,
        "metadata": {
            "source_file": os.path.basename(caminho),
            "doc_type": doc_type,
            "module": modulo,
            "sensitivity": classificar_sensitivity(texto),
        }
    }]


def carregar_pasta_markdown(
    pasta: str,
    doc_type: str,
    modulo_por_subpasta: bool = False
) -> list[dict]:

    documentos = []

    arquivos = sorted(
        glob.glob(
            os.path.join(
                pasta,
                "**",
                "*.md"
            ),
            recursive=True
        )
    )

    for caminho in arquivos:

        modulo = None

        if modulo_por_subpasta:
            modulo = os.path.basename(
                os.path.dirname(caminho)
            )

        documentos.extend(
            carregar_markdown(
                caminho,
                doc_type,
                modulo
            )
        )

    return documentos


# ============================================================
# PDF
# ============================================================

def carregar_pdf(
    caminho: str,
    doc_type: str = "policy"
) -> list[dict]:

    reader = PdfReader(caminho)

    paginas = []

    for page in reader.pages:

        texto = page.extract_text()

        if texto:
            paginas.append(texto)

    texto_completo = "\n\n".join(paginas)

    return [{
        "text": texto_completo,
        "metadata": {
            "source_file": os.path.basename(caminho),
            "doc_type": doc_type,
            "sensitivity": classificar_sensitivity(
                texto_completo
            ),
        }
    }]


# ============================================================
# EMAILS
# ============================================================

_PADRAO_CUSTOMER = re.compile(
    r"customer_(\d+)",
    re.IGNORECASE
)


def carregar_emails(pasta: str) -> list[dict]:

    documentos = []

    arquivos = sorted(
        glob.glob(
            os.path.join(
                pasta,
                "*.txt"
            )
        )
    )

    for caminho in arquivos:

        with open(
            caminho,
            "r",
            encoding="utf-8"
        ) as f:

            texto = f.read()

        nome = os.path.basename(caminho)

        match = _PADRAO_CUSTOMER.search(nome)

        customer_id = (
            f"CUST{match.group(1).zfill(3)}"
            if match
            else None
        )

        documentos.append({
            "text": texto,
            "metadata": {
                "source_file": nome,
                "doc_type": "email",
                "customer_id": customer_id,
                "sensitivity": classificar_sensitivity(
                    texto
                ),
            }
        })

    return documentos


# ============================================================
# CARREGAR TODAS AS FONTES
# ============================================================

def carregar_todas_as_fontes_vetorizaveis(
    data_dir: str
) -> list[dict]:

    documentos = []

    # Customers
    documentos += carregar_customers(
        os.path.join(
            data_dir,
            "structured",
            "customers.csv"
        )
    )

    # Employees
    documentos += carregar_employees(
        os.path.join(
            data_dir,
            "structured",
            "employees.csv"
        )
    )

    # Sales
    documentos += carregar_sales(
        os.path.join(
            data_dir,
            "structured",
            "sales.csv"
        )
    )

    # Logs
    documentos += carregar_system_logs(
        os.path.join(
            data_dir,
            "semi_structured",
            "system_logs.csv"
        )
    )

    # Products
    documentos += carregar_products(
        os.path.join(
            data_dir,
            "structured",
            "products.json"
        )
    )

    # Stores
    documentos += carregar_stores(
        os.path.join(
            data_dir,
            "structured",
            "stores.json"
        )
    )

    # Tickets
    documentos += carregar_tickets(
        os.path.join(
            data_dir,
            "semi_structured",
            "tickets.jsonl"
        )
    )

    # Documentation
    documentos += carregar_pasta_markdown(
        os.path.join(
            data_dir,
            "unstructured",
            "documentation"
        ),
        doc_type="manual",
        modulo_por_subpasta=True
    )

    # Meetings
    documentos += carregar_pasta_markdown(
        os.path.join(
            data_dir,
            "unstructured",
            "meetings"
        ),
        doc_type="ata"
    )

    # Policies Markdown
    documentos += carregar_pasta_markdown(
        os.path.join(
            data_dir,
            "unstructured",
            "policies"
        ),
        doc_type="policy"
    )

    # Emails
    documentos += carregar_emails(
        os.path.join(
            data_dir,
            "unstructured",
            "emails"
        )
    )

    # Policies PDF
    pasta_policies = os.path.join(
        data_dir,
        "unstructured",
        "policies"
    )

    for caminho in sorted(
        glob.glob(
            os.path.join(
                pasta_policies,
                "*.pdf"
            )
        )
    ):

        documentos += carregar_pdf(
            caminho,
            doc_type="policy"
        )

    return documentos