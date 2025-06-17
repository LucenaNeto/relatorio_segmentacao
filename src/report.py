import pandas as pd
from openpyxl import load_workbook

def build_report(metrics_dict: dict[str, dict], template_path: str, output_path: str):
    """
    Cria (ou recria) uma aba 'RESULTADOS' no Excel, 
    garantindo que ao menos UMA aba esteja visível.
    """
    # 1) carrega o template
    book = load_workbook(template_path)

    # 2) garante que todas as abas estão visíveis (pelo menos uma precisa estar)
    for ws in book.worksheets:
        ws.sheet_state = 'visible'

    # 3) monta o DataFrame de resultados
    df = pd.DataFrame(metrics_dict).T
    df.columns = [
      "QT Total de Pedidos","Receita Total",
      "Receita Boletos","QT Boletos","% QT Boleto","% Receitas Boleto",
      "Receita Cartão","QT Cartão","% QT Cartão","% Receitas Cartão"
    ]

    # 4) prepara o ExcelWriter atrelando ao workbook já carregado
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        writer.book = book
        # importante: informar ao writer as abas existentes
        writer.sheets = {ws.title: ws for ws in book.worksheets}

        # 5) escreve a aba de resultados (vai substituir se já existir)
        df.to_excel(writer, sheet_name="RESULTADOS", index_label="PAPEL")

        # 6) salva
        writer.save()
