from finrpt.source.Dataer import Dataer
from tqdm import tqdm


if __name__ == '__main__':
    with open('./CSI300.list', encoding='utf-8') as f:
        stock_list = [line.strip() for line in f.readlines()]
    dataer = Dataer()
    for stock_code in tqdm(stock_list):
        dataer.get_company_report(date='2021-01-01', stock_code=stock_code)
        

    