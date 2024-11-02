#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Table
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import  colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.graphics.barcode import qr


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
 
def main(filename):
    pdfmetrics.registerFont(TTFont('微软雅黑', 'msyh.ttf'))
    
    c = canvas.Canvas(filename)
    c.bookmarkPage("title")
    c.addOutlineEntry("my book", "title", level=0)

    c.setFont("微软雅黑", 16)
    c.setFillColor(Color(0, 0, 1, alpha=0.9))
    c.drawString(320, A4[1] - 95, "超级马里奥兄弟")
    c.setFont("微软雅黑", 12)
    c.setFillColor(Color(0, 0, 0, alpha=0.7))
    c.drawString(320, A4[1] - 125, "SUPER MARIO BROS.")
    c.drawString(320, A4[1] - 195, "1985年9月13日发售")
    
    img = Image("figs/title.png")
    print(img.imageWidth)
    print(img.imageHeight)
    img.drawWidth = 20
    img.drawHeight = 20
    img.drawOn(c, 150, A4[1] - 200)
    
    data = [
        ('经典游戏', '发布年代', '发行商'),
        ('TOP100',),
        ('超级马里奥兄弟', '1985年', '任天堂'),
        ('坦克大战', '1985年', '南梦宫'),
        ('魂斗罗', '1987年', '科乐美'),
        ('松鼠大战', '1990年', '卡普空'),
    ]
    t = draw_table(*data)
    t.wrap(800, 600)
    t.drawOn(c, 50, A4[1] - 400)
    
    styleSheet = getSampleStyleSheet()
    style = styleSheet['BodyText']
    style.fontName = "微软雅黑"
    p=Paragraph(' 《超级马里奥兄弟》于1985年9月13日发售，这是一款任天堂针对FC主机全力度身订造的游戏，被称为TV游戏奠基之作。这个游戏被赞誉为电子游戏的原始范本，确立了角色、游戏目的、流程分布、操作性、隐藏要素、BOSS、杂兵等以后通用至今的制作概念。《超级马里奥兄弟》成为游戏史首部真正意义上的超大作游戏，游戏日本本土销量总计681万份，海外累计更是达到了3342万份的天文数字。',style)
    p.wrap(A4[0]-100, 100)
    p.drawOn(c, 50, A4[1] - 280)
    
    b_data = [(2, 4, 6, 12, 8, 16), (12, 14, 17, 9, 12, 7)]
    ax_data = ['任天堂', '南梦宫', '科乐美', '卡普空', '世嘉', 'SNK']
    leg_items = [(colors.red, '街机'), (colors.green, '家用机')]
    d = draw_bar(b_data, ax_data, leg_items)
    d.drawOn(c, 50, A4[1] - 620)
    
    draw_page_number(c, 1, 2)
    c.bookmarkPage("section1")
    c.addOutlineEntry("first section", "section1", level=1)
    c.showPage()
    
    c.drawString(50, A4[1] - 70, "World")
    
    draw_page_number(c, 2, 2)
    c.bookmarkPage("section2")
    c.addOutlineEntry("second section", "section2", level=1)
    c.showPage()
    
    c.showOutline()
    c.save()

    
if __name__ == "__main__":
    main("Replab6.pdf")
    