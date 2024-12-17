import json
import pdb
import pickle

def del_blank(data):
    new_data = []
    for d in data:
        if len(d['report_paragraphs']) > 0:
            new_data.append(d)
    return new_data

def filter_by_date(data, start_date, end_date):
    filtered_data = [d for d in data if (start_date <= d['publishDate'][:10] and d['publishDate'][:10] <= end_date)]
    return filtered_data

def get_lastEmRatingName(data):
    lastEmRatingName = []
    for d in data:
        lastEmRatingName.append(d['lastEmRatingName'])
    lastEmRatingName = list(set(lastEmRatingName))
    return lastEmRatingName

def filter_by_lastEmRatingName(data, lastEmRatingName):
    # ['', '中性', '增持', '买入', '持有']
    filtered_data = [d for d in data if d['lastEmRatingName'] in lastEmRatingName]
    return filtered_data

def filter_by_csi300(data):
    csi300 = open('csi300.txt', 'r').read().split("\n")
    csi300 = [s[:6] for s in csi300]
    filtered_data = [d for d in data if d['stockCode'] in csi300]
    return filtered_data

def filter_by_csi500(data):
    csi500 = open('csi500.txt', 'r').read().split("\n")
    csi500 = [s[:6] for s in csi500]
    filtered_data = [d for d in data if d['stockCode'] in csi500]
    return filtered_data

def filter_by_csi300_and_csi500(data):
    csi300 = open('csi300.txt', 'r').read().split("\n")
    csi300 = [s[:6] for s in csi300]
    csi500 = open('csi500.txt', 'r').read().split("\n")
    csi500 = [s[:6] for s in csi500]
    filtered_data = [d for d in data if d['stockCode'] in csi300 or d['stockCode'] in csi500]
    return filtered_data

def filter_by_stock_code(data, stock_code):
    filtered_data = [d for d in data if d['stockCode'] == stock_code]
    return filtered_data

def check_by_date_stock_code(data):
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500
    stock_list = [s[:6] for s in stock_list]
    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03']
    data_list_start = ['2024-10-30', '2024-10-23', '2024-10-16', '2024-10-09', '2024-10-02', '2024-09-25', '2024-09-18', '2024-09-11', '2024-09-04', '2024-08-28']
    
    results = {}
    
    for stock_code in stock_list:
        for i in range(len(date_list)):
            data_sub = filter_by_stock_code(data, stock_code)
            data_sub = filter_by_date(data_sub, data_list_start[i], date_list[i])
            results[f"{stock_code}_{date_list[i]}"] = data_sub
    
    for date in date_list:
        sum_len = 0
        for stock_code in stock_list:
            sum_len += len(results[stock_code][date])
        print('{}: {}'.format(date, sum_len / len(stock_list)))
        
    with open('./data/csi300_csi500_report_9-11_checked.jsonl', 'w', encoding='utf-8') as f:
        for d in results:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
            
def check_by_id(data):
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500
    stock_code_list = stock_list
    stock_list = [s[:6] for s in stock_list]
    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03']
    data_list_start = ['2024-10-30', '2024-10-23', '2024-10-16', '2024-10-09', '2024-10-02', '2024-09-25', '2024-09-18', '2024-09-11', '2024-09-04', '2024-08-28']
    results = {}
    
    for i in range(len(stock_list)):
        for j in range(len(date_list)):
            data_sub = filter_by_stock_code(data, stock_list[i])
            data_sub = filter_by_date(data_sub, data_list_start[j], date_list[j])
            results[f"{stock_code_list[i]}_{date_list[j]}"] = data_sub
    pickle.dump(results, open('./data/csi300_csi500_report_9-11_id.pkl', 'wb'))
    

if __name__ == '__main__':
    data = []
    # with open('./data/eastmoney_single_reporter_all.jsonl', encoding='utf-8') as f:
    #     for line in f:
    #         data.append(json.loads(line))
    # print('raw len: ', len(data))
    # data = del_blank(data)
    # print('after del blank len: ', len(data))
    # data = filter_by_date(data, '2024-08-28', '2024-11-05')
    # print('after filter by date len: ', len(data))
    # data = filter_by_csi300_and_csi500(data)
    # print('after filter by csi300_and_csi500 len: ', len(data))
    # data = sorted(data, key=lambda x: x['publishDate'])
    # with open('./data/csi300_csi500_report_9-11.jsonl', 'w', encoding='utf-8') as f:
    #     for d in data:
    #         f.write(json.dumps(d, ensure_ascii=False) + '\n')
    
    with open('./data/csi300_csi500_report_9-11.jsonl', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    print('sum of report: ', len(data))
            
    lastEmRatingNames = get_lastEmRatingName(data)
    print('lastEmRatingNames: ', lastEmRatingNames)
    for lastEmRatingName in lastEmRatingNames:
        data_sub = filter_by_lastEmRatingName(data, [lastEmRatingName])
        print('after filter by lastEmRatingName {} len: '.format(lastEmRatingName), len(data_sub))
        
    # check_by_date_stock_code(data)
    # check_by_id(data)
    
    
            