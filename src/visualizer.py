import matplotlib.pyplot as plt
import os
from datetime import datetime

def plot_payment_methods(metrics_dict: dict, out_folder: str):
    """
    Gera um gráfico de barras empilhadas comparando receita de boleto, cartão e demais métodos
    por segmentação.
    """
    segments = list(metrics_dict.keys())
    # Descobre todos os métodos
    methods = set()
    for seg in segments:
        methods.update(metrics_dict[seg]['methods'].keys())
    # Ordena métodos: boleto, cartão e depois demais em ordem alfabética
    order = ['boleto', 'cartão'] + sorted(m for m in methods if m not in ('boleto', 'cartão'))

    # Prepara dados de receita por método e segmentação
    rev_data = {m: [metrics_dict[seg]['methods'][m]['rev'] for seg in segments] for m in order}

    x = range(len(segments))
    bottoms = [0] * len(segments)

    plt.figure()
    for method in order:
        revs = rev_data[method]
        plt.bar(x, revs, bottom=bottoms, label=method.capitalize())
        bottoms = [b + r for b, r in zip(bottoms, revs)]

    plt.xticks(x, [s.capitalize() for s in segments], rotation=45, ha="right")
    plt.ylabel("Receita (R$)")
    plt.title(f"Receita por Modalidade — {datetime.now():%B %Y}")
    plt.legend()
    plt.tight_layout()

    os.makedirs(out_folder, exist_ok=True)
    path = os.path.join(out_folder, f"payment_methods_{datetime.now():%Y-%m}.png")
    plt.savefig(path)
    plt.clf()
    return path
