import json
import re
import pdb
from rouge import Rouge
from sklearn.metrics import accuracy_score
from sacrebleu.metrics import BLEU
from bert_score import score
from finrpt.utils.data_processing import robust_load_json

def read_jsonl(file_path):
    """Read a JSON Lines (JSONL) file and returns the list of objects it contains."""
    data_list = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = json.loads(line)
            data_list.append(data)
    return data_list

def json_list_to_dict(json_list):
    """Convert a list of JSON objects to a dictionary where each object is indexed by its ID."""
    dict_by_id = {}
    for obj in json_list:
        id_value = obj['id']
        dict_by_id[id_value] = obj
    return dict_by_id

def rouge_score(reference, candidate):
    rouge_calculator = Rouge()
    # Rouge-1 [r, p, f]
    rouge_1 = rouge_calculator.get_scores(candidate, reference, avg=True)['rouge-1']['f']

    # Rouge-2
    rouge_2 = rouge_calculator.get_scores(candidate, reference, avg=True)['rouge-2']['f']

    # Rouge-L
    rouge_l = rouge_calculator.get_scores(candidate, reference, avg=True)['rouge-l']['f']
    
    print('Rouge-L: ', rouge_l * 100)

    return rouge_1, rouge_2, rouge_l

def bert_score(reference, candidate):
    P, R, F1 = score(candidate, reference, model_type="bert-base-chinese", lang="zh", verbose=True)
    print('Bert Score: %s' % F1.mean().item())
    return F1.mean().item()

def number_score(reference, candidate):
    ref_numbers_len = [len(re.findall(r'\d+\.?\d*', ref)) for ref in reference]
    can_numbers_len = [len(re.findall(r'\d+\.?\d*', can)) for can in candidate]
    scores = []
    for ref_len, can_len in zip(ref_numbers_len, can_numbers_len):
        if can_len > ref_len or ref_len == 0:
            scores.append(1)
        else:
            scores.append(can_len / ref_len)
    score = sum(scores) / len(scores) * 100
    return score

def success_score(reference, candidate):
    ref_success = [1 if len(ref) > 17 else 0 for ref in reference]
    can_success = [1 if len(can) > 17 else 0 for can in candidate]
    accuracy = accuracy_score(ref_success, can_success)
    return accuracy * 100

def trend_score(reference, candidate):
    ref_len = len(reference)
    new_reference = []
    new_candidate = []
    for ref, can in zip(reference, candidate):
        if len(can) <= 1:
            continue
        try:
            robust_load_json(ref)[" 评级 "]
            robust_load_json(can)[" 评级 "]
        except Exception:
            continue
        new_reference.append(ref)
        new_candidate.append(can)
    reference = new_reference
    candidate = new_candidate
    ref_trends = [1 if robust_load_json(ref)[" 评级 "] == ' 买入 ' else 0 for ref in reference]
    can_trends = [1 if robust_load_json(can)[" 评级 "] == ' 买入 ' else 0 for can in candidate]
    for i in range(0, ref_len - len(new_reference)):
        ref_trends.append(0)
        can_trends.append(1)
    accuracy = accuracy_score(ref_trends, can_trends)
    return accuracy * 100
    



