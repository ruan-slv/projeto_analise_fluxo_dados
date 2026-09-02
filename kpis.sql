-- ============================================================================
--  10 INDICADORES (KPIs) — consultas OLAP sobre o Data Warehouse
--  Banco: dw_adventureworks  |  Schema: dw
--
--  Execução:  psql -d dw_adventureworks -f kpis.sql
--  Cada KPI está isolado em um bloco com comentário explicativo.
-- ============================================================================
\set ON_ERROR_STOP on

-- ----------------------------------------------------------------------------
-- KPI 01 — Receita Total (R$)
-- Soma de LineTotal de todas as linhas de pedido.
-- ----------------------------------------------------------------------------
SELECT 'KPI01_ReceitaTotal' AS kpi,
       SUM(f.subtotal_linha)::numeric(15,2) AS valor
FROM dw.fct_vendas f;

-- ----------------------------------------------------------------------------
-- KPI 02 — Receita Média por Pedido (ticket médio)
-- Soma das linhas agrupada por pedido / nº de pedidos distintos.
-- ----------------------------------------------------------------------------
SELECT 'KPI02_TicketMedio' AS kpi,
       SUM(sub)::numeric(15,2) / NULLIF(COUNT(*),0) AS valor
FROM (
    SELECT sales_order_id, SUM(subtotal_linha) AS sub
    FROM dw.fct_vendas
    GROUP BY sales_order_id
) h;

-- ----------------------------------------------------------------------------
-- KPI 03 — Quantidade Total de Itens Vendidos
-- ----------------------------------------------------------------------------
SELECT 'KPI03_QtdItens' AS kpi,
       SUM(quantidade) AS valor
FROM dw.fct_vendas;

-- ----------------------------------------------------------------------------
-- KPI 04 — Vendas por Mês (série temporal)
-- ----------------------------------------------------------------------------
SELECT dd.ano, dd.mes, dd.mes_nome,
       SUM(f.subtotal_linha)::numeric(15,2) AS receita,
       SUM(f.quantidade) AS itens
FROM dw.fct_vendas f
JOIN dw.dim_data dd ON f.data_id = dd.data_id
GROUP BY dd.ano, dd.mes, dd.mes_nome
ORDER BY dd.ano, dd.mes;

-- ----------------------------------------------------------------------------
-- KPI 05 — Top 10 Produtos por Receita
-- ----------------------------------------------------------------------------
SELECT dp.nome AS produto, dp.categoria_nome,
       SUM(f.subtotal_linha)::numeric(15,2) AS receita,
       SUM(f.quantidade) AS itens
FROM dw.fct_vendas f
JOIN dw.dim_produto dp ON f.produto_id = dp.produto_id
GROUP BY dp.nome, dp.categoria_nome
ORDER BY receita DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- KPI 06 — Vendas por Território
-- ----------------------------------------------------------------------------
SELECT dt.nome AS territorio, dt.grupo,
       SUM(f.subtotal_linha)::numeric(15,2) AS receita,
       COUNT(DISTINCT f.sales_order_id) AS pedidos
FROM dw.fct_vendas f
JOIN dw.dim_territorio dt ON f.territorio_id = dt.territory_id
GROUP BY dt.nome, dt.grupo
ORDER BY receita DESC;

-- ----------------------------------------------------------------------------
-- KPI 07 — Top 5 Vendedores por Receita (pedidos com vendedor)
-- ----------------------------------------------------------------------------
SELECT dv.nome AS vendedor, dv.cargo,
       SUM(f.subtotal_linha)::numeric(15,2) AS receita,
       COUNT(DISTINCT f.sales_order_id) AS pedidos
FROM dw.fct_vendas f
JOIN dw.dim_vendedor dv ON f.vendedor_id = dv.vendedor_id
GROUP BY dv.nome, dv.cargo
ORDER BY receita DESC
LIMIT 5;

-- ----------------------------------------------------------------------------
-- KPI 08 — Taxa de Conversão Online vs Loja
-- % de receita e % de itens vindos de pedidos online (e-commerce)
-- ----------------------------------------------------------------------------
SELECT
    ROUND(100.0 * SUM(f.subtotal_linha) FILTER (WHERE f.online)
          / NULLIF(SUM(f.subtotal_linha),0), 2) AS pct_receita_online,
    ROUND(100.0 * SUM(f.quantidade) FILTER (WHERE f.online)
          / NULLIF(SUM(f.quantidade),0), 2)     AS pct_itens_online,
    ROUND(100.0 * SUM(f.subtotal_linha) FILTER (WHERE NOT f.online)
          / NULLIF(SUM(f.subtotal_linha),0), 2) AS pct_receita_loja,
    ROUND(100.0 * SUM(f.quantidade) FILTER (WHERE NOT f.online)
          / NULLIF(SUM(f.quantidade),0), 2)     AS pct_itens_loja
FROM dw.fct_vendas f;

-- ----------------------------------------------------------------------------
-- KPI 09 — Vendas com Promoção vs Sem Promoção
-- Mostra o impacto do desconto especial (SpecialOffer) na receita.
-- Obs.: no OLTP, SpecialOfferID=1 ("No Discount") é o sentinela de "sem
-- promoção". Classificamos por desconto REAL (desconto_pct > 0).
-- ----------------------------------------------------------------------------
SELECT
    CASE WHEN dp.desconto_pct > 0 THEN 'Com Promoção' ELSE 'Sem Promoção' END AS tipo,
    SUM(f.subtotal_linha)::numeric(15,2) AS receita,
    SUM(f.quantidade) AS itens,
    ROUND(100.0 * SUM(f.subtotal_linha) / (SELECT SUM(subtotal_linha) FROM dw.fct_vendas), 2) AS pct_receita
FROM dw.fct_vendas f
LEFT JOIN dw.dim_promocao dp ON f.promocao_id = dp.promocao_id
GROUP BY 1
ORDER BY 1;

-- ----------------------------------------------------------------------------
-- KPI 10 — Crescimento Anual (YoY) de Receita
-- Variação percentual ano a ano.
-- ----------------------------------------------------------------------------
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
