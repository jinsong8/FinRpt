"""
Usage:
python3 show_result.py --mode [single|pairwise-baseline|pairwise-all]
"""
import argparse
import pandas as pd
import glob
import json
import os
from tabulate import tabulate
import pdb


def load_results(answer_dir: str):
    filenames = glob.glob(os.path.join(answer_dir, "*_scores.json"))
    filenames.sort()
    model_results = {}

    for filename in filenames:
        model_name = os.path.basename(filename)[:-12]
        with open(filename) as fin:
            model_results[model_name] = json.load(fin)

    return model_results


def display_result(answer_dir):
    results = load_results(answer_dir)
    df = {
        'name': [],
        'success': [],
        'trend': [],
        'rouge-l': [],
        'bert': [],
        'number': []
    }
    
    for k, v in results.items():
        
        df['name'].append(k)
        df['trend'].append(v['trend'])
        df['success'].append(v['success'])
        df['rouge-l'].append(v['all']['rouge-l'] * 100)
        df['bert'].append(v['all']['bert'] * 100)
        df['number'].append(v['all']['number'])

    df = pd.DataFrame(df).sort_values('trend')
    df.set_index('name', inplace=True)
    print(tabulate(df, headers='keys', tablefmt='pretty'))
    df_titile = "name,success,trend,bert,rouge-l,number"
    df_str = "\n".join([f"{str(row[0])},{str(row[1]['success'])},{str(row[1]['trend'])},{str(row[1]['bert'])},{str(row[1]['rouge-l'])},{str(row[1]['number'])}"  for row in df.iterrows()])
    df_str = df_titile + "\n" + df_str
    open(f"{answer_dir}/show.csv", "w").write(df_str)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--results_dir", type=str, default="results/model_results")
    args = argparser.parse_args()
    results_dir = args.results_dir
    display_result(results_dir)
