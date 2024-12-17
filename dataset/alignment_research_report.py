import pickle
import pdb
from tqdm import tqdm
import concurrent.futures
import threading
import json
from finrpt.module.OpenAI import OpenAIModel


def get_report_by_id(id):
    data = pickle.load(open(f'./data/csi300_csi500_report_9-11_id.pkl', 'rb'))
    return data[id]

def alignment_research_report(file_path):
    stock_list_csi300 = open('csi300.txt', 'r').read().split('\n')
    stock_list_csi500 = open('csi500.txt', 'r').read().split('\n')
    stock_list = stock_list_csi300 + stock_list_csi500
    data = pickle.load(open(f'./data/csi300_csi500_report_9-11_id.pkl', 'rb'))
    
    gen_reports = open(file_path, 'r').read().split('\n')
    gen_reports = [json.loads(x) for x in gen_reports]
    gen_reports = {x["id"]: x for x in gen_reports}

    date_list = ['2024-11-05', '2024-10-29', '2024-10-22', '2024-10-15', '2024-10-08', '2024-10-01', '2024-09-24', '2024-09-17', '2024-09-10', '2024-09-03']
    
    def alignment_research_report_row(stock_code, date, lock, progress_bar):
        id = f'{stock_code}_{date}'
        
        if id not in data:
            return
        
        research_reports = data[id]
        if len(research_reports) == 0:
            return
        
        research_reports = research_reports[:7]
        
        research_reports = ["\n".join(x['report_paragraphs']) for x in research_reports]
        
        research_reports = "\n\n\n".join(research_reports)
        
        matter_key = ['finance_write_response', 'news_write_response', 'report_write_response', 'risk_response', 'trend_write_response']
        
        with lock:
            gen_report = gen_reports[id]
        
        gen_report_re = {key: gen_report[key] for key in matter_key}
        
        gen_report_re = json.dumps(gen_report_re, ensure_ascii=False)
        
        alignment_prompt = f"""{research_reports}\n\n\n请参考以上股票研究报告，对下面提供的报告进行适当的修改和纠正。请注意以下几点：
1. 保持原有的JSON格式和结构完整。
2. 提高报告内容的准确性和逻辑性。
3. 确保所有数据和分析结果的一致性。
4. 修正任何语法错误或拼写错误。
5. 确保行业术语的使用正确。
6. 不要修改股票的评级。
只能适当修改和纠正段落内容，不能修改报告原有的股票评级。直接返回修改后的原有json格式的报告，无需解释理由。下面是需要修改的JSON格式报告：\n\n\n{gen_report_re}"""
        
        model = OpenAIModel(model_name='gpt-4o')
        response, response_json = model.json_prompt(alignment_prompt)
        
        
        with lock:
            for key in matter_key:
                if type(response_json[key]) != str:
                    response_json[key] = json.dumps(response_json[key], ensure_ascii=False)
                gen_reports[id][key] = response_json[key]
            
        print(f'{stock_code} {date}')
        print(len(research_reports))
        progress_bar.update(1)
    
    re_param = []
    for stock_code in stock_list:
        for date in date_list:
            re_param.append((stock_code, date))
    
    lock = threading.Lock()
    
    progeress_bar = tqdm(total=len(re_param))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(alignment_research_report_row, stock_code, date, lock, progeress_bar) 
            for stock_code, date in re_param
        ]
        concurrent.futures.wait(futures)
        
    with open('alignment_' + file_path, 'w') as f:
        for item in gen_reports.values():
            f.write(json.dumps(item, ensure_ascii=False)+'\n')
    return 

if __name__ == "__main__":
    alignment_research_report('gpt-4o.jsonl')
            
