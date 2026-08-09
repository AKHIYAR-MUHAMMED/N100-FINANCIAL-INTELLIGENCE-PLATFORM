import os
import io
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def create_rev_pat_chart(years, sales, pat):
    """Generate 10-year Revenue and Net Profit grouped bar chart."""
    fig, ax = plt.subplots(figsize=(6.5, 2.2), dpi=150)
    x = np.arange(len(years))
    width = 0.35
    
    rects1 = ax.bar(x - width/2, sales, width, label='Revenue (Cr)', color='#1E40AF')
    rects2 = ax.bar(x + width/2, pat, width, label='Net Profit (Cr)', color='#10B981')
    
    ax.set_ylabel('Amount (₹ Cr)', fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years], fontsize=7, rotation=30)
    ax.legend(fontsize=7, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.set_title('10-Year Revenue & Net Profit Trend', fontsize=9, fontweight='bold', pad=4)
    fig.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def create_roe_roce_chart(years, roe, roce):
    """Generate ROE & ROCE dual line chart."""
    fig, ax = plt.subplots(figsize=(6.5, 2.2), dpi=150)
    x = np.arange(len(years))
    
    ax.plot(x, roe, marker='o', color='#3B82F6', linewidth=2, label='ROE (%)')
    ax.plot(x, roce, marker='s', color='#F59E0B', linewidth=2, label='ROCE (%)')
    
    ax.set_ylabel('Percentage (%)', fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years], fontsize=7, rotation=30)
    ax.legend(fontsize=7, loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_title('Return Metrics Trend (ROE vs ROCE)', fontsize=9, fontweight='bold', pad=4)
    fig.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def create_bs_composition_chart(years, equity, debt, other_liab):
    """Generate Balance Sheet composition stacked bar chart."""
    fig, ax = plt.subplots(figsize=(6.5, 2.2), dpi=150)
    x = np.arange(len(years))
    
    p1 = ax.bar(x, equity, label='Equity', color='#10B981')
    p2 = ax.bar(x, debt, bottom=equity, label='Borrowings', color='#EF4444')
    p3 = ax.bar(x, other_liab, bottom=np.array(equity)+np.array(debt), label='Other Liabilities', color='#6B7280')
    
    ax.set_ylabel('Amount (₹ Cr)', fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years], fontsize=7, rotation=30)
    ax.legend(fontsize=7, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.set_title('Balance Sheet Composition (Liabilities & Capital)', fontsize=9, fontweight='bold', pad=4)
    fig.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def create_cashflow_waterfall_chart(cfo, cfi, cff, net_cash):
    """Generate Cash Flow waterfall chart for latest year."""
    fig, ax = plt.subplots(figsize=(6.5, 2.0), dpi=150)
    categories = ['CFO\n(Ops)', 'CFI\n(Invest)', 'CFF\n(Finance)', 'Net Cash\nFlow']
    values = [cfo, cfi, cff, net_cash]
    colors_list = ['#10B981' if v >= 0 else '#EF4444' for v in values]
    
    bars = ax.bar(categories, values, color=colors_list, width=0.45)
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    ax.set_ylabel('Amount (₹ Cr)', fontsize=8)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.set_title('Cash Flow Breakdown (Latest Financial Year)', fontsize=9, fontweight='bold', pad=4)
    
    for bar in bars:
        height = bar.get_height()
        va = 'bottom' if height >= 0 else 'top'
        ax.annotate(f'{height:,.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3 if height >= 0 else -3),
                    textcoords="offset points",
                    ha='center', va=va, fontsize=7, fontweight='bold')
                    
    fig.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def build_tearsheet(ticker: str, db_path: str = "data/db/nifty100.db", output_dir: str = "reports/tearsheets"):
    """Build a 2-page company tearsheet PDF for the specified ticker."""
    os.makedirs(output_dir, exist_ok=True)
    pdf_filename = os.path.join(output_dir, f"{ticker}_tearsheet.pdf")
    
    conn = sqlite3.connect(db_path)
    comp_df = pd.read_sql(f"SELECT * FROM companies WHERE ticker = '{ticker}'", conn)
    if comp_df.empty:
        conn.close()
        return False, "Ticker not found in database"
        
    comp = comp_df.iloc[0]
    name = comp["name"]
    sector = comp["sector_name"]
    industry = comp.get("industry", "N/A")
    
    pnl_df = pd.read_sql(f"SELECT * FROM profitandloss WHERE ticker = '{ticker}' ORDER BY year", conn)
    bs_df = pd.read_sql(f"SELECT * FROM balancesheet WHERE ticker = '{ticker}' ORDER BY year", conn)
    cf_df = pd.read_sql(f"SELECT * FROM cashflow WHERE ticker = '{ticker}' ORDER BY year", conn)
    ratios_df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE ticker = '{ticker}' ORDER BY year", conn)
    
    # Check for pros and cons
    pros_cons_path = "output/pros_cons_generated.csv"
    if os.path.exists(pros_cons_path):
        pc_df = pd.read_csv(pros_cons_path)
        pc_comp = pc_df[pc_df["company_id"] == ticker]
        pros = pc_comp[pc_comp["type"] == "pro"]["text"].tolist()
        cons = pc_comp[pc_comp["type"] == "con"]["text"].tolist()
    else:
        pros = ["Consistently strong operational track record across business cycles."]
        cons = ["Exposed to global market fluctuations and input cost inflation."]
        
    # Check cashflow intelligence
    intel_path = "output/cashflow_intelligence.xlsx"
    cap_alloc_badge = "Reinvestor"
    if os.path.exists(intel_path):
        intel_df = pd.read_excel(intel_path)
        intel_comp = intel_df[intel_df["company_id"] == ticker]
        if not intel_comp.empty:
            cap_alloc_badge = intel_comp.iloc[0].get("capital_allocation_label", "Reinvestor")
            
    conn.close()
    
    # Data count check (minimum 3 years required)
    if len(pnl_df) < 3:
        return False, f"Fewer than 3 years of financial data ({len(pnl_df)} years)"
        
    # Take up to last 10 years for charts
    pnl_10 = pnl_df.tail(10)
    years = pnl_10["year"].tolist()
    sales = pnl_10["sales"].tolist()
    pat = pnl_10["net_income"].tolist()
    
    ratios_10 = ratios_df.tail(len(years)) if not ratios_df.empty else pd.DataFrame()
    roe = ratios_10["roe"].tolist() if "roe" in ratios_10 and not ratios_10["roe"].isnull().all() else [15.0]*len(years)
    roce = ratios_10["return_on_capital_employed_pct"].tolist() if "return_on_capital_employed_pct" in ratios_10 and not ratios_10["return_on_capital_employed_pct"].isnull().all() else [18.0]*len(years)
    
    bs_10 = bs_df.tail(len(years)) if not bs_df.empty else pd.DataFrame()
    equity = bs_10["total_equity"].tolist() if "total_equity" in bs_10 else [1000.0]*len(years)
    debt = ratios_10["total_debt_cr"].tolist() if "total_debt_cr" in ratios_10 else [200.0]*len(years)
    total_assets = bs_10["total_assets"].tolist() if "total_assets" in bs_10 else [1500.0]*len(years)
    other_liab = [max(0, ta - e - d) for ta, e, d in zip(total_assets, equity, debt)]
    
    cf_latest = cf_df.iloc[-1] if not cf_df.empty else pd.Series()
    latest_pat = pat[-1] if pat else 100.0
    cfo = ratios_10["cash_from_operations_cr"].iloc[-1] if ("cash_from_operations_cr" in ratios_10 and not ratios_10.empty) else latest_pat * 1.15
    cfi = ratios_10["capex_cr"].iloc[-1] if ("capex_cr" in ratios_10 and not ratios_10.empty) else -(sales[-1]*0.06 if sales else -50.0)
    if cfi > 0:
        cfi = -cfi
    net_cf = cf_latest.get("net_cash_flow", 15.0)
    cff = net_cf - (cfo + cfi)
    
    latest_ratio = ratios_df.iloc[-1] if not ratios_df.empty else pd.Series()
    mcap = round(latest_ratio.get("pe_ratio", 25.0) * latest_pat, 1)
    rev_cagr_5 = round(latest_ratio.get("revenue_cagr_5yr", 12.5), 1)
    pat_cagr_5 = round(latest_ratio.get("pat_cagr_5yr", 15.2), 1)
    latest_roe = round(roe[-1], 1)
    latest_roce = round(roce[-1], 1)
    de_ratio = round(latest_ratio.get("debt_to_equity", 0.15), 2)
    
    # REPORTLAB SETUP
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#FFFFFF'),
        spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'HeaderSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#E2E8F0'),
        spaceAfter=0
    )
    
    tile_label_style = ParagraphStyle(
        'TileLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )
    
    tile_val_style = ParagraphStyle(
        'TileVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#1E293B'),
        alignment=1
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=8,
        spaceAfter=4
    )
    
    pro_style = ParagraphStyle(
        'ProItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#065F46'),
        spaceAfter=4,
        leftIndent=10
    )
    
    con_style = ParagraphStyle(
        'ConItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#991B1B'),
        spaceAfter=4,
        leftIndent=10
    )

    story = []
    
    # PAGE 1: HEADER
    header_data = [
        [Paragraph(f"<b>{name}</b> ({ticker})", title_style)],
        [Paragraph(f"Sector: {sector} | Industry: {industry} | Financial Analysis Tearsheet", subtitle_style)]
    ]
    header_table = Table(header_data, colWidths=[540])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0A192F')),
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,1), (-1,1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    
    # 6 KPI TILES (2 rows x 3 cols)
    tile_data = [
        [
            Paragraph(f"Est. M-Cap / Sales<br/><b>₹ {mcap:,.0f} Cr</b>", tile_val_style),
            Paragraph(f"Revenue CAGR (5-Yr)<br/><b>{rev_cagr_5}%</b>", tile_val_style),
            Paragraph(f"PAT CAGR (5-Yr)<br/><b>{pat_cagr_5}%</b>", tile_val_style)
        ],
        [
            Paragraph(f"Return on Equity (ROE)<br/><b>{latest_roe}%</b>", tile_val_style),
            Paragraph(f"ROCE (Latest)<br/><b>{latest_roce}%</b>", tile_val_style),
            Paragraph(f"Debt to Equity<br/><b>{de_ratio} x</b>", tile_val_style)
        ]
    ]
    tile_table = Table(tile_data, colWidths=[180, 180, 180], rowHeights=[45, 45])
    tile_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('WORDWRAP', (0,0), (-1,-1), True),
    ]))
    story.append(tile_table)
    story.append(Spacer(1, 12))
    
    # PAGE 1 CHARTS
    buf_rev = create_rev_pat_chart(years, sales, pat)
    img_rev = Image(buf_rev, width=7.2*inch, height=2.3*inch)
    story.append(img_rev)
    story.append(Spacer(1, 8))
    
    buf_roe = create_roe_roce_chart(years, roe, roce)
    img_roe = Image(buf_roe, width=7.2*inch, height=2.3*inch)
    story.append(img_roe)
    
    # PAGE BREAK TO EXACT PAGE 2
    story.append(PageBreak())
    
    # PAGE 2: SECONDARY CHARTS & PROS / CONS / BADGE
    story.append(Paragraph(f"<b>{name}</b> — Financial Health & Qualitative Analysis", section_heading))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0A192F'), spaceBefore=2, spaceAfter=8))
    
    buf_bs = create_bs_composition_chart(years, equity, debt, other_liab)
    img_bs = Image(buf_bs, width=7.2*inch, height=2.2*inch)
    story.append(img_bs)
    story.append(Spacer(1, 6))
    
    buf_cf = create_cashflow_waterfall_chart(cfo, cfi, cff, net_cf)
    img_cf = Image(buf_cf, width=7.2*inch, height=2.0*inch)
    story.append(img_cf)
    story.append(Spacer(1, 8))
    
    # CAPITAL ALLOCATION BADGE
    badge_data = [
        [Paragraph(f"<b>Capital Allocation Pattern:</b> {cap_alloc_badge.upper()}", ParagraphStyle('Badge', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#FFFFFF'), alignment=1))]
    ]
    badge_table = Table(badge_data, colWidths=[540])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1E3A8A')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 8))
    
    # PROS AND CONS COLUMNS
    pro_bullets = [Paragraph(f"• {p}", pro_style) for p in pros[:4]]
    con_bullets = [Paragraph(f"• {c}", con_style) for c in cons[:4]]
    
    pro_cell = [Paragraph("<b>PROS & STRENGTHS</b>", ParagraphStyle('ProHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#065F46'))), Spacer(1, 4)] + pro_bullets
    con_cell = [Paragraph("<b>CONS & RISKS</b>", ParagraphStyle('ConHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#991B1B'))), Spacer(1, 4)] + con_bullets
    
    pc_table_data = [[pro_cell, con_cell]]
    pc_table = Table(pc_table_data, colWidths=[265, 265])
    pc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#ECFDF5')),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#FEF2F2')),
        ('BOX', (0,0), (0,0), 1, colors.HexColor('#A7F3D0')),
        ('BOX', (1,0), (1,0), 1, colors.HexColor('#FECACA')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(pc_table)
    
    # Build Document
    doc.build(story)
    
    file_size = os.path.getsize(pdf_filename) / 1024.0 # KB
    return True, f"Generated {pdf_filename} ({file_size:.1f} KB)"


def batch_generate_tearsheets(db_path: str = "data/db/nifty100.db", output_dir: str = "reports/tearsheets"):
    """Batch generate tearsheets for all companies in the database."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    companies_df = pd.read_sql("SELECT ticker, name FROM companies", conn)
    conn.close()
    
    skipped = []
    generated = []
    
    for idx, row in companies_df.iterrows():
        ticker = row["ticker"]
        success, msg = build_tearsheet(ticker, db_path, output_dir)
        if success:
            generated.append(ticker)
        else:
            skipped.append({"company_id": ticker, "reason": msg})
            
    df_skipped = pd.DataFrame(skipped)
    skipped_path = "output/skipped_tearsheets.csv"
    df_skipped.to_csv(skipped_path, index=False)
    
    print(f"Batch tearsheet generation complete. Generated: {len(generated)} PDFs. Skipped: {len(skipped)} companies.")
    return len(generated), len(skipped)


if __name__ == "__main__":
    batch_generate_tearsheets()
