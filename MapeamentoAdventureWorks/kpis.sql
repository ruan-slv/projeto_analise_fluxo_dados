/* ========================================================================================
   PROJETO DE DATA WAREHOUSE - RECURSOS HUMANOS (STAR SCHEMA)
   VALIDAÇÃO DOS 10 INDICADORES DE NEGÓCIO (KPIs)
   ========================================================================================
   Este script contém as consultas analíticas (OLAP) oficiais para homologação do DW.
   Todas as consultas foram validadas e corrigidas segundo a sintaxe do PostgreSQL.
======================================================================================== */

-- ----------------------------------------------------------------------------------------
-- KPI 1: TOTAL DE FUNCIONÁRIOS ATIVOS
-- Objetivo: Monitorar o tamanho real e atual do quadro de colaboradores da empresa.
-- Métrica: Contagem distinta de funcionários cujo status de atividade está marcado como ativo (1).
-- ----------------------------------------------------------------------------------------
SELECT
    COUNT(DISTINCT employeeid) AS total_funcionarios_ativos
FROM
    demployee
WHERE
    currentflag = 1;


-- ----------------------------------------------------------------------------------------
-- KPI 2: CUSTO TOTAL DA FOLHA DE PAGAMENTO POR HORA (RATE)
-- Objetivo: Avaliar o impacto financeiro imediato do custo operacional de pessoal por hora.
-- Métrica: Somatório simples de todas as taxas salariais (rate) contidas na tabela fato.
-- ----------------------------------------------------------------------------------------
SELECT
    SUM(rate) AS custo_total_folha_por_hora
FROM
    fhuman_resources;


-- ----------------------------------------------------------------------------------------
-- KPI 3: MÉDIA SALARIAL (RATE) POR CARGO
-- Objetivo: Analisar a competitividade interna de remuneração e disparidades entre funções.
-- Métrica: Média aritmética do campo rate agrupada pelo título descritivo do cargo (jobtitle).
-- ----------------------------------------------------------------------------------------
SELECT
    e.jobtitle AS cargo,
    ROUND(AVG(f.rate), 2) AS media_salarial_por_hora
FROM
    fhuman_resources f
JOIN
    demployee e ON f.employeeid = e.employeeid
GROUP BY
    e.jobtitle
ORDER BY
    media_salarial_por_hora DESC;


-- ----------------------------------------------------------------------------------------
-- KPI 4: MÉDIA DE HORAS DE FÉRIAS ACUMULADAS POR DEPARTAMENTO
-- Objetivo: Identificar passivos trabalhistas ou setores sobrecarregados com falta de descanso.
-- Métrica: Média das horas de férias registradas na fato, agrupada por nome do departamento.
-- ----------------------------------------------------------------------------------------
SELECT
    d.name AS departamento,
    ROUND(AVG(f.vacationhours), 1) AS media_horas_ferias_pendentes
FROM
    fhuman_resources f
JOIN
    ddepartment d ON f.departmentid = d.departmentid
GROUP BY
    d.name
ORDER BY
    media_horas_ferias_pendentes DESC;


-- ----------------------------------------------------------------------------------------
-- KPI 5: TOTAL DE HORAS DE LICENÇA MÉDICA POR TURNO DE TRABALHO
-- Objetivo: Medir o índice de absenteísmo por motivos de saúde correlacionado ao período/turno.
-- Métrica: Soma total das horas de licença médica agrupadas pela classificação qualitativa do turno.
-- ----------------------------------------------------------------------------------------
SELECT
    s.name AS turno,
    SUM(f.sickleavehours) AS total_horas_licenca_medica
FROM
    fhuman_resources f
JOIN
    dshift s ON f.shiftid = s.shiftid
GROUP BY
    s.name
ORDER BY
    total_horas_licenca_medica DESC;


-- ----------------------------------------------------------------------------------------
-- KPI 6: DISTRIBUIÇÃO E PERCENTUAL DE FUNCIONÁRIOS POR GÊNERO EM CADA DEPARTAMENTO
-- Objetivo: Fornecer dados quantitativos para apoiar políticas de diversidade e inclusão por setor.
-- Métrica: Contagem de funcionários dividida por gênero com cálculo percentual dinâmico usando Window Function.
-- ----------------------------------------------------------------------------------------
SELECT
    d.name AS departamento,
    e.gender AS genero,
    COUNT(DISTINCT f.employeeid) AS total_colaboradores,
    ROUND(
        COUNT(DISTINCT f.employeeid) * 100.0 / SUM(COUNT(DISTINCT f.employeeid)) OVER(PARTITION BY d.name),
        2
    ) AS percentual_no_departamento
FROM
    fhuman_resources f
JOIN
    ddepartment d ON f.departmentid = d.departmentid
JOIN
    demployee e ON f.employeeid = e.employeeid
GROUP BY
    d.name, e.gender
ORDER BY
    d.name, e.gender;


-- ----------------------------------------------------------------------------------------
-- KPI 7: EVOLUÇÃO HISTÓRICA DO TOTAL DE CONTRATAÇÕES POR ANO E SEMESTRE
-- Objetivo: Analisar o ritmo de crescimento e a tração de novos talentos ao longo do tempo.
-- Métrica: Contagem do total de registros agregados pelas partições cronológicas da dimensão ddate.
-- ----------------------------------------------------------------------------------------
SELECT
    d.year AS ano,
    d.semester AS semestre,
    COUNT(f.fhumanresources) AS total_admissoes
FROM
    fhuman_resources f
JOIN
    ddate d ON f.dateid = d.dateid
GROUP BY
    d.year, d.semester
ORDER BY
    ano DESC, semestre DESC;


-- ----------------------------------------------------------------------------------------
-- KPI 8: COMPARAÇÃO DA MAIOR REMUNERAÇÃO (RATE) POR NÍVEL ORGANIZACIONAL (HIERARQUIA)
-- Objetivo: Entender a correlação entre a senioridade/nível de liderança com o teto salarial.
-- Métrica: Valor máximo da taxa (rate) encontrado para cada degrau da estrutura hierárquica.
-- ----------------------------------------------------------------------------------------
SELECT
    COALESCE(e.organizationlevel::text, 'Nível Topo/Diretoria') AS nivel_hierarquico,
    MAX(f.rate) AS maior_taxa_salarial
FROM
    fhuman_resources f
JOIN
    demployee e ON f.employeeid = e.employeeid
GROUP BY
    e.organizationlevel
ORDER BY
    maior_taxa_salarial DESC;


-- ----------------------------------------------------------------------------------------
-- KPI 9: TOTAL DE CANDIDATOS COM CURRÍCULO CAPTURADO POR DEPARTAMENTO
-- Objetivo: Avaliar a eficiência e a atratividade do banco de talentos para cada área de negócio.
-- Métrica: Contagem de chaves de candidatos válidas (removendo registros nulos) associadas a cada setor.
-- ----------------------------------------------------------------------------------------
SELECT
    d.name AS departamento,
    COUNT(f.jobcandidateid) AS total_curriculos_recebidos
FROM
    fhuman_resources f
JOIN
    ddepartment d ON f.departmentid = d.departmentid
WHERE
    f.jobcandidateid IS NOT NULL
GROUP BY
    d.name
ORDER BY
    total_curriculos_recebidos DESC;


-- ----------------------------------------------------------------------------------------
-- KPI 10: MÉDIA DE TEMPO DE CASA (EM ANOS) POR TÍTULO DE CARGO
-- Objetivo: Analisar os padrões de retenção de talentos e o tempo de permanência por função.
-- Métrica: Diferença em anos calculada entre a data de admissão (hiredate) e a data corrente do sistema.
-- ----------------------------------------------------------------------------------------
SELECT
    e.jobtitle AS cargo,
    ROUND(AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hiredate)))::numeric, 1) AS media_anos_tempo_de_casa
FROM
    fhuman_resources f
JOIN
    demployee e ON f.employeeid = e.employeeid
GROUP BY
    e.jobtitle
ORDER BY
    media_anos_tempo_de_casa DESC;
