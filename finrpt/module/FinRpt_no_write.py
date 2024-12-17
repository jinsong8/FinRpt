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

class FinRpt_no_write:
    def __init__(self, model_name="gpt-4o", max_rounds=3, language='zh', database_name='/data/name/FinRpt_v1/finrpt/source/cache.db', save_path='./reports'):
        if "finetune" in model_name:
            real_model_name = model_name
            model_name = 'gpt-4o'
        else:
            real_model_name = model_name
        self.advisor = Advisor(model_name=real_model_name, max_rounds=max_rounds, language=language)
        self.financials_analyzer = FinancialsAnalyzer(model_name=model_name, max_rounds=max_rounds, language=language)
        self.news_analyzer = NewsAnalyzer(model_name=model_name, max_rounds=max_rounds, language=language)
        self.predictor = Predictor(model_name=real_model_name, max_rounds=max_rounds, language=language)
        self.risk_assessor = RiskAssessor(model_name=model_name, max_rounds=max_rounds, language=language)
        self.dataer = Dataer(database_name=database_name)
        self.model_name = model_name
        self.max_rounds = max_rounds
        self.save_path = save_path
        
    def run(self, date, stock_code=None, company_name=None):
        assert (stock_code is not None) or (company_name is not None), 'stock_code or company_name must be provided'
        run_path = os.path.join(self.save_path, stock_code + "_" + date + "_" + self.model_name + "_no_write")
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
        
        logger.info("Analyzing news for %s at %s" % (data["company_name"], data["date"]))
        data["analyze_news"] = self.news_analyzer.run(data, run_path=run_path)
        
        logger.info("Analyzing financials for %s at %s" % (data["company_name"], data["date"]))
        data["analyze_income"], data["analyze_balance"], data["analyze_cash"] = self.financials_analyzer.run(data, run_path=run_path)
        
        logger.info("Analyzing advisor for %s at %s" % (data["company_name"], data["date"]))
        data['analyze_advisor'] = self.advisor.run(data, run_path=run_path)
        
        from finrpt.module.Advisor import PROMPT_ZH
        financials_prompt = "季度损益:" + data['analyze_income'] + '\n资产负债:' + data['analyze_balance'] + '\n现金流量:' + data['analyze_cash']
        concise_news = [new['concise_new'] for new in data['analyze_news']]
        news_prompt = '\n'.join(concise_news)
        report_prompt = data['report']['title'] + ":[[[" + data['report']['summary'].strip() + "]]]"
        advisor_prompt = "分析日期: " + data["date"] + "\n\n" + \
                 "公司名称: " + data["company_name"] + "\n\n" + \
                 "财务数据:\n" + financials_prompt + "\n\n" + \
                 "关键新闻:\n" + news_prompt + "\n\n" + \
                 "股票半年报或年报:\n" + report_prompt + "\n\n\n" + PROMPT_ZH
        res, res_json = OpenAIModel(model_name=self.model_name, max_rounds=self.max_rounds).json_prompt(advisor_prompt)
        data['analyze_advisor'] = res_json['report']
        
        logger.info("Analyzing risk for %s at %s" % (data["company_name"], data["date"]))
        data['analyze_risk'] = self.risk_assessor.run(data, run_path=run_path)
        
        logger.info("Predicting future for %s at %s" % (data["company_name"], data["date"]))
        data['analyze_predict'] = self.predictor.run(data, run_path=run_path)
        
        data['report_title'] = data["company_info"]["company_name"] + "研报（" + date + "）"
        
        result_save_path = os.path.join(run_path, 'result.pkl')
        pickle.dump(data['save'], open(result_save_path, 'wb'))
        
        logger.info("Building report for %s at %s" % (data["company_name"], data["date"]))
        
        logger.info("Trend %s" % (data["trend"]))
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
    finrpt = FinRpt(model_name="gpt-4o-mini")
    # finrpt = FinRpt(model_name="gpt-4o-mini")
    # finrpt.run(date='2024-10-28', stock_code='002594.SZ')
    # finrpt.run(date='2024-10-28', stock_code='600519.SS')
    # finrpt.run(date='2024-10-28', stock_code='600029.SZ')
    # finrpt.run(date='2024-10-28', stock_code='600941.SS')
    # finrpt.run(date='2024-10-08', stock_code='000002.SZ')
    # TODO: debug for report not found
    finrpt.run(date='2024-11-05', stock_code='600519.SS')
    