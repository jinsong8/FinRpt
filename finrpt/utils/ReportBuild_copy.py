import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib import pagesizes
from reportlab.platypus import (
    SimpleDocTemplate,
    Frame,
    Paragraph,
    Image,
    PageTemplate,
    FrameBreak,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from finrpt.utils.charting import get_share_performance, get_pe_eps_performance, get_revenue_preformanace
import pickle
import pdb

FINE2C = {
    'Tax Effect Of Unusual Items': '异常项目的税收影响',
    'Tax Rate For Calcs': '计算用税率',
    'Normalized EBITDA': '标准化息税折旧摊销前利润',
    'Total Unusual Items': '总异常项目',
    'Total Unusual Items Excluding Goodwill': '不含商誉的总异常项目',
    'Net Income From Continuing Operation Net Minority Interest': '持续经营净收入（扣除少数股东权益）',
    'Reconciled Cost Of Revenue': '调整后的收入成本',
    'EBITDA': '息税折旧摊销前利润',
    'EBIT': '息税前利润',
    'Net Interest Income': '净利息收入',
    'Interest Expense': '利息支出',
    'Interest Income': '利息收入',
    'Normalized Income': '标准化收入',
    'Net Income From Continuing And Discontinued Operation': '持续和非持续经营净收入',
    'Total Expenses': '总费用',
    'Total Operating Income As Reported': '报告的总营业收入',
    'Diluted Average Shares': '稀释平均股数',
    'Basic Average Shares': '基本平均股数',
    'Diluted EPS': '稀释每股收益',
    'Basic EPS': '基本每股收益',
    'Net Income Common Stockholders': '普通股股东净收入',
    'Otherunder Preferred Stock Dividend': '优先股股息下的其他',
    'Net Income': '净收入',
    'Minority Interests': '少数股东权益',
    'Net Income Including Noncontrolling Interests': '包括非控股权益的净收入',
    'Net Income Continuous Operations': '持续经营净收入',
    'Tax Provision': '税项准备',
    'Pretax Income': '税前收入',
    'Other Non Operating Income Expenses': '其他非经营性收入费用',
    'Special Income Charges': '特殊收入费用',
    'Other Special Charges': '其他特殊费用',
    'Write Off': '核销',
    'Net Non Operating Interest Income Expense': '净非经营性利息收入费用',
    'Total Other Finance Cost': '其他财务费用总计',
    'Interest Expense Non Operating': '非经营性利息支出',
    'Interest Income Non Operating': '非经营性利息收入',
    'Operating Income': '营业收入',
    'Operating Expense': '营业费用',
    'Other Operating Expenses': '其他营业费用',
    'Research And Development': '研发费用',
    'Selling General And Administration': '销售、一般及行政费用',
    'Selling And Marketing Expense': '销售和营销费用',
    'General And Administrative Expense': '一般及行政费用',
    'Gross Profit': '毛利润',
    'Cost Of Revenue': '收入成本',
    'Total Revenue': '总收入',
    'Operating Revenue': '营业收入'
}

def build_report(
    res_data,
    date,   
    save_path='./reports/'
):
    try:
        get_share_performance(res_data, res_data['stock_code'], date)
        get_pe_eps_performance(res_data, res_data['stock_code'], date)
        share_performance_image_path="./figs/share_performance.png"
        pe_eps_performance_image_path="./figs/pe_eps.png"
        pdfmetrics.registerFont(TTFont('SimSun', 'SimSun.ttf'))
        pdfmetrics.registerFont(TTFont('SimHei', 'SimHei.ttf')) 
        page_width, page_height = pagesizes.A4
        left_column_width = page_width * 2 / 3
        right_column_width = page_width - left_column_width
        margin = 4

        pdf_path = (
            os.path.join(save_path, f"{res_data['company_name']}_研究报告_{date}_{res_data['model_name']}.pdf")
            if os.path.isdir(save_path)
            else save_path
        )
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        doc = SimpleDocTemplate(pdf_path, pagesize=pagesizes.A4)

        frame_left = Frame(
            margin,
            margin,
            left_column_width - margin * 2,
            page_height - margin * 2,
            id="left",
        )
        frame_right = Frame(
            left_column_width,
            margin,
            right_column_width - margin * 2,
            page_height - margin * 2,
            id="right",
        )

        page_template = PageTemplate(
            id="TwoColumns", frames=[frame_left, frame_right]
        )
        
        doc.addPageTemplates([page_template])

        styles = getSampleStyleSheet()

        custom_style = ParagraphStyle(
            name="Custom",
            parent=styles["Normal"],
            fontName="SimSun",
            fontSize=10,
            # leading=15,
            alignment=TA_JUSTIFY,
        )

        title_style = ParagraphStyle(
            name="TitleCustom",
            parent=styles["Title"],
            fontName="SimHei",
            fontSize=19,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=10,
        )

        subtitle_style = ParagraphStyle(
            name="Subtitle",
            parent=styles["Heading2"],
            fontName="SimHei",
            fontSize=14,
            leading=12,
            alignment=TA_LEFT,
            spaceAfter=6,
        )

        table_style2 = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, -1), "SimSun", 7),
                ("FONT", (0, 0), (-1, 0), "SimHei", 14),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("LINEBELOW", (0, 0), (-1, 0), 2, colors.black),
                ("LINEBELOW", (0, -1), (-1, -1), 2, colors.black),
            ]
        )

        # name = YFinanceUtils.get_stock_info(ticker_symbol)["shortName"]
        content = []
        content.append(
            Paragraph(
                f"{res_data['company_name']}研报",
                title_style,
            )
        )

        for sub_advisor in res_data["analyze_advisor"]:
            content.append(Paragraph(sub_advisor['title'], subtitle_style))
            content.append(Paragraph(sub_advisor['content'], custom_style))
            
        content.append(Paragraph("风险评估", subtitle_style))
        risk_assessment = ""
        for idx, risk in enumerate(res_data["analyze_risk"]):
            risk_assessment += "(" + str(idx + 1) + ")" + risk + ";"
        content.append(Paragraph(risk_assessment, custom_style))
        content.append(Spacer(1, 0.15 * inch))
        
        # df = FMPUtils.get_financial_metrics(ticker_symbol, years=5)
        df = res_data["financials"]['stock_income'].tail(15)
        df.reset_index(inplace=True)
        # currency = YFinanceUtils.get_stock_info(ticker_symbol)["currency"]
        # df.rename(columns={"index": f"FY ({currency} mn)"}, inplace=True)
        table_data = [["金融指标"]]
        df_columns = df.columns
        df_new_columns = ["日期"]
        for column_name in list(df_columns)[1:]:
            df_new_columns.append(str(column_name)[:10])
        df.columns = df_new_columns
        df = df[df.columns[:-1]]
        df.iloc[:, 0] = df.iloc[:, 0].apply(lambda x: FINE2C[x][:9])
        table_data += [df.columns.to_list()] + df.values.tolist()

        col_widths = [(left_column_width - margin * 4) / df.shape[1]] * df.shape[1]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(table_style2)
        content.append(table)

        content.append(FrameBreak()) 

        table_style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, -1), "SimSun", 8),
                ("FONT", (0, 0), (-1, 0), "SimHei", 12),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("LINEBELOW", (0, 0), (-1, 0), 2, colors.black),
            ]
        )
        full_length = right_column_width - 2 * margin
        
        content.append(Spacer(1, 0.15 * inch))
        content.append(Spacer(1, 0.15 * inch))
        content.append(Spacer(1, 0.15 * inch))

        data = [
            ["FinRpt"],
            ["ALOHA-FinTech"],
            ["https://github.com/jinsong8"],
            [f"报告日期: {date}"],
        ]
        col_widths = [full_length]
        table = Table(data, colWidths=col_widths)
        table.setStyle(table_style)
        content.append(table)

        content.append(Spacer(1, 0.15 * inch))
        key_data = {
            "公司名称": res_data["company_name"],
            "股票代码": res_data['stock_code'],
            "行业": res_data["company_info"]["industry_category"],
            "地址": res_data["company_info"]["address"][:10],
            "交易所": res_data["company_info"]["stock_exchange"]
        }
        data = [["关键数据", ""]]
        data += [[k, v] for k, v in key_data.items()]
        col_widths = [full_length // 3 * 2, full_length // 3]
        table = Table(data, colWidths=col_widths)
        table.setStyle(table_style)
        content.append(table)
        
        content.append(Spacer(1, 0.15 * inch))

        data = [["股票表现"]]
        col_widths = [full_length]
        table = Table(data, colWidths=col_widths)
        table.setStyle(table_style)
        content.append(table)

        width = right_column_width
        height = width // 2
        content.append(Image(share_performance_image_path, width=width, height=height))

        data = [["PE & EPS"]]
        col_widths = [full_length]
        table = Table(data, colWidths=col_widths)
        table.setStyle(table_style)
        content.append(table)

        width = right_column_width
        height = width // 2
        content.append(Image(pe_eps_performance_image_path, width=width, height=height))

        doc.build(content)

        return True

    except Exception as e:
        print(e)
        return False
    
    
if __name__ == '__main__':
    date = '2024-10-28'
    data = pickle.load(open('maotai_1028_gpt4o.pkl', 'rb'))
    build_report(data, date)
