import sqlite3
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import pickle
import yfinance as yf
import akshare as ak
import pdb
import concurrent.futures
import threading
import sqlite3
import os
import json
from sklearn.metrics import accuracy_score

def check_news():
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500
    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03', '2024-08-27', '2024-08-20', '2024-08-13', '2024-08-06', '2024-07-30', '2024-07-23', '2024-07-16', '2024-07-09', '2024-07-02', '2024-06-25', '2024-06-18']
    date2num = {}
    for stock_code in stock_list:
        for date in date_list:
            end_date = date
            start_date = datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=1)
            start_date = start_date.strftime("%Y-%m-%d")
            try:
                conn = sqlite3.connect(database_name)
                cursor = conn.cursor()
                query = f"SELECT * FROM news WHERE stock_code='{stock_code}' AND news_time BETWEEN '{start_date}' AND '{end_date}';"
                cursor.execute(query)
                result = cursor.fetchall()
                print(f'{stock_code}, {end_date}: {len(result)}')
                if end_date not in date2num:
                    date2num[end_date] = [len(result)]
                else:
                    date2num[end_date].append(len(result))
            except Exception as e:
                print(f'Error occurred while executing the SQL query: {e}')
                
    date2num_list = [(date, sum(num_list)/len(num_list)) for date, num_list in date2num.items()]
    print(date2num_list)
        
    with open('date2num.pkl', 'wb') as f:
        pickle.dump(date2num, f)
            
def check_trend():
    results = pickle.load(open('csi800_change.pkl', 'rb'))
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500
    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03']
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    standard_ids = []
    for stock_code in stock_list:
        for date in date_list:
            standard_id = f'{stock_code}_{date}'
            standard_ids.append(standard_id)
    try:
        conn = sqlite3.connect(database_name)
        c = conn.cursor()
        c.execute(''' SELECT * FROM trend ''')
        query_results = c.fetchall()
    except Exception as e:
        print(f'Error occurred while executing the SQL query: {e}')
    query_ids = [query_result[0] for query_result in query_results]
    diff_ids = list(set(standard_ids) - set(query_ids))
    diff_ids = sorted(diff_ids)
    print(diff_ids)

def check_financials():
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03']
    
    try:
        conn = sqlite3.connect(database_name)
        c = conn.cursor()
        c.execute(''' SELECT * FROM financials ''')
        query_results = c.fetchall()
    except Exception as e:
        print(f'Error occurred while executing the SQL query: {e}')
    
    query_ids = [query_result[0] for query_result in query_results]
    standard_ids = []
    for stock_code in stock_list:
        for date in date_list:
            standard_id = f'{stock_code}_{date}'
            standard_ids.append(standard_id)
    diff_ids = list(set(standard_ids) - set(query_ids))
    diff_ids = sorted(diff_ids)
            
    print(diff_ids)
   
def check_company_report():
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    
    query_stocks = []
    
    for stock_code in stock_list:
        try:
            conn = sqlite3.connect(database_name)
            c = conn.cursor()
            c.execute(f''' SELECT * FROM company_report WHERE report_id='{stock_code}_2024_Q2' ''')
            query_results = c.fetchall()
            if query_results:
                query_stocks.append(stock_code)
        except Exception as e:
            print(f'Error occurred while executing the SQL query: {e}')
    
    diff_ids = list(set(stock_list) - set(query_stocks))
    print(diff_ids)

def check_report():
    dir = 'reports'
    root_files = os.listdir(dir)
    jsonl = []
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    matter_key = ['id', 'stock_code', 'date', 'news_anlyzer_prompt', 'news_anlyzer_response', 'income_prompt', 'income_response', 'balance_prompt', 'balance_response', 'cash_prompt', 'cash_response', 'finance_write_prompt', 'finance_write_response', 'news_write_prompt', 'news_write_response', 'report_write_prompt', 'report_write_response', 'risk_prompt', 'risk_response', 'trend_write_prompt', 'trend_write_response']
    query_list = []
    standard_list = []
    
    for root_file in root_files:
        files = os.listdir(os.path.join(dir, root_file))
        if len(files) < 3:
            continue
        root_file_list = root_file.split('_')
        stock_code = root_file_list[0]
        date = root_file_list[1]
        model_name = root_file_list[2]
        json_raw = pickle.load(open(os.path.join(dir, root_file, 'result.pkl'), 'rb'))
        json_fillter = {key: json_raw[key] for key in matter_key}
        id=json_raw["id"]
        jsonl.append(json.dumps(json_fillter, ensure_ascii=False))
        query_list.append(1 if json.loads(json_raw["trend_write_response"])["评级"] == "买入" else 0)
        try:
            conn = sqlite3.connect(database_name)
            c = conn.cursor()
            c.execute(f''' SELECT * FROM trend WHERE id='{id}' ''')
            query_results = c.fetchone()
        except Exception as e:
            print(f'Error occurred while executing the SQL query: {e}')
        standard_list.append(1 if query_results[3] > 0 else 0)
        
    print(query_list)
    print(sum(query_list) / len(query_list))
    print(standard_list)
    print(sum(standard_list) / len(standard_list))
    acc = accuracy_score(standard_list, query_list)
    print(acc)
    
    with open(f"{model_name}.jsonl", "w", encoding="utf-8") as f:
        f.write("\n".join(jsonl))
        
        
def check_report_from_jsonl(file_path):
    dir = 'reports'
    root_files = os.listdir(dir)
    jsonl = []
    database_name = '/data/name/FinRpt_v1/finrpt/source/cache.db'
    matter_key = ['id', 'stock_code', 'date', 'news_anlyzer_prompt', 'news_anlyzer_response', 'income_prompt', 'income_response', 'balance_prompt', 'balance_response', 'cash_prompt', 'cash_response', 'finance_write_prompt', 'finance_write_response', 'news_write_prompt', 'news_write_response', 'report_write_prompt', 'report_write_response', 'risk_prompt', 'risk_response', 'trend_write_prompt', 'trend_write_response']
    query_list = []
    standard_list = []
    
    gen_reports = open(file_path, 'r').read().split('\n')
    gen_reports = [json.loads(x) for x in gen_reports]
    gen_reports = {x["id"]: x for x in gen_reports}
    
    for id, gen_report in gen_reports.items():
        json_raw = gen_report
        json_fillter = {key: json_raw[key] for key in matter_key}
        id = json_raw["id"]
        jsonl.append(json.dumps(json_fillter, ensure_ascii=False))
        query_list.append(1 if json.loads(json_raw["trend_write_response"])["评级"] == "买入" else 0)
        try:
            conn = sqlite3.connect(database_name)
            c = conn.cursor()
            c.execute(f''' SELECT * FROM trend WHERE id='{id}' ''')
            query_results = c.fetchone()
        except Exception as e:
            print(f'Error occurred while executing the SQL query: {e}')
        standard_list.append(1 if query_results[3] > 0 else 0)
        
    print(sum(query_list) / len(query_list))
    print(sum(standard_list) / len(standard_list))
    acc = accuracy_score(standard_list, query_list)
    print(acc)
    
    

if __name__ == '__main__':
    check_report_from_jsonl('filter_filter_alignment_gpt-4o.jsonl')