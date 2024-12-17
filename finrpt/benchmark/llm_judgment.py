import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import dataclasses
import os
import glob
import time
import pdb
from functools import reduce
from finrpt.module.OpenAI import OpenAIModel
from finrpt.source.Dataer import Dataer
from finrpt.utils.data_processing import convert_df_to_text


import numpy as np
from tqdm import tqdm


@dataclasses.dataclass
class MatchSingle:
    question_id: dict
    model: str
    answer: dict
    judge_model: str


@dataclasses.dataclass
class MatchPair:
    question_id: dict
    model_1: str
    model_2: str
    answer_1: dict
    answer_2: dict
    judge_model: str
    

def load_model_answers(answer_dir: str):
    """Load model answers.

    The return value is a python dict of type:
    Dict[model_name: str -> Dict[question_id: int -> answer: dict]]
    """
    filenames = glob.glob(os.path.join(answer_dir, "*.jsonl"))
    filenames.sort()
    model_answers = {}

    for filename in filenames:
        model_name = os.path.basename(filename)[:-6]
        answer = {}
        with open(filename) as fin:
            for line in fin:
                line = json.loads(line)
                answer[line["id"]] = line
        model_answers[model_name] = answer

    return model_answers


def load_questions(question_dir: str):
    filenames = glob.glob(os.path.join(question_dir, "*.jsonl"))
    filenames.sort()
    questions = {}
    for filename in filenames:
        model_name = os.path.basename(filename)[:-6]
        question = []
        with open(filename) as fin:
            for line in fin:
                line = json.loads(line)
                question.append(line['id'])
        questions[model_name] = question
    questions_set = reduce(set.intersection, (set(lst) for lst in questions.values()))
    return list(questions_set)


def get_model_list(answer_dir):
    file_paths = glob.glob(f"{answer_dir}/*.jsonl")
    file_names = [os.path.splitext(os.path.basename(f))[0] for f in file_paths]
    return file_names

def run_judge_pair(question_id, answer_a, answer_b, judge_model):
    metrics = ["数据准确性、财务分析的深度", "新闻分析的相关性和覆盖度", "对公司管理与发展、市场趋势和行业状况的理解", "投资建议是否基于全面和理性的分析", "是否全面地分析了投资该股票的潜在风险", "整体连贯性、可读性和逻辑性"]
    model = judge_model
    
    prompt_template = """请担任公正的裁判，评估由两个AI助手生成的股票研究报告的质量。每份报告都是基于一个给定的股票代码和分析日期创建的。您的任务是选择哪个助手更有效地提供了一份满足用户要求的报告。考虑因素包括：{metric}。开始您的评估，通过比较这两份报告并提供简明的解释您的决定。避免任何立场偏见，确保不会因报告呈现的顺序而影响您的判断。不要让报告的长度影响您的决定。客观评估，在提供理由之后，按照以下格式确定更好的报告：如果助手A的报告更优，使用“[[A]]”；如果助手B的报告更优，使用“[[B]]”；若两者相当，使用“[[C]]”。
[用户要求] 
为{report_stock}在{date}生成一份股票研究报告。 

[助手A的股票研究报告开始]
{report_a} 
[助手A的股票研究报告结束] 

[助手B的股票研究报告开始] 
{report_b} 
[助手B的股票研究报告结束]"""

    prompt_template_en = ""
    
    stock_code, date = question_id.split("_")
    
    financial = Dataer().get_finacncials_ak(stock_code, date)
    try:
        income = convert_df_to_text(financial['stock_income']).split('\n')[0]
        balance_sheet = convert_df_to_text(financial['stock_balance_sheet']).split('\n')[0]
        cash_flow = convert_df_to_text(financial['stock_cash_flow']).split('\n')[0]
        financial_str = '\n'.join(["利润表: " + income, "资产负债表: " + balance_sheet, "现金流表: " + cash_flow])
    except Exception as e:
        print(e)
        financial_str = ''
    
    report_a = '\n'.join([answer_a['finance_write_response'],answer_a['news_write_response'],answer_a['report_write_response'],answer_a['trend_write_response'], answer_a['risk_response']])
    report_b = '\n'.join([answer_b['finance_write_response'],answer_b['news_write_response'],answer_b['report_write_response'],answer_b['trend_write_response'], answer_b['risk_response']])
    
    winners = []
    user_prompts = []
    judgments = []
    
    for metric in metrics:
        user_prompt = prompt_template.format(
            metric=metric,
            report_stock=stock_code,
            date=date,
            report_a=report_a,
            report_b=report_b,
        )
        
        if "数据准确性" in metric:
            user_prompt = f"股票相关的参考数据表:[[[{financial_str}]]]" + "\n\n" + user_prompt
            
        winner = "error"
        
        model = OpenAIModel(model_name=judge_model)
        judgment = model.simple_prompt(user_prompt)[0]

        if "[[A]]" in judgment:
            winner = "A"
        elif "[[B]]" in judgment:
            winner = "B"
        elif "[[C]]" in judgment:
            winner = "tie"
        else:
            winner = "error"
        winners.append(winner)
        user_prompts.append(user_prompt)
        judgments.append(judgment)

    return winners, user_prompts, judgments


def make_match(
    questions,
    models,
    model_answers,
    baseline_model,
    judge_model
):
    matches = []
    for q_id in questions:
        for i in range(len(models)):
            m_1 = models[i]
            m_2 = baseline_model
            if m_1 == m_2:
                continue
            a_1 = model_answers[m_1][q_id]
            a_2 = model_answers[baseline_model][q_id]
            match = MatchPair(q_id, m_1, m_2, a_1, a_2, judge_model)
            matches.append(match)
    return matches


def make_match_all_pairs(
    questions,
    models,
    model_answers,
    baseline_model,
    judge_model
):
    exist = open('exist.txt', 'r').read().split('\n')
    matches = []
    for q_id in questions:
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                m_1 = models[i]
                m_2 = models[j]
                a_1 = model_answers[m_1][q_id]
                a_2 = model_answers[m_2][q_id]
                if q_id + m_1 + m_2 in exist:
                    continue
                match = MatchPair(q_id, m_1, m_2, a_1, a_2, judge_model)
                matches.append(match)
    return matches


def make_match_single(
    questions,
    models,
    model_answers,
    baseline_model,
    jugde_model
):
    matches = []
    for q_id in questions:
        for i in range(len(models)):
            m = models[i]
            a = model_answers[m][q_id]
            matches.append(MatchSingle(q_id, m, a, jugde_model))
    return matches


def play_a_match_pair(match: MatchPair, output_file: str):
    question_id, model_1, model_2, answer_1, answer_2, judge_model = (
        match.question_id,
        match.model_1,
        match.model_2,
        match.answer_1,
        match.answer_2,
        match.judge_model
    )

    g1_winners, g1_user_prompts, g1_judgments = run_judge_pair(question_id, answer_1, answer_2, judge_model)
    g2_winners, g2_user_prompts, g2_judgments = run_judge_pair(question_id, answer_2, answer_1, judge_model)

    g1_map = {"A": "model_1", "B": "model_2"}
    g2_map = {"A": "model_2", "B": "model_1"}
    new_g1_winners = []
    new_g2_winners = []
    for g1_winner, g2_winner in zip(g1_winners, g2_winners):
        g1_winner = g1_map.get(g1_winner, g1_winner)
        g2_winner = g2_map.get(g2_winner, g2_winner)
        new_g1_winners.append(g1_winner)
        new_g2_winners.append(g2_winner)
    g1_winners = new_g1_winners
    g2_winners = new_g2_winners

    result = {
        "question_id": question_id,
        "model_1": model_1,
        "model_2": model_2,
        "g1_winners": g1_winners,
        "g2_winners": g2_winners,
        "g1_user_prompts": g1_user_prompts,
        "g1_judgments": g1_judgments,
        "g2_user_prompts": g2_user_prompts,
        "g2_judgments": g2_judgments,
        "tstamp": time.time(),
    }

    print(
        f"question: {question_id}, model_1: {model_1}, model_2: {model_2}, "
        f"g1_winners: {g1_winners}, g2_winners: {g2_winners}, "
    )

    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "a") as fout:
            fout.write(json.dumps(result, ensure_ascii=False) + "\n")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge-model", type=str, default="gpt-4o")
    parser.add_argument("--baseline-model", type=str, default="standard")
    parser.add_argument(
        "--mode",
        type=str,
        default="pairwise-all",
        choices=["pairwise-baseline", "pairwise-all", "single"],
        help=(
            "Evaluation mode. "
            "`pairwise-baseline` runs pairwise comparision against a baseline. "
            "`pairwise-all` runs pairwise comparision between all pairs. "
            "`single` runs single answer grading."
        ),
    )
    parser.add_argument(
        "--model-list",
        type=str,
        nargs="+",
        default=None,
        help="A list of models to be evaluated",
    )
    parser.add_argument(
        "--parallel", type=int, default=100, help="The number of concurrent API calls."
    )
    parser.add_argument(
        "--first-n", type=int, help="A debug option. Only run the first `n` judgments."
    )
    args = parser.parse_args()

    answer_dir = f"./results/model_results"

    # Load answers
    model_answers = load_model_answers(answer_dir)
    # Load questions
    questions = load_questions(answer_dir)
    
    
    if args.first_n:
        questions = questions[: args.first_n]

    if args.model_list is None:
        models = get_model_list(answer_dir)
    else:
        models = args.model_list

    if args.mode == "single":
        play_a_match_func = play_a_match_single
        output_file = (
            f"./results/model_judgment/{args.judge_model}_single.jsonl"
        )
        make_match_func = make_match_single
        baseline_model = None
    else:
        play_a_match_func = play_a_match_pair
        output_file = (
            f"./results/model_judgment/{args.judge_model}_pair.jsonl"
        )
        if args.mode == "pairwise-all":
            make_match_func = make_match_all_pairs
            baseline_model = None
        else:
            make_match_func = make_match
            baseline_model = args.baseline_model
            
    # Make matches
    matches = make_match_func(questions, models, model_answers, baseline_model, args.judge_model)

    match_stat = {}
    match_stat["mode"] = args.mode
    match_stat["baseline"] = baseline_model
    match_stat["model_list"] = models
    match_stat["total_num_questions"] = len(questions)
    match_stat["total_num_matches"] = len(matches)
    match_stat["output_path"] = output_file

    # Show match stats and prompt enter to continue
    print("Stats:")
    print(json.dumps(match_stat, indent=4))
    input("Press Enter to confirm...")
    
    # Play matches
    if args.parallel == 1:
        for match in tqdm(matches):
            play_a_match_func(match, output_file=output_file)
    else:

        def play_a_match_wrapper(match):
            play_a_match_func(match, output_file=output_file)

        np.random.seed(0)
        np.random.shuffle(matches)

        with ThreadPoolExecutor(args.parallel) as executor:
            for match in tqdm(
                executor.map(play_a_match_wrapper, matches), total=len(matches)
            ):
                pass
