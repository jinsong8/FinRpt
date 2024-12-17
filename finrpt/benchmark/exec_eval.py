import argparse
from tqdm import tqdm
import os
import pdb
import jieba
import glob
from finrpt.benchmark.eval_utils import *
from concurrent.futures import ThreadPoolExecutor


os.environ['JIEBA_CACHE_DIR'] = os.path.dirname(os.path.abspath(__file__))
jieba.initialize()


def run_app(args):
    model = args.model_name

    dataset = 'finrpt'

    responses = []
    for _, record in tqdm(dataset.iterrows()):
        prompt = record['instruction']
        model_response = model.generate(prompt)
        responses.append(model_response)
    result_path = os.path.join(args.save_result_dir, f"{args.model_name}_application_result.json")
    if args.save_result_dir:
        dataset["model_response"] = responses
        os.makedirs(args.save_result_dir, exist_ok=True)
        dataset.to_json(result_path, orient='records', force_ascii=False)


def get_score(_path, model_name):
    standard_path = f'{_path}/standard.jsonl'
    file_path = f'{_path}/{model_name}.jsonl'
    standards = read_jsonl(standard_path)
    standards = json_list_to_dict(standards)
    results = read_jsonl(file_path)
    results = json_list_to_dict(results)
    
    sub_task_references = {}
    sub_task_candidates = {}
    sub_tasks = ['finance_write_response', 'news_write_response', 'report_write_response', 'trend_write_response', 'risk_response', 'all']
    
    for id, record in results.items():
        if id not in standards:
            continue
        ref_record = standards[id]
        for sub_task in sub_tasks:
            if sub_task not in sub_task_references:
                sub_task_references[sub_task] = []
                sub_task_candidates[sub_task] = []
            if sub_task != 'all':
                sub_task_references[sub_task].append(" ".join(jieba.lcut(ref_record[sub_task])))
                sub_task_candidates[sub_task].append(" ".join(jieba.lcut(record[sub_task])))
            else:
                rec_text = '\n'.join([ref_record['finance_write_response'],ref_record['news_write_response'],ref_record['report_write_response'],ref_record['trend_write_response'], ref_record['risk_response']])
                ref_text = '\n'.join([record['finance_write_response'],record['news_write_response'],record['report_write_response'],record['trend_write_response'],ref_record['risk_response']])
                sub_task_references[sub_task].append(" ".join(jieba.lcut(ref_text)))
                sub_task_candidates[sub_task].append(" ".join(jieba.lcut(rec_text)))
    
    scores = {}
    trend = trend_score(sub_task_references['trend_write_response'], sub_task_candidates['trend_write_response'])
    scores['trend'] = trend
    for sub_task in tqdm(sub_tasks):
        print(f"Sub-task: {sub_task}")
        references = sub_task_references[sub_task]
        candidates = sub_task_candidates[sub_task]
        _, _, rouge_l = rouge_score(references, candidates)
        bert = bert_score(references, candidates)
        number = number_score(references, candidates)
        scores[sub_task] = {
            "rouge-l": rouge_l,
            "bert": bert,
            'number': number
        }
    
    print(scores)
    with open(f'{_path}/{model_name}_scores.json', 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False)
        
def get_score_all(_path, model_name):
    standard_path = f'{_path}/standard.jsonl'
    file_path = f'{_path}/{model_name}.jsonl'
    standards = read_jsonl(standard_path)
    standards = json_list_to_dict(standards)
    results = read_jsonl(file_path)
    results = json_list_to_dict(results)
    
    sub_task_references = {}
    sub_task_candidates = {}
    sub_tasks = ['finance_write_response', 'news_write_response', 'report_write_response', 'trend_write_response', 'risk_response', 'all']
    
    blank_can = {'finance_write_response':' ', 'news_write_response':' ', 'report_write_response':' ', 'trend_write_response':' ', 'risk_response':' '}
    
    for id, ref_record in standards.items():
        if id not in results:
            can_record = blank_can
        else:
            can_record = results[id]
            
        for sub_task in sub_tasks[:-1]:
            if sub_task not in can_record:
                can_record[sub_task] = ' '
                
        for sub_task in sub_tasks:
            if sub_task not in sub_task_references:
                sub_task_references[sub_task] = []
                sub_task_candidates[sub_task] = []
            if sub_task != 'all':
                sub_task_references[sub_task].append(" ".join(jieba.lcut(ref_record[sub_task])))
                sub_task_candidates[sub_task].append(" ".join(jieba.lcut(can_record[sub_task])))
            else:
                ref_text = '\n'.join([ref_record['finance_write_response'],ref_record['news_write_response'],ref_record['report_write_response'],ref_record['trend_write_response'], ref_record['risk_response']])
                can_text = '\n'.join([can_record['finance_write_response'],can_record['news_write_response'],can_record['report_write_response'],can_record['trend_write_response'],can_record['risk_response']])
                sub_task_references[sub_task].append(" ".join(jieba.lcut(ref_text)))
                sub_task_candidates[sub_task].append(" ".join(jieba.lcut(can_text)))
    
    scores = {}
    trend = trend_score(sub_task_references['trend_write_response'], sub_task_candidates['trend_write_response'])
    scores['trend'] = trend
    success = success_score(sub_task_references['all'], sub_task_candidates['all'])
    scores['success'] = success
    for sub_task in tqdm(sub_tasks):
        print(f"Sub-task: {sub_task}")
        references = sub_task_references[sub_task]
        candidates = sub_task_candidates[sub_task]
        _, _, rouge_l = rouge_score(references, candidates)
        bert = bert_score(references, candidates)
        number = number_score(references, candidates)
        scores[sub_task] = {
            "rouge-l": rouge_l,
            "bert": bert,
            'number': number
        }
    
    print(scores)
    with open(f'{_path}/{model_name}_scores.json', 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False)
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default='')
    parser.add_argument('--results_dir', type=str, default='results/model_results')
    args = parser.parse_args()
    if args.model_name == '':
        file_paths = glob.glob(f"{args.results_dir}/*.jsonl")
        model_names = [os.path.splitext(os.path.basename(f))[0] for f in file_paths]
    else:
        model_names = args.model_name.split(',')
    def get_score_all_wrapper(model_name):
            get_score_all(args.results_dir, model_name)
    
    with ThreadPoolExecutor(100) as executor:
            for match in tqdm(
                executor.map(get_score_all_wrapper, model_names), total=len(model_names)
            ):
                pass