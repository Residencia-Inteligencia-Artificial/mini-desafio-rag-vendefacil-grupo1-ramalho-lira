# Mini Desafio — Assistente RAG Corporativo VendeFácil

## Sobre o projeto

Projeto desenvolvido em dupla durante a Residência em Inteligência Artificial do programa TIC em Trilhas, em parceria com o Instituto ECOA da PUC-Rio.

O objetivo foi desenvolver um assistente corporativo baseado em Inteligência Artificial Generativa e RAG (Retrieval-Augmented Generation), utilizando diferentes fontes de conhecimento para recuperar informações e produzir respostas fundamentadas.

A solução explora técnicas de embeddings, busca híbrida, indexação vetorial, geração de respostas e avaliação de resultados.

## Tecnologias utilizadas

- Python
- Inteligência Artificial Generativa
- Retrieval-Augmented Generation (RAG)
- FAISS
- BM25
- Modelos de Linguagem (LLMs)
- Streamlit

## Desenvolvimento colaborativo

O projeto foi desenvolvido por Janice Lira e Emilly Ramalho.

Contribuições de Janice Lira: ingestão e organização de dados, revisão do tratamento de informações sensíveis, documentação técnica e versionamento dos entregáveis no GitHub.

O desenvolvimento proporcionou experiência prática com recuperação de informações, integração de componentes de IA e avaliação de respostas.

---
## Resultados e Avaliação do RAG

O assistente RAG corporativo VendeFácil foi submetido a um benchmark composto por 20 perguntas, com o objetivo de avaliar a recuperação de informações, a qualidade das respostas e sua fundamentação nas fontes consultadas.

### Métricas registradas

| Indicador | Resultado |
|---|---|
| Perguntas avaliadas | 20 |
| Taxa de acertos | 55% |
| Relevância do contexto | 0,88 |
| Relevância da resposta | 1,00 |
| Fundamentação das respostas (Groundedness) | 0,87 |

### Principais aprendizados

A avaliação permitiu identificar oportunidades de melhoria na recuperação de informações, na filtragem por metadados e no tratamento de perguntas que exigem a combinação de múltiplas fontes.

O projeto também contemplou mecanismos de proteção de informações sensíveis, considerando princípios de Segurança da Informação e LGPD.

Os resultados demonstram a importância da avaliação contínua de aplicações RAG, especialmente quanto à precisão, à rastreabilidade das respostas e à segurança dos dados.

**Relatório técnico completo:** [RELATORIO.md](RELATORIO.md)

**Análise das falhas identificadas:** [failure_report.md](reports/failure_report.md)
## Mini Desafio RAG — VendeFácil Knowledge Base

---

Bem-vindo ao **Mini Desafio RAG (Retrieval-Augmented Generation)** baseado no ecossistema da empresa fictícia **VendeFácil Tecnologia Ltda.**!

Este repositório contém a bases de dados sintéticas multi-formato e orientações pedagógicas para a realização de um mini desafio prático projetado ser realizado em **duplas**.

---

## Contexto do Negócio: VendeFácil Tecnologia Ltda.

A VendeFácil é uma empresa brasileira de tecnologia que fornece sistemas de gestão para pequenos e médios varejistas (supermercados, farmácias, lojas de vestuário, petshops, etc.). O portfólio da empresa é composto por 5 produtos principais:

1. **VendeFácil PDV:** Sistema de frente de caixa com suporte a NFC-e, SAT e funcionamento offline.
2. **VendeFácil Estoque:** Gestão de inventário multiloja, inventário cego, transferência entre filiais e entrada via XML de NF-e.
3. **VendeFácil Loja:** Plataforma de e-commerce omnicanal e catálogo para WhatsApp/marketplaces.
4. **VendeFácil Analytics:** Dashboards executivos, DRE gerencial e curva ABC de vendas.
5. **VendeFácil Pay:** Solução de pagamento com TEF IP e PIX dinâmico integrado às maquininhas Pinpad.

---

## O Desafio

O objetivo das duplas é **construir um Assistente de Inteligência Artificial para a Knowledge Base da VendeFácil**, capaz de:

- Processar e indexar fontes de dados heterogêneas (CSV, JSON, JSONL, Markdown, PDF e TXT).
- Executar busca híbrida (Embeddings + BM25) com **filtragem avançada por metadados** (ex: estado `MG`, módulo `estoque`, cliente `CUST001`).
- Gerar respostas estritamente fundamentadas em fatos, com **saída estruturada em Pydantic** citando fontes e nível de confiança.
- Aplicar **Guardrails e regras de segurança (LGPD)** para impedir o vazamento de informações sensíveis (salários de colaboradores, senhas/chaves de API) e reconhecer perguntas fora do escopo.
- Avaliar o desempenho do sistema através do benchmark fornecido utilizando as métricas da **RAG Triad** (Relevância do Contexto, Relevância da Resposta e Groundedness).

---

## Estrutura do Repositório

```
mini-desafio/
├── data/                                 # Base de Conhecimento VendeFácil (Multi-formato)
│   ├── structured/                       # CSV e JSON (employees, customers, products, stores)
│   ├── semi_structured/                  # JSONL e CSV (tickets.jsonl, system_logs.csv)
│   └── unstructured/                     # Documentação (.md), Políticas (.pdf/.md), Reuniões (.md), E-mails (.txt)
├── starter/                              # Código de partida para os alunos
│   ├── requirements.txt                  # Dependências Python recomendadas
│   ├── schema.py                         # Estrutura Pydantic exigida para as respostas
│   └── ingest_template.py                # Esqueleto didático do pipeline de ingestão
└── docs/                                 # Documentação Didática


```

---

## Cronograma do Desafio

| Aula        | Carga Horária | Tópico Principal                                | Entregável da Aula                                                                      |
| ----------- | ------------- | ----------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Etapa 1** | 4h            | **Ingestão Heterogênea, Metadados e Vector DB** | Pipeline de carregamento, chunking e indexação no FAISS/Qdrant com metadados extraídos. |
| **Etapa 2** | 4h            | **Busca Híbrida e Filtragem por Metadados**     | Roteador de queries e buscador híbrido (Embeddings + BM25/Filtros).                     |
| **Etapa 3** | 4h            | **Síntese Estruturada e Guardrails / LGPD**     | Pipeline LLM com saída Pydantic, citação de evidências e bloqueio de dados sensíveis.   |
| **Etapa 4** | 4h            | **Avaliação (RAG Triad), UI e Defesa Técnica**  | Execução do benchmark, relatório de métricas e apresentação da dupla para a turma.      |

---

## Início Rápido

### 1. Pré-requisitos

- Python 3.10+
- Chave de API de LLM (OpenAI, Groq, OpenRouter ou ambiente Ollama local)

### 2. Instalação das Dependências

```bash
# Clone ou acesse a pasta do repositório
cd mini-desafio

# Crie e ative um ambiente virtual
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r starter/requirements.txt
```

### 3. Executar o sistema

Reconstrua o índice quando os dados forem alterados:

```bash
python -m src.build_index
```

Execute o benchmark oficial com as 20 perguntas Q01-Q20:

```bash
python -m eval.run_benchmark
```

Os resultados são gerados em `reports/benchmark_results.json`,
`reports/results.json`, `reports/benchmark_results.csv`,
`reports/failure_report.md` e `RELATORIO.md`.

Para demonstrar o assistente pelo terminal:

```bash
python -m src.demo_cli
```

Para abrir a interface web:

```bash
streamlit run streamlit_app.py
```

### 4. Consultar o Guia Didático

- [Guia Didático - Mini Desafio RAG VendeFácil](https://app.notion.com/p/IA-Generativa-RAG-3b3185f9f7ed806b8820ee5292611ee4)
