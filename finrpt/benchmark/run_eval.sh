#!/bin/bash

model_name=""  
checkpoint_path=""  
save_result_dir="./results"

python cflue_main.py \
    --model_name ${model_name} \
    --checkpoint_path ${checkpoint_path} \
    --save_result_dir ${save_result_dir}