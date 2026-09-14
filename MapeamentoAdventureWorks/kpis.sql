SELECT
    COUNT(DISTINCT employeeid) AS total_funcionarios_ativos
FROM
    demployee
WHERE
    currentflag = 1;


SELECT
    SUM(rate) AS custo_total_folha_por_hora
FROM
    fhuman_resources;


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
