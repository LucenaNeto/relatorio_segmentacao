import os
from glob import glob
from datetime import datetime
from src.loader import load_sheets
from src.metrics import compute_metrics
from src.visualizer import plot_payment_methods
from src.report_pdf import build_pdf_report, build_comparative_report

# Diretórios de entrada e saída
DATA_DIR = r"C:\Users\NOTE_TI_CARLOS\Projetos_py\relatorio_seguimentacao\data"
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
GRAPH_DIR = os.path.join(OUTPUT_DIR, "graficos")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)

# Segmentações (abas) a processar
SHEETS = ["bronze", "prata", "ouro", "platina", "rubi", "esmeralda", "diamante"]

def extract_date_from_filename(path: str) -> datetime:
    import re
    name = os.path.basename(path)
    m = re.search(r"(\d{8})", name)
    return datetime.strptime(m.group(1), "%Y%m%d") if m else datetime.now()


def process_file(filepath: str):
    """
    Processa um arquivo Excel inteiro:
      - gera PDF individual por segmentação
      - coleta métricas e gera relatório comparativo ao final
    """
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    report_date = extract_date_from_filename(filepath)

    # Carrega todas as abas e calcula métricas isoladas
    data_dict = load_sheets(filepath)
    metrics_all = {}
    for sheet in SHEETS:
        df = data_dict.get(sheet)
        if df is None:
            print(f"⚠️ Aba '{sheet}' não encontrada em {base_name}")
            continue
        # filtra linhas do segmento
        df_seg = df[df['segmentacao'].str.lower().str.contains(sheet, na=False)]
        if df_seg.empty:
            print(f"⚠️ Sem dados para segmento '{sheet}' em {base_name}")
            continue
        # calcula métricas e salva
        metrics = compute_metrics(df_seg)
        metrics_all[sheet] = metrics
        # gera gráfico e PDF por segmento
        plot_payment_methods({sheet: metrics}, GRAPH_DIR)
        out_pdf = os.path.join(OUTPUT_DIR, f"relatorio_{sheet}_{base_name}.pdf")
        build_pdf_report(
            {sheet: metrics}, GRAPH_DIR, out_pdf,
            report_date, logo_path=r"C:\Users\NOTE_TI_CARLOS\Projetos_py\relatorio_seguimentacao\assets\logo.png"
        )
        print(f"→ PDF gerado para {sheet}: {out_pdf}")

    # Após todos os segmentos, gera comparativo se houver dados
    if metrics_all:
        comp_out = os.path.join(OUTPUT_DIR, f"comparativo_{base_name}.pdf")
        build_comparative_report(
            metrics_all, comp_out,
            report_date, logo_path=r"C:\Users\NOTE_TI_CARLOS\Projetos_py\relatorio_seguimentacao\assets\logo.png"
        )
        print(f"→ PDF comparativo gerado em: {comp_out}")


def main():
    excel_files = glob(os.path.join(DATA_DIR, "*.xlsx"))
    if not excel_files:
        print(f"⚠️ Nenhum arquivo .xlsx encontrado em {DATA_DIR}")
        return
    for excel in excel_files:
        print(f"\nProcessando arquivo: {os.path.basename(excel)}")
        process_file(excel)

if __name__ == "__main__":
    main()
