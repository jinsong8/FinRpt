import json
import pdb
from finrpt.source.Dataer import Dataer


def per_stock(gen_reports):
    stock2num = {}
    for report in gen_reports:
        if report['stock_code'] not in stock2num:
            stock2num[report['stock_code']] = 1
        else:
            stock2num[report['stock_code']] += 1
    count = 0
    sum = 0
    for k, v in stock2num.items():
        count += 1
        sum += v
    return sum / count

def per_date(gen_reports):
    date2num = {}
    for report in gen_reports:
        if report['date'] not in date2num:
            date2num[report['date']] = 1
        else:
            date2num[report['date']] += 1
    count = 0
    sum = 0
    for k, v in date2num.items():
        count += 1
        sum += v
    return sum / count

def csi300_count(gen_reports):
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    count  = 0
    for report in gen_reports:
        if report['stock_code'] in stock_list_csi300:
            count += 1
    return count

def csi500_count(gen_reports):
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    count = 0
    for report in gen_reports:
        if report['stock_code'] in stock_list_csi500:
            count += 1
    return count

def buy_ratio(gen_reports):
    count = 0
    for report in gen_reports:
        trend  = 1 if json.loads(report['trend_write_response'])['评级'] == '买入' else 0
        if trend == 1:
            count += 1
    return count / len(gen_reports)

def month_count(gen_reports):
    _9 = 0
    _10 = 0
    _11 = 0
    for report in gen_reports:
        if report['date'].startswith('2024-09'):
            _9 += 1
        elif report['date'].startswith('2024-10'):
            _10 += 1
        elif report['date'].startswith('2024-11'):
            _11 += 1
    return [_9, _10, _11]

def stock_category_count(gen_reports):
    stock_category_count = {}
    dataer = Dataer()
    for report in gen_reports:
        try:
            company_info = dataer.get_company_info(stock_code=report['stock_code'])
            category = company_info['stock_category']
            if category not in stock_category_count:
                stock_category_count[category] = 1
            else:
                stock_category_count[category] += 1
        except Exception as e:
            print(e)
    return stock_category_count

def industry_count(gen_reports):
    dataer = Dataer()
    stock_industry_count = {}
    for report in gen_reports:
        try:
            company_info = dataer.get_company_info(stock_code=report['stock_code'])
            industry = company_info['industry_category'].split('-')[0]
            if industry not in stock_industry_count:
                stock_industry_count[industry] = 1
            else:
                stock_industry_count[industry] += 1
        except Exception as e:
            print(e)
    return stock_industry_count

def employees_number_count(gen_reports):
    _0_500 = 0
    _500_1000 = 0
    _1000_10000 = 0
    _10000_100000 = 0
    _100000 = 0
    dataer = Dataer()
    for report in gen_reports:
        try:
            company_info = dataer.get_company_info(stock_code=report['stock_code'])
            employees_number = int(company_info['employees_number'])
            if employees_number < 500:
                _0_500 += 1
            elif employees_number >= 500 and employees_number < 1000:
                _500_1000 += 1
            elif employees_number >= 1000 and employees_number < 10000:
                _1000_10000 += 1
            elif employees_number >= 10000 and employees_number < 100000:
                _10000_100000 += 1
            else:
                _100000 += 1
        except Exception as e:
            print(e)
    return {'0-500': _0_500, '500-1000': _500_1000, '1000-10000': _1000_10000, '10000-100000': _10000_100000, '> 100000': _100000}
    

def registered_capital_count(gen_reports):
    _0 = 0
    _1000000000_10000000000 = 0
    _10000000000_100000000000 = 0
    _100000000000 = 0
    dataer = Dataer()
    for report in gen_reports:
        try:
            company_info = dataer.get_company_info(stock_code=report['stock_code'])
            registered_capital = float(company_info['registered_capital'])
            if registered_capital * 10000 < 1000000000:
                _0 += 1
            elif registered_capital * 10000 >= 1000000000 and registered_capital * 10000 < 10000000000:
                _1000000000_10000000000 += 1
            elif registered_capital * 10000 >= 10000000000 and registered_capital * 10000 < 100000000000:
                _10000000000_100000000000 += 1
            else:
                _100000000000 += 1
            
        except Exception as e:
            print(e)
    return {
        '0-1000000000': _0,
        '1000000000-10000000000': _1000000000_10000000000,
        '10000000000-100000000000': _10000000000_100000000000,
        '> 100000000000': _100000000000
    }



if __name__ == "__main__":
    file_path = 'filter_filter_alignment_gpt-4o.jsonl'
    gen_reports = open(file_path, 'r').read().split('\n')
    gen_reports = [json.loads(x) for x in gen_reports]
    total_number_of_reports = len(gen_reports)
    print('total number of reports: {}'.format(total_number_of_reports))
    number_of_reports_per_stock = per_stock(gen_reports)
    print('number of reports per stock: {}'.format(number_of_reports_per_stock))
    number_of_reports_per_date = per_date(gen_reports)
    print('number of reports per date: {}'.format(number_of_reports_per_date))
    number_of_reports_in_csi300 = csi300_count(gen_reports)
    print('number of reports in csi300: {}'.format(number_of_reports_in_csi300))
    number_of_reports_in_csi500 = csi500_count(gen_reports)
    print('number of reports in csi500: {}'.format(number_of_reports_in_csi500))
    buy_ratio = buy_ratio(gen_reports)
    print('buy ratio: {}'.format(buy_ratio))
    number_of_reports_in_09, number_of_reports_in_10, number_of_reports_in_11 = month_count(gen_reports)
    print('number of reports in 09: {}, number of reports in 10: {}, number of reports in 11: {}'.format(number_of_reports_in_09, number_of_reports_in_10, number_of_reports_in_11))
    number_of_reports_per_stock_category = stock_category_count(gen_reports)
    print('number of reports per stock category: {}'.format(number_of_reports_per_stock_category))
    number_of_reports_per_industry = industry_count(gen_reports)
    print('number of reports per industry: {}'.format(number_of_reports_per_industry))
    employees_number = employees_number_count(gen_reports)
    print('employees number: {}'.format(employees_number))
    registered_capital = registered_capital_count(gen_reports)
    print('registered capital: {}'.format(registered_capital))