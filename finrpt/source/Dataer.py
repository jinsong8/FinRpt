import requests
import time
import sqlite3
import akshare as ak
from datetime import datetime
from dateutil.relativedelta import relativedelta
from finrpt.module.OpenAI import OpenAIModel
from finrpt.utils.data_processing import post_process_report
from lxml import etree
import re
import pandas as pd
from tqdm import tqdm
import yfinance as yf
import pickle
import json
import pytz
import pdb

from finrpt.source.database_init import (
    company_info_table_init, 
    company_report_table_init, 
    announcement_table_init, 
    company_news_table_init,
    COMPANY_INFO_TABLE_COLUMNS, 
    COMPANY_REPORT_TABLE_COLUMNS
)
from finrpt.source.database_insert import (
    company_info_table_insert_em, 
    company_report_table_insert, 
    announcement_table_insert,
    company_news_table_insert
)
    
from finrpt.source.database_query import company_news_table_query_by_url, announcement_table_query_by_url

class Dataer:
    def __init__(self, max_retry=1, database_name = '/data/jinsong/FinRpt_v1/finrpt/source/cache.db', model_name = 'gpt-4o-mini'):
        self.max_retry = max_retry
        self.database_name = database_name
        self.model = OpenAIModel(model_name=model_name)
        self._init_db()

    def _init_db(self):
        # create table for company info
        company_info_table_init(self.database_name)
        company_report_table_init(self.database_name)
        announcement_table_init(self.database_name)
        company_news_table_init(self.database_name)

    def _request_get(self, url, headers = None, verify = None, params = None):
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        max_retry = self.max_retry
        for _ in range(max_retry):
            try:
                response = requests.get(url = url, headers = headers, verify = verify, params = params)
                if response.status_code == 200:
                    break
            except:
                response = None

        if response is not None and response.status_code != 200:
            response = None
            
        return response
    
    def _request_post(self, url, headers = None, json = None):
        if headers is None:
            headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0"
            }
        max_retry = self.max_retry
        for _ in range(max_retry):
            try:
                response = requests.post(url = url, headers = headers, json = json)
                if response.status_code == 200:
                    break
            except:
                response = None

        if response is not None and response.status_code != 200:
            response = None

        return response
    
    def get_company_info(self, stock_code = None, company_name = None):
        assert company_name or stock_code, "company_name or company_code must be provided"
        stock_code_ori = stock_code

        result = None
        try:
            conn = sqlite3.connect(self.database_name)
            c = conn.cursor()
            c.execute('SELECT * FROM company_info WHERE stock_code = ?', (stock_code_ori,))
            result = c.fetchone()
            c.close()
        except Exception as e:
            print(e)
        if result:
            return dict(zip(COMPANY_INFO_TABLE_COLUMNS, result))
        
        normal2em = {'SS': 'SH', 'SZ': 'SZ'}
        if stock_code:
            assert len(stock_code) >= 6, "stock_code must be at least 6 characters"
            exchange = normal2em[stock_code[-2:]]
            stock_code = stock_code[:6] + '.' + exchange
            pass
        else:
            return None


        url = f'https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_BASIC_ORGINFO&columns=ALL&filter=(SECUCODE%3D%22{stock_code}%22)&pageNumber=1&pageSize=1&source=HSF10&client=PC'
        try:
            response = self._request_get(url)
            data = response.json()['result']['data'][0]
            company_info_table_insert_em(db=self.database_name, data=data, stock_code=stock_code_ori)
            return self.get_company_info(stock_code=stock_code_ori)
        except Exception as e:
            print(e)

        return None
    
    def get_company_report_em(self, date, stock_code):
        
        def _get_report_content(art_code):
            url = f"https://np-cnotice-stock.eastmoney.com/api/content/ann?art_code={art_code}&client_source=web"
            response = self._request_get(url)
            if response is None:
                return ""
            try:
                page_size = json.loads(response.text)['data']['page_size']
            except Exception as e:
                print(e)
                return ""
            report_contents = []
            for page_index in range(1, page_size + 1):
                page_url = f"https://np-cnotice-stock.eastmoney.com/api/content/ann?art_code={art_code}&client_source=web&page_index={page_index}"
                page_response = self._request_get(page_url)
                if page_response is None:
                    return ""
                try:
                    page_content = json.loads(page_response.text)['data']['notice_content']
                except Exception as e:
                    print(e)
                    continue
                report_contents.append(page_content)
            return "\n".join(report_contents).strip().replace("\u3000", " ")
        
        def _get_report_id(report_type, date, stock_code):
            if report_type == '半年度报告全文':
                report_id = stock_code + '_' + date[:4] + '_Q2'
            else:
                date = datetime.strptime(date, "%Y-%m-%d") - relativedelta(years=1)
                date = date.strftime("%Y-%m-%d")
                report_id = stock_code + '_' + date[:4] + '_Q4'
            return report_id
        
        report_start_date = datetime.strptime(date, "%Y-%m-%d") - relativedelta(years=1)
        report_start_date = report_start_date.strftime("%Y-%m-%d")
        report_date = date
        
        break_flag = False
        content = ""
        for page_index in range(1, 10):
            url = f'https://np-anotice-stock.eastmoney.com/api/security/ann?ann_type=A&stock_list={stock_code[:6]}&page_index={page_index}&page_size=100'
            response  = self._request_get(url)
            try:
                reprot_list = json.loads(response.text)['data']['list']
            except Exception as e:
                print(e)
                continue
            for report in reprot_list:
                try:
                    date = report['notice_date'][:10]
                    if date > report_date:
                        continue
                    if date < report_start_date:
                        break_flag = True
                        break
                    the_report_type = report['columns'][0]['column_name']
                    if the_report_type not in ['半年度报告全文', '年度报告全文']:
                        continue
                    title = report['title']
                    if "英文" in title or "摘要" in title:
                        continue
                    art_code = report['art_code']
                    the_report_id = _get_report_id(the_report_type, date, stock_code)
                    
                    try:
                        conn = sqlite3.connect(self.database_name)
                        c = conn.cursor()
                        c.execute('SELECT * FROM company_report WHERE report_id = ?', (the_report_id,))
                        query_result = c.fetchone()
                        c.close()
                    except Exception as e:
                        query_result = None
                    
                    if query_result:
                        content = dict(zip(COMPANY_REPORT_TABLE_COLUMNS, query_result))
                        return content
                    else:
                        return None # for report generate
                        content = _get_report_content(art_code=art_code)
                    break_flag = True
                    break
                except Exception as e:
                    print(e)
                    continue
            if break_flag:
                    break
        if content == "":
            return None
        
        core_content = post_process_report(content)
        for retry in range(3):
            report_agent_summary = self.model.simple_prompt('内容：\n' + core_content + '\n\n\n\n为了便于后续的大模型阅读理解，请将以上内容重新排版，舍弃表格等不重要信息。')[0]
            if len(report_agent_summary) > 200:
                break
        
        result = {
            'report_id': the_report_id,
            'date': date,
            'content': content,
            'stock_code': stock_code,
            'title': title,
            'core_content': core_content,
            'summary': report_agent_summary
        }
        company_report_table_insert(db=self.database_name, data=result)
        return result 

    def get_company_report(self, date, stock_code = None):
        assert date or stock_code, "date or stock_code must be provided"
        
        year = datetime.strptime(date, '%Y-%m-%d').year
        month = datetime.strptime(date, '%Y-%m-%d').month
        request_list = []
        if month > 3:
            request_list.append("_".join([stock_code, str(year), "Q1"]))
        if month > 6:
            request_list.append("_".join([stock_code, str(year), "Q2"]))
        if month > 9:
            request_list.append("_".join([stock_code, str(year), "Q3"]))
        for year in range(year - 3, year):
            for quarter in range(1, 5):
                request_list.append("_".join([stock_code, str(year), f"Q{quarter}"]))

        results = []
        try:
            conn = sqlite3.connect(self.database_name)
            c = conn.cursor()
            for report_id in request_list:
                c.execute('SELECT * FROM company_report WHERE company_report_code = ?', (report_id,))
                result = c.fetchone()
                if result:
                    request_list.remove(report_id)
                    results.append(dict(zip(COMPANY_INFO_TABLE_COLUMNS, result)))    
            c.close()
        except Exception as e:
            print(e)
        if len(request_list) == 0:
            return results

        stock_code_simple = stock_code[:6]
        top_url = 'https://vip.stock.finance.sina.com.cn/'
        url_Q1 = f'https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_BulletinYi/stockid/{stock_code_simple}/page_type/yjdbg.phtml'
        url_Q2 = f'https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_BulletinZhong/stockid/{stock_code_simple}/page_type/zqbg.phtml'
        url_Q3 = f'https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_BulletinSan/stockid/{stock_code_simple}/page_type/sjdbg.phtml'
        url_Q4 = f'https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_Bulletin/stockid/{stock_code_simple}/page_type/ndbg.phtml'
        pattern1 = r'.*报告(全文)?$'
        pattern2 = r'(\d+)年'
        # Q1
        for q, url in zip(['Q1', 'Q2', 'Q3', 'Q4'], [url_Q1, url_Q2, url_Q3, url_Q4]):
            response = self._request_get(url_Q1)
            try:
                page = etree.HTML(response.text)
                report_date = [s.strip() for s in page.xpath('//div[@class="datelist"]/ul/text()')]
                report_a = page.xpath('//div[@class="datelist"]/ul/a')
            except Exception as e:
                print(e)
                continue

            for id, element in enumerate(report_a):
                title = element.text.strip() 
                link = element.get('href')  
                if not re.match(pattern1, title):
                    continue
                match_year = re.findall(pattern2, title)
                if not match_year:
                    continue
                match_year = match_year[0]
                company_report_code = "_".join([stock_code, match_year, q])
                if company_report_code in request_list:
                    data_response = self._request_get(top_url + link)
                    try:
                        data_page = etree.HTML(data_response.text)
                        report_data = data_page.xpath('//*[@id="content"]')[0]
                        report_data = etree.tostring(report_data, encoding='unicode')
                    except Exception as e:
                        print(e)
                        continue
                    insert_data = {
                        "company_report_code": company_report_code, 
                        "report_data": report_data,  
                        "stock_code": stock_code,  
                        "release_time": report_date[id],  
                        "title": title 
                    }
                    if company_report_table_insert(self.database_name, insert_data):
                        request_list.remove(company_report_code)
                        results.append(insert_data)
        return results

    def get_company_announcement(self, stock_code, end_date, start_date = None):
        
        def _get_announcement_from_url(url):
            data_response = self._request_get(url)
            try:
                data_page = etree.HTML(data_response.text)
                ann_data = data_page.xpath('//*[@id="content"]')[0]
                ann_data = etree.tostring(ann_data, encoding='unicode')
            except Exception as e:
                print(e)
                ann_data = None
            return ann_data

        top_url = 'https://vip.stock.finance.sina.com.cn/'

        if not start_date:
            start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(month=3)
            start_date = start_date.strftime("%Y-%m-%d")

        result = []
        stock = stock_code[:-3]
        flag = False
        for page in range(1, 100):
            url = f"https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletin.php?stockid={stock}&Page={page}"
            response = self._request_get(url)
            try:
                page = etree.HTML(response.text)
                ann_date = [s.strip() for s in page.xpath('//div[@class="datelist"]/ul/text()')]
                ann_a = page.xpath('//div[@class="datelist"]/ul/a')
            except Exception as e:
                print(e)
                continue
            for id, element in enumerate(ann_a):
                if ann_date[id] < start_date:
                    flag = True
                    break
                if ann_date[id] > end_date:
                    continue
                title = element.text.strip() 
                link = element.get('href')  
                query_result = content = announcement_table_query_by_url(db=self.database_name, url=link)
                if content is None:
                    content = _get_announcement_from_url(top_url + link)
                if not content:
                    continue
                one_announcement = {
                    "title": title,
                    "date": ann_date[id],
                    "content": content,
                    "stock_code": stock_code,
                    "url": link
                }
                result.append(one_announcement)
                if not query_result:
                    announcement_table_insert(db=self.database_name, data=one_announcement)
            if flag:
                break
        return result

    def get_company_news(self, stock_code, end_date, start_date = None):

        def get_one_page(news_url):
            response = self._request_get(news_url)
            response.encoding = 'utf-8'
            data = etree.HTML(response.text)
            data = data.xpath('//*[@id="zw_body"]')[0]
            news_content = []
            for i in data:
                if i.tag == 'p':
                    str = i.xpath('string()').strip()
                    if str == '' or str == 'EM_StockImg_Start' or str == 'EM_StockImg_End':
                        continue
                    news_content.append(str)
            return '\n'.join(news_content)

        if not start_date:
            start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(month=3)
            start_date = start_date.strftime("%Y-%m-%d")

        result = []
        stock = stock_code[:-3]
        flag = False
        for page in range(1, 100):
            url = f"https://guba.eastmoney.com/list,{stock},1,f_{page}.html"
            response = self._request_get(url)
            response.encoding = 'utf-8'
            try:
                data = etree.HTML(response.text)
                data = data.xpath('//tbody[@class="listbody"]')[0]
            except Exception as e:
                print(e)
                continue
            for item in data:
                try:
                    read_num = item[0][0].text
                    reply_num = item[1][0].text
                    news_url = 'https://guba.eastmoney.com' + item[2][0][0].get('href')
                    news_title = item[2][0][0].text
                    news_author = item[3][0][0].text
                    news_time = '2024-' + item[4][0].text[:5]
                    if news_time < start_date:
                        flag = True
                        break
                    query_result = news_content = company_news_table_query_by_url(news_url=news_url, db=self.database_name)
                    if not news_content:
                        news_content = get_one_page(news_url)
                    if not news_content:
                        continue
                    one_news = {
                        "read_num": read_num,
                        "reply_num": reply_num,
                        "news_url": news_url,
                        "news_title": news_title,
                        "news_author": news_author,
                        "news_time": news_time,
                        "news_content": news_content,
                        "stock_code": stock_code
                    }
                    result.append(one_news)
                    if not query_result:
                        company_news_table_insert(db=self.database_name, data=one_news)
                except Exception as e:
                    print(e)
            if flag:
                break
        print(result)

    def get_company_news_sina(self, stock_code, end_date, start_date = None, company_name=""):
        
        stock_map = {
            "SS": "sh",
            "SZ": "sz"
        }
        
        # # for report generate
        # try:
        #     conn = sqlite3.connect(self.database_name)
        #     c = conn.cursor()
        #     c.execute('''SELECT * FROM newsdup WHERE id=?''', (f"{stock_code}_{end_date}",))
        #     result = c.fetchone()
        #     return pickle.loads(result[1])
        # except Exception as e:
        #     return None
      

        def _get_news_from_url(url):
            data_response = self._request_get(url)
            data_response.encoding = 'utf-8'
            one_news = None
            try:
                data_page = etree.HTML(data_response.text)
                ann_data = data_page.xpath('//*[@id="artibody"]')[0]
                one_news = ann_data.xpath('string()').strip().split('\n\n')[0].strip()
                one_news = one_news.split('\t\t')[0]
            except IndexError as e:
                data_response.encoding = 'gb2312'
                data_page = etree.HTML(data_response.text)
                try:
                    ann_data = data_page.xpath('//*[@class="blk_container"]')[0]
                    one_news = ann_data.xpath('string()').strip().split('\n\n')[0].strip()
                except IndexError as e:
                    try:
                        data_response.encoding = 'gbk'
                        data_page = etree.HTML(data_response.text)
                        ann_data = data_page.xpath('//*[@id="artibody"]')[0]
                        one_news = ann_data.xpath('string()').strip().split('\n\n')[0].strip()
                        one_news = one_news.split('\t\t')[0]
                    except Exception as e:
                        # print(e)
                        one_news = None
            except Exception as e:
                print(e)
                one_news = None
            return one_news

        if not start_date:
            start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=1)
            start_date = start_date.strftime("%Y-%m-%d")
            
        # for report generate
        # try:
        #     conn = sqlite3.connect(self.database_name)
        #     c = conn.cursor()
        #     c.execute('''SELECT * FROM newsduped WHERE stock_code = ? AND news_time BETWEEN ? and ? ''', (stock_code, start_date, end_date))
        #     results = c.fetchall()
        #     resutls_list = []
        #     for row in results:
        #         resutls_list.append({
        #             "news_url":row[0],
        #             "read_num":row[1],
        #             "reply_num":row[2],
        #             "news_title":row[3],
        #             "news_author":row[4],
        #             "news_time":row[5],
        #             "stock_code":row[6],
        #             "news_content":row[7],
        #             "news_summary":row[8],
        #             "dec_response":row[9],
        #             "news_decision":row[10]
        #         })
        #     return resutls_list
        # except Exception as e:
        #     return None
            
        # for report generate
        try:
            conn = sqlite3.connect(self.database_name)
            c = conn.cursor()
            c.execute('''SELECT * FROM newsemb WHERE stock_code = ? AND news_time BETWEEN ? and ? ''', (stock_code, start_date, end_date))  
            results = c.fetchall()
            resutls_list = []
            for row in results:
                resutls_list.append({
                    "news_url":row[0],
                    "read_num":row[1],
                    "reply_num":row[2],
                    "news_title":row[3],
                    "news_author":row[4],
                    "news_time":row[5],
                    "stock_code":row[6],
                    "news_content":row[7],
                    "news_summary":row[8],
                    "dec_response":row[9],
                    "news_decision":row[10],
                    "news_embedding":pickle.loads(row[11]),
                })
            return resutls_list
        except Exception as e:
            return []
            
        result = []
        stock = stock_map[stock_code[-2:]] + stock_code[:-3]
        flag = False
        for page in range(1, 50):
            url = f"https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php?symbol={stock}&Page={page}"
            response = self._request_get(url)
            try:
                page = etree.HTML(response.text)
                ann_date = [s.strip()[:10] for s in page.xpath('//div[@class="datelist"]/ul/text()')]
                ann_date = ann_date[::2]
                ann_a = page.xpath('//div[@class="datelist"]/ul/a')
            except Exception as e:
                print(e)
                continue
            for id, element in enumerate(ann_a):
                if ann_date[id] < start_date:
                    flag = True
                    break
                if ann_date[id] > end_date:
                    continue
                
                if str(element.text) == 'None':
                    continue

                try:
                    title = element.text.strip() 
                    link = element.get('href')  
                except Exception as e:
                    print(e)
                    continue
                
                query_result = content = company_news_table_query_by_url(db=self.database_name, news_url=link)
                if content is None:
                    continue # for report generate
                    content = _get_news_from_url(link)
                    if content is None:
                        continue
                    
                    news_summary_prompt = """请总结以上新闻内容，最多不超过200个字。"""
                    for retry_count in range(self.max_retry):
                        try:
                            news_summary = self.model.simple_prompt(content + "\n\n\n\n" + news_summary_prompt)[0]
                            break
                        except Exception as e:
                            pass
                    dec_prompt = """作为金融分析助手，你的任务是评估新闻事件对股票市场的潜在影响。请判断所提供的新闻是否可能影响{company_name}的未来股票走势。注意，单日的股票涨跌数据并不在考虑之列。提供分析理由时，请基于以下判定标准：
行业动态：新闻是否反映出整体行业的重大变化或趋势？
监管政策：新闻中是否提到影响该公司运作的政策或法规变动？
公司财务：新闻是否涉及公司的财务报告、收购、合并等重大事项？
市场竞争：新闻是否涉及该公司竞争对手的新战略或技术突破？
宏观经济：新闻是否反映出可能影响公司运营的宏观经济变化？
参考这些标准，给出分析理由，在提供理由之后，如果判断提供的新闻可能影响{company_name}公司未来股票变化,回答"[[[是]]]"，否则回答"[[[否]]]"。"""
                    dec_prompt = dec_prompt.format(company_name=company_name)
                    for retry_count in range(self.max_retry):
                        try:
                            dec_response = self.model.simple_prompt("新闻内容：" + news_summary + "\n\n\n\n" + dec_prompt)[0]
                            if "[[[是]]]" in dec_response or "[[[否]]]" in dec_response:
                                break
                        except Exception as e:
                            pass
                    if "[[[是]]]" in dec_response:
                        dec = "是"
                    elif "[[[否]]]" in dec_response:
                        dec = "否"
                    else:
                        continue
                    
                    try:
                        one_news = {
                                "read_num": 0,
                                "reply_num": 0,
                                "news_url": link,
                                "news_title": title,
                                "news_author": "sina",
                                "news_time": ann_date[id],
                                "news_content": content,
                                "stock_code": stock_code,
                                "news_summary": news_summary,
                                "dec_response": dec_response,
                                "news_decision": dec
                        }
                    except Exception as e:
                        print(e)
                        continue
                    result.append(one_news)
                    company_news_table_insert(db=self.database_name, data=one_news)
                else:
                    one_news = {
                                "read_num": 0,
                                "reply_num": 0,
                                "news_url": link,
                                "news_title": title,
                                "news_author": "sina",
                                "news_time": ann_date[id],
                                "news_content": query_result[-4],
                                "stock_code": stock_code,
                                "news_summary": query_result[-3],
                                "dec_response": query_result[-2],
                                "news_decision": query_result[-1]
                        }
                    result.append(one_news)
            if flag:
                break
        return result
    
    def get_finacncials_yf(self, stock_code, end_date, start_date=None):
        if not start_date:
            start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=3)
            start_date = start_date.strftime("%Y-%m-%d")
        ticker = yf.Ticker(stock_code)
        stock_info = ticker.info
        stock_data = ticker.history(start=start_date, end=end_date)
        stock_income = ticker.quarterly_income_stmt
        stock_income = stock_income.loc[:, stock_income.columns <= pd.to_datetime(end_date)]
        stock_balance_sheet = ticker.quarterly_balance_sheet
        stock_balance_sheet = stock_balance_sheet.loc[:, stock_balance_sheet.columns <= pd.to_datetime(end_date)]
        stock_cash_flow = ticker.quarterly_cashflow
        stock_cash_flow = stock_cash_flow.loc[:, stock_cash_flow.columns <= pd.to_datetime(end_date)]
        result = {
            "stock_info": stock_info,
            "stock_data": stock_data,
            "stock_income": stock_income,
            "stock_balance_sheet": stock_balance_sheet,
            "stock_cash_flow": stock_cash_flow
        }
        return result
    
    def get_finacncials_ak(self, stock_code, end_date, start_date=None):
        pd.options.mode.chained_assignment = None
        if not start_date:
            start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=1)
            start_date = start_date.strftime("%Y-%m-%d")
            
        # for report generate
        try:
            conn = sqlite3.connect(self.database_name)
            c = conn.cursor()
            c.execute(f"SELECT * FROM financials WHERE id='{stock_code}_{end_date}'")
            result_raw = c.fetchone()
            result = {
                "stock_info": pickle.loads(pickle.loads(result_raw[1])),
                "stock_data": pickle.loads(pickle.loads(result_raw[2])),
                "stock_income": pickle.loads(pickle.loads(result_raw[3])),
                "stock_balance_sheet": pickle.loads(pickle.loads(result_raw[4])),
                "stock_cash_flow": pickle.loads(pickle.loads(result_raw[5])),
                "csi300_stock_data": pickle.loads(pickle.loads(result_raw[6]))
            }
            return result
        except Exception as e:
            return None
            
            
            
        start_date_report = (datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(years=2)).strftime("%Y-%m-%d")
            
        if stock_code[-2:] == 'SS':
            stock_code_zh = 'sh' + stock_code[:-3]
        if stock_code[-2:] == 'SZ':
            stock_code_zh = 'sz' + stock_code[:-3]
            
        start_date_zh = start_date.replace('-', '')
        end_date_zh = end_date.replace('-', '')
        start_date_report_zh = start_date_report.replace('-', '')
            
        stock_info = ak.stock_individual_info_em(symbol=stock_code[:-3])
        stock_info = stock_info.set_index('item')['value'].to_dict()
        
        # stock_data = ak.stock_zh_a_daily(symbol=stock_code_zh, start_date=start_date_zh, end_date=end_date_zh)
        stock_data = ak.stock_zh_a_hist_tx(symbol=stock_code_zh, start_date=start_date_zh, end_date=end_date_zh)
        stock_data = stock_data.rename(columns={'open': 'Open', 'close': 'Close', 'high': 'High', 'low': 'Low', 'volume': 'Volume'})
        
        csi300_stock_data = ak.stock_zh_a_hist_tx(symbol="sh000300", start_date=start_date_zh, end_date=end_date_zh)
        
        income_key = [
            "报告日",
            "营业总收入",
            "营业总成本",
            "营业利润",
            "净利润",
            "基本每股收益",
            "稀释每股收益",
            "投资收益",
        ]
        income_rename_dict = {
            "营业收入": "营业总收入",
            "营业支出": "营业总成本"
        }
        income = ak.stock_financial_report_sina(stock=stock_code_zh, symbol="利润表")
        income = income.rename(columns={k: v for k, v in income_rename_dict.items() if k in income.columns and v not in income.columns})
        stock_income = income[income_key]
        
        # qoq
        quarter_over_quarter = [] 
        for i in range(0, len(stock_income) - 1):
            prev_value = stock_income['营业总收入'].iloc[i + 1]
            current_value = stock_income['营业总收入'].iloc[i]
            growth = (current_value - prev_value) / prev_value * 100
            quarter_over_quarter.append(growth)
        quarter_over_quarter += [None]
        stock_income['收入环比增长率'] = quarter_over_quarter
        # yoy
        year_over_year = [] 
        for i in range(0, len(stock_income) - 4):
            prev_value = stock_income['营业总收入'].iloc[i + 4]
            current_value = stock_income['营业总收入'].iloc[i]
            growth = (current_value - prev_value) / prev_value * 100
            year_over_year.append(growth)
        year_over_year += [None, None, None, None]
        stock_income['收入同比增长率'] = year_over_year
        # Gross Profit Margin
        stock_income['毛利率'] = (stock_income['营业总收入'] - stock_income['营业总成本']) / stock_income['营业总收入'] * 100
        # Operating Profit Margin
        stock_income['营业利润率'] = stock_income['营业利润'] / stock_income['营业总收入'] * 100
        # Net Profit Margin
        stock_income['净利润率'] = stock_income['净利润'] / stock_income['营业总收入'] * 100
        stock_income = stock_income[(stock_income['报告日'] >= start_date_report_zh) & (stock_income['报告日'] <= end_date_zh)]
        # date
        stock_income['报告日'] = pd.to_datetime(stock_income['报告日'], format='%Y%m%d')
        stock_income['报告日'] = stock_income['报告日'].dt.strftime('%Y-%m-%d')
        stock_income = stock_income.rename(columns={'报告日': '日期'})
        
        balance_key = [
            '报告日',
            '流动资产合计',
            '非流动资产合计',
            '货币资金',
            '应收账款',
            '存货',
            '固定资产净值',
            '商誉',
            '流动负债合计',
            '非流动负债合计',
            '短期借款',
            '长期借款',
            '应付账款',
            '所有者权益',
            '未分配利润',
            '负债合计',
            '所有者权益(或股东权益)合计',
            '资产总计',
            '负债和所有者权益(或股东权益)总计'
        ]
        balance = ak.stock_financial_report_sina(stock=stock_code_zh, symbol="资产负债表")
        balance_key_copy = []
        for me in balance_key:
            if me in balance.columns:
                balance_key_copy.append(me)
        balance_key = balance_key_copy
        stock_balance_sheet = balance[balance_key]
        stock_balance_sheet['长期债务比率'] = stock_balance_sheet['长期借款'] / stock_balance_sheet['负债合计'] * 100
        stock_balance_sheet = stock_balance_sheet[(stock_balance_sheet['报告日'] >= start_date_report_zh) & (stock_balance_sheet['报告日'] <= end_date_zh)]
        stock_balance_sheet['报告日'] = pd.to_datetime(stock_balance_sheet['报告日'], format='%Y%m%d')
        stock_balance_sheet['报告日'] = stock_balance_sheet['报告日'].dt.strftime('%Y-%m-%d')
        stock_balance_sheet = stock_balance_sheet.rename(columns={'报告日': '日期'})
        
        cash_flow_key = [
            '报告日',
            '经营活动产生的现金流量净额',
            '投资活动产生的现金流量净额',
            '筹资活动产生的现金流量净额',
            '现金及现金等价物净增加额',
            '收回投资所收到的现金',
            '取得投资收益收到的现金',
            '购建固定资产、无形资产和其他长期资产所支付的现金',
            '吸收投资收到的现金',
            '取得借款收到的现金',
            '偿还债务支付的现金',
            '分配股利、利润或偿付利息所支付的现金'
        ]
        cash_flow = ak.stock_financial_report_sina(stock=stock_code_zh, symbol="现金流量表")
        cash_flow_key_copy = []
        for me in cash_flow_key:
            if me in cash_flow.columns:
                cash_flow_key_copy.append(me)
        cash_flow_key = cash_flow_key_copy
        stock_cash_flow = cash_flow[cash_flow_key]
        stock_cash_flow = stock_cash_flow[(stock_cash_flow['报告日'] >= start_date_report_zh) & (stock_cash_flow['报告日'] <= end_date_zh)]
        stock_cash_flow['报告日'] = pd.to_datetime(stock_cash_flow['报告日'], format='%Y%m%d')
        stock_cash_flow['报告日'] = stock_cash_flow['报告日'].dt.strftime('%Y-%m-%d')
        stock_cash_flow = stock_cash_flow.rename(columns={'报告日': '日期'})
        
        result = {
            "stock_info": stock_info,
            "stock_data": stock_data,
            "stock_income": stock_income,
            "stock_balance_sheet": stock_balance_sheet,
            "stock_cash_flow": stock_cash_flow,
            "csi300_stock_data": csi300_stock_data
        }
        return result



if __name__ == "__main__":
    dataer = Dataer()
    result = dataer.get_company_news_sina(stock_code='600519.SS', end_date='2024-10-25', company_name='贵州茅台')
    # result = dataer.get_company_info(stock_code='600519.SS')
    # result = dataer.get_company_announcement(stock_code='600519.SS', end_date='2024-10-19')
    # result = dataer.get_company_report(stock_code='600519.SS', date='2024-10-19')
    # result = dataer.get_company_news_sina(end_date='2024-10-19', stock_code='600519.SS')
    # dataer.get_finacncials_yf(stock_code='600519.SS', end_date='2024-10-28')
    # result = dataer.get_company_report_em(stock_code='600519.SS', date='2024-10-28')
    # result = dataer.get_finacncials_ak(stock_code='600519.SS', end_date='2024-10-27')
    # result = dataer.get_company_news_sina(stock_code='600519.SS', end_date='2024-8-27', company_name='贵州茅台')    
    
    # stock_list = open('csi50.txt', 'r').read().split('\n')
    # for stock_code in stock_list:
    #     try:
    #         print(stock_code)
    #         result = dataer.get_company_report_em(date='2024-10-27', stock_code=stock_code)
    #         print(result)
    #     except Exception as e:
    #         print(e)
            
    
    
    
    