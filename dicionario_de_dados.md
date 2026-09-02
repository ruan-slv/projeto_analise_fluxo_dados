# Dicionário de Dados — Data Warehouse (Star Schema)

> Banco: `dw_adventureworks` · Schema: `dw` · Fonte OLTP: AdventureWorks 2016
> Convenções: `PK` = chave primária · `UK` = única · `FK` = estrangeira · `NN` = não nulo
> Chaves substitutas (`*_id`) são `INT GENERATED ALWAYS AS IDENTITY` (1..N), desacopladas do OLTP.

---

## 1. Tabela de Fato

### `dw.fct_vendas` — Vendas (grão: linha do pedido)

| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `fato_id` | BIGINT | PK | Identificador interno do fato (auto-incremento). |
| `data_id` | INT | FK | → `dim_data`. Data da compra (OrderDate). |
| `produto_id` | INT | FK | → `dim_produto`. Item vendido. |
| `cliente_id` | INT | FK | → `dim_cliente`. Cliente (pessoa ou loja). |
| `vendedor_id` | INT | FK | → `dim_vendedor`. Vendedor (NULL p/ pedidos online sem SP). |
| `territorio_id` | INT | FK | → `dim_territorio`. Território do pedido. |
| `moeda_id` | INT | FK | → `dim_moeda`. Moeda do pedido (via CurrencyRateId). |
| `promocao_id` | INT | FK | → `dim_promocao`. Oferta especial (1 = "No Discount"). |
| `sales_order_id` | INT | — | FK lógica p/ `SalesOrderHeader` (OLTP). |
| `line_id` | INT | — | `SalesOrderDetailId` (OLTP). |
| `quantidade` | INT | NN | `OrderQty` — unidades na linha. |
| `preco_unit` | NUMERIC(19,4) | NN | `UnitPrice` — preço unitário original. |
| `desconto_unit` | NUMERIC(19,4) | NN | `UnitPriceDiscount` — desconto aplicado. |
| `subtotal_linha` | NUMERIC(23,6) | NN | `LineTotal` — total da linha (principal medida). |
| `online` | BOOLEAN | — | `OnlineOrderFlag` — pedido online vs loja. |
| `status_pedido` | SMALLINT | — | `Status` do pedido (0..5). |
| `total_pedido` | NUMERIC(19,4) | — | `TotalDue` — total do pedido (header). |
| `taxas` | NUMERIC(19,4) | — | `TaxAmt` (header). |
| `frete` | NUMERIC(19,4) | — | `Freight` (header). |
| `dt_pedido` | DATE | — | `OrderDate` (redundante p/ performance). |
| `oltp_modified` | TIMESTAMP | NN | `GREATEST(detail.modified, header.modified)` — controle incremental. |

**Restrição:** `UNIQUE (sales_order_id, line_id)` — garante idempotência do UPSERT.

---

## 2. Dimensões

### `dw.dim_data` — Tempo (grão: dia)
| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `data_id` | INT | PK | Chave substituta. |
| `data` | DATE | UK | Data (2010-01-01 a 2015-12-31). |
| `ano` | INT | NN | Ano. |
| `trimestre` | INT | NN | Trimestre (1-4). |
| `mes` | INT | NN | Mês (1-12). |
| `mes_nome` | VARCHAR(3) | NN | Nome do mês (jan, fev, ...). |
| `semestre` | INT | NN | Semestre (1-2). |
| `dia_semana` | INT | NN | Dia da semana (1=seg a 7=dom, ISO). |
| `dia_semana_nome` | VARCHAR(10) | NN | Nome do dia. |
| `dia_do_ano` | INT | NN | Dia do ano (1-366). |
| `dia_do_mes` | INT | NN | Dia do mês (1-31). |
| `semana_ano` | INT | NN | Semana do ano (ISO). |
| `fim_de_semana` | BOOLEAN | NN | true se sáb/dom. |
| `flag_mes` | BOOLEAN | NN | true se 1º dia do mês. |

### `dw.dim_produto` — Produto (grão: item)
| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `produto_id` | INT | PK | Chave substituta. |
| `product_oltp_id` | INT | UK | `Production.Product.ProductID`. |
| `nome` | VARCHAR(50) | NN | Nome do produto. |
| `numero` | VARCHAR(25) | — | Código (ProductNumber). |
| `cor` | VARCHAR(15) | — | Cor. |
| `tamanho` | VARCHAR(50) | — | Tamanho. |
| `classe` | CHAR(1) | — | Classe (1-3). |
| `estilo` | CHAR(2) | — | Estilo (M/T/U). |
| `fabrica` | BOOLEAN | — | MakeFlag. |
| `custo_padrao` | NUMERIC(19,4) | — | StandardCost. |
| `preco_lista` | NUMERIC(19,4) | — | ListPrice. |
| `peso` | NUMERIC(8,2) | — | Peso. |
| `subcategoria_id` | INT | — | FK lógica p/ subcategoria. |
| `categoria_id` | INT | — | FK lógica p/ categoria. |
| `subcategoria_nome` | VARCHAR(50) | — | Nome da subcategoria. |
| `categoria_nome` | VARCHAR(50) | — | Nome da categoria. |
| `dt_venda_inicio` | DATE | — | SellStartDate. |
| `dt_venda_fim` | DATE | — | SellEndDate. |

### `dw.dim_cliente` — Cliente (grão: customer)
| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `cliente_id` | INT | PK | Chave substituta. |
| `customer_oltp_id` | INT | UK | `Sales.Customer.CustomerID`. |
| `tipo_cliente` | VARCHAR(10) | NN | 'Individual' ou 'Loja'. |
| `nome` | VARCHAR(110) | — | Nome (pessoa) ou nome da loja. |
| `sobrenome` | VARCHAR(50) | — | Sobrenome. |
| `titulo` | VARCHAR(50) | — | Título (Mr., Ms., ...). |
| `email_promocao` | INT | — | 0/1 — opt-in de e-mail. |
| `loja_nome` | VARCHAR(50) | — | Nome da loja (se for store). |
| `territorio_id` | INT | FK | → `dim_territorio`. |
| `account_number` | VARCHAR(15) | — | AccountNumber. |

### `dw.dim_vendedor` — Vendedor (grão: salesperson)
| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `vendedor_id` | INT | PK | Chave substituta. |
| `salesperson_oltp` | INT | UK | `Sales.SalesPerson.BusinessEntityID`. |
| `nome` | VARCHAR(110) | — | Nome completo. |
| `cargo` | VARCHAR(50) | — | JobTitle. |
| `territorio_id` | INT | FK | → `dim_territorio`. |
| `quota` | NUMERIC(19,4) | — | SalesQuota. |
| `bonus` | NUMERIC(19,4) | — | Bonus. |
| `comissao` | NUMERIC(5,2) | — | CommissionPct. |

### `dw.dim_territorio` — Território (grão: territory)
| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `territory_id` | INT | PK | Chave substituta. |
| `territory_oltp_id` | INT | UK | `Sales.SalesTerritory.TerritoryID`. |
| `nome` | VARCHAR(50) | NN | Nome do território. |
| `grupo` | VARCHAR(50) | — | Grupo (North America/Europe/Pacific). |
| `codigo_pais` | CHAR(3) | — | CountryRegionCode. |
| `nome_pais` | VARCHAR(50) | — | Nome do país. |
| `codigo_estado` | CHAR(3) | — | StateProvinceCode. |
| `nome_estado` | VARCHAR(50) | — | Nome do estado/província. |
| `vendas_ano` | NUMERIC(19,4) | — | SalesYTD. |
| `vendas_ano_ant` | NUMERIC(19,4) | — | SalesLastYear. |
| `custo_ano` | NUMERIC(19,4) | — | CostYTD. |
| `custo_ano_ant` | NUMERIC(19,4) | — | CostLastYear. |

### `dw.dim_moeda` — Moeda (grão: currency code)
| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `moeda_id` | INT | PK | Chave substituta. |
| `currency_code` | CHAR(3) | UK | `Sales.Currency.CurrencyCode`. |
| `nome_moeda` | VARCHAR(50) | NN | Nome da moeda. |
| `taxa_media` | NUMERIC(18,6) | — | Taxa média p/ USD (CurrencyRate). |
| `taxa_fim_dia` | NUMERIC(18,6) | — | Taxa de fim de dia p/ USD. |

### `dw.dim_promocao` — Promoção (grão: special offer)
| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `promocao_id` | INT | PK | Chave substituta. |
| `specialoffer_oltp` | INT | UK | `Sales.SpecialOffer.SpecialOfferID`. |
| `descricao` | VARCHAR(50) | NN | Descrição. |
| `tipo` | VARCHAR(50) | — | Tipo (No Discount/Volume/...). |
| `categoria` | VARCHAR(50) | — | Categoria (Reseller/Customer). |
| `desconto_pct` | NUMERIC(5,2) | — | Desconto (%). |
| `qty_minima` | INT | — | Quantidade mínima. |
| `qty_maxima` | INT | — | Quantidade máxima. |
| `dt_inicio` | DATE | — | Data de início. |
| `dt_fim` | DATE | — | Data de fim. |

---

## 3. Controle do ETL

### `dw.etl_watermark` — Watermarks incrementais
| Coluna | Tipo | Chave | Descrição |
|---|---|---|---|
| `tabela_oltp` | VARCHAR(80) | PK | Nome da tabela de origem (OLTP). |
| `last_modified` | TIMESTAMP | NN | Maior `modifieddate` já processado. |
| `last_run` | TIMESTAMP | NN | Data/hora da última carga. |
| `rows_loaded` | BIGINT | NN | Linhas carregadas na última execução. |
