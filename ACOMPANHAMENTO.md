# Acompanhamento - Mini Desafio RAG VendeFácil

**Integrante 1:** Janice Lira - [@Janice977](https://github.com/Janice977)
**Integrante 2:** Emilly Ramalho - [@EmillySRamalho](https://github.com/EmillySRamalho)

**Repositório:** `mini-desafio-rag-vendefacil-grupo1-ramalho-lira`

---

## Como preencher

- Um bloco por encontro, em **ordem cronológica** - o encontro mais recente vai no **fim** do arquivo.
- O relato individual é escrito **pelo próprio integrante**, em primeira pessoa. Não escreva pelo colega.
- Escrever entre **17:30 e 17:40**. `commit` + `push` até as **18:00**, mesmo que o dia não tenha fechado.
- Mensagem de commit: `acompanhamento: AAAA-MM-DD`

**Um relato útil responde:** o que eu implementei, qual decisão técnica eu tomei e por quê, onde travei, e como (ou se) resolvi.

<details>
<summary>Exemplo de relato individual bom × ruim</summary>

❌ *"Trabalhei na parte de ingestão junto com meu colega. Avançamos bastante e conseguimos carregar os arquivos."*

✅ *"Implementei os loaders de CSV e JSONL em `src/ingest.py`. Decidi serializar cada linha do `customers.csv` como frase em linguagem natural em vez de manter o formato separado por vírgula, porque nos primeiros testes de similaridade os chunks CSV crus não recuperavam nada - o embedding não separa campo de valor. Travei ~40 min no `tickets.jsonl`: o `state` estava indo para o texto do chunk mas não para os metadados, então o filtro voltava vazio. Resolvi movendo a extração para antes da criação do `Document`. Usei o Claude para gerar o esqueleto do parser de JSONL; ajustei o schema de metadados na mão."*

</details>

---

## Encontro 1 - AAAA-MM-DD

**Etapa:** 1 - Ingestão heterogênea, metadados e indexação vetorial

### Relato individual - [Nome do Integrante 1]

<!-- Escreva você mesmo, em primeira pessoa. O que implementou, que decisão tomou e por quê, onde travou. -->

### Relato individual - Emilly Santos Ramalho

Eu criei a organização no github e adicionei os membros
Criei o repositorio do Desafio
Clonamos os repositórios em nossa máquina
Demos inicio a etapa 1, ainda está sendo revisada e sendo feita algumas alterações.


### Resumo do dia (escrito em conjunto)

Nós decidimos realizar todas as etapas em conjunto, trabalhando em parceria direta durante a sessão no Colab. Clonamos o repositório lado a lado e executamos o pipeline de ingestão desenvolvido para o projeto.

Ao executar o comando `python -m src.ingest`, acompanhamos todo o processamento de **217 documentos provenientes de fontes heterogêneas**, como e-mails, políticas e tickets, que resultou na geração de **251 chunks**.

Durante a execução, discutimos as decisões relacionadas ao tratamento dos dados. Em conjunto, concluímos que manter as tabelas `customers.csv`, `sales.csv` e `system_logs.csv` fora do índice vetorial seria a abordagem mais adequada, considerando que dados estruturados de grande volume e consultas de agregação não se encaixam bem no modelo de busca semântica.

Embora tenhamos utilizado o Claude como apoio para acelerar a criação da estrutura inicial, incluindo os carregadores, a lógica de chunking e a integração com FAISS, realizamos uma análise conjunta e detalhada da implementação. Revisamos linha por linha, principalmente a lógica responsável pela detecção e tratamento de dados sensíveis.

Por fim, realizamos testes manuais em conjunto, utilizando consultas de exemplo para validar o comportamento do sistema. Esses testes permitiram confirmar, na prática, que os filtros baseados em metadados, como `state` e `doc_type`, estavam sendo aplicados corretamente e retornando os documentos esperados.

**Entregamos hoje:**

* [ ] Clonagem e configuração do repositório no Colab.
* [ ] Execução do pipeline de ingestão com sucesso.
* [ ] Processamento de 217 documentos de fontes heterogêneas.
* [ ] Geração de 251 chunks.
* [ ] Definição dos arquivos CSV que permanecerão fora do índice vetorial.
* [ ] Revisão conjunta da lógica de detecção de dados sensíveis.
* [ ] Validação dos filtros por metadados (`state` e `doc_type`) por meio de testes manuais.

**Ficou pendente:**

* [ ] Continuar a validação do pipeline com outros cenários de consulta.
* [ ] Avaliar possíveis ajustes na estratégia de chunking e recuperação, caso sejam identificados problemas nos próximos testes.

**Bloqueios em aberto:**

* [ ] Nenhum bloqueio técnico identificado até o momento.

**Próximo passo (início do encontro 2):**

* [ ] Dar continuidade aos testes do sistema de busca.
* [ ] Avaliar a qualidade e relevância dos resultados recuperados.
* [ ] Verificar se os filtros e metadados continuam funcionando corretamente em diferentes cenários.
* [ ] Avançar para as próximas etapas da implementação do pipeline RAG.

**Uso de assistentes de IA:**

* Utilizamos o Claude como ferramenta de apoio para acelerar a criação da estrutura inicial do projeto, principalmente nos carregadores, na lógica de chunking e na integração com FAISS.
* Todo o código gerado com auxílio da IA foi analisado, discutido e revisado em conjunto antes de ser utilizado.
* A lógica de detecção de dados sensíveis recebeu revisão manual detalhada, garantindo que as decisões técnicas fossem compreendidas e validadas pela equipe.


## Encontro 2 - AAAA-MM-DD

**Etapa:** 2 - Busca híbrida e filtragem por metadados

### Relato individual - [Nome do Integrante 1]

### Relato individual - [Nome do Integrante 2]

### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**
-

**Ficou pendente:**
-

**Bloqueios em aberto:**
-

**Próximo passo (início do encontro 3):**
-

**Uso de assistentes de IA:**
-

---

## Encontro 3 - AAAA-MM-DD

**Etapa:** 3 - Síntese estruturada, evidência e guardrails de LGPD

### Relato individual - [Nome do Integrante 1]

### Relato individual - [Nome do Integrante 2]

### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**
-

**Ficou pendente:**
-

**Bloqueios em aberto:**
-

**Próximo passo (início do encontro 4):**
-

**Uso de assistentes de IA:**
-

---

## Encontro 4 - AAAA-MM-DD

**Etapa:** 4 - Avaliação (RAG Triad), interface e relatório

### Relato individual - [Nome do Integrante 1]

### Relato individual - [Nome do Integrante 2]

### Resumo do dia (escrito em conjunto)

**Entregamos hoje:**
-

**Ficou pendente:**
-

**Bloqueios em aberto:**
-

**Preparação para o Demo Day:**
-

**Uso de assistentes de IA:**
-

---

*TIC em Trilhas · PUC-Rio · Instituto ECOA · MCTI Futuro · Softex*
