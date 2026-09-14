# Dicionário de Dados — Data Warehouse Recursos Humanos

Este documento apresenta a especificação técnica da estrutura de dados implementada no Data Warehouse (DW) em ambiente PostgreSQL, utilizando a modelagem multidimensional *Star Schema* (Modelo Estrela).

---

## 🏛️ Tabela Fato

### fhuman_resources
* **Descrição:** Centraliza os eventos de recursos humanos relativos aos colaboradores, unificando os relacionamentos com as dimensões qualitativas e armazenando as métricas e medidas de negócio.

| Nome da Coluna | Tipo de Dado | Restrição | Tabela Referenciada | Descrição / Regra de Negócio |
| :--- | :--- | :---: | :--- | :--- |
| **fhumanresources** | `serial` | PK | — | Identificador único sequencial e automático do registro do fato. |
| **dateid** | `int` | FK | `ddate (DateID)` | Associa o evento de recursos humanos a uma data na dimensão cronológica. |
| **timeid** | `int` | FK | `dtime (TimeID)` | Associa o evento a um horário específico na dimensão de tempo. |
| **departmentid** | `int` | FK | `ddepartment (DepartmentID)` | Vincula o fato ao departamento associado ao colaborador no momento do registro. |
| **employeeid** | `int` | FK | `demployee (EmployeeID)` | Identifica o colaborador (funcionário) associado ao evento. |
| **payhistoryid** | `int` | FK | `dpay_history (PayHistoryID)` | Aponta para o registro correspondente à frequência de pagamento do funcionário. |
| **shiftid** | `int` | FK | `dshift (ShiftID)` | Determina o turno de trabalho em que o colaborador atua. |
| **jobcandidateid** | `int` | FK | `djob_candidate (JobCandidateID)` | *Opcional (Permite Null).* Vincula o registro ao currículo caso o funcionário tenha vindo de uma candidatura interna. |
| **rate** | `numeric(15,2)` | Not Null | — | Medida quantitativa. Representa o valor do salário ou taxa paga por hora trabalhada. |
| **vacationhours** | `smallint` | Not Null | — | Medida quantitativa. Total de horas de férias acumuladas ou pendentes do colaborador. |
| **sickleavehours** | `smallint` | Not Null | — | Medida quantitativa. Quantidade acumulada de horas de licença médica concedidas. |

---

## 📐 Tabelas de Dimensão

### demployee
* **Descrição:** Dimensão que armazena os dados cadastrais, atributos e perfis qualitativos de cada funcionário.

| Nome da Coluna | Tipo de Dado | Restrição | Descrição / Regra de Negócio |
| :--- | :--- | :---: | :--- |
| **employeeid** | `int` | PK | Identificador único do funcionário (Business Key originada do sistema de origem). |
| **nationalidnumber** | `varchar(15)` | Not Null | Número de identificação nacional ou registro oficial do colaborador. |
| **loginid** | `varchar(256)` | Not Null | Credencial ou ID de usuário para autenticação nos sistemas da empresa. |
| **organizationnode** | `varchar(892)` | — | Representação em texto da estrutura de nós do organograma corporativo. |
| **organizationlevel** | `smallint` | — | Nível ordinal hierárquico ocupado pelo cargo na árvore da empresa. |
| **jobtitle** | `varchar(50)` | Not Null | Nome descritivo da função ou cargo exercido (ex: 'Design Engineer'). |
| **maritalstatus** | `char(1)` | Not Null | Estado civil do colaborador (ex: 'S' para Solteiro, 'M' para Casado). |
| **gender** | `char(1)` | Not Null | Gênero biológico registrado do colaborador ('M' ou 'F'). |
| **birthdate** | `date` | Not Null | Data de nascimento do funcionário. |
| **hiredate** | `date` | Not Null | Data oficial de admissão/contratação do colaborador. |
| **salariedflag** | `smallint` | Check (0,1) | Indicador binário: 1 para regime de salário fixo, 0 para recebimento por hora. |
| **currentflag** | `smallint` | Check (0,1) | Indicador binário de status atual: 1 para funcionário ativo, 0 para desligado. |

### ddepartment
* **Descrição:** Dimensão nominal contendo o mapeamento das áreas e setores que compõem a organização.

| Nome da Coluna | Tipo de Dado | Restrição | Descrição / Regra de Negócio |
| :--- | :--- | :---: | :--- |
| **departmentid** | `int` | PK | Identificador numérico único do departamento na empresa. |
| **name** | `varchar(100)` | Not Null | Nome formal descritivo do setor ou departamento (ex: 'Marketing'). |
| **groupname** | `varchar(100)` | Not Null | Nome do grupo macro ou diretoria à qual o setor responde (ex: 'Sales and Marketing'). |

### ddate
* **Descrição:** Dimensão cronológica (calendário virtual) responsável por permitir análises e agrupamentos temporais de longo prazo no DW.

| Nome da Coluna | Tipo de Dado | Restrição | Descrição / Regra de Negócio |
| :--- | :--- | :---: | :--- |
| **dateid** | `serial` | PK | Identificador sequencial do registro do calendário. |
| **fulldate** | `date` | Not Null | Representação real da data em formato ISO (`YYYY-MM-DD`). |
| **day** | `smallint` | Not Null | Valor numérico isolado correspondente ao dia do mês (1 a 31). |
| **month** | `smallint` | Not Null | Valor numérico correspondente ao mês do ano (1 a 12). |
| **year** | `smallint` | Not Null | Ano civil do registro representado com 4 dígitos (ex: 2026). |
| **semester** | `smallint` | Not Null | Divisão semestral do ano. Armazena valor `1` para o primeiro semestre ou `2` para o segundo. |

### dtime
* **Descrição:** Dimensão cronológica intradiária, com precisão em segundos, utilizada para decompor métricas de tempo em faixas de horários específicas.

| Nome da Coluna | Tipo de Dado | Restrição | Descrição / Regra de Negócio |
| :--- | :--- | :---: | :--- |
| **timeid** | `serial` | PK | Identificador sequencial único do carimbo de tempo. |
| **fulltime** | `time` | Not Null | O horário em formato de relógio puro (`HH:MM:SS`). |
| **hour** | `smallint` | Not Null | Componente numérico isolado correspondente à hora (0 a 23). |
| **minute** | `smallint` | Not Null | Componente numérico correspondente ao minuto (0 a 59). |
| **second** | `smallint` | Not Null | Componente numérico correspondente ao segundo (0 a 59). |

### dshift
* **Descrição:** Dimensão qualificadora contendo os parâmetros operacionais dos turnos de trabalho estabelecidos pela corporação.

| Nome da Coluna | Tipo de Dado | Restrição | Descrição / Regra de Negócio |
| :--- | :--- | :---: | :--- |
| **shiftid** | `int` | PK | Identificador numérico do turno de trabalho. |
| **name** | `varchar(100)` | Not Null | Nome descritivo do período do turno (ex: 'Day', 'Evening', 'Night'). |
| **starttime** | `time` | Not Null | Horário contratual padronizado de início do expediente. |
| **endtime** | `time` | — | Horário contratual padronizado de encerramento do expediente. |

### djob_candidate
* **Descrição:** Armazena as informações qualitativas de candidatos recrutados pelo departamento de recursos humanos.

| Nome da Coluna | Tipo de Dado | Restrição | Descrição / Regra de Negócio |
| :--- | :--- | :---: | :--- |
| **jobcandidateid** | `int` | PK | Identificador exclusivo do candidato mapeado. |
| **resume** | `text` | — | Conteúdo descriptografado ou traduzido em formato de texto contendo o currículo do candidato. |

### dpay_history
* **Descrição:** Dimensão categórica ordinal criada para segmentar os funcionários conforme as janelas ou frequências contratuais de depósito salarial.

| Nome da Coluna | Tipo de Dado | Restrição | Descrição / Regra de Negócio |
| :--- | :--- | :---: | :--- |
| **payhistoryid** | `int` | PK | Identificador gerado pela esteira de transformação para indexar uma modalidade salarial. |
| **payfrequence** | `smallint` | Not Null | Código ordinal representando a periodicidade da folha (ex: 1 para mensal, 2 para quinzenal). |

---

## ⚙️ Tabela de Controle e Orquestração (Metadados)

### dw_metadata
* **Descrição:** Tabela técnica e operacional isolada do modelo estrela analítico. Sua função primordial é monitorar e gerenciar a execução de pipelines de ETL incrementais, registrando marcas temporais (*watermarks*).

| Nome da Coluna | Tipo de Dado | Restrição | Descrição / Regra de Negócio |
| :--- | :--- | :---: | :--- |
| **id** | `serial` | PK | Identificador sequencial autoincrementável do histórico de logs. |
| **table_name** | `varchar(100)` | Not Null | Identifica o nome físico da tabela de origem monitorada no processo (ex: 'HumanResources.Employee'). |
| **last_load_date** | `timestamp` | Not Null | Registra a estampa de data e hora exata em que a última janela de carga incremental foi executada com sucesso. |
| **records_processed** | `int` | Default 0 | Registra volumetria, salvando o total de linhas afetadas (inseridas ou modificadas) naquela janela de processamento. |
