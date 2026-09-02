# Análise e Fluxo de Dados: Modelagem Multidimensional e ETL Incremental sobre o AdventureWorks

> **Artigo acadêmico — padrão Unisales**
> Repositório: <https://github.com/ruan-slv/projeto_analise_fluxo_dados>

---

## Resumo

Este trabalho apresenta o projeto de um Data Warehouse (DW) em PostgreSQL a partir do banco
transacional (OLTP) AdventureWorks 2016, aplicando os conceitos de **modelagem
multidimensional** (Star Schema) e de **pipeline de ETL incremental** implementado em
Python. São definidos **dez indicadores de negócio (KPIs)** que suportam a análise de
vendas, e demonstrado que a carga incremental processa apenas registros novos ou
alterados (com base na coluna `modifieddate` e em *watermarks*), garantindo
idempotência e baixo custo de processamento. O artigo descreve a análise do modelo
OLTP, a proposta do modelo estrela, o dicionário de dados, a estratégia de ETL e as
consultas SQL que comprovam o cálculo dos indicadores.

**Palavras-chave:** Data Warehouse; Star Schema; ETL incremental; OLAP; Business
Intelligence; PostgreSQL; AdventureWorks.

---

## 1. Introdução

A quantidade de dados gerada por sistemas transacionais (OLTP) cresce de forma
contínua. Esses sistemas, porém, são otimizados para operações de inserção, atualização
e exclusão (CRUD) de alto volume e baixo latência — não para consultas analíticas
complexas que agregam grandes volumes de histórico. Consultas analíticas pesadas
executadas diretamente sobre o OLTP degradam o desempenho dos processos operacionais.

Para resolver essa tensão, a arquitetura clássica separa o mundo operacional (OLTP) do
mundo analítico (OLAP) através de um **Data Warehouse**: um repositório integrado,
historizado, estável e não volátil, modelado para leitura e análise (Inmon, 2005). A
população do DW é feita por um pipeline **ETL** (Extract, Transform, Load).

O objetivo deste trabalho é exercitar, na prática, essa arquitetura utilizando o banco de
exemplo **AdventureWorks 2016** (Microsoft). Especificamente, o grupo: (i) avalia o
modelo relacional OLTP de origem; (ii) elabora dez indicadores relevantes para o
negócio; (iii) projeta um modelo multidimensional (Star Schema); (iv) implementa o DW no
PostgreSQL; (v) constrói uma ETL **incremental** em Python que processa apenas dados
novos ou alterados; e (vi) implementa as consultas SQL que comprovam o cálculo dos
indicadores.

O repositório completo do projeto — scripts SQL, pipeline Python, diagramas e este
artigo — está disponível em
<https://github.com/ruan-slv/projeto_analise_fluxo_dados>.

### 1.1 Objetivos

**Objetivo geral:** projetar e implementar um Data Warehouse (Star Schema) e um pipeline
de ETL incremental em Python/PostgreSQL a partir do AdventureWorks 2016, suportando dez
KPIs de vendas.

**Objetivos específicos:**
1. Analisar o modelo relacional (OLTP) do AdventureWorks.
2. Definir dez indicadores (KPIs) relevantes para o negócio.
3. Projetar o modelo multidimensional (Star Schema).
4. Implementar o DW no PostgreSQL.
5. Construir a ETL incremental em Python (apenas dados novos/alterados).
6. Implementar as consultas SQL que comprovam os KPIs.

### 1.2 Metodologia

Adotou-se uma abordagem **descrente (top-down)** combinada com prototipagem: partiu-se
dos requisitos analíticos (KPIs) para derivar as dimensões e o fato, e iterou-se a
implementação validando cada etapa contra a fonte. A fonte AdventureWorks 2016 foi
restaurada em uma instância PostgreSQL (o backup nativo `.bak` do SQL Server não é
compatível com PostgreSQL; utilizou-se um dump PostgreSQL equivalente). O DW foi
implementado no PostgreSQL e a ETL em Python (`psycopg2`).

---

## 2. Fundamentação Teórica

### 2.1 OLTP vs OLAP

Sistemas **OLTP** (Online Transaction Processing) suportam transações curtas, de alto
volume e baixa latência, com normalização (3FN) para minimizar redundância e garantir
consistência. Sistemas **OLAP** (Online Analytical Processing) suportam consultas
analíticas complexas sobre grandes volumes históricos, priorizando a leitura e
agregação. A tabela 1 resume as diferenças.

**Tabela 1 — OLTP × OLAP**

| Critério | OLTP | OLAP |
|---|---|---|
| Foco | Transações (CRUD) | Análise/consultas |
| Volume de dados | Atual | Histórico (grande) |
| Modelagem | Relacional normalizada | Multidimensional (estrela) |
| Usuários | Operacionais | Analistas/Gestores |
| Latência | Baixa (ms) | Alta (agregações) |
| Operações | INSERT/UPDATE/DELETE | SELECT agregado |

### 2.2 Modelagem Multidimensional (Star Schema)

A **modelagem multidimensional** organiza os dados em **fatos** (métricas numéricas) e
**dimensões** (contexto descritivo). O **Star Schema** (modelo estrela), proposto por
Inmon e popularizado por Kimball, é a estrutura mais comum: uma tabela de fato central
circundada por tabelas de dimensão, ligadas por chaves estrangeiras (Kimball; Ross,
2013).

- **Fato:** tabela contendo as medidas (ex.: quantidade, receita) e as chaves que
  apontam para as dimensões. O **grão** do fato (a menor unidade de negócio de uma
  linha) é a decisão mais importante do design.
- **Dimensão:** tabela descritiva (ex.: produto, cliente, tempo, território) que
  fornece o "contexto" para filtrar e agrupar as análises.
- **Chave substituta (surrogate key):** chave gerada no DW (ex.: `1..N`),
  independente da chave do OLTP, que desacopla a carga e simplifica a modelagem.

O Star Schema favorega o desempenho analítico (menos *joins*, cardinalidade baixa nas
dimensões) e é nativamente suportado por ferramentas de BI e por agregações SQL.

### 2.3 ETL e carga incremental

O processo **ETL** move dados da origem (Extract), aplica regras de negócio e
transformações (Transform) e grava no destino (Load). Uma **carga incremental** não
recarrega o histórico a cada execução: identifica apenas os registros **novos ou
alterados** desde a última carga.

A AdventureWorks expõe, em praticamente todas as tabelas, a coluna
`modifieddate` (timestamp da última modificação). Essa coluna é o mecanismo natural de
*Change Data Capture* (CDC) para o nosso caso. A estratégia adotada:

1. **Watermark:** para cada tabela de origem, guarda-se o maior `modifieddate` já
   processado em `dw.etl_watermark`. Na primeira carga o watermark é o epoch (leitura
   completa).
2. **Delta:** selecionam-se as linhas com `modifieddate >= watermark` (usa-se `>=` e
   não `>` porque existem *ties* no timestamp — várias linhas podem compartilhar o
   mesmo instante; com `>=` + UPSERT a carga permanece **idempotente** e nenhuma
   alteração é perdida).
3. **Upsert:** as linhas são gravadas com `INSERT ... ON CONFLICT DO UPDATE`, de modo
   que reprocessar o mesmo intervalo não crie duplicatas.
4. **Avanço do watermark:** ao final, o watermark é atualizado para o maior
   `modifieddate` encontrado.

**Complexidade:** a carga incremental lê `O(delta)` linhas em vez de `O(N)` (todo o
histórico). Em execuções subsequentes, quando o sistema está estável, o delta é
próximo de zero, reduzindo drasticamente I/O e tempo de processamento.

---

## 3. Desenvolvimento

### 3.1 Análise do modelo OLTP AdventureWorks

O AdventureWorks 2016 modela uma empresa de bicicletas. Os schemas relevantes para o
nosso DW são:

- `sales` — pedidos (`salesorderheader`, `salesorderdetail`), clientes (`customer`),
  vendedores (`salesperson`), territórios (`salesterritory`), moedas (`currency`,
  `currencyrate`), promoções (`specialoffer`), cartões (`creditcard`).
- `person` — pessoas (`person`), estados/países (`stateprovince`, `countryregion`).
- `production` — produtos (`product`, `productsubcategory`, `productcategory`).
- `humanresources` — funcionários (`employee`).

Observações importantes da análise:
- O **grão natural** de uma análise de vendas é a **linha do pedido**
  (`salesorderdetail`), que referencia o cabeçalho (`salesorderheader`) por
  `salesorderid`.
- `sales.customer` unifica dois tipos de cliente: **pessoas** (`personid`) e
  **lojas** (`storeid`).
- `sales.specialofferid = 1` é o *sentinela* "No Discount" (sem promoção); promoções
  reais têm `discountpct > 0`.
- `sales.salespersonid` pode ser `NULL` (pedidos online sem vendedor) — cerca de
  60.398 linhas.
- `sales.currencyrateid` liga o pedido à moeda via `currencyrate`
  (`fromcurrencycode='USD'`, `tocurrencycode` = moeda do pedido).

### 3.2 Definição dos 10 Indicadores (KPIs)

**Tabela 2 — KPIs implementados (arquivo `kpis.sql`)**

| # | Indicador | Descrição |
|---|---|---|
| 1 | Receita Total | Soma de `LineTotal` (receita bruta). |
| 2 | Ticket Médio | Receita total / nº de pedidos. |
| 3 | Itens Vendidos | Soma de `OrderQty`. |
| 4 | Vendas por Mês | Série temporal (ano/mês) de receita e itens. |
| 5 | Top 10 Produtos | Produtos com maior receita. |
| 6 | Vendas por Território | Receita e pedidos por território. |
| 7 | Top 5 Vendedores | Vendedores com maior receita. |
| 8 | Online × Loja | % de receita e itens por canal. |
| 9 | Com × Sem Promoção | Receita por presença de desconto real. |
| 10 | Crescimento Anual (YoY) | Variação % da receita ano a ano. |

### 3.3 Modelo Multidimensional (Star Schema)

O DW adota **um fato** (`fct_vendas`, grão = linha do pedido) e **sete dimensões**
(`dim_data`, `dim_produto`, `dim_cliente`, `dim_vendedor`, `dim_territorio`,
`dim_moeda`, `dim_promocao`). O diagrama está em `star_schema.svg` (visual) e
`star_schema.puml` (fonte PlantUML).

**Justificativas de modelagem:**
- **Grão = linha do pedido:** permite análises por produto, cliente, território,
  vendedor, moeda, promoção e tempo sem perda de granularidade.
- **Chaves substitutas** (`*_id`, `INT IDENTITY`) desacoplam o DW do OLTP e
  simplificam `joins`.
- **`dim_cliente` unifica pessoa e loja** (via `tipo_cliente`), refletindo a
  estrutura de `sales.customer`.
- **`dim_data`** cobrindo 2010–2015 (dados vão de 2011 a 2014) com atributos de
  tempo prontos para *slicers*.
- **Moeda resolvida no fato** (`moeda_id`) via `currencyrateid → tocurrencycode`
  (default `USD`), permitindo análises por moeda.
- **Promoção** mantida como dimensão para suportar o KPI 09 (desconto real).

### 3.4 Implementação do Data Warehouse no PostgreSQL

O schema (`etl/schema_dw.sql`) cria o schema `dw` com as oito tabelas e índices nas
chaves estrangeiras do fato (para acelerar as agregações OLAP). A dimensão de tempo é
semeada por `etl/seed_dim_data.sql` (série de 2010 a 2015). O banco de destino é
`dw_adventureworks`.

### 3.5 Pipeline de ETL Incremental (Python)

Implementado em `etl/pipeline.py` (orquestração), `etl/etl_core.py` (watermarks e
upsert) e `etl/db.py` (conexão). A ordem de carga respeita as dependências:

```
dim_data (seed) → dim_produto, dim_cliente, dim_vendedor,
dim_territorio, dim_moeda, dim_promocao → fct_vendas
```

Cada dimensão lê o **delta** (`modifieddate >= watermark`) da fonte e grava via
**UPSERT** (`execute_values` + `ON CONFLICT DO UPDATE`, em páginas de 2000 linhas para
eficiência). O fato resolve as chaves substitutas das dimensões em Python (dicionários
`oltp_id → surrogate_id`) e usa `GREATEST(detail.modifieddate, header.modifieddate)`
como watermark, de modo que alterações no cabeçalho (status, moeda) também atualizam o
fato.

**Resultados de execução:**
- Carga inicial (full): **18,4 s** para 121.317 linhas de fato + 20.682 linhas de
  dimensões.
- Carga incremental (sistema estável): **~1 s**, processando apenas o delta.
- **0 duplicatas** e **0 FKs órfãs** no fato após execuções repetidas (idempotência).

### 3.6 Comprovação dos Indicadores (SQL)

O arquivo `kpis.sql` contém as dez consultas. Exemplos representativos:

```sql
-- KPI 01 — Receita Total
SELECT 'KPI01_ReceitaTotal' AS kpi,
       SUM(f.subtotal_linha)::numeric(15,2) AS valor
FROM dw.fct_vendas f;

-- KPI 05 — Top 10 Produtos por Receita
SELECT dp.nome AS produto, dp.categoria_nome,
       SUM(f.subtotal_linha)::numeric(15,2) AS receita,
       SUM(f.quantidade) AS itens
FROM dw.fct_vendas f
JOIN dw.dim_produto dp ON f.produto_id = dp.produto_id
GROUP BY dp.nome, dp.categoria_nome
ORDER BY receita DESC
LIMIT 10;

-- KPI 10 — Crescimento Anual (YoY)
WITH anual AS (
    SELECT dd.ano, SUM(f.subtotal_linha)::numeric(15,2) AS receita
    FROM dw.fct_vendas f
    JOIN dw.dim_data dd ON f.data_id = dd.data_id
    GROUP BY dd.ano
)
SELECT a.ano, a.receita,
       LAG(a.receita) OVER (ORDER BY a.ano) AS receita_anterior,
       ROUND(100.0 * (a.receita - LAG(a.receita) OVER (ORDER BY a.ano))
             / NULLIF(LAG(a.receita) OVER (ORDER BY a.ano),0), 2) AS var_pct
FROM anual a
ORDER BY a.ano;
```

**Saídas observadas (amostra):** Receita Total = **109.846.381,40**; Ticket Médio =
**3.491,07**; Itens = **274.914**; Top produto = *Mountain-200 Black, 38* (4.400.592,80);
Top território = *Southwest* (24.184.609,60); Top vendedor = *Linda Mitchell*
(10.367.007,43); Receita online = **26,73%**; Sem promoção = **93,20%**; Crescimento
2012 = **+165,19%**, 2013 = **+30,12%**, 2014 = **−54,02%** (ano parcial).

### 3.7 Dicionário de Dados

O dicionário completo (colunas, tipos, chaves e descrições das oito tabelas) está em
`dicionario_de_dados.md`.

---

## 4. Considerações Finais

Este trabalho demonstrou, de ponta a ponta, o fluxo de dados de um sistema OLTP para um
Data Warehouse OLAP. A modelagem em Star Schema, com chaves substitutas e um fato de
grão fino (linha do pedido), permitiu expressar os dez KPIs com consultas SQL simples e
eficientes, sem comprometer o sistema transacional de origem.

A **ETL incremental** baseada em `modifieddate` + *watermarks* + UPSERT atendeu ao
requisito obrigatório de processar apenas dados novos ou alterados, mantendo a carga
**idempotente** (reexecuções não criam duplicatas) e reduzindo o custo de processamento
de `O(N)` para `O(delta)`. O teste automatizado (`etl/test_incremental.py`) comprovou
que uma alteração na fonte é propagada ao DW em uma única execução incremental, com
avanço correto dos watermarks e sem duplicatas.

Como limitação, o AdventureWorks é um conjunto de dados estático (histórico de 2011 a
2014), de modo que o "incremental" é demonstrado artificialmente ao alterar registros na
fonte. Em um cenário real, a mesma estratégia se aplicaria a feeds contínuos. Como
trabalho futuro, sugere-se a adoção de CDC nativo (ex.: `logical replication` do
PostgreSQL), a criação de *aggregate tables* (cubos) para KPIs de alto volume e a
extensão do DW a outros domínios do AdventureWorks (estoque, suprimentos, recursos
humanos).

---

## 5. Referências

- INMON, W. H. **Building the Data Warehouse**. 5. ed. Wiley, 2005.
- KIMBALL, R.; ROSS, M. **The Data Warehouse Toolkit: The Definitive Guide to
  Dimensional Modeling**. 3. ed. Wiley, 2013.
- MICROSOFT. **AdventureWorks 2016 — Database documentation.** Microsoft Learn.
  Disponível em: https://learn.microsoft.com/pt-br/sql/samples/adventureworks-install-configure.
- WIKIPEDIA. **Star schema.** Disponível em: https://en.wikipedia.org/wiki/Star_schema.
- UNIVERSIDADE SALESBERRY. **Guia de Elaboração e Normalização de Trabalhos Acadêmicos
  e de Pesquisa.** Unisales, 2024.
- REPOSITÓRIO DO PROJETO. Disponível em:
  https://github.com/ruan-slv/projeto_analise_fluxo_dados.
