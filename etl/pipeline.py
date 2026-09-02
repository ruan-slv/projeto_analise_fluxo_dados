# -*- coding: utf-8 -*-
"""
PIPELINE ETL INCREMENTAL — AdventureWorks (OLTP) -> DW (Star Schema)

Uso:
    python -m etl.pipeline            # incremental (usa watermarks)
    python -m etl.pipeline --reset    # limpa watermarks + fato e recarrega tudo

Ordem de carga (dependências):
    dim_data (seed) -> dim_produto, dim_cliente, dim_vendedor,
    dim_territorio, dim_moeda, dim_promocao  ->  fct_vendas

Cada dimensão lê o DELTA (modifieddate >= watermark) da fonte e grava via
UPSERT. O fato resolve as chaves substitutas (FKs) das dimensões em Python
a partir dos dicionários carregados.
"""
import sys
import time
import datetime as dt
import psycopg2
import psycopg2.extras

from . import db
from .etl_core import get_watermark, set_watermark, upsert, max_modified, fetch_delta

# ---------------------------------------------------------------------------
#  Consultas de origem (OLTP). Cada uma termina com o filtro incremental.
#  O placeholder %s recebe o watermark (datetime).
# ---------------------------------------------------------------------------
Q_PRODUTO = """
SELECT p.productid, p.name, p.productnumber, p.color, p.size, p.class, p.style,
       p.makeflag, p.standardcost, p.listprice, p.weight,
       p.productsubcategoryid, sc.name AS subcat, pc.name AS cat,
       p.sellstartdate, p.sellenddate, p.modifieddate
FROM production.product p
LEFT JOIN production.productsubcategory sc ON p.productsubcategoryid = sc.productsubcategoryid
LEFT JOIN production.productcategory pc ON sc.productcategoryid = pc.productcategoryid
WHERE p.modifieddate >= %s
"""

Q_CLIENTE = """
SELECT c.customerid,
       CASE WHEN c.personid IS NOT NULL THEN 'Individual' ELSE 'Loja' END AS tipo,
       p.firstname, p.lastname, p.title, p.emailpromotion,
       s.name AS loja, c.territoryid, c.accountnumber, c.modifieddate
FROM sales.customer c
LEFT JOIN person.person p ON c.personid = p.businessentityid
LEFT JOIN sales.store s ON c.storeid = s.businessentityid
WHERE c.modifieddate >= %s
"""

Q_VENDEDOR = """
SELECT sp.businessentityid,
       per.firstname || ' ' || per.lastname AS nome,
       e.jobtitle, sp.territoryid, sp.salesquota, sp.bonus, sp.commissionpct,
       sp.modifieddate
FROM sales.salesperson sp
LEFT JOIN humanresources.employee e ON sp.businessentityid = e.businessentityid
LEFT JOIN person.person per ON e.businessentityid = per.businessentityid
WHERE sp.modifieddate >= %s
"""

Q_TERRITORIO = """
SELECT st.territoryid, st.name, st."group",
       cr.countryregioncode AS cod_pais, cr.name AS nome_pais,
       sp.name AS estado, sp.stateprovincecode,
       st.salesytd, st.saleslastyear, st.costytd, st.costlastyear, st.modifieddate
FROM sales.salesterritory st
LEFT JOIN person.countryregion cr ON st.countryregioncode = cr.countryregioncode
LEFT JOIN LATERAL (
    SELECT sp2.name, sp2.stateprovincecode
    FROM person.stateprovince sp2
    WHERE sp2.territoryid = st.territoryid
    ORDER BY sp2.stateprovincecode
    LIMIT 1
) sp ON true
WHERE st.modifieddate >= %s
"""

Q_MOEDA = """
SELECT cu.currencycode, cu.name,
       (SELECT r.averagerate FROM sales.currencyrate r
         WHERE r.fromcurrencycode = 'USD' AND r.tocurrencycode = cu.currencycode
         ORDER BY r.currencyratedate DESC LIMIT 1) AS taxa,
       cu.modifieddate
FROM sales.currency cu
WHERE cu.modifieddate >= %s
"""

Q_PROMOCAO = """
SELECT specialofferid, description, type, category, discountpct,
       minqty, maxqty, startdate, enddate, modifieddate
FROM sales.specialoffer
WHERE modifieddate >= %s
"""

Q_FACT = """
SELECT d.salesorderid, d.salesorderdetailid, d.orderqty, d.unitprice,
       d.unitpricediscount, d.linetotal, d.productid, d.specialofferid,
       h.customerid, h.salespersonid, h.territoryid, h.status, h.onlineorderflag,
       h.subtotal, h.taxamt, h.freight, h.totaldue, h.orderdate,
       COALESCE(cr.tocurrencycode, 'USD') AS moeda,
       GREATEST(d.modifieddate, h.modifieddate) AS wm
FROM sales.salesorderdetail d
JOIN sales.salesorderheader h ON d.salesorderid = h.salesorderid
LEFT JOIN sales.currencyrate cr ON h.currencyrateid = cr.currencyrateid
WHERE GREATEST(d.modifieddate, h.modifieddate) >= %s
"""


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------
def _log(msg):
    print(f"  {msg}", flush=True)


def _rcur(conn):
    """Cursor que devolve linhas como dict (para mapeamentos FK)."""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
#  Carregadores específicos (cada um controla o mapeamento FK)
# ---------------------------------------------------------------------------
def load_dim_produto(src, dst):
    cur = _rcur(dst)
    wm = get_watermark(cur, "production.product")
    _log(f"[dim_produto] wm={wm:%Y-%m-%d %H:%M}")
    rows = fetch_delta(src, Q_PRODUTO, wm)
    if not rows:
        _log("[dim_produto] delta vazio")
        return {}
    cols = ["product_oltp_id","nome","numero","cor","tamanho","classe","estilo",
            "fabrica","custo_padrao","preco_lista","peso","subcategoria_id",
            "categoria_id","subcategoria_nome","categoria_nome","dt_venda_inicio",
            "dt_venda_fim"]
    vals = []
    for r in rows:
        vals.append((
            r["productid"], r["name"], r["productnumber"], r["color"], r["size"],
            r["class"], r["style"], r["makeflag"], r["standardcost"], r["listprice"],
            r["weight"], r["productsubcategoryid"], r["productsubcategoryid"],
            r["subcat"], r["cat"],
            r["sellstartdate"].date() if r["sellstartdate"] else None,
            r["sellenddate"].date() if r["sellenddate"] else None,
        ))
    upsert(dst, "dw.dim_produto", ["product_oltp_id"], cols, vals)
    new_wm = max_modified(rows) or wm
    set_watermark(cur, "production.product", new_wm, len(vals)); dst.commit()
    _log(f"[dim_produto] {len(vals)} linhas -> wm={new_wm:%Y-%m-%d %H:%M}")
    # mapeia productid -> produto_id
    cur.execute("SELECT produto_id, product_oltp_id FROM dw.dim_produto")
    return {r["product_oltp_id"]: r["produto_id"] for r in cur.fetchall()}


def load_dim_cliente(src, dst):
    cur = _rcur(dst)
    wm = get_watermark(cur, "sales.customer")
    _log(f"[dim_cliente] wm={wm:%Y-%m-%d %H:%M}")
    rows = fetch_delta(src, Q_CLIENTE, wm)
    if not rows:
        _log("[dim_cliente] delta vazio")
        return {}
    cols = ["customer_oltp_id","tipo_cliente","nome","sobrenome","titulo",
            "email_promocao","loja_nome","territorio_id","account_number"]
    vals = []
    for r in rows:
        nome = (r["firstname"] or "") + " " + (r["lastname"] or "")
        nome = nome.strip() or r["loja"]
        vals.append((
            r["customerid"], r["tipo"], nome, r["lastname"], r["title"],
            r["emailpromotion"], r["loja"], r["territoryid"], r["accountnumber"],
        ))
    upsert(dst, "dw.dim_cliente", ["customer_oltp_id"], cols, vals)
    new_wm = max_modified(rows) or wm
    set_watermark(cur, "sales.customer", new_wm, len(vals)); dst.commit()
    _log(f"[dim_cliente] {len(vals)} linhas -> wm={new_wm:%Y-%m-%d %H:%M}")
    cur.execute("SELECT cliente_id, customer_oltp_id FROM dw.dim_cliente")
    return {r["customer_oltp_id"]: r["cliente_id"] for r in cur.fetchall()}


def load_dim_vendedor(src, dst):
    cur = _rcur(dst)
    wm = get_watermark(cur, "sales.salesperson")
    _log(f"[dim_vendedor] wm={wm:%Y-%m-%d %H:%M}")
    rows = fetch_delta(src, Q_VENDEDOR, wm)
    if not rows:
        _log("[dim_vendedor] delta vazio")
        return {}
    cols = ["salesperson_oltp","nome","cargo","territorio_id","quota","bonus","comissao"]
    vals = []
    for r in rows:
        vals.append((
            r["businessentityid"], r["nome"], r["jobtitle"], r["territoryid"],
            r["salesquota"], r["bonus"], r["commissionpct"],
        ))
    upsert(dst, "dw.dim_vendedor", ["salesperson_oltp"], cols, vals)
    new_wm = max_modified(rows) or wm
    set_watermark(cur, "sales.salesperson", new_wm, len(vals)); dst.commit()
    _log(f"[dim_vendedor] {len(vals)} linhas -> wm={new_wm:%Y-%m-%d %H:%M}")
    cur.execute("SELECT vendedor_id, salesperson_oltp FROM dw.dim_vendedor")
    return {r["salesperson_oltp"]: r["vendedor_id"] for r in cur.fetchall()}


def load_dim_territorio(src, dst):
    cur = _rcur(dst)
    wm = get_watermark(cur, "sales.salesterritory")
    _log(f"[dim_territorio] wm={wm:%Y-%m-%d %H:%M}")
    rows = fetch_delta(src, Q_TERRITORIO, wm)
    if not rows:
        _log("[dim_territorio] delta vazio")
        return {}
    cols = ["territory_oltp_id","nome","grupo","codigo_pais","nome_pais",
            "codigo_estado","nome_estado","vendas_ano","vendas_ano_ant",
            "custo_ano","custo_ano_ant"]
    vals = []
    for r in rows:
        vals.append((
            r["territoryid"], r["name"], r["group"], r["cod_pais"], r["nome_pais"],
            r["stateprovincecode"], r["estado"], r["salesytd"], r["saleslastyear"],
            r["costytd"], r["costlastyear"],
        ))
    upsert(dst, "dw.dim_territorio", ["territory_oltp_id"], cols, vals)
    new_wm = max_modified(rows) or wm
    set_watermark(cur, "sales.salesterritory", new_wm, len(vals)); dst.commit()
    _log(f"[dim_territorio] {len(vals)} linhas -> wm={new_wm:%Y-%m-%d %H:%M}")
    cur.execute("SELECT territory_id, territory_oltp_id FROM dw.dim_territorio")
    return {r["territory_oltp_id"]: r["territory_id"] for r in cur.fetchall()}


def load_dim_moeda(src, dst):
    cur = _rcur(dst)
    wm = get_watermark(cur, "sales.currency")
    _log(f"[dim_moeda] wm={wm:%Y-%m-%d %H:%M}")
    rows = fetch_delta(src, Q_MOEDA, wm)
    if not rows:
        _log("[dim_moeda] delta vazio")
        return {}
    cols = ["currency_code","nome_moeda","taxa_media"]
    vals = [(r["currencycode"], r["name"], r["taxa"]) for r in rows]
    upsert(dst, "dw.dim_moeda", ["currency_code"], cols, vals)
    new_wm = max_modified(rows) or wm
    set_watermark(cur, "sales.currency", new_wm, len(vals)); dst.commit()
    _log(f"[dim_moeda] {len(vals)} linhas -> wm={new_wm:%Y-%m-%d %H:%M}")
    cur.execute("SELECT moeda_id, currency_code FROM dw.dim_moeda")
    return {r["currency_code"]: r["moeda_id"] for r in cur.fetchall()}


def load_dim_promocao(src, dst):
    cur = _rcur(dst)
    wm = get_watermark(cur, "sales.specialoffer")
    _log(f"[dim_promocao] wm={wm:%Y-%m-%d %H:%M}")
    rows = fetch_delta(src, Q_PROMOCAO, wm)
    if not rows:
        _log("[dim_promocao] delta vazio")
        return {}
    cols = ["specialoffer_oltp","descricao","tipo","categoria","desconto_pct",
            "qty_minima","qty_maxima","dt_inicio","dt_fim"]
    vals = []
    for r in rows:
        vals.append((
            r["specialofferid"], r["description"], r["type"], r["category"],
            r["discountpct"], r["minqty"], r["maxqty"],
            r["startdate"].date() if r["startdate"] else None,
            r["enddate"].date() if r["enddate"] else None,
        ))
    upsert(dst, "dw.dim_promocao", ["specialoffer_oltp"], cols, vals)
    new_wm = max_modified(rows) or wm
    set_watermark(cur, "sales.specialoffer", new_wm, len(vals)); dst.commit()
    _log(f"[dim_promocao] {len(vals)} linhas -> wm={new_wm:%Y-%m-%d %H:%M}")
    cur.execute("SELECT promocao_id, specialoffer_oltp FROM dw.dim_promocao")
    return {r["specialoffer_oltp"]: r["promocao_id"] for r in cur.fetchall()}


def load_dim_data_map(dst):
    """Carrega dim_data (seed) e devolve {date: data_id}."""
    cur = _rcur(dst)
    cur.execute("SELECT data_id, data FROM dw.dim_data")
    return {r["data"]: r["data_id"] for r in cur.fetchall()}


def load_fact(src, dst, maps):
    """
    Carrega o fato incrementalmente, resolvendo as FKs das dimensões.
    `maps` = dict com os dicionários oltp->surrogate de cada dimensão.
    """
    cur = _rcur(dst)
    wm = get_watermark(cur, "sales.salesorderdetail")
    _log(f"[fct_vendas] wm={wm:%Y-%m-%d %H:%M}")
    rows = fetch_delta(src, Q_FACT, wm)
    if not rows:
        _log("[fct_vendas] delta vazio")
        return

    # mapeia data -> data_id (com fallback p/ datas fora do range)
    data_map = maps["data"]
    def data_id(d):
        if d is None:
            return None
        return data_map.get(d.date() if isinstance(d, dt.datetime) else d)

    cols = ["data_id","produto_id","cliente_id","vendedor_id","territorio_id",
            "moeda_id","promocao_id","sales_order_id","line_id","quantidade",
            "preco_unit","desconto_unit","subtotal_linha","online","status_pedido",
            "total_pedido","taxas","frete","dt_pedido","oltp_modified"]
    vals = []
    missing = {"produto":0,"cliente":0,"data":0}
    for r in rows:
        did = data_id(r["orderdate"])
        if did is None:
            missing["data"] += 1
        pid = maps["produto"].get(r["productid"])
        if pid is None:
            missing["produto"] += 1
        cid = maps["cliente"].get(r["customerid"])
        if cid is None:
            missing["cliente"] += 1
        vals.append((
            did, pid, cid,
            maps["vendedor"].get(r["salespersonid"]),
            maps["territorio"].get(r["territoryid"]),
            maps["moeda"].get(r["moeda"]),
            maps["promocao"].get(r["specialofferid"]),
            r["salesorderid"], r["salesorderdetailid"], r["orderqty"],
            r["unitprice"], r["unitpricediscount"], r["linetotal"],
            r["onlineorderflag"], r["status"], r["totaldue"], r["taxamt"],
            r["freight"], r["orderdate"].date() if r["orderdate"] else None,
            r["wm"],
        ))
    upsert(dst, "dw.fct_vendas", ["sales_order_id","line_id"], cols, vals)
    new_wm = max_modified(rows, key="wm") or wm
    set_watermark(cur, "sales.salesorderdetail", new_wm, len(vals)); dst.commit()
    _log(f"[fct_vendas] {len(vals)} linhas -> wm={new_wm:%Y-%m-%d %H:%M}")
    if any(missing.values()):
        _log(f"[fct_vendas] AVISO FK ausentes: {missing}")


# ---------------------------------------------------------------------------
#  Orquestrador
# ---------------------------------------------------------------------------
def run(reset=False):
    t0 = time.time()
    src = db.connect_source()
    dst = db.connect_dw()

    if reset:
        c = dst.cursor()
        c.execute("TRUNCATE dw.fct_vendas RESTART IDENTITY")
        c.execute("DELETE FROM dw.etl_watermark")
        dst.commit()
        _log("RESET: fato truncado e watermarks zerados.")

    _log("Carregando dimensões...")
    maps = {
        "data":       load_dim_data_map(dst),
        "produto":    load_dim_produto(src, dst),
        "cliente":    load_dim_cliente(src, dst),
        "vendedor":   load_dim_vendedor(src, dst),
        "territorio": load_dim_territorio(src, dst),
        "moeda":      load_dim_moeda(src, dst),
        "promocao":   load_dim_promocao(src, dst),
    }
    _log("Carregando fato...")
    load_fact(src, dst, maps)

    src.close(); dst.close()
    _log(f"\nPipeline concluído em {time.time()-t0:.1f}s.")


def main():
    reset = "--reset" in sys.argv
    print("=" * 60)
    print("PIPELINE ETL INCREMENTAL — AdventureWorks -> DW")
    print("=" * 60)
    run(reset=reset)


if __name__ == "__main__":
    main()
