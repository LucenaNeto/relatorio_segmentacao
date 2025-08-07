from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as PlatypusImage
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas
from datetime import datetime
import os



def build_pdf_report(metrics_dict, graphs_folder, output_path, report_date=None, logo_path=None):
   
    # Data e hora
    if report_date is None:
        fname = os.path.basename(output_path)
        try:
            report_date = datetime.strptime(fname[:8], "%Y%m%d")
        except:
            report_date = datetime.now()
    date_str = report_date.strftime("%d/%m/%Y")

    # Marca d'água e numeração de páginas
    def add_watermark(c: pdfcanvas.Canvas, doc):
        if logo_path and os.path.exists(logo_path):
            c.saveState()
            try:
                c.setFillAlpha(0.15)
            except:
                pass
            w, h = landscape(A4)
            img_w, img_h = 140 * mm, 140 * mm
            x = (w - img_w) / 2
            y = (h - img_h) / 2
            c.drawImage(logo_path, x, y, width=img_w, height=img_h, mask='auto')
            c.restoreState()
        
        page_num = c.getPageNumber()
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.grey)
        c.drawRightString(w - 10*mm, 10*mm, f"Página {page_num}")

    # Documento
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles['Title'], fontSize=20,
        textColor=colors.HexColor('#2E4053'), alignment=1, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle", parent=styles['Heading2'], fontSize=14,
        textColor=colors.HexColor('#4F81BD'), alignment=1, spaceAfter=12
    )
    story = []

    # segmentação
    for segment, metrics in metrics_dict.items():
        # Header
        story.append(Paragraph(f"Relatório: {segment.capitalize()}", title_style))
        story.append(Paragraph(f"Data: {date_str}", styles['Normal']))
        story.append(Spacer(1, 12))
        # Payment mode cards section
        story.append(Paragraph("<b>Modalidades Principais</b>", subtitle_style))
        boleto = metrics['methods']['boleto']
        cartao = metrics['methods']['cartão']
        card_common = [('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('GRID',(0,0),(-1,-1),0.5,colors.lightgrey)]
        tbl_boleto = Table([
            ['Boleto', ''],
            ['Pedidos', boleto['qty']],
            ['Receita', f"R$ {boleto['rev']:,.2f}"],
            ['% Pedidos', f"{boleto['pct_qty']*100:.1f}%"],
            ['% Receita', f"{boleto['pct_rev']*100:.1f}%"]
        ], colWidths=[50*mm, 30*mm])
        tbl_boleto.setStyle(TableStyle(card_common + [
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#D6EAF8')), ('SPAN',(0,0),(1,0))
        ]))
        tbl_cartao = Table([
            ['Cartão', ''],
            ['Pedidos', cartao['qty']],
            ['Receita', f"R$ {cartao['rev']:,.2f}"],
            ['% Pedidos', f"{cartao['pct_qty']*100:.1f}%"],
            ['% Receita', f"{cartao['pct_rev']*100:.1f}%"]
        ], colWidths=[50*mm, 30*mm])
        tbl_cartao.setStyle(TableStyle(card_common + [
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#FADBD8')), ('SPAN',(0,0),(1,0))
        ]))
        story.append(Table([[tbl_boleto, tbl_cartao]], colWidths=[80*mm,80*mm], hAlign='CENTER'))
        story.append(Spacer(1, 16))

        # Sumario
        story.append(Paragraph("<b> Resumo Consolidado </b>", subtitle_style))
        data_main = [['Indicador','Valor'],
                     ['Total Pedidos', metrics['total_orders']],
                     ['Receita Total', f"R$ {metrics['total_revenue']:,.2f}"]]
        for key in ['boleto','cartão']:
            m = metrics['methods'][key]
            data_main += [
                [f"Pedidos {key.capitalize()}", m['qty']],
                [f"Receita {key.capitalize()}", f"R$ {m['rev']:,.2f}"],
                [f"% Pedidos {key.capitalize()}", f"{m['pct_qty']*100:.1f}%"],
                [f"% Receita {key.capitalize()}", f"{m['pct_rev']*100:.1f}%"]
            ]
        tbl_main = Table(data_main, colWidths=[70*mm,40*mm], hAlign='CENTER')
        tbl_main.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#2E4053')), ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('ALIGN',(1,1),(-1,-1),'RIGHT'), ('GRID',(0,0),(-1,-1),0.3,colors.lightgrey),
            ('FONTSIZE',(0,0),(-1,0),12), ('FONTSIZE',(0,1),(-1,-1),9),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.lightgrey])
        ]))
        story.append(tbl_main)
        story.append(Spacer(1, 12))

        # Metodos adiconais nos planos de pagamento
        for method, m in metrics['methods'].items():
            if method in ('boleto','cartão'): continue
            story.append(PageBreak())
            story.append(Paragraph(f"Relatório Método: {method.capitalize()}", title_style))
            story.append(Paragraph(f"Segmentação: {segment.capitalize()}", styles['Normal']))
            story.append(Paragraph(f"Data: {date_str}", styles['Normal']))
            story.append(Spacer(1,12))
            data_method = [['Indicador','Valor'],
                           ['Pedidos', m['qty']],
                           ['Receita', f"R$ {m['rev']:,.2f}"],
                           ['% Pedidos', f"{m['pct_qty']*100:.1f}%"],
                           ['% Receita', f"{m['pct_rev']*100:.1f}%"]]
            tbl_m = Table(data_method, colWidths=[70*mm,40*mm], hAlign='CENTER')
            tbl_m.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#34495E')),
                ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                ('ALIGN',(1,1),(-1,-1),'RIGHT'),('GRID',(0,0),(-1,-1),0.3,colors.lightgrey),
                ('FONTSIZE',(0,0),(-1,0),12),('FONTSIZE',(0,1),(-1,-1),9),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.lightgrey])
            ]))
            story.append(tbl_m)
            story.append(Spacer(1,12))

        
        story.append(PageBreak())

    
    if logo_path and os.path.exists(logo_path):
        doc.build(story, onFirstPage=add_watermark, onLaterPages=add_watermark)
    else:
        doc.build(story)
