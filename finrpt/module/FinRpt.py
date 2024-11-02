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
import pdb

class FinRpt:
    def __init__(self, model_name="gpt-4o", max_rounds=3, language='zh', database_name='/home/jinsong/FinRpt/finrpt/source/cache.db'):
        self.advisor = Advisor(model_name=model_name, max_rounds=max_rounds, language=language)
        self.financials_analyzer = FinancialsAnalyzer(model_name=model_name, max_rounds=max_rounds, language=language)
        self.news_analyzer = NewsAnalyzer(model_name=model_name, max_rounds=max_rounds, language=language)
        self.predictor = Predictor()
        self.risk_assessor = RiskAssessor(model_name=model_name, max_rounds=max_rounds, language=language)
        self.dataer = Dataer(database_name=database_name)
        self.model_name = model_name
        
    def run(self, date, stock_code=None, company_name=None):
        assert (stock_code is not None) or (company_name is not None), 'stock_code or company_name must be provided'
        data = {}
        data["model_name"] = self.model_name
        data["date"] = date
        data["company_info"] = self.dataer.get_company_info(stock_code=stock_code, company_name=company_name)
        data["stock_code"] = data["company_info"]["stock_code"]
        data["company_name"] = data["company_info"]["company_name"]
        data["financials"] = self.dataer.get_finacncials_yf(stock_code=data["stock_code"], end_date=date)
        news = self.dataer.get_company_news_sina(stock_code=data["stock_code"], end_date=date)
        # news = [{"news_title": "test", "news_content": "test", "news_time": "2023-07-01"}]
        data["news"] = self.post_process_news(news)
        # data["news"] = news
        report = self.dataer.get_company_report_em(stock_code=stock_code, date=date)
        if not report:
            report = {
                'report_id': data['stock_code'] + date,
                'date': date,
                'content': '',
                'stock_code': data['stock_code'],
                'title': ''
            }
            print("No report found for this date")
        data["report"] = self.post_process_report(report)
        data["analyze_news"] = self.news_analyzer.run(data)
        data["analyze_income"], data["analyze_balance"], data["analyze_cash"] = self.financials_analyzer.run(data)
        data['analyze_advisor'] = self.advisor.run(data)
        data['analyze_risk'] = self.risk_assessor.run(data)
        data['report_title'] = data["company_info"]["company_name"] + "研报（" + date + "）"
        build_report(data, date)
        
    def post_process_news(self, news):
        news, short_ratio = short_eliminate(news)
        news, bert_ratio = duplication_eliminate_bert(news)
        news, hash_raito = duplication_eliminate_hash(news)
        news, date_ratio = filter_news_by_date(news)
        news, limit_ratio = limit_by_amount(news, 20)
        return news
    
    def post_process_report(self, report):
        content = report["content"]
        start = '第三节  管理层讨论与分析\n'
        end = '第四节  公司治理\n'
        report['content'] = content[content.find(start):content.find(end)]
        return report
        
        
if __name__ == '__main__':
    finrpt = FinRpt(model_name="gpt-4o")
    # finrpt.run(date='2024-10-28', stock_code='002594.SZ')
    # finrpt.run(date='2024-10-28', stock_code='600519.SS')
    # finrpt.run(date='2024-10-28', stock_code='600029.SZ')
    # finrpt.run(date='2024-10-28', stock_code='600941.SS')
    # finrpt.run(date='2024-10-28', stock_code='000538.SZ')
    finrpt.run(date='2024-10-28', stock_code='300750.SZ')
    
        
        
    