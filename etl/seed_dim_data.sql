-- ============================================================================
--  DIM_DATA — geração da dimensão de tempo (2010-01-01 .. 2015-12-31)
--  Aborda 2010-2015 para cobrir o range do OLTP (2011-2014) + folga.
--  Execução idempotente: limpa e recria os dados.
-- ============================================================================
DELETE FROM dw.dim_data;
ALTER SEQUENCE dw.dim_data_data_id_seq RESTART WITH 1;

INSERT INTO dw.dim_data (
    data, ano, trimestre, mes, mes_nome, semestre,
    dia_semana, dia_semana_nome, dia_do_ano, dia_do_mes,
    semana_ano, fim_de_semana, flag_mes
)
SELECT
    d::date                                          AS data,
    EXTRACT(YEAR FROM d)::int                        AS ano,
    EXTRACT(QUARTER FROM d)::int                     AS trimestre,
    EXTRACT(MONTH FROM d)::int                       AS mes,
    to_char(d, 'Mon')                                AS mes_nome,
    CASE WHEN EXTRACT(MONTH FROM d) <= 6 THEN 1 ELSE 2 END AS semestre,
    EXTRACT(ISODOW FROM d)::int                      AS dia_semana,
    to_char(d, 'Day')                                AS dia_semana_nome,
    EXTRACT(DOY FROM d)::int                         AS dia_do_ano,
    EXTRACT(DAY FROM d)::int                         AS dia_do_mes,
    EXTRACT(WEEK FROM d)::int                        AS semana_ano,
    (EXTRACT(ISODOW FROM d) >= 6)                   AS fim_de_semana,
    (EXTRACT(DAY FROM d) = 1)                       AS flag_mes
FROM generate_series('2010-01-01'::date, '2015-12-31'::date, '1 day'::interval) AS s(d);

ANALYZE dw.dim_data;
