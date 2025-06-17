import os
from glob import glob
from datetime import datetime
from src.loader      import load_sheets
from src.metrics     import compute_metrics
from src.visualizer  import plot_payment_methods
from src.report_pdf  import build_pdf_report

# Diretórios de entrada e saída
DATA_DIR   = r"C:\Users\NOTE_TI_CARLOS\Projetos_py\relatorio_seguimentacao\data"
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
GRAPH_DIR  = os.path.join(OUTPUT_DIR, "graficos")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)

# Segmentações (abas) a processar
SHEETS = ["bronze", "prata", "ouro", "platina", "rubi", "esmeralda", "diamante"]

def extract_date_from_filename(path: str) -> datetime:
    import re
    name = os.path.basename(path)
    m = re.search(r"(\d{8})", name)
    return datetime.strptime(m.group(1), "%Y%m%d") if m else datetime.now()


def process_sheet(filepath: str, sheet: str):
    """
    Processa uma única aba (segmentação), gera gráfico e PDF próprio.
    """
    # 1) Carrega todas as abas do arquivo
    data_dict = load_sheets(filepath)

    # 2) Obtém o DataFrame bruto da aba específica
    if sheet not in data_dict:
        print(f"⚠️ Aba '{sheet}' não encontrada em {os.path.basename(filepath)}")
        return
    raw_df = data_dict[sheet]

    # 3) Filtra apenas as linhas correspondentes à segmentação
    df = raw_df[ raw_df['segmentacao'].str.lower() == sheet ]
    if df.empty:
        print(f"⚠️ Sem dados para segmento '{sheet}' em {os.path.basename(filepath)}")
        return

    # 4) Calcula métricas isoladas para esta segmentação
    metrics = compute_metrics(df)

    # 5) Gera gráfico exclusivo desta segmentação
    plot_payment_methods({sheet: metrics}, GRAPH_DIR)

    # 6) Prepara data e saída de PDF
    report_date = extract_date_from_filename(filepath)
    base_name   = os.path.splitext(os.path.basename(filepath))[0]
    out_pdf     = os.path.join(
        OUTPUT_DIR,
        f"relatorio_{sheet}_{base_name}.pdf"
    )
    # 7) Gera PDF apenas para esta segmentação
    build_pdf_report({sheet: metrics}, GRAPH_DIR, out_pdf, report_date)
    print(f"→ PDF gerado para {sheet}: {out_pdf}")


def main():
    # Localiza todos os arquivos .xlsx na pasta
    excel_files = glob(os.path.join(DATA_DIR, "*.xlsx"))
    if not excel_files:
        print(f"⚠️ Nenhum arquivo .xlsx encontrado em {DATA_DIR}")
        return
    for excel in excel_files:
        print(f"\nProcessando arquivo: {os.path.basename(excel)}")
        for sheet in SHEETS:
            process_sheet(excel, sheet)

if __name__ == "__main__":
    main()
