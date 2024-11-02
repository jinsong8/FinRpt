from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Table, TableStyle, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import  colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame, Flowable
from finrpt.utils.charting import get_share_performance, get_pe_eps_performance
import pandas as pd
from datetime import timedelta, datetime
import yfinance as yf
import requests
import pickle
import os
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

TARGETMAP = {
    'Total Revenue': '总收入(百万元)',
    'Net Income': '净收入(百万元)',
    'EBITDA': '息税前利润(百万元)',
    'Gross Profit': '毛利润(百万元)',
    'Operating Income': '营业收入(百万元)',
    'Net Income From Continuing Operation Net Minority Interest': '持续经营净收入(百万元)',
    'Operating Expense': '营业费用(百万元)',
    'Pretax Income': '税前收入(百万元)',
    'Tax Provision': '税项准备(百万元)',
    'EBIT': '息税前利润(百万元)',
    'Cost Of Revenue': '收入成本(百万元)',
    'Total Operating Income As Reported': '报告的总营业收入(百万元)',
    'Net Income Including Noncontrolling Interests': '包括非控股权益的净收入(百万元)'
}

BASE_key_mapping = {
    '6m avg daily vol (CNYmn)': '日均成交量(百万元)',
    'Closing Price (CNY)': '收盘价(元)',
    '52 Week Price Range (CNY)': '52周价格范围(元)'
}


def get_next_weekday(date):

    if not isinstance(date, datetime):
        date = datetime.strptime(date, "%Y-%m-%d")

    if date.weekday() >= 5:
        days_to_add = 7 - date.weekday()
        next_weekday = date + timedelta(days=days_to_add)
        return next_weekday
    else:
        return date

def get_historical_market_cap(
    ticker_symbol,
    date
) -> str:
    """Get the historical market capitalization for a given stock on a given date"""
    date = get_next_weekday(date).strftime("%Y-%m-%d")
    url = f"https://financialmodelingprep.com/api/v3/historical-market-capitalization/{ticker_symbol}?limit=100&from={date}&to={date}&apikey={fmp_api_key}"

    # 发送GET请求
    mkt_cap = None
    response = requests.get(url)

    # 确保请求成功
    if response.status_code == 200:
        # 解析JSON数据
        data = response.json()
        mkt_cap = data[0]["marketCap"]
        return mkt_cap
    else:
        return f"Failed to retrieve data: {response.status_code}"
    
def get_historical_bvps(
    ticker_symbol,
    target_date
):
    """Get the historical book value per share for a given stock on a given date"""
    # 从FMP API获取历史关键财务指标数据
    url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker_symbol}?limit=40&apikey={fmp_api_key}"
    response = requests.get(url)
    data = response.json()

    if not data:
        return "No data available"

    # 找到最接近目标日期的数据
    closest_data = None
    min_date_diff = float("inf")
    target_date = datetime.strptime(target_date, "%Y-%m-%d")
    for entry in data:
        date_of_data = datetime.strptime(entry["date"], "%Y-%m-%d")
        date_diff = abs(target_date - date_of_data).days
        if date_diff < min_date_diff:
            min_date_diff = date_diff
            closest_data = entry

    if closest_data:
        return closest_data.get("bookValuePerShare", "No BVPS data available")
    else:
        return "No close date data found"


def get_key_data(ticker_symbol, filing_date):

    if not isinstance(filing_date, datetime):
        filing_date = datetime.strptime(filing_date, "%Y-%m-%d")

    # Fetch historical market data for the past 6 months
    start = (filing_date - timedelta(weeks=52)).strftime("%Y-%m-%d")
    end = filing_date.strftime("%Y-%m-%d")
    
    hist = yf.Ticker(ticker_symbol).history(start=start, end=end)

    info = yf.Ticker(ticker_symbol).info
    
    close_price = hist["Close"].iloc[-1]

    # Calculate the average daily trading volume
    six_months_start = (filing_date - timedelta(weeks=26)).strftime("%Y-%m-%d")
    hist_last_6_months = hist[
        (hist.index >= six_months_start) & (hist.index <= end)
    ]

    # 计算这6个月的平均每日交易量
    avg_daily_volume_6m = (
        hist_last_6_months["Volume"].mean()
        if not hist_last_6_months["Volume"].empty
        else 0
    )

    fiftyTwoWeekLow = hist["High"].min()
    fiftyTwoWeekHigh = hist["Low"].max()

    # avg_daily_volume_6m = hist['Volume'].mean()

    # convert back to str for function calling
    filing_date = filing_date.strftime("%Y-%m-%d")

    # Print the result
    # print(f"Over the past 6 months, the average daily trading volume for {ticker_symbol} was: {avg_daily_volume_6m:.2f}")
    # rating, _ = YFinanceUtils.get_analyst_recommendations(ticker_symbol)
    # target_price = FMPUtils.get_target_price(ticker_symbol, filing_date)
    result = {
        # "Rating": rating,
        # "Target Price": target_price,
        f"6m avg daily vol ({info['currency']}mn)": "{:.2f}".format(
            avg_daily_volume_6m / 1e6
        ),
        f"Closing Price ({info['currency']})": "{:.2f}".format(close_price),
        # f"Market Cap ({info['currency']}mn)": "{:.2f}".format(
        #     get_historical_market_cap(ticker_symbol, filing_date) / 1e6
        # ),
        f"52 Week Price Range ({info['currency']})": "{:.2f} - {:.2f}".format(
            fiftyTwoWeekLow, fiftyTwoWeekHigh
        ),
        # f"BVPS ({info['currency']})": "{:.2f}".format(
        #     get_historical_bvps(ticker_symbol, filing_date)
        # ),
    }
    return result


class BulletParagraph(Flowable):
    def __init__(self, icon_path, text, font_name):
        Flowable.__init__(self)
        self.icon_path = icon_path
        styles = getSampleStyleSheet()
        custom_style = ParagraphStyle(
            'CustomStyle',
            parent=styles['Normal'],
            fontName=font_name,  
            fontSize=10,
            leading=14,
            spaceAfter=12,
            textColor=colors.black,
            alignment=0  
        )
        self.paragraph = Paragraph(text, custom_style)
        self.icon = Image(self.icon_path, 10, 10)

    def wrap(self, availWidth, availHeight):
        icon_width, icon_height = self.icon.drawWidth, self.icon.drawHeight
        para_width, para_height = self.paragraph.wrap(availWidth - icon_width - 6, availHeight)
        self.width = icon_width + 6 + para_width
        self.height = max(icon_height, para_height)
        return self.width, self.height

    def draw(self):
        self.icon.drawOn(self.canv, 0, self.height - self.icon.drawHeight - 3)
        self.paragraph.drawOn(self.canv, self.icon.drawWidth + 6, 0)
 
def draw_frame_title(text, set_color, col_width, font_name):
    data = [[text]]
    table = Table(data, colWidths=col_width)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), set_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
    ]))
    return table

def get_base_table(font_name, data):
    styles = getSampleStyleSheet()
    style_left = styles['Normal']
    style_left.fontName = font_name
    style_left.fontSize = 9

    style_right = styles['Normal']
    style_right.fontName = font_name
    style_right.fontSize = 9

    for da in data:
        [Paragraph(da[0], style_left), Paragraph(da[1], style_right)]
        

    table = Table(data, colWidths=[90, 90])

    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('FONT', (0, 0), (0, -1), font_name,9),
        ('FONT', (1, 0), (1, -1), font_name, 9),
        # ('LEADING', (0, 0), (-1, -1), 30),
        # ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    return table


def get_financias_table(font_name, data):
    col_widths = [115, 55, 55, 55, 55]

    table = Table(data, colWidths=col_widths)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # 表头背景色
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),             # 居中对齐
        ('FONTNAME', (0, 0), (-1, -1), font_name),   # 表头字体加粗
        ('FONTSIZE', (0, 0), (-1, -1), 8),                # 字体大小
        # ('BOTTOMPADDING', (0, 0), (-1, 0), 12),            # 表头底部填充
    ])

    for i in range(1, len(data)):
        if i % 2 == 0:
            bg_color = colors.whitesmoke
        else:
            bg_color = colors.white
        style.add('BACKGROUND', (0, i), (-1, i), bg_color)

    table.setStyle(style)
    return table

def build_report(
    res_data,
    date,   
    save_path='./reports/'
):
    get_share_performance(res_data, res_data['stock_code'], date)
    get_pe_eps_performance(res_data, res_data['stock_code'], date)
    share_performance_image_path="./figs/share_performance.png"
    pe_eps_performance_image_path="./figs/pe_eps.png"
    
    pdfmetrics.registerFont(TTFont('微软雅黑', 'msyh.ttf'))
    styles = getSampleStyleSheet()
    color1 = Color(red=158 / 255.0,green=31 / 255.0,blue=0)

    filename = (
            os.path.join(save_path, f"{res_data['company_name']}_研究报告_{date}_{res_data['model_name']}.pdf")
            if os.path.isdir(save_path)
            else save_path
        )
    c = canvas.Canvas(filename)

    img = Image("figs/logo.png")
    raw_width = img.imageWidth
    raw_height = img.imageHeight
    img.drawHeight = 40
    img.drawWidth = img.drawHeight * (raw_width / raw_height)
    img.drawOn(c, 40, A4[1] - 70)
    
    company_name = res_data['company_name']
    stock_code = res_data['stock_code']
    
    c.setStrokeColor(colors.black)
    c.setFont("微软雅黑", 12)
    c.drawString(28, A4[1] - 95, f"{company_name}（{stock_code}）")
    c.drawString(210, A4[1] - 95, f"{date}")

    title = company_name + ":" + res_data['report_title'] if \
        company_name not in res_data['report_title'] else res_data['report_title']
    
    title_style = ParagraphStyle(
        name='CustomStyle',
        parent=styles['Normal'],  
        fontName='微软雅黑',
        fontSize=17,
        leading=0,
        textColor=color1,
        alignment=1, 
        spaceBefore=10,
        spaceAfter=10
    )
    title_paragraph = Paragraph(title, title_style)
    frame_title = Frame(
        x1=160, 
        y1=A4[1] - 65, 
        width=400, 
        height=30, 
        showBoundary=0
    )
    frame_title.addFromList([title_paragraph], c)
    
    
    c.setStrokeColor(color1)
    c.line(A4[0] - 210, A4[1] - 120, A4[0] - 210, 50)
    
    # frame_left
    c.setStrokeColor(colors.black)
    frame_left_list = []
    frame_left = Frame(
        x1=25, 
        y1=0, 
        width=A4[0] - 235, 
        height=A4[1] - 120, 
        showBoundary=0,
        topPadding=0,
        leftPadding=4, 
        rightPadding=4
    )
    
    frame_title1 = draw_frame_title("核心观点", color1, A4[0] - 243, '微软雅黑')
    frame_left_list.append(frame_title1)
    frame_left_list.append(Spacer(1, 4))
    
    for sub_advisor in res_data["analyze_advisor"]:
        paragraph_text = '<font color="#9E1F00"><b>' + sub_advisor['title'] + '：</b></font>' + sub_advisor['content']
        paragraph_advisor = BulletParagraph('figs/icon.png', paragraph_text, '微软雅黑')
        frame_left_list.append(paragraph_advisor)
        frame_left_list.append(Spacer(1, 4))
        
    risk_assessment = ""
    for idx, risk in enumerate(res_data["analyze_risk"]):
        risk_assessment += "(" + str(idx + 1) + ")" + risk + ";"
    paragraph_text = '<font color="#9E1F00"><b>风险评估：</b></font>' + risk_assessment
    paragraph_advisor = BulletParagraph('figs/icon.png', paragraph_text, '微软雅黑')
    frame_left_list.append(paragraph_advisor)
    frame_left_list.append(Spacer(1, 4))
        
    frame_title2 = draw_frame_title("财务数据", color1, A4[0] - 243, '微软雅黑')
    frame_left_list.append(frame_title2)
    frame_left_list.append(Spacer(1, 5))
    df = res_data["financials"]['stock_income']
    df.reset_index(inplace=True)
    df = df[df['index'].isin(TARGETMAP.keys())]
    df['index'] = df['index'].map(TARGETMAP)
    df = df.applymap(lambda x: int(x / 1000000) if isinstance(x, (int, float)) and not pd.isna(x) else x)
    df_columns = df.columns
    df_new_columns = [""]
    for column_name in list(df_columns)[1:]:
        df_new_columns.append(str(column_name)[:10])
    df.columns = df_new_columns
    df = df[df.columns[:5]]
    table_data = []
    table_data += [df.columns.to_list()] + df.values.tolist()
    financias_table = get_financias_table('微软雅黑', table_data)
    frame_left_list.append(financias_table)
    frame_left.addFromList(frame_left_list, c)
    
    
    # frame_right
    frame_right_list = []
    frame_right = Frame(
        x1=A4[0] - 210, 
        y1=0, 
        width=185, 
        height=A4[1] - 120, 
        showBoundary=0,
        topPadding=0
    )
    frame_right.addFromList(frame_right_list, c)
    
    frame_title3 = draw_frame_title("作者", color1, 177, '微软雅黑')
    _1, _2 = frame_title3.wrap(0, 0)
    frame_title3.drawOn(c, A4[0] - 206, A4[1] - 120 - 21)
    
    c.setStrokeColor(color1)
    c.line(A4[0] - 206, A4[1] - 150, A4[0] - 29, A4[1] - 150)
    c.setStrokeColor(colors.black)
    c.setFont("微软雅黑", 9)
    height_1 = A4[1] - 170
    c.drawString(A4[0] - 200, height_1, "分析师: FinRpt")
    c.drawString(A4[0] - 200, height_1 - 20, "版权: ALOHA FinTech")
    c.drawString(A4[0] - 200, height_1 - 40, "地址: 中国人民大学高瓴人工智能学院")
    
    frame_title4 = draw_frame_title("基本状况", color1, 177, '微软雅黑')
    _1, _2 = frame_title4.wrap(0, 0)
    frame_title4.drawOn(c, A4[0] - 206, A4[1] - 245)
    
    key_data = get_key_data(stock_code, date)
    base_data = {BASE_key_mapping[key]: value for key, value in key_data.items()}
    base_data["交易所"] = res_data["company_info"]["stock_exchange"]
    base_data["行业"] = res_data["company_info"]["industry_category"][-11:]
    base_data = [[k, v] for k, v in base_data.items()]
    base_table = get_base_table('微软雅黑', base_data)
    base_table.wrap(0, 0)
    base_table.drawOn(c, A4[0] - 205, A4[1] - 345)
    
    frame_title5 = draw_frame_title("股市与市场走势对比", color1, 177, '微软雅黑')
    _1, _2 = frame_title5.wrap(0, 0)
    frame_title5.drawOn(c, A4[0] - 206, A4[1] - 375)
    img = Image(share_performance_image_path)
    raw_width = img.imageWidth
    raw_height = img.imageHeight
    img.drawWidth = 170
    img.drawHeight = img.drawWidth * (raw_height / raw_width)
    img.drawOn(c, A4[0] - 205, A4[1] - 485)
    
    frame_title6 = draw_frame_title("PE & EPS", color1, 177, '微软雅黑')
    frame_title6.wrap(0, 0)
    frame_title6.drawOn(c, A4[0] - 206, A4[1] - 510)
    img = Image(pe_eps_performance_image_path)
    raw_width = img.imageWidth
    raw_height = img.imageHeight
    img.drawWidth = 170
    img.drawHeight = img.drawWidth * (raw_height / raw_width)
    img.drawOn(c, A4[0] - 205, A4[1] - 620)
    c.save()

    
if __name__ == "__main__":
    date = '2024-10-28'
    data = pickle.load(open('maotai_1028_gpt4o.pkl', 'rb'))
    data['report_title'] = "业绩增长韧性延续，全年目标完成在望"
    build_report(data, date)
    