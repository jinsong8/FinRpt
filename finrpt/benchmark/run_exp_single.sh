for model_name in 'gpt-4o-mini' 'gpt-4o' 'llama3.1:8b-instruct-fp16' 'qwen2.5:14b-instruct-fp16' 'qwen2.5:7b-instruct-fp16' 'llama3.1:70b' 'llama-xy:13b' 'finma:7b' 'finrpt:7b' 'qwen2.5:72b' 'deepseek-v2:16b' 'glm4:9b-chat-fp16' 'gemma2:9b-instruct-fp16' 'gemma2:27b-instruct-fp16'
do
    /data/name/miniconda3/envs/finrpt/bin/python /data/name/FinRpt_v1/finrpt/benchmark/exec_exp.py --model_name=$model_name --exp_type='single' 
done


for model_name in 'gpt-4o-mini' 'gpt-4o' 'llama3.1:8b-instruct-fp16' 'qwen2.5:14b-instruct-fp16' 'qwen2.5:7b-instruct-fp16' 'llama3.1:70b' 'llama-xy:13b' 'finma:7b' 'finrpt:7b' 'qwen2.5:72b' 'deepseek-v2:16b' 'glm4:9b-chat-fp16' 'gemma2:9b-instruct-fp16' 'gemma2:27b-instruct-fp16'
do
    /data/name/miniconda3/envs/finrpt/bin/python /data/name/FinRpt_v1/finrpt/benchmark/convsingle.py --model_name=$model_name &
done