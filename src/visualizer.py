import matplotlib.pyplot as plt
import os
from datetime import datetime

def plot_payment_methods(metrics_dict: dict, out_folder: str):
    """
    Gera um gráfico de barras empilhadas comparando receita de:
    Boleto, Cartão e Outras modalidades, por segmentação.
    """
    segments = list(metrics_dict.keys())
    rev_b = [metrics_dict[s]["boleto_revenue"] for s in segments]
    rev_c = [metrics_dict[s]["card_revenue"]   for s in segments]
    rev_o = [metrics_dict[s]["other_revenue"]  for s in segments]

    x = range(len(segments))
    plt.bar(x, rev_b)
    plt.bar(x, rev_c, bottom=rev_b)
    bottom_bc = [b + c for b, c in zip(rev_b, rev_c)]
    plt.bar(x, rev_o, bottom=bottom_bc)

    plt.xticks(x, segments, rotation=45, ha="right")
    plt.ylabel("Receita (R$)")
    plt.title(f"Receita por Modalidade — {datetime.now():%B %Y}")
    plt.tight_layout()

    os.makedirs(out_folder, exist_ok=True)
    path = os.path.join(out_folder, f"payment_methods_{datetime.now():%Y-%m}.png")
    plt.savefig(path)
    plt.clf()
    return path
