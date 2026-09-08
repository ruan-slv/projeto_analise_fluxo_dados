FROM mcr.microsoft.com/mssql/server:2025-latest

USER root
RUN mkdir -p /var/opt/mssql/backup

COPY AdventureWorks2025.bak /var/opt/mssql/backup/

RUN chown -R mssql:root /var/opt/mssql/backup

USER mssql
