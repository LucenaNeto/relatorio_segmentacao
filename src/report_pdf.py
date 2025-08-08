from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, PageBreak, Image as PlatypusImage
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas
from datetime import datetime
import os
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader

# -------------------------------------------------------------------
# Helpers: logo badge (top-right), footer, and BaseDocTemplate builder
# -------------------------------------------------------------------

def _draw_logo_badge(c, logo_path, *, badge_w_mm=36, badge_h_mm=14,
                     margin_mm=12, pad_mm=3, alpha=0.95, radius_mm=4):
    """Desenha a logo no topo direito (paisagem), acima do conteúdo, com um 'chip' branco atrás.
    Ajustes pensados para A4 em modo paisagem:
      - tamanho padrão maior (36×14 mm) para melhor legibilidade
      - margens um pouco menores (12 mm) para alinhar com topo/direita
      - preserva proporção da imagem e limita a altura a ~12% da página
    """
    if not (logo_path and os.path.exists(logo_path)):
        return
    page_w, page_h = landscape(A4)

    # Tamanho base em mm → px
    bw, bh = badge_w_mm * mm, badge_h_mm * mm

    # Tentar preservar aspecto da logo e limitar a dimensão
    try:
        iw, ih = ImageReader(logo_path).getSize()
        ratio = (iw / ih) if ih else 1.0
        # Limites relativos à página (paisagem)
        max_h = 0.20 * page_h  # até 12% da altura
        max_w = 0.26 * page_w  # até 18% da largura
        # Ajusta largura primeiro
        bw = min(bw, max_w)
        bh_calc = bw / ratio
        if bh_calc > max_h:
            bh = max_h
            bw = bh * ratio
        else:
            bh = bh_calc
    except Exception:
        # fallback: usa os mm informados
        pass

    m   = margin_mm * mm
    pad = pad_mm * mm
    x = page_w - m - bw  # canto superior direito
    y = page_h - m - bh

    c.saveState()
    try:
        c.setFillAlpha(alpha)
    except Exception:
        pass  # versões antigas do reportlab sem alpha
    # chip branco de fundo p/ contraste
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(x - pad, y - pad, bw + 2*pad, bh + 2*pad, radius_mm * mm, stroke=0, fill=1)
    # imagem da logo (mantendo proporção calculada)
    c.drawImage(logo_path, x, y, bw, bh, mask='auto')
    c.restoreState()


def _footer(c):
    page_w, _ = landscape(A4)
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.grey)
    c.drawRightString(page_w - 10*mm, 10*mm, f"Página {c.getPageNumber()}")


def _build_doc(story, output_path: str, logo_path: str, *, logo_badge_mm=(36, 14)):
    """Monta o PDF com badge da logo no topo direito (sempre visível) e rodapé."""
    doc = BaseDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')

    def on_page(_c, _d):
        # nada sob o conteúdo (sem watermark tiled)
        pass

    def on_page_end(c, d):
        # desenha badge por cima do conteúdo
        _draw_logo_badge(
            c, logo_path,
            badge_w_mm=logo_badge_mm[0],
            badge_h_mm=logo_badge_mm[1]
        )
        _footer(c)

    tpl = PageTemplate(id='default', frames=[frame], onPage=on_page, onPageEnd=on_page_end)
    doc.addPageTemplates([tpl])
    doc.build(story)


# -----------------------------
# Gráfico: linha por método
# -----------------------------

def _generate_segment_line_chart(segment, metrics, path):
    """Gera gráfico de LINHA da receita por método (ordenado por receita)."""
    items = sorted(metrics['methods'].items(), key=lambda kv: kv[1]['rev'], reverse=True)
    methods = [m.capitalize() for m, _ in items]
    revs = [d['rev'] for _, d in items]

    xs = list(range(len(methods)))
    plt.figure(figsize=(9, 3))
    plt.plot(xs, revs, marker='o')
    plt.xticks(xs, methods, rotation=45, ha='right')
    plt.ylabel('Receita (R$)')
    plt.title(f'Receita por Método – {segment.capitalize()}')
    plt.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path)
    plt.clf()


# ======================================================
# Relatório por segmentação (duas páginas por segmento)
# ======================================================

def build_pdf_report(metrics_dict, graphs_folder, output_path,
                     report_date=None, logo_path=None, logo_badge_mm=(36, 14)):
    """
    Para cada segmentação em metrics_dict, gera:
      • Página 1: título, cards Boleto/Cartão e resumo centralizado
      • Página 2: gráfico de LINHA (Receita por Método) + tabela por método
    """
    # Data
    if report_date is None:
        try:
            report_date = datetime.strptime(os.path.basename(output_path)[:8], "%Y%m%d")
        except Exception:
            report_date = datetime.now()
    date_str = report_date.strftime("%d/%m/%Y")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=22,
                                 textColor=colors.HexColor('#1F618D'), alignment=1, spaceAfter=8)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Heading2'], fontSize=14,
                                    textColor=colors.HexColor('#2874A6'), alignment=1, spaceAfter=10)
    normal = styles['Normal']

    story = []

    for segment, metrics in metrics_dict.items():
        # ===== Página 1 =====
        story.append(Paragraph(f'Detalhamento – {segment.capitalize()}', title_style))
        story.append(Paragraph(f'Data: {date_str}', normal))
        story.append(Spacer(1, 10))
        story.append(Paragraph('Modalidades principais', subtitle_style))

        b = metrics['methods'].get('boleto', {'qty': 0, 'rev': 0, 'pct_qty': 0, 'pct_rev': 0})
        c = metrics['methods'].get('cartão', {'qty': 0, 'rev': 0, 'pct_qty': 0, 'pct_rev': 0})

        card_style = [
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 10)
        ]
        tbl_b = Table([
            ['Boleto', ''],
            ['Pedidos', b['qty']],
            ['Receita', f"R$ {b['rev']:,.2f}"],
            ['% Pedidos', f"{b['pct_qty']*100:.1f}%"],
            ['% Receita', f"{b['pct_rev']*100:.1f}%"],
        ], colWidths=[50 * mm, 30 * mm])
        tbl_b.setStyle(TableStyle(card_style + [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D6EAF8')),
            ('SPAN', (0, 0), (1, 0)),
        ]))
        tbl_c = Table([
            ['Cartão', ''],
            ['Pedidos', c['qty']],
            ['Receita', f"R$ {c['rev']:,.2f}"],
            ['% Pedidos', f"{c['pct_qty']*100:.1f}%"],
            ['% Receita', f"{c['pct_rev']*100:.1f}%"],
        ], colWidths=[50 * mm, 30 * mm])
        tbl_c.setStyle(TableStyle(card_style + [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FADBD8')),
            ('SPAN', (0, 0), (1, 0)),
        ]))
        story.append(Table([[tbl_b, tbl_c]], colWidths=[85 * mm, 85 * mm], hAlign='CENTER'))
        story.append(Spacer(1, 12))

        data_main = [[
            'Indicador', 'Valor'
        ], [
            'Total Pedidos', metrics['total_orders']
        ], [
            'Receita Total', f"R$ {metrics['total_revenue']:,.2f}"
        ], [
            'Pedidos Boleto', b['qty']
        ], [
            'Receita Boleto', f"R$ {b['rev']:,.2f}"
        ], [
            'Pedidos Cartão', c['qty']
        ], [
            'Receita Cartão', f"R$ {c['rev']:,.2f}"
        ]]
        tbl_main = Table(data_main, colWidths=[70 * mm, 40 * mm], hAlign='CENTER')
        tbl_main.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E4053')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, 0), 12), ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
        ]))
        story.append(tbl_main)

        # ===== Página 2 =====
        story.append(PageBreak())
        story.append(Paragraph('Receita por Método', subtitle_style))
        detail_chart = os.path.join(graphs_folder, f'linhas_{segment}_{report_date:%Y-%m}.png')
        _generate_segment_line_chart(segment, metrics, detail_chart)
        if os.path.exists(detail_chart):
            story.append(PlatypusImage(detail_chart, width=180 * mm, height=80 * mm))
            story.append(Spacer(1, 10))

        method_rows = [['Método', 'Pedidos', 'Receita (R$)', '% Pedidos', '% Receita']]
        for method, vals in sorted(metrics['methods'].items(), key=lambda kv: kv[1]['rev'], reverse=True):
            method_rows.append([
                method.capitalize(),
                vals['qty'],
                f"R$ {vals['rev']:,.2f}",
                f"{vals['pct_qty']*100:.1f}%",
                f"{vals['pct_rev']*100:.1f}%",
            ])
        tbl_methods = Table(method_rows, colWidths=[60 * mm, 30 * mm, 40 * mm, 30 * mm, 30 * mm], hAlign='CENTER')
        tbl_methods.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, 0), 11), ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
        ]))
        story.append(tbl_methods)
        story.append(PageBreak())

    # Build com logo-badge visível
    _build_doc(story, output_path, logo_path, logo_badge_mm=logo_badge_mm)


# ======================================================
# Relatório comparativo: total + % participação
# ======================================================

def build_comparative_report(metrics_dict, output_path, report_date=None, logo_path=None, logo_badge_mm=(36, 14)):
    """
    Gera um PDF comparativo entre segmentações com:
      • Gráfico de barras da receita total por segmentação (ordenado)
      • KPI de Receita Total (todas as segmentações)
      • Tabela com Receita e % de participação no total por segmentação
    """
    if report_date is None:
        try:
            report_date = datetime.strptime(os.path.basename(output_path)[:8], "%Y%m%d")
        except Exception:
            report_date = datetime.now()
    date_str = report_date.strftime("%d/%m/%Y")

    total_geral = float(sum(m['total_revenue'] for m in metrics_dict.values()))
    ordered = sorted(metrics_dict.items(), key=lambda x: x[1]['total_revenue'], reverse=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=22,
                                 textColor=colors.HexColor('#1F618D'), alignment=1, spaceAfter=8)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Heading2'], fontSize=14,
                                    textColor=colors.HexColor('#2874A6'), alignment=1, spaceAfter=8)
    normal = styles['Normal']

    story = []
    story.append(Paragraph('Comparativo entre Segmentações', title_style))
    story.append(Paragraph(f'Data: {date_str}', normal))
    story.append(Spacer(1, 8))

    # Chart
    segs = [s.capitalize() for s, _ in ordered]
    revs = [m['total_revenue'] for _, m in ordered]
    chart_path = os.path.join(os.path.dirname(output_path), f'comparativo_{report_date:%Y-%m}.png')
    plt.figure(figsize=(10, 4))
    plt.bar(segs, revs, color='#5DADE2')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Receita (R$)')
    plt.title('Receita Total por Segmentação')
    plt.tight_layout()
    os.makedirs(os.path.dirname(chart_path), exist_ok=True)
    plt.savefig(chart_path)
    plt.clf()
    if os.path.exists(chart_path):
        story.append(PlatypusImage(chart_path, width=180 * mm, height=80 * mm))
        story.append(Spacer(1, 8))

    # KPI Total
    kpi = Table([["Receita Total (Todas as Segmentações)", f"R$ {total_geral:,.2f}"]],
                colWidths=[120 * mm, 60 * mm], hAlign='CENTER')
    kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F618D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, 0), 13),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#1F618D')),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.lightgrey)
    ]))
    story.append(kpi)
    story.append(Spacer(1, 8))

    # Tabela com % de participação
    data = [['Segmentação', 'Receita Total (R$)', '% do Total']]
    for seg, m in ordered:
        receita = float(m['total_revenue'])
        pct = (receita / total_geral * 100) if total_geral else 0.0
        data.append([seg.capitalize(), f"{receita:,.2f}", f"{pct:.2f}%"])
    tbl = Table(data, colWidths=[90 * mm, 60 * mm, 30 * mm], hAlign='CENTER')
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F618D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('FONTSIZE', (0, 0), (-1, 0), 12), ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
    ]))
    story.append(tbl)

    # Build com logo-badge visível
    _build_doc(story, output_path, logo_path, logo_badge_mm=logo_badge_mm)
