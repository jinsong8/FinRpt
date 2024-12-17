#!/bin/sh

for ablation in 'analyst_finance' 'analyst_news' 'no_write'
do
    /data/jinsong/miniconda3/envs/finrpt/bin/python /data/jinsong/FinRpt_v1/finrpt/benchmark/exec_exp.py --model_name="finetune-qwen" --ablation=$ablation 
done

# for ablation in 'analyst_finance' 'analyst_news' 'no_write'
# do
#     /data/jinsong/miniconda3/envs/finrpt/bin/python /data/jinsong/FinRpt_v1/finrpt/benchmark/exec_exp.py --model_name="finetune-glm" --ablation=$ablation 
# done

for ablation in 'analyst_finance' 'analyst_news' 'no_write'
do
    /data/jinsong/miniconda3/envs/finrpt/bin/python /data/jinsong/FinRpt_v1/finrpt/benchmark/exec_exp.py --model_name="finetune-llama" --ablation=$ablation 
done