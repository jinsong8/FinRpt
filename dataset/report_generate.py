import requests
import ast
import csv
import re
import os
from datetime import datetime
import requests
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import concurrent.futures
import threading
import sqlite3
from finrpt.module.FinRpt import FinRpt
from finrpt.utils.data_processing import (
    duplication_eliminate_hash,
    duplication_eliminate_bert, 
    short_eliminate,
    filter_news_by_date,
    limit_by_amount)
from finrpt.module.OpenAI import OpenAIModel
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
from sentence_transformers import SentenceTransformer
import torch
import json
import pickle
import pdb
import pandas as pd
import akshare as ak
import time

def get_news_embeddings():
    
    def company_newsemb_table_init(db):
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS newsemb (
            news_url TEXT PRIMARY KEY,
            read_num TEXT,
            reply_num TEXT,
            news_title TEXT,
            news_author TEXT,
            news_time TEXT,
            stock_code TEXT,
            news_content TEXT,
            news_summary TEXT,
            dec_response TEXT,
            news_decision TEXT,
            news_embedding BLOB
        )
        ''')
        conn.commit()
        conn.close()
        
    def company_newsemb_table_insert(db, data):
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute('''
            INSERT INTO newsemb (
                news_url, read_num, reply_num, news_title, news_author, news_time, stock_code, news_content, news_summary, dec_response, news_decision, news_embedding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
            data.get('news_url'),
            data.get('read_num'),
            data.get('reply_num'),
            data.get('news_title'),
            data.get('news_author'),
            data.get('news_time'),
            data.get('stock_code'),
            data.get('news_content'),
            data.get('news_summary'),
            data.get('dec_response'),
            data.get('news_decision'),
            pickle.dumps(data.get('news_embedding'))
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if conn:
                conn.close()
            print(e)
            return False
    
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    
    company_newsemb_table_init(database_name)
    
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    cursor.execute(""" SELECT * FROM news WHERE news_decision="是" """)
    rows = cursor.fetchall()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SentenceTransformer('BAAI/bge-large-zh-v1.5').to(device)
    if torch.cuda.device_count() > 1:
        print(f'Using {torch.cuda.device_count()} GPUs')
        model = torch.nn.DataParallel(model)
    
    batch_size = 3000
    for i in tqdm(range(0, len(rows), batch_size)):
        batch = rows[i:i+batch_size]
        texts = [row[-3] for row in batch]
        embeddings = model.module.encode(texts, normalize_embeddings=True)
        for j, embedding in enumerate(embeddings):
            data = {
                'news_url': batch[j][0],
                'read_num': batch[j][1],
                'reply_num': batch[j][2],
                'news_title': batch[j][3],
                'news_author': batch[j][4],
                'news_time': batch[j][5],
                'stock_code': batch[j][6],
                'news_content': batch[j][7],
                'news_summary': batch[j][8],
                'dec_response': batch[j][9],
                'news_decision': batch[j][10],
                'news_embedding': embedding
            }
            company_newsemb_table_insert(database_name, data)
      
def get_dup_news_async():
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500
    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03']
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'      
    
    def company_newsdup_table_init(db):
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS newsdup (
            id TEXT PRIMARY KEY,
            news BLOB
        )
        ''')
        conn.commit()
        conn.close()
        
    def company_newsdup_table_insert(db, data):
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute('''
            INSERT INTO newsdup (
                id, news
            ) VALUES (?, ?)
            ''', (
            data.get('id'),
            data.get('news')
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if conn:
                conn.close()
            print(e)
            return False
        
    def _get_dup_news_row(stock_code, date, lock, progress_bar):
        id = f"{stock_code}_{date}"
        
        try:
            with lock:
                conn = sqlite3.connect(database_name)
                c = conn.cursor()
                c.execute('''SELECT * FROM newsdup WHERE id = ? ''', (id,))  
                result = c.fetchone()
            if result:
                print(f"{stock_code} {date} already exists")
                progress_bar.update(1)
        except Exception as e:
            print(e)
            return False
        
        start_date = datetime.strptime(date, "%Y-%m-%d") - relativedelta(months=1)
        start_date = start_date.strftime("%Y-%m-%d")
            
        try:
            conn = sqlite3.connect(database_name)
            c = conn.cursor()
            c.execute('''SELECT * FROM newsemb WHERE stock_code = ? AND news_time BETWEEN ? and ? ''', (stock_code, start_date, date))  
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
        except Exception as e:
            print(e)
            return False
        
        news = resutls_list
        news, short_ratio = short_eliminate(news)
        news, bert_ratio = duplication_eliminate_bert(news)
        news, hash_raito = duplication_eliminate_hash(news)
        news, date_ratio = filter_news_by_date(news)
        news_url = [x['news_url'] for x in news]
        with lock:
            conn = sqlite3.connect(database_name)
            c = conn.cursor()
            c.execute('''INSERT INTO newsdup (id, news) VALUES (?, ?)''', (id, pickle.dumps(news_url)))
            conn.commit()
            conn.close()
            progress_bar.update(1)
    
    company_newsdup_table_init(database_name)
    
    re_param = []
    for stock_code in stock_list:
        for date in date_list:
            re_param.append((stock_code, date))
    
    lock = threading.Lock()
    
    progress_bar = tqdm(total=len(re_param))
    
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_get_dup_news_row, stock_code, date, lock, progress_bar) 
            for stock_code, date in re_param
        ]
        concurrent.futures.wait(futures)
        
def get_duped_news_async():
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500
    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03']
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'      
    
    def company_newsduped_table_init(db):
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS newsduped (
            news_url TEXT PRIMARY KEY,
            read_num TEXT,
            reply_num TEXT,
            news_title TEXT,
            news_author TEXT,
            news_time TEXT,
            stock_code TEXT,
            news_content TEXT,
            news_summary TEXT,
            dec_response TEXT,
            news_decision TEXT
        )
        ''')
        conn.commit()
        conn.close()
        
    def company_newstag_table_init(db):
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS newstag (
            id TEXT PRIMARY KEY,
            tag TEXT
        )
        ''')
        conn.commit()
        conn.close()
        
    def company_newsduped_table_insert(db, data):
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute('''
            INSERT INTO newsduped (
                news_url, read_num, reply_num, news_title, news_author, news_time, stock_code, news_content, news_summary, dec_response, news_decision
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
            data.get('news_url'),
            data.get('read_num'),
            data.get('reply_num'),
            data.get('news_title'),
            data.get('news_author'),
            data.get('news_time'),
            data.get('stock_code'),
            data.get('news_content'),
            data.get('news_summary'),
            data.get('dec_response'),
            data.get('news_decision'),
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if conn:
                conn.close()
            print(e)
            return False
        
    def company_newstag_table_insert(db, data):
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute('''
            INSERT INTO newstag (
                id, tag
            ) VALUES (?, ?)
            ''', (
            data.get('id'),
            data.get('tag')
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if conn:
                conn.close()
            print(e)
            return False
        
    def _get_duped_news_row(stock_code, date, lock, progress_bar):
        id = f"{stock_code}_{date}"
        try:
            conn = sqlite3.connect(database_name)
            c = conn.cursor()
            c.execute('''SELECT * FROM newstag WHERE id = ? ''', (id,))  
            result = c.fetchone()
            if result:
                print(f"{stock_code} {date} already exists")
                progress_bar.update(1)
        except Exception as e:
            print(e)
            return False
        
        start_date = datetime.strptime(date, "%Y-%m-%d") - relativedelta(months=1)
        start_date = start_date.strftime("%Y-%m-%d")
            
        try:
            conn = sqlite3.connect(database_name)
            c = conn.cursor()
            c.execute('''SELECT * FROM newsemb WHERE stock_code = ? AND news_time BETWEEN ? and ? ''', (stock_code, start_date, date))  
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
        except Exception as e:
            print(e)
            return False
        
        news = resutls_list
        news, short_ratio = short_eliminate(news)
        news, bert_ratio = duplication_eliminate_bert(news)
        news, hash_raito = duplication_eliminate_hash(news)
        news, date_ratio = filter_news_by_date(news)
        for new in news:
            with lock:
                company_newsduped_table_insert(database_name, new)
        
        company_newstag_table_insert(database_name, {"id":id,"tag":"duplicated"})
        progress_bar.update(1)
    
    company_newsduped_table_init(database_name)
    company_newstag_table_init(database_name)
    
    re_param = []
    for stock_code in stock_list:
        for date in date_list:
            re_param.append((stock_code, date))
    
    lock = threading.Lock()
    
    progress_bar = tqdm(total=len(re_param))
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_get_duped_news_row, stock_code, date, lock, progress_bar) 
            for stock_code, date in re_param
        ]
        concurrent.futures.wait(futures)
        
def get_financials_async():
    
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500

    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03']
    
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    
    def _financials_table_init(db):
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS financials (
            id TEXT PRIMARY KEY,
            stock_info BLOB,
            stock_data BLOB,
            stock_income BLOB,
            stock_balance_sheet BLOB,
            stock_cash_flow BLOB,
            csi300_stock_data BLOB
        )
        ''')
        conn.commit()
        conn.close()
        
    def _financials_table_insert(db, data):
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute('''
            INSERT INTO financials (
                id, stock_info, stock_data, stock_income, stock_balance_sheet, stock_cash_flow, csi300_stock_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
            data.get('id'),
            pickle.dumps(data.get('stock_info')),
            pickle.dumps(data.get('stock_data')),
            pickle.dumps(data.get('stock_income')),
            pickle.dumps(data.get('stock_balance_sheet')),
            pickle.dumps(data.get('stock_cash_flow')),
            pickle.dumps(data.get('csi300_stock_data'))
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if conn:
                conn.close()
            print(e)
            return False
    
    def _request_get(url, headers = None, verify = None, params = None):
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        max_retry = 3
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
    
    def stock_financial_report_sina(
        stock: str = "sh600600", symbol: str = "资产负债表"
    ) -> pd.DataFrame:
        """
        新浪财经-财务报表-三大报表
        https://vip.stock.finance.sina.com.cn/corp/go.php/vFD_FinanceSummary/stockid/600600/displaytype/4.phtml?source=fzb&qq-pf-to=pcqq.group
        :param stock: 股票代码
        :type stock: str
        :param symbol: choice of {"资产负债表", "利润表", "现金流量表"}
        :type symbol: str
        :return: 新浪财经-财务报表-三大报表
        :rtype: pandas.DataFrame
        """
        symbol_map = {"资产负债表": "fzb", "利润表": "lrb", "现金流量表": "llb"}
        url = f"https://quotes.sina.cn/cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022?paperCode={stock}&source={symbol_map[symbol]}&type=0&page=1&num=100"
        r = _request_get(url)
        data_json = r.json()
        df_columns = [
            item["date_value"] for item in data_json["result"]["data"]["report_date"]
        ]
        big_df = pd.DataFrame()
        temp_df = pd.DataFrame()
        for date_str in df_columns:
            temp_df = pd.DataFrame(
                data_json["result"]["data"]["report_list"][date_str]["data"]
            )
            temp_df = temp_df[["item_title", "item_value"]]
            temp_df["item_value"] = pd.to_numeric(temp_df["item_value"], errors="coerce")
            temp_tail_df = pd.DataFrame.from_dict(
                data={
                    "数据源": data_json["result"]["data"]["report_list"][date_str][
                        "data_source"
                    ],
                    "是否审计": data_json["result"]["data"]["report_list"][date_str][
                        "is_audit"
                    ],
                    "公告日期": data_json["result"]["data"]["report_list"][date_str][
                        "publish_date"
                    ],
                    "币种": data_json["result"]["data"]["report_list"][date_str][
                        "rCurrency"
                    ],
                    "类型": data_json["result"]["data"]["report_list"][date_str]["rType"],
                    "更新日期": datetime.fromtimestamp(
                        data_json["result"]["data"]["report_list"][date_str]["update_time"]
                    ).isoformat(),
                },
                orient="index",
            )
            temp_tail_df.reset_index(inplace=True)
            temp_tail_df.columns = ["item_title", "item_value"]
            temp_df = pd.concat(objs=[temp_df, temp_tail_df], ignore_index=True)
            temp_df.columns = ["项目", date_str]
            big_df = pd.concat(objs=[big_df, temp_df[date_str]], axis=1, ignore_index=True)

        big_df = big_df.T
        big_df.columns = temp_df["项目"]
        big_df = pd.concat(objs=[pd.DataFrame({"报告日": df_columns}), big_df], axis=1)
        big_df = big_df.loc[:, ~big_df.columns.duplicated(keep="first")]
        return big_df
    
    def _get_finacncials_ak(stock_code, end_date, lock, progress_bar):
        
        financials_id = stock_code + "_" + end_date
        
        try:
            with lock:
                conn = sqlite3.connect(database_name)
                c = conn.cursor()
                c.execute('SELECT * FROM financials WHERE id=?', (financials_id,))
                result = c.fetchone()
                if result is not None:
                    print(f'{financials_id} already exists')
                    progress_bar.update(1)
                    return
        except Exception as e:
            print(e)
            
        pd.options.mode.chained_assignment = None
        start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=1)
        start_date = start_date.strftime("%Y-%m-%d")
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
        
        stock_data = ak.stock_zh_a_hist_tx(symbol=stock_code_zh, start_date=start_date_zh, end_date=end_date_zh)
        stock_data = stock_data.rename(columns={'open': 'Open', 'close': 'Close', 'high': 'High', 'low': 'Low', 'volume': 'Volume'})
        
        csi300_stock_data = ak.stock_zh_a_hist_tx(symbol="sh000300", start_date=start_date_zh, end_date=end_date_zh)
        
        income_key = [
            "报告日",
            "营业总收入",
            "营业总成本",
            "营业利润",
            # "净利润",
            "基本每股收益",
            "稀释每股收益",
            "投资收益",
        ]
        income_rename_dict = {
            "营业收入": "营业总收入",
            "营业支出": "营业总成本"
        }
        income = stock_financial_report_sina(stock=stock_code_zh, symbol="利润表")
        income = income.rename(columns={k: v for k, v in income_rename_dict.items() if k in income.columns and v not in income.columns})
        stock_income = income[income_key]
        
        # qoq
        quarter_over_quarter = [] 
        for i in range(0, len(stock_income) - 1):
            prev_value = stock_income['营业总收入'].iloc[i + 1]
            current_value = stock_income['营业总收入'].iloc[i]
            if prev_value == 0:
                stock_income['营业总收入'].iloc[i + 1] = stock_income['营业总收入'].iloc[i]
                growth = None
            else:
                growth = (current_value - prev_value) / prev_value * 100
            quarter_over_quarter.append(growth)
        quarter_over_quarter += [None]
        stock_income['收入环比增长率'] = quarter_over_quarter
        # yoy
        year_over_year = [] 
        for i in range(0, len(stock_income) - 4):
            prev_value = stock_income['营业总收入'].iloc[i + 4]
            current_value = stock_income['营业总收入'].iloc[i]
            if prev_value == 0:
                growth = None
            else:
                growth = (current_value - prev_value) / prev_value * 100
            year_over_year.append(growth)
        year_over_year += [None, None, None, None]
        stock_income['收入同比增长率'] = year_over_year
        # Gross Profit Margin
        stock_income['毛利率'] = (stock_income['营业总收入'] - stock_income['营业总成本']) / stock_income['营业总收入'] * 100
        # Operating Profit Margin
        stock_income['营业利润率'] = stock_income['营业利润'] / stock_income['营业总收入'] * 100
        # Net Profit Margin
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
        balance = stock_financial_report_sina(stock=stock_code_zh, symbol="资产负债表")
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
        cash_flow = stock_financial_report_sina(stock=stock_code_zh, symbol="现金流量表")
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
            "id": f"{stock_code}_{end_date}",
            "stock_info": pickle.dumps(stock_info),
            "stock_data": pickle.dumps(stock_data),
            "stock_income": pickle.dumps(stock_income),
            "stock_balance_sheet": pickle.dumps(stock_balance_sheet),
            "stock_cash_flow": pickle.dumps(stock_cash_flow),
            "csi300_stock_data": pickle.dumps(csi300_stock_data)
        }
        with lock:
            _financials_table_insert(database_name, result)
            print(f"{stock_code} {end_date}")
            progress_bar.update(1)
        return result
    
    def _get_finacncials_ak_new(stock_code, end_date, lock):
        
        financials_id = stock_code + "_" + end_date
        
        try:
            with lock:
                conn = sqlite3.connect(database_name)
                c = conn.cursor()
                c.execute('SELECT * FROM financials WHERE id=?', (financials_id,))
                result = c.fetchone()
                if result is not None:
                    print(f'{financials_id} already exists')
                    return
        except Exception as e:
            print(e)
            
        pd.options.mode.chained_assignment = None
        start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=1)
        start_date = start_date.strftime("%Y-%m-%d")
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
        
        stock_data = ak.stock_zh_a_hist_tx(symbol=stock_code_zh, start_date=start_date_zh, end_date=end_date_zh)
        stock_data = stock_data.rename(columns={'open': 'Open', 'close': 'Close', 'high': 'High', 'low': 'Low', 'volume': 'Volume'})
        
        csi300_stock_data = ak.stock_zh_a_hist_tx(symbol="sh000300", start_date=start_date_zh, end_date=end_date_zh)
        
        ref_id = stock_code + "_" + "2024-11-05"
        try:
            with lock:
                conn = sqlite3.connect(database_name)
                c = conn.cursor()
                c.execute('SELECT * FROM financials WHERE id=?', (ref_id,))
                result_raw = c.fetchone()
                result = {
                    "id": financials_id,
                    "stock_info": result_raw[1],
                    "stock_data": stock_data,
                    "stock_income": result_raw[3],
                    "stock_balance_sheet": result_raw[4],
                    "stock_cash_flow": result_raw[5],
                    "csi300_stock_data": csi300_stock_data
                }
        except Exception as e:
            print(e)
        with lock:
            _financials_table_insert(database_name, result)
            print(f"{stock_code} {end_date}")
        return result
    
    _financials_table_init(database_name)
    
    re_param = []
    
    for stock_code in stock_list:
        for date in date_list:
            re_param.append((stock_code, date))
    
    lock = threading.Lock()
    
    progress_bar = tqdm(total=len(re_param))
    
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_get_finacncials_ak, stock_code, date, lock, progress_bar) 
            for stock_code, date in re_param
        ]
        concurrent.futures.wait(futures)

    
def get_trend_async():
    
    stock_list_csi_300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi_500 = open('csi500.txt', 'r').read().split('\n')
    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03']
    stock_list = stock_list_csi_300 + stock_list_csi_500
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    
    def _trend_table_init(db):
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS trend (
            id TEXT PRIMARY KEY,
            csi300_change REAL,
            change REAL,
            rel_change REAL
        )
        ''')
        conn.commit()
        conn.close()
        
    def _trend_table_insert(db, data):
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute('''
            INSERT INTO trend (
                id, csi300_change, change, rel_change
            ) VALUES (?, ?, ?, ?)
            ''', (
            data.get('id'),
            data.get('csi300_change'),
            data.get('change'),
            data.get('rel_change')
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            if conn:
                conn.close()
            print(e)
            return False
    
    def _get_trend_row(stock_code, date, end_date, before_date, csi300_change, lock, progress_bar):
        
        id = f"{stock_code}_{date}"
        try:
            with lock:
                conn = sqlite3.connect(database_name)
                c = conn.cursor()
                c.execute('''
                SELECT * FROM trend WHERE id = ?
                ''', (id,))
                row = c.fetchone()
                conn.close()
            if row is not None:
                print(f"{stock_code} {date} already exists")
                progress_bar.update(1)
                return row
        except Exception as e:
            if conn:
                conn.close()
            print(e)
        
        if stock_code[-2:] == 'SS':
            stock_code_zh = 'sh' + stock_code[:-3]
        if stock_code[-2:] == 'SZ':
            stock_code_zh = 'sz' + stock_code[:-3]
        target = ak.stock_zh_a_hist_tx(symbol=stock_code_zh, start_date=date.replace('-', ''), end_date=end_date.replace('-', '')).iloc[-1]['close']
        cur = ak.stock_zh_a_hist_tx(symbol=stock_code_zh, start_date=before_date.replace('-', ''), end_date=date.replace('-', '')).iloc[-1]['close']
        change = (target - cur) / cur * 100
        with lock:
            _trend_table_insert(database_name, {'id': id, 'csi300_change': float(csi300_change), 'change': float(change), 'rel_change': float(change - csi300_change)})
            print(f"{stock_code} {date} inserted successfully")
            progress_bar.update(1)
    
    def copy_from_pkl():
        results = pickle.load(open('csi800_change.pkl', 'rb'))
        for k, v in results.items():
            for _k, _v in v.items():
                _trend_table_insert(database_name, {'id': f"{k}_{_k}", 'csi300_change': float(_v['csi300_change']), 'change': float(_v['change']), 'rel_change': float(_v['rel_change'])})
    
    _trend_table_init(database_name)

    tqdm_bar = tqdm(total=len(date_list) * len(stock_list))
    
    for date in date_list:
        end_date = datetime.strptime(date, "%Y-%m-%d") + relativedelta(weeks=3) 
        end_date = end_date.strftime("%Y-%m-%d")
        before_date = datetime.strptime(date, "%Y-%m-%d") - relativedelta(weeks=1)
        before_date = before_date.strftime("%Y-%m-%d")
        csi300_target  = ak.stock_zh_a_hist_tx(symbol="sh000300", start_date=date.replace('-', ''), end_date=end_date.replace('-', '')).iloc[-1]['close']
        csi300_cur = ak.stock_zh_a_hist_tx(symbol="sh000300", start_date=before_date.replace('-', ''), end_date=date.replace('-', '')).iloc[-1]['close']
        csi300_change = (csi300_target - csi300_cur) / csi300_cur * 100
            
        lock = threading.Lock()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(_get_trend_row, stock_code, date, end_date, before_date, csi300_change, lock, tqdm_bar) 
                for stock_code in stock_list_csi_300 + stock_list_csi_500
            ]
            concurrent.futures.wait(futures)

def run_report_em_download_async(model_name):
    stock_list_csi_300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi_500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi_300 + stock_list_csi_500
    
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    
    def _request_get(url, headers = None, verify = None, params = None):
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        max_retry = 3
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
    
    def get_company_report_em(date, stock_code, lock, progress_bar):
        
        def _get_report_content(art_code):
            url = f"https://np-cnotice-stock.eastmoney.com/api/content/ann?art_code={art_code}&client_source=web"
            response = _request_get(url)
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
                page_response = _request_get(page_url)
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
        
        def post_process_report(content):
            start = '第三节  管理层讨论与分析\n'
            if content.find(start) == -1:
                start = '管理层讨论与分析\n'
            end = '第四节  公司治理\n'
            if content.find(end) == -1:
                end = '公司治理\n'
            result = content[content.find(start):content.find(end)].strip()
            if len(result) < 10:
                result = content[:100000]
            return result
        
        id = stock_code + '_2024_Q2'
        
        try:
            with lock:
                conn = sqlite3.connect(database_name)
                c = conn.cursor()
                c.execute('SELECT * FROM company_report WHERE report_id = ?', (id,))
                query_result = c.fetchone()
                c.close()
            if query_result:
                content = dict(zip(COMPANY_REPORT_TABLE_COLUMNS, query_result))
                print(f"{stock_code} {date} already exists")
                progress_bar.update(1)
                return content
        except Exception as e:
            query_result = None
        
        model = OpenAIModel(model_name=model_name)
        
        report_start_date = datetime.strptime(date, "%Y-%m-%d") - relativedelta(years=1)
        report_start_date = report_start_date.strftime("%Y-%m-%d")
        report_date = date
        
        break_flag = False
        content = ""
        for page_index in range(1, 10):
            url = f'https://np-anotice-stock.eastmoney.com/api/security/ann?ann_type=A&stock_list={stock_code[:6]}&page_index={page_index}&page_size=100'
            response  = _request_get(url)
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
                        with lock:
                            conn = sqlite3.connect(database_name)
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
            report_agent_summary = model.simple_prompt('内容：\n' + core_content + '\n\n\n\n为了便于后续的大模型阅读理解，请将以上内容重新排版，舍弃表格等不重要信息。')[0]
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
        with lock:
            company_report_table_insert(db=database_name, data=result)
            print(f'{the_report_id}, {title}')
            progress_bar.update(1)
        return result 
    
    lock = threading.Lock()
    
    progress_bar = tqdm(total=len(stock_list))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(get_company_report_em, '2024-11-25', stock_code, lock, progress_bar) 
            for stock_code in stock_list
        ]
        concurrent.futures.wait(futures)
    return 

def report_generate_async(model_name):
    
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500

    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03']
    
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    
    def report_generate_row(stock_code, date, lock, progress_bar):
        finrpt = FinRpt(model_name=model_name)
        finrpt.run(date=date, stock_code=stock_code)
        print(f'{stock_code} {date}')
        progress_bar.update(1)
    
    re_param = []
    for stock_code in stock_list:
        for date in date_list:
            re_param.append((stock_code, date))
    
    lock = threading.Lock()
    
    progeress_bar = tqdm(total=len(re_param))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(report_generate_row, stock_code, date, lock, progeress_bar) 
            for stock_code, date in re_param[3000:4000]
        ]
        concurrent.futures.wait(futures)
    return 




if __name__ == "__main__":
    report_generate_async("gpt-4o")