from finrpt.module.Advisor import Advisor
from finrpt.module.FinancialsAnalyzer import FinancialsAnalyzer
from finrpt.module.NewsAnalyzer import NewsAnalyzer
from finrpt.module.Predictor import Predictor
from finrpt.module.RiskAssessor import RiskAssessor
from finrpt.source.Dataer import Dataer
from finrpt.utils.data_processing import (
    duplication_eliminate_hash,
    duplication_eliminate_bert, 
    short_eliminate,
    filter_news_by_date,
    limit_by_amount)
from finrpt.utils.ReportBuild import build_report
from finrpt.module.OpenAI import OpenAIModel
import logging
import os
import json
import pickle
import pdb
import sqlite3


PROMPT_FINANCE = """请根据以上提供的股票的财务数据，总结该股票的财务数据，分析其近期的财务表现，包括收入、利润、负债、现金流等关键指标的变化。生成股票研报中的单一段落，不超过200字，生成内容需包括具体财务数据。请返回如下json格式的文本:
{"段落": "单一段落内容", "标题": "根据段落内容生成的简洁合适标题"}"""

PROMPT_NEWS = """请根据以上提供的股票的关键新闻，分析市场对该股票的影响，讨论可能的短期和长期趋势，包括市场情绪和外部因素的影响。生成股票研报中的单一段落，不超过200字。请返回如下json格式的文本:
{"段落": "单一段落内容", "标题": "根据段落内容生成的简洁合适标题"}"""

PROMPT_REPORT = """请根据以上提供的股票的年报或半年报，探讨该公司的战略方向和未来发展潜力，评估其在行业中的竞争地位。生成股票研报中的单一段落，不超过200字。请返回如下json格式的文本:
{"段落": "单一段落内容", "标题": "根据段落内容生成的简洁合适标题"}"""

PROMPT_TREND = """根据以上信息，请提供投资建议，并预测未来三周该公司股票变化趋势。若该公司股票的预期涨幅高于沪深300指数涨幅，则给予“买入”评级；若低于，则给予"卖出"评级。撰写一段不超过200字的股票研究报告内容。请返回如下json格式的文本
{"段落": "单一段落内容", "标题": "根据段落内容生成的简洁合适标题", "评级": "买入/卖出"}
"""

PROMPT_RISK = """请参考结合以上半年报或年报、股票近期总结信息和你自己的知识，分析该股票可能面临的风险因素。可以参考半年报或年报里提及的风险。返回至少三个不同的风险。每个风险精简不超过10个字。

请将您的输出格式转化为JSON,能直接被json.loads()函数加载:
{"risks": ["风险1", "风险2", ..., "风险n"]}"""


def setup_logger(log_name='finrpt', log_file='finrpt.log'):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger

class FinRptSingle:
    def __init__(self, model_name="gpt-4o", max_rounds=3, language='zh', database_name='/data/name/FinRpt_v1/finrpt/source/cache.db', save_path='./reports'):
        self.advisor = Advisor(model_name=model_name, max_rounds=max_rounds, language=language)
        self.financials_analyzer = FinancialsAnalyzer(model_name=model_name, max_rounds=max_rounds, language=language)
        self.news_analyzer = NewsAnalyzer(model_name=model_name, max_rounds=max_rounds, language=language)
        self.predictor = Predictor()
        self.risk_assessor = RiskAssessor(model_name=model_name, max_rounds=max_rounds, language=language)
        self.dataer = Dataer(database_name=database_name)
        self.model_name = model_name
        self.save_path = save_path
        
    def run(self, date, stock_code=None, company_name=None):
        assert (stock_code is not None) or (company_name is not None), 'stock_code or company_name must be provided'
        run_path = os.path.join(self.save_path, 'single_' + stock_code + "_" + date + "_" + self.model_name)
        if not os.path.exists(run_path):
            os.mkdir(run_path)
        log_file = os.path.join(run_path, 'finrpt.log')
        if os.path.isfile(log_file):
            os.remove(log_file)
        logger = setup_logger(log_name=run_path, log_file=os.path.join(run_path, 'finrpt.log'))
        
        data = {"save":{}}
        data["save"]["id"] = stock_code + "_" + date
        data["save"]["stock_code"] = stock_code
        data["save"]["date"] = date
        data["model_name"] = self.model_name
        data["date"] = date

        logger.info("Starting FinRpt")
        
        logger.info("Getting compnay info")
        data["company_info"] = self.dataer.get_company_info(stock_code=stock_code, company_name=company_name)
        data["save"]["company_info"] = data["company_info"]
        data["stock_code"] = data["company_info"]["stock_code"]
        data["company_name"] = data["company_info"]["company_name"]
        logger.info("Got company info successfully!")
        logger.debug(str(data["company_info"]))
        
        logger.info("Getting financials for %s at %s" % (data["company_name"], data["date"]))
        data["financials"] = self.dataer.get_finacncials_ak(stock_code=data["stock_code"], end_date=date)
        if not data["financials"]:
            raise Exception("No financials found for this date")
        data["save"]["financials"] = data["financials"]
        logger.info("Got financials successfully!")
        logger.debug(str(data["financials"]))
        
        logger.info("Getting news for %s at %s" % (data["company_name"], data["date"]))
        news = self.dataer.get_company_news_sina(stock_code=data["stock_code"], end_date=date, company_name=data["company_name"])
        if not news:
            raise Exception("No news found for this date")
        new_news = []
        for new in news:
            if new['news_decision'] == '是':
                new_news.append(new)
        news = new_news
        data["news"] = self.post_process_news(news)
        data["save"]["news"] = data["news"]
        logger.debug(str(data["news"]))
        # data["news"] = news
        
        logger.info("Getting report for %s at %s" % (data["company_name"], data["date"]))
        report = self.dataer.get_company_report_em(stock_code=stock_code, date=date)
        logger.info("Got report successfully!")
        
        if not report:
            report = {
                'report_id': data['stock_code'] + date,
                'date': date,
                'content': '',
                'stock_code': data['stock_code'],
                'title': '',
                'core_content': ''
                
            }
            print("No report found for this date")
        data["report"] = report
        data["save"]["report"] = data["report"]
        logger.debug(str(data["report"]['summary']))
        
        
        try:
            conn = sqlite3.connect(self.dataer.database_name)
            c = conn.cursor()
            c.execute(f''' SELECT * FROM trend WHERE  id='{stock_code}_{date}' ''')
            trend = c.fetchone()
            c.close()
            conn.close()
        except Exception as e:
            trend = None
            
        data["trend"] = 1 if trend[3] > 0 else 0
        
        self.model = OpenAIModel(model_name=self.model_name, max_rounds=3)
        
        financials_prompt = "季度损益:" + data["financials"]['stock_income'].to_string() + '\n资产负债:' + data["financials"]['stock_balance_sheet'].to_string() + '\n现金流量:' + data["financials"]['stock_cash_flow'].to_string()
        concise_news = [new['news_time'] + ': ' + new['news_summary'] for new in data['news'] if new['news_decision']=='是']
        news_prompt = '\n'.join(concise_news)
        report_prompt = data['report']['title'] + ":[[[" + data['report']['summary'].strip() + "]]]"
        stock_price = ", ".join(str(d) + ": " + str(p) for d, p in zip(data['financials']['stock_data']['date'], data['financials']['stock_data']['Close']))
        csi300_price = ", ".join(str(d) + ": " + str(p) for d, p in zip(data['financials']['csi300_stock_data']['date'], data['financials']['csi300_stock_data']['close']))
        stock_price_prompt = "最近一个月沪深300指数历史价格： " + csi300_price  + "\n\n" + "最近一个月该股票公司历史价格：" + stock_price 
        prompt = "分析日期: " + data["date"] + "\n\n" + \
            "公司名称: " + data["company_name"] + "\n\n" + \
            "股票近期财务数据:\n" + financials_prompt[:4000] + "\n\n" + \
            "股票近期新闻信息:\n" + news_prompt[:4000] + "\n\n" + \
            "股票半年报或年报:\n" + report_prompt[:4000] + "\n\n" + \
            "股票近期价格:\n" + stock_price_prompt[:4000] + "\n\n"
            
        finance_response, finance_response_json = self.model.json_prompt(prompt + "\n\n\n" + PROMPT_FINANCE)
        logger.debug('<<<finance_response>>>\n' + str(finance_response))
        news_response, news_response_json = self.model.json_prompt(prompt + "\n\n\n" + PROMPT_NEWS)
        logger.debug('<<<news_response>>>\n' + str(news_response))
        report_response, report_response_json = self.model.json_prompt(prompt + "\n\n\n" + PROMPT_REPORT)
        logger.debug('<<<report_response>>>\n' + str(report_response))
        trend_response, trend_response_json = self.model.json_prompt(prompt + "\n\n\n" + PROMPT_TREND)
        logger.debug('<<<trend_response>>>\n' + str(trend_response))
        risk_response, risk_response_json = self.model.json_prompt(prompt + "\n\n\n" + PROMPT_RISK)
        logger.debug('<<<risk_response>>>\n' + str(risk_response))
        
        data['save']['finance_write_response'] = json.dumps(finance_response_json, ensure_ascii=False)
        data['save']['news_write_response'] = json.dumps(news_response_json, ensure_ascii=False)
        data['save']['report_write_response'] = json.dumps(report_response_json, ensure_ascii=False)
        data['save']['trend_write_response'] = json.dumps(trend_response_json, ensure_ascii=False)
        data['save']['risk_response'] = json.dumps(risk_response_json, ensure_ascii=False)
        
        data['report_title'] = data["company_info"]["company_name"] + "研报（" + date + "）"
        
        result_save_path = os.path.join(run_path, 'result.pkl')
        pickle.dump(data['save'], open(result_save_path, 'wb'))
        
        # build_report(data, date, run_path)
        
    def post_process_news(self, news):
        news, short_ratio = short_eliminate(news)
        news, bert_ratio = duplication_eliminate_bert(news)
        news, hash_raito = duplication_eliminate_hash(news)
        news, date_ratio = filter_news_by_date(news)
        news, limit_ratio = limit_by_amount(news, 50)
        return news
    
    def post_process_report(self, report):
        content = report["content"]
        start = '第三节  管理层讨论与分析\n'
        if content.find(start) == -1:
            start = '第三节 管理层讨论与分析\n'
        end = '第四节  公司治理\n'
        if content.find(end) == -1:
            end = '第四节 公司治理\n'
        report['content'] = content[content.find(start):content.find(end)].strip()
        return report
        
        
if __name__ == '__main__':
    finrpt = FinRptSingle(model_name="gpt-4o-mini")
    finrpt.run(date='2024-11-05', stock_code='601857.SS')
    