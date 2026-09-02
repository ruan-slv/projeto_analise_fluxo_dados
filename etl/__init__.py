# -*- coding: utf-8 -*-
"""Pacote ETL — pipeline incremental AdventureWorks (OLTP) -> DW (Star Schema).

Importa apenas os módulos de apoio (db, etl_core). O orquestrador `pipeline`
é chamado via `python -m etl.pipeline` (evita import duplo / aviso do runpy).
"""
from . import db  # noqa: F401
from . import etl_core  # noqa: F401
