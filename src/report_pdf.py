from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from datetime import datetime
import os

def build_pdf_report(metrics_dict: dict, graphs_folder: str, output_path: str, report_date: datetime = None):
    """
    Gera um PDF em A4 paisagem contendo:
      - Cabeçalho 'Relatório - DATA'
      - Seção para cada segmentação com seus indicadores
      - Gráficos em outra página
    """
    # Extrai data do nome do arquivo se não fornecida
    if report_date is None:
        filename = os.path.basename(output_path)
        date_str = filename[:8]  # AAAAMMDD
        try:
            report_date = datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            report_date = datetime.now()
    formatted_date = report_date.strftime("%d/%m/%Y")

    # Documento em landscape A4 e margens de 10 mm
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm,
        topMargin=10*mm, bottomMargin=10*mm
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Title"], fontSize=16, leading=18, alignment=1
    )
    header_style = ParagraphStyle(
        "header", parent=styles["Heading2"], fontSize=14, leading=16
    )
    normal_style = styles["Normal"]

    story = []

    # 1) Cabeçalho
    title = Paragraph(f"Relatório - {formatted_date}", title_style)
    story.append(title)
    story.append(Spacer(1, 6))

    # 2) Seções por segmentação
    for segment, m in metrics_dict.items():
        story.append(Paragraph(segment.capitalize(), header_style))
        story.append(Spacer(1, 4))

        # Tabela de indicadores
        data = [
            ["Receita Total", f"R$ {m['total_revenue']:,.2f}"],
            ["QT Total de Pedidos", m['total_orders']],
            ["Receita Total de Boletos", f"R$ {m['boleto_revenue']:,.2f}"],
            ["QT de Boletos", m['boleto_qty']],
            ["% QT de Boletos / QT Total de Pedidos", f"{m['pct_qty_boleto']*100:.1f}%"],
            ["Receita de Boletos / Total", f"{m['pct_rev_boleto']*100:.1f}%"],
            ["Receita de Cartão", f"R$ {m['card_revenue']:,.2f}"],
            ["QT de Cartão", m['card_qty']],
            ["% QT de Cartão / QT Total de Pedidos", f"{m['pct_qty_card']*100:.1f}%"],
            ["Receita Cartão / Total", f"{m['pct_rev_card']*100:.1f}%"],
        ]
        col_widths = [50*mm, 30*mm]
        tbl = Table(data, colWidths=col_widths)
        tbl.setStyle(TableStyle([
            ('ALIGN',(1,0),(-1,-1),'RIGHT'),
            ('FONTSIZE',(0,0),(-1,-1),8),
            ('BOTTOMPADDING',(0,0),(-1,-1),2),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 8))

    # 3) Gráficos em nova página
    story.append(PageBreak())
    graph_path = os.path.join(
        graphs_folder, f"boleto_vs_cartao_{report_date:%Y-%m}.png"
    )
    if os.path.exists(graph_path):
        story.append(Paragraph("Gráficos", header_style))
        story.append(Spacer(1, 6))
        usable_width = landscape(A4)[0] - 20*mm
        img = Image(graph_path, width=usable_width, height=usable_width * 0.4)
        story.append(img)

    # Finaliza construção
    doc.build(story)
