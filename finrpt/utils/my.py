#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Table, TableStyle, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import  colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame, Flowable
from reportlab.graphics.barcode import qr


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

def draw_bar(bar_data: list, ax: list, items: list):
    drawing = Drawing(500, 200)
    bc = VerticalBarChart()
    bc.x = 45       # 整个图表的x坐标
    bc.y = 45      # 整个图表的y坐标
    bc.height = 150     # 图表的高度
    bc.width = 350      # 图表的宽度
    bc.data = bar_data
    bc.strokeColor = colors.black       # 顶部和右边轴线的颜色
    bc.valueAxis.valueMin = 0           # 设置y坐标的最小值
    bc.valueAxis.valueMax = 20         # 设置y坐标的最大值
    bc.valueAxis.valueStep = 5         # 设置y坐标的步长
    bc.categoryAxis.labels.dx = 2
    bc.categoryAxis.labels.dy = -8
    bc.categoryAxis.labels.angle = 20
    bc.categoryAxis.labels.fontName = '微软雅黑'
    bc.categoryAxis.categoryNames = ax
    
    # 图示
    leg = Legend()
    leg.fontName = '微软雅黑'
    leg.alignment = 'right'
    leg.boxAnchor = 'ne'
    leg.x = 475         # 图例的x坐标
    leg.y = 140
    leg.dxTextSpace = 10
    leg.columnMaximum = 3
    leg.colorNamePairs = items
    drawing.add(leg)
    drawing.add(bc)
    return drawing


def draw_table(*args):
    col_width = 120
    style = [
        ('FONTNAME', (0, 0), (-1, -1), '微软雅黑'),  # 字体
        ('FONTSIZE', (0, 0), (-1, 0), 12),  # 第一行的字体大小
        ('FONTSIZE', (0, 1), (-1, -1), 10),  # 第二行到最后一行的字体大小
        ('BACKGROUND', (0, 0), (-1, 0), '#d5dae6'),  # 设置第一行背景颜色
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # 第一行水平居中
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),  # 第二行到最后一行左右左对齐
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # 所有表格上下居中对齐
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.darkslategray),  # 设置表格内文字颜色
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # 设置表格框线为grey色，线宽为0.5
        ('SPAN', (0, 1), (2, 1)),  # 合并第二行一二三列
    ]
    table = Table(args, colWidths=col_width, style=style)
    return table
 
def draw_page_number(c, page, count):
    c.setFillColorRGB(1, 0, 0)
    c.setFont("微软雅黑", 9)
    c.drawCentredString(A4[0]/2, A4[1]-9*mm, "XX有限公司版权所有")
    qr_code = qr.QrCode('https://www.cnblogs.com/windfic', width=45, height=45)
    c.setFillColorRGB(0, 0, 0)
    qr_code.drawOn(c, 0, A4[1]-45)
    c.line(10*mm, A4[1]-45, A4[0], A4[1]-45)
    
    c.setFont("微软雅黑", 9)
    c.setStrokeColor(Color(0, 0, 0, alpha=0.5))
    c.line(10*mm, 15*mm, A4[0] - 10*mm, 15*mm)
    c.setFillColor(Color(0, 0, 0, alpha=0.5))
    c.drawCentredString(A4[0]/2, 10*mm, "Page %d of %d" % (page, count))
 
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

def get_base_table(font_name):
    styles = getSampleStyleSheet()
    style_left = styles['Normal']
    style_left.fontName = font_name
    style_left.fontSize = 9

    style_right = styles['Normal']
    style_right.fontName = font_name
    style_right.fontSize = 9

    data = [
        [Paragraph('总股本(百万股)', style_left), Paragraph('1,256.20', style_right)],
        [Paragraph('流通股本(百万股)', style_left), Paragraph('1,256.20', style_right)],
        [Paragraph('市价(元)', style_left), Paragraph('1,558.85', style_right)],
        [Paragraph('市值(百万元)', style_left), Paragraph('1,958,223.94', style_right)],
        [Paragraph('流通市值(百万元)', style_left), Paragraph('1,958,223.94', style_right)],
    ]

    table = Table(data, colWidths=[90, 90])

    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('FONT', (0, 0), (0, -1), font_name,9),
        ('FONT', (1, 0), (1, -1), font_name, 9),
        # ('LEADING', (0, 0), (-1, -1), 30),
        # ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    return table


def get_financias_table(font_name):
    data = [
        ["", "2021A", "2022A", "2023E", "2024E", "2025E"],
        ["营业收入(百万元)", "106,190", "124,100", "146,190", "170,749", "198,069"],
        ["YOY(%)", "11.9", "16.9", "17.8", "16.8", "16.0"],
        ["净利润(百万元)", "52,460", "62,716", "74,317", "86,803", "100,831"],
        ["YOY(%)", "12.3", "19.6", "18.5", "16.8", "16.2"],
        ["毛利率(%)", "91.5", "91.9", "92.4", "92.7", "93.0"],
        ["净利率(%)", "49.4", "50.5", "50.8", "50.8", "50.9"],
        ["ROE(%)", "27.7", "31.8", "33.4", "34.5", "35.4"],
        ["EPS(摊薄/元)", "41.76", "49.93", "59.16", "69.10", "80.27"],
        ["P/E(倍)", "45.0", "37.7", "31.8", "27.2", "23.4"],
        ["P/B(倍)", "12.5", "12.0", "10.6", "9.4", "8.3"]
    ]

    col_widths = [80, 50, 50, 50, 50, 50]

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

def main(filename):
    pdfmetrics.registerFont(TTFont('微软雅黑', 'msyh.ttf'))
    styles = getSampleStyleSheet()
    color1 = Color(red=158 / 255.0,green=31 / 255.0,blue=0)
    print(A4[0], A4[1])
    
    c = canvas.Canvas(filename)

    img = Image("figs/logo.png")
    raw_width = img.imageWidth
    raw_height = img.imageHeight
    img.drawHeight = 40
    img.drawWidth = img.drawHeight * (raw_width / raw_height)
    img.drawOn(c, 40, A4[1] - 70)
    
    company_name = "贵州茅台"
    stock_code = "600519.SS"
    date = "2024-10-31"
    
    c.setStrokeColor(colors.black)
    c.setFont("微软雅黑", 12)
    c.drawString(28, A4[1] - 95, f"{company_name}（{stock_code}）")
    c.drawString(210, A4[1] - 95, f"{date}")
    
    
    

    title = "贵州茅台：业绩增长韧性延续，全年目标完成在望"
    title_style = ParagraphStyle(
        name='CustomStyle',
        parent=styles['Normal'],  # 可以继承自已有样式
        fontName='微软雅黑',
        fontSize=17,
        leading=0,
        textColor=color1,
        # backColor=colors.lightgrey,
        alignment=1,  # 0=left, 1=center, 2=right, 4=justify
        spaceBefore=10,
        spaceAfter=10
    )
    title_paragraph = Paragraph(title, title_style)
    frame_title = Frame(
        x1=160, 
        y1=A4[1] - 65, 
        width=400, 
        height=30, 
        showBoundary=1
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
        showBoundary=1,
        topPadding=0,
        leftPadding=4, 
        rightPadding=4
    )
    
    frame_title1 = draw_frame_title("核心观点", color1, A4[0] - 243, '微软雅黑')
    frame_left_list.append(frame_title1)
    frame_left_list.append(Spacer(1, 3))
    paragraph_1_text = '''
    <font color="#9E1F00"><b>这是第一句，字体是红色并加粗。</b></font><br/>
    <font color="blue"><b>这是第二句，字体是蓝色并加粗。</b></font><br/>
    <font color="green"><b>这是第三句，字体是绿色并加粗。</b></font>
    '''
    paragraph_1 = BulletParagraph('figs/icon.png', paragraph_1_text, '微软雅黑')
    frame_left_list.append(paragraph_1)
    frame_left_list.append(Spacer(1, 3))
    frame_title2 = draw_frame_title("财务数据", color1, A4[0] - 243, '微软雅黑')
    frame_left_list.append(frame_title2)
    frame_left_list.append(Spacer(1, 5))
    financias_table = get_financias_table('微软雅黑')
    frame_left_list.append(financias_table)
    frame_left.addFromList(frame_left_list, c)
    
    
    # frame_right
    frame_right_list = []
    frame_right = Frame(
        x1=A4[0] - 210, 
        y1=0, 
        width=185, 
        height=A4[1] - 120, 
        showBoundary=1,
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
    c.drawString(A4[0] - 200, height_1 - 40, "地址: 高瓴人工智能学院")
    
    frame_title4 = draw_frame_title("基本状况", color1, 177, '微软雅黑')
    _1, _2 = frame_title4.wrap(0, 0)
    frame_title4.drawOn(c, A4[0] - 206, A4[1] - 245)
    
    base_table = get_base_table('微软雅黑')
    base_table.wrap(0, 0)
    base_table.drawOn(c, A4[0] - 205, A4[1] - 345)
    
    frame_title5 = draw_frame_title("股市与市场走势对比", color1, 177, '微软雅黑')
    _1, _2 = frame_title5.wrap(0, 0)
    frame_title5.drawOn(c, A4[0] - 206, A4[1] - 375)
    img = Image("figs/share_performance.png")
    raw_width = img.imageWidth
    raw_height = img.imageHeight
    img.drawWidth = 170
    img.drawHeight = img.drawWidth * (raw_height / raw_width)
    img.drawOn(c, A4[0] - 205, A4[1] - 470)
    
    frame_title6 = draw_frame_title("PE & EPS", color1, 177, '微软雅黑')
    frame_title6.wrap(0, 0)
    frame_title6.drawOn(c, A4[0] - 206, A4[1] - 500)
    img = Image("figs/pe_eps.png")
    raw_width = img.imageWidth
    raw_height = img.imageHeight
    img.drawWidth = 170
    img.drawHeight = img.drawWidth * (raw_height / raw_width)
    img.drawOn(c, A4[0] - 205, A4[1] - 595)
    
    
    

    
    

    
    
    
    # c.setFont("微软雅黑", 12)
    # c.setFillColor(Color(0, 0, 0, alpha=0.7))
    # c.drawString(320, A4[1] - 125, "SUPER MARIO BROS.")
    # c.drawString(320, A4[1] - 195, "1985年9月13日发售")
    
    # img = Image("figs/title.png")
    # print(img.imageWidth)
    # print(img.imageHeight)
    # img.drawWidth = 20
    # img.drawHeight = 20
    # img.drawOn(c, 150, A4[1] - 200)
    
    # data = [
    #     ('经典游戏', '发布年代', '发行商'),
    #     ('TOP100',),
    #     ('超级马里奥兄弟', '1985年', '任天堂'),
    #     ('坦克大战', '1985年', '南梦宫'),
    #     ('魂斗罗', '1987年', '科乐美'),
    #     ('松鼠大战', '1990年', '卡普空'),
    # ]
    # t = draw_table(*data)
    # t.wrap(800, 600)
    # t.drawOn(c, 50, A4[1] - 400)
    
    # styleSheet = getSampleStyleSheet()
    # style = styleSheet['BodyText']
    # style.fontName = "微软雅黑"
    # p=Paragraph(' 《超级马里奥兄弟》于1985年9月13日发售，这是一款任天堂针对FC主机全力度身订造的游戏，被称为TV游戏奠基之作。这个游戏被赞誉为电子游戏的原始范本，确立了角色、游戏目的、流程分布、操作性、隐藏要素、BOSS、杂兵等以后通用至今的制作概念。《超级马里奥兄弟》成为游戏史首部真正意义上的超大作游戏，游戏日本本土销量总计681万份，海外累计更是达到了3342万份的天文数字。',style)
    # p.wrap(A4[0]-100, 100)
    # p.drawOn(c, 50, A4[1] - 280)
    
    # b_data = [(2, 4, 6, 12, 8, 16), (12, 14, 17, 9, 12, 7)]
    # ax_data = ['任天堂', '南梦宫', '科乐美', '卡普空', '世嘉', 'SNK']
    # leg_items = [(colors.red, '街机'), (colors.green, '家用机')]
    # d = draw_bar(b_data, ax_data, leg_items)
    # d.drawOn(c, 50, A4[1] - 620)
    
    # draw_page_number(c, 1, 2)

    # c.showPage()
    
    # c.drawString(50, A4[1] - 70, "World")
    
    # draw_page_number(c, 2, 2)
    
    # c.showPage()
    

    c.save()

    
if __name__ == "__main__":
    main("my.pdf")
    