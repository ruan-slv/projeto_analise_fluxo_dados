/* ========================================================================================
   PROJETO DE DATA WAREHOUSE - RECURSOS HUMANOS (STAR SCHEMA)
   ========================================================================================
   Ordem de criação: Dimensões (qualitativas) primeiro, Fato (quantitativa/métricas) por último.
   Isso é obrigatório para que as chaves estrangeiras (Foreign Keys) encontrem as tabelas.
======================================================================================== */

/* ----------------------------------------------------------------------------------------
   1. DIMENSÃO DATA (ddate)
   Explicação: A data atua como um dado QUALITATIVO no Data Warehouse. Em vez de somar datas, 
   você as utiliza para agrupar as métricas (ex: "Total de contratações agrupadas pelo Ano 2026").
   A chave primária é gerada pelo próprio Postgres (serial).
---------------------------------------------------------------------------------------- */
CREATE TABLE ddate(
    DateID serial primary key,
    FullDate date not null,       -- A data real: '2026-09-12'
    Day smallint not null,        -- O dia isolado: 12 (útil para relatórios diários)
    Month smallint not null,      -- O mês isolado: 9 (útil para sazonalidade)
    Year smallint not null,       -- O ano isolado: 2026
    Semester smallint not null    -- Qualitativo de período: 1 ou 2
);

/* ----------------------------------------------------------------------------------------
   2. DIMENSÃO TEMPO (dtime)
   Explicação: Assim como a data, o tempo ganha uma tabela própria para categorizar o horário
   exato de um evento. Se uma métrica exige precisão, ela aponta para cá.
---------------------------------------------------------------------------------------- */
CREATE TABLE dtime(
    TimeID serial primary key,
    Hour smallint not null,       -- Hora (0 a 23)
    Minute smallint not null,     -- Minuto (0 a 59)
    Second smallint not null      -- Segundo (0 a 59)
);

/* ----------------------------------------------------------------------------------------
   3. DIMENSÃO TURNO (dshift)
   Explicação: Agrupador qualitativo que descreve o período de trabalho.
---------------------------------------------------------------------------------------- */
CREATE TABLE dshift(
    ShiftID serial primary key,
    Name varchar(100) not null,   -- Ex: 'Day', 'Evening', 'Night'
    StartTime time not null,      -- O horário que o turno começa
    EndTime time                  -- O horário que o turno termina
); 

/* ----------------------------------------------------------------------------------------
   4. DIMENSÃO DEPARTAMENTO (ddepartment)
   Explicação: Armazena os dados nominais (textos) que descrevem as áreas da empresa.
---------------------------------------------------------------------------------------- */
CREATE TABLE ddepartment(
    DepartmentID serial primary key,
    Name varchar(100) not null,
    GroupName varchar(100) not null
);

/* ----------------------------------------------------------------------------------------
   5. DIMENSÃO CANDIDATO (djob_candidate)
   Explicação: Isola os dados dos candidatos. O currículo (XML na origem) é tipado como TEXT 
   para melhor manuseio e segurança no Postgres.
---------------------------------------------------------------------------------------- */
CREATE TABLE djob_candidate(
    JobCandidateID serial primary key,
    Resume text 
);

/* ----------------------------------------------------------------------------------------
   6. DIMENSÃO HISTÓRICO DE PAGAMENTO (dpay_history)
   Explicação: Categoria ordinal. A frequência de pagamento não é algo que você soma.
---------------------------------------------------------------------------------------- */
CREATE TABLE dpay_history(
    PayHistoryID serial primary key,
    PayFrequence smallint not null -- Categoria: 1 (Mensal), 2 (Quinzenal), etc.
);

/* ----------------------------------------------------------------------------------------
   7. DIMENSÃO FUNCIONÁRIO (demployee)
   Explicação: A tabela mais rica. Recebe todos os atributos que descrevem O QUEM.
   Aqui aplicamos restrições CHECK para garantir que dados incorretos (como SalariedFlag = 3) 
   não entrem no banco, priorizando a segurança e a integridade da informação.
---------------------------------------------------------------------------------------- */
CREATE TABLE demployee(
    EmployeeID serial primary key,          -- Surrogate Key (A chave artificial do DW)
    NationalIDNumber varchar(15) not null,  -- Business Key (O dado real de identificação)
    LoginID varchar(256) not null,
    OrganizationNode varchar(892),
    OrganizationLevel smallint,             -- Qualitativo ordinal (Nível da hierarquia)
    JobTitle varchar(50) not null,          -- Qualitativo nominal (Nome do cargo)
    MaritalStatus char(1) not null,
    Gender char(1) not null,
    BirthDate date not null,                -- Data atrelada à pessoa (característica)
    HireDate date not null,                 -- Data atrelada à pessoa (característica)
    
    -- Restrições CHECK para segurança absoluta dos dados categóricos (0 ou 1):
    SalariedFlag smallint check(SalariedFlag in (0,1)), 
    CurrentFlag smallint check(CurrentFlag in (0,1))
);

/* ----------------------------------------------------------------------------------------
   8. TABELA FATO (fhuman_resources)
   Explicação: O coração do Data Warehouse. Ela NÃO POSSUI textos ou categorias. 
   Ela guarda apenas duas coisas:
   A) IDs que apontam para as Dimensões (Onde, Quando e Quem).
   B) Métricas matemáticas reais (O Quanto).
---------------------------------------------------------------------------------------- */
CREATE TABLE fhuman_resources(
    FHumanResources serial primary key,
    
    -- CHAVES ESTRANGEIRAS (FOREIGN KEYS)
    -- Declaração inline: O comando 'REFERENCES' cria a ligação física automaticamente.
    -- Isso blinda o banco: você não consegue inserir um evento de um funcionário que não existe.
    DateID int not null REFERENCES ddate(DateID),           
    TimeID int not null REFERENCES dtime(TimeID),
    DepartmentID int not null REFERENCES ddepartment(DepartmentID),
    EmployeeID int not null REFERENCES demployee(EmployeeID),
    PayHistoryID int not null REFERENCES dpay_history(PayHistoryID),
    ShiftID int not null REFERENCES dshift(ShiftID),
    JobCandidateID int REFERENCES djob_candidate(JobCandidateID), 
    
    -- DADOS QUANTITATIVOS (MÉTRICAS / FATOS)
    -- Esses são os únicos dados que farão parte das suas operações de SUM(), AVG(), etc.
    Rate numeric(15,2) not null,       -- Quantidade de dinheiro (Tipado com segurança no Postgres)
    VacationHours smallint not null,   -- Quantidade de horas de férias tomadas
    SickLeaveHours smallint not null   -- Quantidade de horas de licença tomadas
);










