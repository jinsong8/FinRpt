import argparse
from tqdm import tqdm
import os
from finrpt.module.FinRpt import FinRpt
from finrpt.module.FinRpt_single import FinRptSingle
from finrpt.module.FinRpt_analyst_finance import FinRpt_analyst_finance
from finrpt.module.FinRpt_analyst_news import FinRpt_analyst_news
from finrpt.module.FinRpt_no_write import FinRpt_no_write
import pickle
import json
import concurrent.futures
import threading
import pdb

LOCAL_MODELS = ['llama3.1:8b-instruct-fp16', 'qwen2.5:14b-instruct-fp16', 'qwen2.5:7b-instruct-fp16', 'llama3.1:70b', 'llama-xy:13b', 'mixtral:8x7b', 'finma:7b', 'finrpt:7b', 'llama2:13b', 'qwen2.5:72b', 'maxkb/baichuan2:13b-chat', 'deepseek-v2:16b', 'glm4:9b-chat-fp16', 'gemma2:9b-instruct-fp16', 'gemma2:27b-instruct-fp16', 'finetune-llama', 'finetune-qwen', 'finetune-glm']
REMOTE_MODELS = ['gpt-4o', 'gpt-4o-mini']

class_dict = {
    'normal': FinRpt,
    'analyst_finance': FinRpt_analyst_finance,
    'analyst_news': FinRpt_analyst_news,
    'no_write': FinRpt_no_write
}

def run_local(model_name, exp_type, ablation):
    stock_ids = open('results/standard.txt', 'r').read().split('\n')
    date = '2024-11-05'
    
    if exp_type == 'single':
        run_dir = f'results/single_{model_name}'
    else:
        if ablation != 'normal':
            run_dir = f'results/{model_name}_{ablation}'
        else:
            run_dir = f'results/{model_name}'
    
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)

    for stock_id in tqdm(stock_ids, desc='Stocks'):
        stock_code, date = stock_id.split('_')
        if exp_type == 'single':
            stock_report_path = os.path.join(f'./results/single_{model_name}', 'single_' + stock_code + "_" + date + "_" + model_name)
        else:
            if ablation != 'normal':
                stock_report_path = os.path.join(f'./results/{model_name}_{ablation}', stock_code + "_" + date + "_" + model_name + "_" + ablation)
            else:
                stock_report_path = os.path.join(f'./results/{model_name}', stock_code + "_" + date + "_" + model_name)
        if os.path.exists(stock_report_path):
            files = os.listdir(stock_report_path)
            if len(files) >= 2:
                print("skip: " + stock_code + "_" + date + "_" + model_name)
                continue
        try:
            if exp_type == 'single':
                finrpt = FinRptSingle(model_name=model_name, save_path=run_dir)
            else:
                finrpt = class_dict[ablation](model_name=model_name, save_path=run_dir)
            finrpt.run(date=date, stock_code=stock_code)
            print(f'{stock_code} {date}')
        except Exception as e:
            print(e)
            
    root_files = os.listdir(run_dir)
    jsonl = []
    matter_key = ['id', 'stock_code', 'date', 'news_anlyzer_prompt', 'news_anlyzer_response', 'income_prompt', 'income_response', 'balance_prompt', 'balance_response', 'cash_prompt', 'cash_response', 'finance_write_prompt', 'finance_write_response', 'news_write_prompt', 'news_write_response', 'report_write_prompt', 'report_write_response', 'risk_prompt', 'risk_response', 'trend_write_prompt', 'trend_write_response']
    
    for root_file in root_files:
        files = os.listdir(os.path.join(run_dir, root_file))
        if len(files) < 2:
            continue
        json_raw = pickle.load(open(os.path.join(run_dir, root_file, 'result.pkl'), 'rb'))
        json_fillter = {key: json_raw[key] for key in matter_key if key in json_raw}
        jsonl.append(json.dumps(json_fillter, ensure_ascii=False))
    
    if exp_type == 'single':
        with open(f"results/single_{model_name}.jsonl", "w", encoding="utf-8") as f:
            f.write("\n".join(jsonl))
    else:
        if ablation != 'normal':
            with open(f"results/{model_name}_{ablation}.jsonl", "w", encoding="utf-8") as f:
                f.write("\n".join(jsonl))
        else:
            with open(f"results/{model_name}.jsonl", "w", encoding="utf-8") as f:
                f.write("\n".join(jsonl))

        
def run_remote(model_name, exp_type, ablation):
    stock_ids = open('results/standard.txt', 'r').read().split('\n')
    
    if exp_type == 'single':
        run_dir = f'results/single_{model_name}'
    else:
        if ablation != 'normal':
            run_dir = f'results/{model_name}_{ablation}/'
        else:
            run_dir = f'results/{model_name}/'
    
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)
        
    def _run_remote_run(stock_id, exp_type, progress_bar):
        stock_code, date = stock_id.split('_')
        if exp_type == 'single':
            stock_report_path = os.path.join(f'./results/single_{model_name}', 'single_' + stock_code + "_" + date + "_" + model_name)
        else:
            if ablation != 'normal':
                stock_report_path = os.path.join(f'./results/{model_name}_{ablation}', stock_code + "_" + date + "_" + model_name + "_" + ablation)
            else:
                stock_report_path = os.path.join(f'./results/{model_name}', stock_code + "_" + date + "_" + model_name)
        if os.path.exists(stock_report_path):
            files = os.listdir(stock_report_path)
            if len(files) >= 2:
                print("skip: " + stock_code + "_" + date + "_" + model_name)
                progress_bar.update(1)
                return
        try:
            if exp_type == 'single':
                finrpt = FinRptSingle(model_name=model_name, save_path=run_dir)
            else:
                finrpt = class_dict[ablation](model_name=model_name, save_path=run_dir)
            finrpt.run(date=date, stock_code=stock_code)
            print(f'{stock_code} {date}')
            progress_bar.update(1)
        except Exception as e:
            print(e)
        

    progress_bar = tqdm(total=len(stock_ids))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_run_remote_run, stock_id, exp_type, progress_bar) 
            for stock_id in stock_ids
        ]
        concurrent.futures.wait(futures)
            
    root_files = os.listdir(run_dir)
    jsonl = []
    matter_key = ['id', 'stock_code', 'date', 'news_anlyzer_prompt', 'news_anlyzer_response', 'income_prompt', 'income_response', 'balance_prompt', 'balance_response', 'cash_prompt', 'cash_response', 'finance_write_prompt', 'finance_write_response', 'news_write_prompt', 'news_write_response', 'report_write_prompt', 'report_write_response', 'risk_prompt', 'risk_response', 'trend_write_prompt', 'trend_write_response']
    
    for root_file in root_files:
        files = os.listdir(os.path.join(run_dir, root_file))
        if len(files) < 2:
            continue
        json_raw = pickle.load(open(os.path.join(run_dir, root_file, 'result.pkl'), 'rb'))
        json_fillter = {key: json_raw[key] for key in matter_key if key in json_raw}
        jsonl.append(json.dumps(json_fillter, ensure_ascii=False))
        
    if exp_type == 'single':
        with open(f"results/single_{model_name}.jsonl", "w", encoding="utf-8") as f:
            f.write("\n".join(jsonl))
    else:
        if ablation != 'normal':
            with open(f"results/{model_name}_{ablation}.jsonl", "w", encoding="utf-8") as f:
                f.write("\n".join(jsonl))
        else:
            with open(f"results/{model_name}.jsonl", "w", encoding="utf-8") as f:
                f.write("\n".join(jsonl))
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default='llama3.1:8b-instruct-fp16')
    parser.add_argument('--exp_type', type=str, default='agent')
    parser.add_argument('--ablation', type=str, default='normal')
    args = parser.parse_args()
    model_names = args.model_name.split(',')
    for model_name in model_names:
        if model_name in LOCAL_MODELS:
            run_local(model_name, args.exp_type, args.ablation)
        elif model_name in REMOTE_MODELS:
            run_remote(model_name, args.exp_type, args.ablation)