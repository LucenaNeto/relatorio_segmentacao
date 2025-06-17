import pandas as pd

def compute_metrics(df: pd.DataFrame) -> dict[str, float]:
    """
    Calcula, em uma única aba:
      - total_orders
      - total_revenue
      - Para cada categoria de pagamento (boleto, cartão, outras):
        * qty, revenue, %qty sobre total_orders, %revenue sobre total_revenue
    """
    total_orders  = len(df)
    total_revenue = df["ValorLiquido"].sum()

    # máscaras para cada tipo
    mask_boleto = df["PlanoPagamento"].str.contains("boleto", case=False, na=False)
    mask_card   = df["PlanoPagamento"].str.contains("cartão", case=False, na=False)
    mask_other  = ~(mask_boleto | mask_card)

    # cálculo por categoria
    def calc(mask):
        qty     = int(mask.sum())
        rev     = float(df.loc[mask, "ValorLiquido"].sum())
        pct_qty = qty / total_orders if total_orders else 0
        pct_rev = rev / total_revenue if total_revenue else 0
        return qty, rev, pct_qty, pct_rev

    b_qty, b_rev, b_pq, b_pr = calc(mask_boleto)
    c_qty, c_rev, c_pq, c_pr = calc(mask_card)
    o_qty, o_rev, o_pq, o_pr = calc(mask_other)

    return {
        "total_orders":      total_orders,
        "total_revenue":     total_revenue,
        "boleto_qty":        b_qty,
        "boleto_revenue":    b_rev,
        "pct_qty_boleto":    b_pq,
        "pct_rev_boleto":    b_pr,
        "card_qty":          c_qty,
        "card_revenue":      c_rev,
        "pct_qty_card":      c_pq,
        "pct_rev_card":      c_pr,
        "other_qty":         o_qty,
        "other_revenue":     o_rev,
        "pct_qty_other":     o_pq,
        "pct_rev_other":     o_pr,
    }
