from finrpt.module.OpenAI import OpenAIModel
from tqdm import tqdm
import concurrent.futures
import threading
import pdb
import json

PROMPT = "将下面的中文内容翻译成英文，直接返回翻译成英文后的文本:\n"

risk_prompt_translate = """\n\nPlease refer to the above semi annual or annual reports, recent stock summary information, and your own knowledge to analyze the potential risk factors that the stock may face. You can refer to the risks mentioned in the semi annual or annual report. Return at least three different risks. Each risk should be condensed into no more than 10 words. \Please convert your output format to JSON, which can be directly loaded by the json. loads() function: \ n {"risks": ["risk 1", "risk 2",..., "risk n"]}"""

finance = """\n\n\nPlease summarize the financial data of the stock provided above and analyze its recent financial performance, including changes in key indicators such as revenue, profit, liabilities, and cash flow. Generate a single paragraph in the stock research report, not exceeding 200 words, and the generated content should include specific financial data. Please return the following JSON formatted text:\n {"Paragraph": "Single paragraph content", "Title": "Concise and appropriate title generated based on paragraph content"}"""
news = """\n\n\nPlease analyze the market's impact on the stock based on the key news provided above, discuss possible short-term and long-term trends, including market sentiment and external factors. Generate a single paragraph in a stock research report, not exceeding 200 words. Please return the following JSON formatted text: \n {"Paragraph": "Single paragraph content", "Title": "Concise and appropriate title generated based on paragraph content"}"""
report = """\n\n\nPlease explore the company's strategic direction and future development potential based on the annual or semi annual reports provided above, and evaluate its competitive position in the industry. Generate a single paragraph in a stock research report, not exceeding 200 words. Please return the following JSON formatted text: \n {"Paragraph": "Single paragraph content", "Title": "Concise and appropriate title generated based on paragraph content"}"""
risk = """\n\nPlease refer to the above semi annual or annual reports, recent stock summary information, and your own knowledge to analyze the potential risk factors that the stock may face. You can refer to the risks mentioned in the semi annual or annual report. Return at least three different risks. Each risk should be condensed into no more than 10 words. \n\nPlease convert your output format to JSON, which can be directly loaded by the json.loads() function: \n {"risks": ["risk 1", "risk 2",..., "risk n"]}"""
trend = """\n\n\nBased on the above information, please provide investment advice and predict the trend of the company's stock changes in the next three weeks. If the expected increase in the company's stock is higher than the increase in the Shanghai and Shenzhen 300 Index, a 'buy' rating will be given; If it is below, a 'sell' rating will be given. Write a stock research report of no more than 200 words. Please return the following JSON formatted text \n {"Paragraph": "Single paragraph content", "Title": "Concise and appropriate title generated based on paragraph content", "Rating": "Buy/Sell"}\n"""

file_path = '/data/name/FinRpt_v1/dataset/filter_filter_alignment_gpt-4o.jsonl'
gen_reports = open(file_path, 'r').read().split('\n')
gen_reports = [json.loads(x) for x in gen_reports]
results_gen_reports = []

def translate_row(gen_report, lock, progress_bar):
    gen = gen_report.copy()
    model = OpenAIModel(model_name="gpt-4o-mini")
    new_gen = {}
    new_gen['id'] = gen_report['id']
    new_gen['stock_code'] = gen_report['stock_code']
    new_gen['date'] = gen_report['date']
    
    finance_prompt, _ = gen_report['finance_write_prompt'].split('\n\n\n请根据以上提供的股票的财务数据，总结该股票的财务数据，分析其近期的财务表现，')
    new_gen['finance_write_prompt'] = model.simple_prompt(PROMPT + finance_prompt)[0] + finance
    new_gen['finance_write_response'] = model.simple_prompt(PROMPT + gen['finance_write_response'])[0]
    news_prompt, _ = gen_report['news_write_prompt'].split('\n\n\n请根据以上提供的股票的关键新闻，分析市场对该股票的影响，讨论可能的短期和长期趋势，')
    new_gen['news_write_prompt'] = model.simple_prompt(PROMPT + news_prompt)[0] + news
    new_gen['news_write_response'] = model.simple_prompt(PROMPT + gen['news_write_response'])[0]
    report_prompt, _ = gen_report['report_write_prompt'].split('\n\n\n请根据以上提供的股票的年报或半年报，探讨该公司的战略方向和未来发展潜')
    new_gen['report_write_prompt'] = model.simple_prompt(PROMPT + report_prompt)[0] + report
    new_gen['report_write_response'] = model.simple_prompt(PROMPT + gen['report_write_response'])[0]
    risk_prompt, _ = gen_report['risk_prompt'].split('\n\n请参考结合以上半年报或年报、股票近期总结信息和你自己的知识，')
    new_gen['risk_prompt'] = model.simple_prompt(PROMPT + risk_prompt)[0] + risk
    new_gen['risk_response'] = model.simple_prompt(PROMPT + gen['risk_response'])[0]
    trend_prompt, _ = gen_report['trend_write_prompt'].split('\n\n\n根据以上信息，请提供投资建议，')
    new_gen['trend_write_prompt'] = model.simple_prompt(PROMPT + trend_prompt)[0] + trend
    new_gen['trend_write_response'] = model.simple_prompt(PROMPT + gen['trend_write_response'])[0]
    
    with lock:
        results_gen_reports.append(new_gen)
        progress_bar.update(1)
    pass

lock = threading.Lock()

progeress_bar = tqdm(total=len(gen_reports))

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [
        executor.submit(translate_row, gen_report, lock, progeress_bar) 
        for gen_report in gen_reports
    ]
    concurrent.futures.wait(futures)
    
results_gen_reports_str = [json.dumps(x, ensure_ascii=False) for x in results_gen_reports]    
with open('/data/name/FinRpt_v1/dataset/en_filter_filter_alignment_gpt-4o.jsonl', 'w') as f:
    f.write("\n".join(results_gen_reports_str))

    