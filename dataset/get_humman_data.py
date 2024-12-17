import json
import random
import pdb
import pickle
import openpyxl

workbook = openpyxl.Workbook()
sheet = workbook.active

file_path = 'filter_filter_alignment_gpt-4o.jsonl'
data = pickle.load(open(f'./data/csi300_csi500_report_9-11_id.pkl', 'rb'))
stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
date = '2024-10-29'
# get_stock_list = []
# for stock in stock_list_csi300:
#     if stock + "_" + date in data:
#         if len(data[stock + '_' + date]) > 0:
#             get_stock_list.append(stock)
#             if len(get_stock_list) >= 50:
#                 break
# print(get_stock_list)
# while True:
#     try:
#         stock_list = random.sample(stock_list_csi300, 30)
#         dec = True
#         for stock in stock_list:
#             if stock + "_" + date not in data:
#                 dec = False
#                 break
#             if len(data[stock + '_' + date]) == 0:
#                 dec = False
#                 break
#         if dec:
#             print(stock_list)
#             break
#     except ValueError:
#         continue

# stock_list = ['600276.SS', '601360.SS', '000625.SZ', '688065.SS', '600588.SS', '601600.SS', '000157.SZ', '300601.SZ', '601088.SS', '688223.SS', '688111.SS', '000963.SZ', '600887.SS', '601628.SS', '002916.SZ', '600989.SS', '601985.SS', '000895.SZ', '601021.SS', '600015.SS', '600196.SS', '600754.SS', '600048.SS', '600886.SS', '600028.SS', '600519.SS', '600760.SS', '000723.SZ', '601865.SS', '688981.SS']
# stock_list = ['002001.SZ', '600795.SS', '601117.SS', '600919.SS', '000338.SZ', '002311.SZ', '600031.SS', '600050.SS', '002714.SZ', '000651.SZ', '000301.SZ', '600132.SS', '002120.SZ', '000723.SZ', '300759.SZ', '601668.SS', '600028.SS', '600600.SS', '601021.SS', '300433.SZ', '600803.SS', '601155.SS', '300496.SZ', '601838.SS', '601878.SS', '002415.SZ', '688012.SS', '000166.SZ', '600460.SS', '000800.SZ']
# stock_list = ['000063.SZ', '000408.SZ', '000568.SZ', '000625.SZ', '000661.SZ', '000708.SZ', '000733.SZ', '000786.SZ', '000792.SZ', '000963.SZ', '002001.SZ', '002027.SZ', '002064.SZ', '002142.SZ', '002202.SZ', '002230.SZ', '002236.SZ', '002241.SZ', '002252.SZ', '002271.SZ', '002311.SZ', '002352.SZ', '002415.SZ', '002475.SZ', '002601.SZ', '002648.SZ', '002709.SZ', '002916.SZ', '002938.SZ', '003816.SZ']
# stock_list = get_stock_list
stock_list = ['300496.SZ', '002064.SZ', '300498.SZ', '000408.SZ', '300750.SZ', '000661.SZ', '000708.SZ', '300433.SZ', '002415.SZ', '300059.SZ', '300014.SZ', '002027.SZ', '300015.SZ', '002352.SZ', '300316.SZ', '600028.SS', '002648.SZ', '002236.SZ', '002142.SZ', '000786.SZ', '002601.SZ', '300896.SZ', '000733.SZ', '000625.SZ', '300033.SZ', '300782.SZ', '300124.SZ', '000063.SZ', '300454.SZ', '300751.SZ']
file_path = 'filter_filter_alignment_gpt-4o.jsonl'
matter_key = ['finance_write_response', 'news_write_response', 'report_write_response', 'risk_response', 'trend_write_response']
gen_reports = open(file_path, 'r').read().split('\n')
gen_reports = [json.loads(x) for x in gen_reports]

filter_gen_reports = []
for report in gen_reports:
    if report['stock_code'] in stock_list and date == report['date']:
        filter_gen_reports.append(report)

csv_title = ["id, report,数据准确性、财务分析的深度,新闻分析的相关性和覆盖度,对公司管理与发展、市场趋势和行业状况的理解,投资建议是否基于全面和理性的分析,是否全面地分析了投资该股票的潜在风险,整体连贯性、可读性和逻辑性"]
sheet.append(csv_title)


filter_research_reports = []
for report in filter_gen_reports:
    id = report['id']
    research_reports = data[id][0]
    research_reports = "\n".join(research_reports['report_paragraphs'])
    filter_research_reports.append(research_reports)
with open("human_evaluation_result.jsonl", "w") as f:
    for i, (report, research_report) in enumerate(zip(filter_gen_reports, filter_research_reports)):
        report_str = "\n".join([report[key] for key in matter_key])
        f.write(json.dumps({"id": report['id'], "gen_report": report_str, "research_report": research_report}, ensure_ascii=False) + '\n')
        sheet.append([report['id'], report_str, '', '', '', '', '', ''])
        sheet.append([report['id'], research_report, '', '', '', '', '', ''])
        
workbook.save('human_evaluation_result.xlsx')
        