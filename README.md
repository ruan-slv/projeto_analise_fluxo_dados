# Projeto de Análise e Fluxo de Dados — OLAP e ETL

## 📌 Visão Geral do Projeto
Este projeto tem como objetivo exercitar e aplicar na prática conceitos fundamentais de Engenharia de Dados e Business Intelligence, utilizando o banco de dados de exemplo **AdventureWorks**.

O foco principal do trabalho é a **Modelagem Multidimensional** (Star Schema) e a implementação de um **pipeline de ETL incremental** robusto em Python, armazenando os dados em um Data Warehouse PostgreSQL.

---

## 🎯 Objetivos
- **Processos de ETL Incremental:** Construção de pipeline capaz de processar apenas registros novos ou modificados.
- **Modelagem Multidimensional:** Modelagem baseada no padrão *Star Schema* (Modelo Estrela).
- **Indicadores de Negócio (KPIs):** Definição e implementação de 10 métricas/KPIs essenciais.
- **Engenharia de Dados em Data Warehouse:** Implementação do DW no PostgreSQL e validação das métricas via SQL.

---

## 📝 Enunciado & Requisitos
O trabalho é realizado em grupos de no máximo 4 estudantes. A partir da restauração e análise do modelo relacional (OLTP) do banco **AdventureWorks**, o grupo deverá:

1. **Avaliar** o modelo de dados OLTP do *AdventureWorks*.
2. **Elaborar** 10 indicadores (métricas/KPIs) relevantes para o negócio.
3. **Projetar** um modelo multidimensional (*Star Schema*) adequado para suportar os indicadores.
4. **Implementar** o Data Warehouse no banco de dados **PostgreSQL**.
5. **Construir** uma ETL em **Python** para popular o Data Warehouse.
   - *Requisito obrigatório:* A ETL deve ser **incremental**, processando apenas dados novos ou alterados.
6. **Implementar** consultas SQL para comprovar o cálculo dos 10 indicadores.
7. *(Nota: Não é necessária a criação de dashboards de visualização).*

---

## 📋 Atividades a Desenvolver
- [ ] Análise do modelo OLTP *AdventureWorks*.
- [ ] Definição dos 10 indicadores (KPIs).
- [ ] Proposta e desenho do diagrama do modelo multidimensional (*Star Schema*) utilizando Draw.io, PlantUML ou ferramenta similar.
- [ ] Criação e estruturação do Data Warehouse no PostgreSQL.
- [ ] Desenvolvimento do script/pipeline de ETL incremental em Python.
- [ ] Versionamento e disponibilização do projeto em repositório no GitHub.
- [ ] Escrita de artigo acadêmico no padrão **Unisales** contendo:
  - **Introdução**
  - **Fundamentação Teórica** (Modelagem Multidimensional e ETL)
  - **Desenvolvimento**
  - **Considerações Finais**

---

## 📄 Estrutura do Artigo Unisales
O artigo acadêmico deve conter obrigatoriamente:
- Modelo estrela proposto e diagrama multidimensional.
- Dicionário de dados do Data Warehouse.
- Descrição detalhada da estratégia de ETL incremental adotada.
- Justificativa técnica das decisões de modelagem.
- Link direto para o repositório do projeto no GitHub.
- Scripts SQL que comprovem a execução dos indicadores.

---

## 📚 Referências & Links Úteis
- 📌 **Documentação & Instalação AdventureWorks:** [Microsoft Learn](https://learn.microsoft.com/pt-br/sql/samples/adventureworks-install-configure?view=sql-server-ver17&tabs=ssms)
- 🖼️ **Diagrama do Modelo OLTP AdventureWorks:** [Schema GIF](https://blogdozouza.wordpress.com/wp-content/uploads/2019/10/adventureworks2008_schema.gif)
- 📐 **Conceitos de Modelagem Multidimensional (Star Schema):** [Wikipedia](https://en.wikipedia.org/wiki/Star_schema)
- 📖 **Guia Unisales para Trabalhos Acadêmicos:** [PDF Unisales](https://unisales.br/wp-content/uploads/2024/07/NOVO-GUIA-DE-ELABORACAO-E-NORMALIZACAO-DE-TRABALHOS-ACADEMICOS-E-DE-PESQUISA-29.05.pdf)
- 💾 **Download da Base de Dados (AdventureWorks2016.bak):** [GitHub Releases](https://github.com/Microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorks2016.bak)
