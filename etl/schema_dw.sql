-- ============================================================================
--  DATA WAREHOUSE — OLAP (Star Schema)
--  Base: AdventureWorks 2016 (OLTP)  ->  PostgreSQL (DW)
-- ----------------------------------------------------------------------------
--  Modelo Estrela (Star Schema):
--    * 1 tabela FATO  : fct_vendas      (grão = linha de pedido)
--    * 7 tabelas DIM  : dim_data, dim_produto, dim_cliente, dim_vendedor,
--                       dim_territorio, dim_moeda, dim_promocao
--  Decisões de modelagem:
--    * Convensão "surrogate keys" (chaves substitutas) INT geradas no DW
--      (1..N) para desacoplar do OLTP.
--    * dim_data cobrindo 2010-2015 (dados OLTP vão de 2011 a 2014).
--    * dim_cliente unifica Pessoa (cliente individual) e Loja (store).
--    * A medida "quantidade" e valores monetários ficam no FATO (facts).
-- ============================================================================

-- (Re)cria o schema dw caso já exista ----------------------------------------
DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;

-- ----------------------------------------------------------------------------
-- DIM_DATA — dimensão de tempo (gerada, não vem do OLTP)
-- ----------------------------------------------------------------------------
CREATE TABLE dw.dim_data (
    data_id        INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data           DATE NOT NULL UNIQUE,
    ano            INT  NOT NULL,
    trimestre      INT  NOT NULL,
    mes            INT  NOT NULL,
    mes_nome       VARCHAR(3) NOT NULL,   -- 'jan','fev',...
    semestre       INT  NOT NULL,
    dia_semana     INT  NOT NULL,         -- 1=seg .. 7=dom
    dia_semana_nome VARCHAR(10) NOT NULL,
    dia_do_ano     INT  NOT NULL,
    dia_do_mes     INT  NOT NULL,
    semana_ano     INT  NOT NULL,         -- número da semana (ISO)
    fim_de_semana  BOOLEAN NOT NULL,
    flag_mes       BOOLEAN NOT NULL       -- 1º dia do mês (útil p/ slicers)
);
COMMENT ON TABLE dw.dim_data IS 'Dimensão de tempo (grão = dia), gerada para 2010-2015.';

-- ----------------------------------------------------------------------------
-- DIM_PRODUTO — hierarquia Categoria > Subcategoria > Produto
-- ----------------------------------------------------------------------------
CREATE TABLE dw.dim_produto (
    produto_id          INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_oltp_id     INT NOT NULL UNIQUE,   -- FK p/ Production.Product
    nome                VARCHAR(50)  NOT NULL,
    numero              VARCHAR(25),
    cor                 VARCHAR(15),
    tamanho             VARCHAR(50),
    classe              CHAR(1),              -- '1'..'3'
    estilo              CHAR(2),              -- 'M','T','U'
    fabrica             BOOLEAN,
    custo_padrao        NUMERIC(19,4),
    preco_lista         NUMERIC(19,4),
    peso                NUMERIC(8,2),
    subcategoria_id     INT,                  -- FK p/ dim_produto.subcategoria
    categoria_id        INT,
    subcategoria_nome   VARCHAR(50),
    categoria_nome      VARCHAR(50),
    dt_venda_inicio     DATE,
    dt_venda_fim        DATE
);
COMMENT ON TABLE dw.dim_produto IS 'Dimensão Produto (grão = item) com hierarquia de categoria.';

-- ----------------------------------------------------------------------------
-- DIM_CLIENTE — unifica Pessoa (individual) e Loja (store)
-- ----------------------------------------------------------------------------
CREATE TABLE dw.dim_cliente (
    cliente_id        INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_oltp_id  INT NOT NULL UNIQUE,    -- FK p/ Sales.Customer
    tipo_cliente      VARCHAR(10) NOT NULL,   -- 'Individual' | 'Loja'
    nome              VARCHAR(110),           -- nome do cliente (pessoa ou loja)
    sobrenome         VARCHAR(50),
    titulo            VARCHAR(50),
    email_promocao    INT,                    -- 0/1
    loja_nome         VARCHAR(50),
    territorio_id     INT,
    account_number    VARCHAR(15)
);
COMMENT ON TABLE dw.dim_cliente IS 'Dimensão Cliente (grão = customer), unificando pessoa e loja.';

-- ----------------------------------------------------------------------------
-- DIM_VENDEDOR — SalesPerson + Employee
-- ----------------------------------------------------------------------------
CREATE TABLE dw.dim_vendedor (
    vendedor_id       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    salesperson_oltp  INT NOT NULL UNIQUE,    -- FK p/ Sales.SalesPerson
    nome              VARCHAR(110),
    cargo             VARCHAR(50),
    territorio_id     INT,
    quota            NUMERIC(19,4),
    bonus            NUMERIC(19,4),
    comissao         NUMERIC(5,2)
);
COMMENT ON TABLE dw.dim_vendedor IS 'Dimensão Vendedor (grão = salesperson).';

-- ----------------------------------------------------------------------------
-- DIM_TERRITORIO — SalesTerritory (+ estado/país)
-- ----------------------------------------------------------------------------
CREATE TABLE dw.dim_territorio (
    territory_id       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    territory_oltp_id  INT NOT NULL UNIQUE,   -- FK p/ Sales.SalesTerritory
    nome               VARCHAR(50) NOT NULL,
    grupo              VARCHAR(50),           -- 'North America'|'Europe'
    codigo_pais        CHAR(3),
    nome_pais         VARCHAR(50),
    codigo_estado     CHAR(3),
    nome_estado       VARCHAR(50),
    vendas_ano       NUMERIC(19,4),
    vendas_ano_ant   NUMERIC(19,4),
    custo_ano        NUMERIC(19,4),
    custo_ano_ant    NUMERIC(19,4)
);
COMMENT ON TABLE dw.dim_territorio IS 'Dimensão Território (grão = territory).';

-- ----------------------------------------------------------------------------
-- DIM_MOEDA — Currency + (opcional) taxa de câmbio do dia
-- ----------------------------------------------------------------------------
CREATE TABLE dw.dim_moeda (
    moeda_id         INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    currency_code    CHAR(3) NOT NULL UNIQUE, -- FK p/ Sales.Currency
    nome_moeda       VARCHAR(50) NOT NULL,
    taxa_media       NUMERIC(18,6),           -- taxa p/ USD (CurrencyRate)
    taxa_fim_dia     NUMERIC(18,6)
);
COMMENT ON TABLE dw.dim_moeda IS 'Dimensão Moeda (grão = currency code).';

-- ----------------------------------------------------------------------------
-- DIM_PROMOCAO — SpecialOffer (aplicada na linha do pedido)
-- ----------------------------------------------------------------------------
CREATE TABLE dw.dim_promocao (
    promocao_id       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    specialoffer_oltp INT NOT NULL UNIQUE,    -- FK p/ Sales.SpecialOffer
    descricao         VARCHAR(50) NOT NULL,
    tipo              VARCHAR(50),
    categoria         VARCHAR(50),
    desconto_pct      NUMERIC(5,2),
    qty_minima       INT,
    qty_maxima       INT,
    dt_inicio        DATE,
    dt_fim           DATE
);
COMMENT ON TABLE dw.dim_promocao IS 'Dimensão Promoção (grão = special offer).';

-- ----------------------------------------------------------------------------
-- FCT_VENDAS — fato transacional (grão = linha de pedido)
-- ----------------------------------------------------------------------------
CREATE TABLE dw.fct_vendas (
    fato_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- chaves estrangeiras p/ dimensões
    data_id         INT NOT NULL REFERENCES dw.dim_data(data_id),
    produto_id      INT NOT NULL REFERENCES dw.dim_produto(produto_id),
    cliente_id      INT NOT NULL REFERENCES dw.dim_cliente(cliente_id),
    vendedor_id     INT REFERENCES dw.dim_vendedor(vendedor_id),
    territorio_id   INT REFERENCES dw.dim_territorio(territory_id),
    moeda_id        INT REFERENCES dw.dim_moeda(moeda_id),
    promocao_id     INT REFERENCES dw.dim_promocao(promocao_id),
    -- identificadores OLTP (para rastreamento / incremental)
    sales_order_id  INT NOT NULL,             -- FK p/ SalesOrderHeader
    line_id         INT NOT NULL,             -- SalesOrderDetailId
    -- medidas (fatos)
    quantidade      INT  NOT NULL,            -- OrderQty
    preco_unit      NUMERIC(19,4) NOT NULL,   -- UnitPrice
    desconto_unit   NUMERIC(19,4) NOT NULL,   -- UnitPriceDiscount
    subtotal_linha  NUMERIC(23,6) NOT NULL,   -- LineTotal
    -- flags / atributos do pedido (header)
    online          BOOLEAN,
    status_pedido   SMALLINT,
    total_pedido    NUMERIC(19,4),
    taxas          NUMERIC(19,4),
    frete          NUMERIC(19,4),
    dt_pedido      DATE,                      -- OrderDate (redundante p/ performance)
    -- controle incremental
    oltp_modified  TIMESTAMP NOT NULL,        -- último modifieddate visto no OLTP
    UNIQUE (sales_order_id, line_id)
);
COMMENT ON TABLE dw.fct_vendas IS 'Fato de Vendas (grão = linha do pedido).';

-- Índices de performance para as consultas OLAP (KPIs) -----------------------
CREATE INDEX idx_fct_data      ON dw.fct_vendas(data_id);
CREATE INDEX idx_fct_produto   ON dw.fct_vendas(produto_id);
CREATE INDEX idx_fct_cliente   ON dw.fct_vendas(cliente_id);
CREATE INDEX idx_fct_vendedor  ON dw.fct_vendas(vendedor_id);
CREATE INDEX idx_fct_territ    ON dw.fct_vendas(territorio_id);
CREATE INDEX idx_fct_promocao  ON dw.fct_vendas(promocao_id);
CREATE INDEX idx_fct_moeda     ON dw.fct_vendas(moeda_id);
CREATE INDEX idx_fct_dt        ON dw.fct_vendas(dt_pedido);
CREATE INDEX idx_fct_mod       ON dw.fct_vendas(oltp_modified);

-- ============================================================================
--  METADADOS DE CONTROLE DO ETL (watermarks incrementais)
--  Cada tabela guarda o "ponto de corte" (max modifieddate) já carregado.
-- ============================================================================
CREATE TABLE dw.etl_watermark (
    tabela_oltp    VARCHAR(80) PRIMARY KEY,   -- nome da tabela de origem
    last_modified  TIMESTAMP NOT NULL,        -- maior modifieddate processado
    last_run       TIMESTAMP NOT NULL,        -- quando a carga ocorreu
    rows_loaded    BIGINT NOT NULL DEFAULT 0  -- linhas carregadas na última vez
);
COMMENT ON TABLE dw.etl_watermark IS 'Watermarks incrementais por tabela de origem (OLTP).';
