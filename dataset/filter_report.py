import json
import sqlite3
import pdb
import pickle


def filter_by_trend_and_threshold(file_path, threshold=0):
    gen_reports = open(file_path, 'r').read().split('\n')    
    gen_reports = [json.loads(x) for x in gen_reports]
    
    rel_reports = open('gpt-4o.jsonl', 'r').read().split('\n')
    rel_reports = [json.loads(x) for x in rel_reports]
    rel_reports = {x["id"]: x for x in rel_reports}
    
    database_name = '/data/jinsong/FinRpt_v1/finrpt/source/cache.db'
    filter_gen_reports = []
    for i in range(len(gen_reports)):
        id = gen_reports[i]['id']
        trend_write_response = json.loads(gen_reports[i]['trend_write_response'])
        if '评级' not in trend_write_response:
            filter_gen_reports.append(rel_reports[id])
            continue
        if trend_write_response['评级'] != '买入':
            trend_write_response['评级'] = '卖出'
        try:
            conn = sqlite3.connect(database_name)
            c = conn.cursor()
            c.execute(f''' SELECT * FROM trend WHERE id='{id}' ''')
            query_results = c.fetchone()
        except Exception as e:
            print(f'Error occurred while executing the SQL query: {e}')
            
        if abs(query_results[3]) < threshold:
            continue
        gen_result = 1 if json.loads(gen_reports[i]["trend_write_response"])["评级"] == "买入" else 0
        real_result = 1 if query_results[3] > 0 else 0
        if gen_result != real_result:
            continue
        gen_reports[i]['trend_write_response'] = json.dumps(trend_write_response, ensure_ascii=False)
        filter_gen_reports.append(gen_reports[i])
        
    filter_gen_reports_str = [json.dumps(x, ensure_ascii=False) for x in filter_gen_reports]
    with open("filter_" + file_path, 'w') as f:
        f.write("\n".join(filter_gen_reports_str))
    return filter_gen_reports

def filter_by_news_report_financials(file_path):
    gen_reports = open(file_path, 'r').read().split('\n')
    gen_reports = [json.loads(x) for x in gen_reports]
    filter_gen_reports = []
    for i in range(len(gen_reports)):
        path = './reports/' + gen_reports[i]["id"] + '_gpt-4o/' + 'result.pkl'
        raw_report = pickle.load(open(path, 'rb'))
        
        if len(raw_report['report']['summary']) < 300:
            continue
        if len(raw_report['news']) < 2:
            continue
        if len(raw_report['financials']) == 0:
            continue
        filter_gen_reports.append(gen_reports[i])
    filter_gen_reports_str = [json.dumps(x, ensure_ascii=False) for x in filter_gen_reports]
    with open("filter_" + file_path, 'w') as f:
        f.write("\n".join(filter_gen_reports_str))
        

def filter_by_train(file_path):
    gen_reports = open(file_path, 'r').read().split('\n')
    gen_reports = [json.loads(x) for x in gen_reports]
    key_matter = ['finance_write_response', 'trend_write_response', 'news_write_response', 'report_write_response']
    for gen_report in gen_reports:
        for k in key_matter:
            json.loads(gen_report[k])
    filter_gen_reports = []
    date = '2024-11-05'
    for gen_report in gen_reports:
        if gen_report['date'] == date:
            continue
        filter_gen_reports.append(gen_report)
    filter_gen_reports_str = [json.dumps(x, ensure_ascii=False) for x in filter_gen_reports]    
    with open("train_" + file_path, 'w') as f:
        f.write("\n".join(filter_gen_reports_str))
        
def filter_by_test(file_path):
    gen_reports = open(file_path, 'r').read().split('\n')
    gen_reports = [json.loads(x) for x in gen_reports]
    key_matter = ['finance_write_response', 'trend_write_response', 'news_write_response', 'report_write_response']
    for gen_report in gen_reports:
        for k in key_matter:
            json.loads(gen_report[k])
    filter_gen_reports = []
    date = '2024-11-05'
    for gen_report in gen_reports:
        if gen_report['date'] != date:
            continue
        filter_gen_reports.append(gen_report)
    filter_gen_reports_str = [json.dumps(x, ensure_ascii=False) for x in filter_gen_reports]    
    with open("test_" + file_path, 'w') as f:
        f.write("\n".join(filter_gen_reports_str))
    


if __name__ == '__main__':
    # filter_by_trend_and_threshold('alignment_gpt-4o.jsonl', threshold=0.3)
    # filter_by_news_report_financials('filter_alignment_gpt-4o.jsonl')
    # filter_by_train('filter_filter_alignment_gpt-4o.jsonl')
    filter_by_test('filter_filter_alignment_gpt-4o.jsonl')