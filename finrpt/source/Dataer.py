import requests
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
from lxml import etree
import re
import pandas as pd
from tqdm import tqdm
import yfinance as yf
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
    def __init__(self, max_retry=1, database_name = 'cache.db'):
        self.max_retry = max_retry
        self.database_name = database_name
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
        
        year = datetime.strptime(date, '%Y-%m-%d').year
        month = datetime.strptime(date, '%Y-%m-%d').month
        request_list = []
        if month > 6:
            request_type = '半年度报告全文'
            report_id = stock_code + '_' + str(year) + '_Q2'
            report_date = str(year) + '-06-30'
            report_year = str(year)
        else:
            request_type = '年度报告全文'
            report_id = stock_code + '_' + str(year - 1) + '_Q4'
            report_date = str(year - 1) + '-12-31' 
            report_year = str(year - 1)
        
        try:
            conn = sqlite3.connect(self.database_name)
            c = conn.cursor()
            c.execute('SELECT * FROM company_report WHERE report_id = ?', (report_id,))
            result = c.fetchone()
            c.close()
        except Exception as e:
            result = None
            print(e)
            
        if result:
            return dict(zip(COMPANY_REPORT_TABLE_COLUMNS, result))
        
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
                    if date < report_date:
                        break_flag = True
                        break
                    the_report_type = report['columns'][0]['column_name']
                    if the_report_type != request_type:
                        continue
                    title = report['title']
                    if "英文" in title or "摘要" in title:
                        continue
                    if report_year not in title:
                        continue
                    art_code = report['art_code']
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
        
        result = {
            'report_id': report_id,
            'date': date,
            'content': content,
            'stock_code': stock_code,
            'title': title
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

    def get_company_news_sina(self, stock_code, end_date, start_date = None):
        
        stock_map = {
            "SS": "sh",
            "SZ": "sz"
        }

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
                    print(e)
            except Exception as e:
                print(e)
                one_news = None
            return one_news

        if not start_date:
            start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=3)
            start_date = start_date.strftime("%Y-%m-%d")
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

                try:
                    title = element.text.strip() 
                    link = element.get('href')  
                except Exception as e:
                    print(e)
                    continue

                query_result = content = company_news_table_query_by_url(db=self.database_name, news_url=link)
                if content is None:
                    content = _get_news_from_url(link)
                if not content:
                    continue
                try:
                    one_news = {
                            "read_num": 0,
                            "reply_num": 0,
                            "news_url": link,
                            "news_title": title,
                            "news_author": "sina",
                            "news_time": ann_date[id],
                            "news_content": content[7],
                            "stock_code": stock_code
                    }
                except Exception as e:
                    print(e)
                    continue
                result.append(one_news)
                if not query_result:
                    company_news_table_insert(db=self.database_name, data=one_news)
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
    
    def get_financials_ak(self, stock_code, end_date, start_date=None):
        if not start_date:
            start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=3)
            start_date = start_date.strftime("%Y-%m-%d")
        pass


if __name__ == "__main__":
    dataer = Dataer()
    # result = dataer.get_company_info(stock_code='600519.SS')
    # result = dataer.get_company_announcement(stock_code='600519.SS', end_date='2024-10-19')
    # result = dataer.get_company_report(stock_code='600519.SS', date='2024-10-19')
    # result = dataer.get_company_news_sina(end_date='2024-10-19', stock_code='600519.SS')
    # dataer.get_finacncials_yf(stock_code='600519.SS', end_date='2024-10-28')
    result = dataer.get_company_report_em(stock_code='600519.SS', date='2024-10-28')
    
    
    
    
    