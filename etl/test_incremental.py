# -*- coding: utf-8 -*-
"""
TESTE DE ETL INCREMENTAL
=======================
Prova que o pipeline captura APENAS as linhas alteradas na fonte (OLTP),
sem recarregar o histórico e sem criar duplicatas.

Cenário:
  1. Escolhe 1 produto (production.product) e 1 linha de pedido (sales.salesorderdetail).
  2. Registra os valores ORIGINAIS (fonte e DW).
  3. ALTERA os valores na fonte e atualiza modifieddate = agora (simula um CDC).
  4. Roda o pipeline em modo INCREMENTAL (sem --reset).
  5. ASSERT: o DW reflete a alteração, o watermark avançou e NÃO há duplicatas.
  6. Restaura a fonte e re-sincroniza o DW (deixa tudo no estado canônico).

Uso:  python -m etl.test_incremental
"""
import datetime as dt
from . import db
from . import pipeline

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results = []

def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(f"  [{PASS if cond else FAIL}] {name} {extra}")

def main():
    src = db.connect_source()
    dst = db.connect_dw()
    sc, dc = src.cursor(), dst.cursor()
    now = dt.datetime.now()

    print("=" * 62)
    print("TESTE — ETL INCREMENTAL (captura apenas o delta)")
    print("=" * 62)

    # ---- 1. alvos: 1 produto e 1 linha de pedido ----------------------------
    sc.execute("SELECT productid, name FROM production.product WHERE productid=1")
    pid, p_name = sc.fetchone()
    sc.execute("SELECT salesorderid, salesorderdetailid, orderqty FROM sales.salesorderdetail ORDER BY salesorderdetailid LIMIT 1")
    hid, lid, d_qty = sc.fetchone()
    print(f"  Alvos: productid={pid} (name='{p_name}') | detalhe ({hid},{lid}) qty={d_qty}")

    # valores atuais no DW
    dc.execute("SELECT nome FROM dw.dim_produto WHERE product_oltp_id=%s", (pid,))
    dw_name_before = dc.fetchone()[0]
    dc.execute("SELECT quantidade FROM dw.fct_vendas WHERE sales_order_id=%s AND line_id=%s", (hid, lid))
    dw_qty_before = dc.fetchone()[0]

    # watermarks antes
    def wm(t):
        dc.execute("SELECT last_modified FROM dw.etl_watermark WHERE tabela_oltp=%s", (t,))
        r = dc.fetchone()
        return r[0] if r else None
    wm_prod_before = wm("production.product")
    wm_det_before = wm("sales.salesorderdetail")

    # ---- 2. ALTERA a fonte (simula CDC) ------------------------------------
    new_name = p_name + "_TESTE"
    sc.execute("UPDATE production.product SET name=%s, modifieddate=%s WHERE productid=%s", (new_name, now, pid))
    sc.execute("UPDATE sales.salesorderdetail SET orderqty=%s, modifieddate=%s WHERE salesorderdetailid=%s", (d_qty + 1, now, lid))
    src.commit()
    print(f"  Fonte alterada: product.name -> '{new_name}' | detalhe.qty {d_qty}->{d_qty+1} (modifieddate=now)")

    # ---- 3. roda pipeline INCREMENTAL --------------------------------------
    print("  Rodando pipeline (incremental)...")
    pipeline.run(reset=False)

    # ---- 4. ASSERT no DW ---------------------------------------------------
    dc.execute("SELECT nome FROM dw.dim_produto WHERE product_oltp_id=%s", (pid,))
    dw_name_after = dc.fetchone()[0]
    dc.execute("SELECT quantidade FROM dw.fct_vendas WHERE sales_order_id=%s AND line_id=%s", (hid, lid))
    dw_qty_after = dc.fetchone()[0]
    wm_prod_after = wm("production.product")
    wm_det_after = wm("sales.salesorderdetail")

    # duplicatas
    dc.execute("SELECT count(*) FROM (SELECT product_oltp_id FROM dw.dim_produto GROUP BY 1 HAVING count(*)>1) x")
    dup_prod = dc.fetchone()[0]
    dc.execute("SELECT count(*) FROM (SELECT sales_order_id,line_id FROM dw.fct_vendas GROUP BY 1,2 HAVING count(*)>1) x")
    dup_fact = dc.fetchone()[0]
    dc.execute("SELECT count(*) FROM dw.fct_vendas")
    fact_total = dc.fetchone()[0]

    check("produto atualizado no DW", dw_name_after == new_name, f"(antes='{dw_name_before}')")
    check("fato atualizado no DW", dw_qty_after == d_qty + 1, f"(antes={dw_qty_before}, esperado={d_qty+1})")
    check("watermark product avançou",
          wm_prod_after is not None and wm_prod_after >= now - dt.timedelta(seconds=1),
          f"{wm_prod_before} -> {wm_prod_after}")
    check("watermark detail avançou",
          wm_det_after is not None and wm_det_after >= now - dt.timedelta(seconds=1),
          f"{wm_det_before} -> {wm_det_after}")
    check("sem duplicatas em dim_produto", dup_prod == 0)
    check("sem duplicatas em fct_vendas", dup_fact == 0)
    check("total de fato estável (121317)", fact_total == 121317, f"(total={fact_total})")

    # ---- 5. RESTAURA a fonte e re-sincroniza o DW ---------------------------
    print("  Restaurando fonte para o estado canônico...")
    sc.execute("UPDATE production.product SET name=%s, modifieddate=%s WHERE productid=%s", (p_name, dt.datetime.now(), pid))
    sc.execute("UPDATE sales.salesorderdetail SET orderqty=%s, modifieddate=%s WHERE salesorderdetailid=%s", (d_qty, dt.datetime.now(), lid))
    src.commit()
    pipeline.run(reset=False)
    dc.execute("SELECT nome FROM dw.dim_produto WHERE product_oltp_id=%s", (pid,))
    check("fonte restaurada e DW re-sincronizado", dc.fetchone()[0] == p_name)

    src.close(); dst.close()

    ok = sum(1 for _, r in results if r)
    print("-" * 62)
    print(f"RESULTADO: {ok}/{len(results)} verificações passaram.")
    if ok != len(results):
        raise SystemExit(1)
    print("✅ ETL incremental validado.")

if __name__ == "__main__":
    main()
