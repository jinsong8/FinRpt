#!/bin/sh

# for model_name in 'llama3.1:8b-instruct-fp16'
# do
#     /data/jinsong/miniconda3/envs/finrpt/bin/python /data/jinsong/FinRpt_v1/finrpt/benchmark/exec_exp.py --model_name=$model_name &
# done

# for model_name in 'llama3.1:8b-instruct-fp16' 'qwen2.5:7b-instruct-fp16' 'glm4:9b-chat-fp16' 'gemma2:9b-instruct-fp16'
# do
#     /data/jinsong/miniconda3/envs/finrpt/bin/python /data/jinsong/FinRpt_v1/finrpt/benchmark/exec_exp.py --model_name=$model_name &
# done

# for model_name in 'llama-xy:13b' 'deepseek-v2:16b' 'qwen2.5:14b-instruct-fp16'
# do
#     /data/jinsong/miniconda3/envs/finrpt/bin/python /data/jinsong/FinRpt_v1/finrpt/benchmark/exec_exp.py --model_name=$model_name 
# done


# for model_name in  'llama3.1:70b' 'qwen2.5:72b' 'gemma2:27b-instruct-fp16'  
# do
#     /data/jinsong/miniconda3/envs/finrpt/bin/python /data/jinsong/FinRpt_v1/finrpt/benchmark/exec_exp.py --model_name=$model_name &
# done

for model_name in  'finetune-qwen' 'finetune-glm' 'finetune-llama'
do
    /data/jinsong/miniconda3/envs/finrpt/bin/python /data/jinsong/FinRpt_v1/finrpt/benchmark/exec_exp.py --model_name=$model_name 
done


# for model_name in  'gpt-4o' 'gpt-4o-mini'
# do
#     /data/jinsong/miniconda3/envs/finrpt/bin/python /data/jinsong/FinRpt_v1/finrpt/benchmark/exec_exp.py --model_name=$model_name &
# done