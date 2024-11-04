from finrpt.module.Base import BaseModel
from finrpt.utils.data_processing import robust_load_json
import pdb
import json

PROMPT_EN = """Please refer to and combine the semi-annual or annual report, recent stock summary information, and your own knowledge to analyze the potential risk factors faced by this stock. You can refer to the risks mentioned in the semi-annual or annual report. Return at least three different risks. Each risk should be concise and not exceed 10 words. Output format in JSON.

Output format:
{
"risks": [
"Risk 1",
"Risk 2",
...
"Risk n"
]
}"""

PROMPT_ZH = """请参考结合以上半年报或年报、股票近期总结信息和你自己的知识，分析该股票可能面临的风险因素。可以参考半年报或年报里提及的风险。返回至少三个不同的风险。每个风险精简不超过10个字。

请将您的输出格式转化为JSON,能直接被json.loads()函数加载:
{
  "risks": [
    "风险1",
    "风险2",
    ...
    "风险n"
  ]
}"""


class RiskAssessor(BaseModel):
    def __init__(self, max_rounds=3, model_name="gpt-4", language='zh'):
        super().__init__(max_rounds=max_rounds, model_name=model_name, language=language)
        if self.language == 'en':
            self.system_prompt = PROMPT_EN
        elif self.language == 'zh':
            self.system_prompt = PROMPT_ZH
            
    def run(self, data):
        advisor_prompt = "\n".join([ad["title"] + ":" + ad["content"] for ad in data["analyze_advisor"]])
        report_prompt = data['report']['title'] + ":[[[" + data['report']['content'].strip() + "]]]"
        advisor_prompt = "分析日期: " + data["date"] + "\n\n" + \
            "公司名称: " + data["company_name"] + "\n\n" + \
            "股票近期总结信息:\n" + advisor_prompt + "\n\n" + \
            "股票半年报或年报:\n" + report_prompt + "\n\n" + \
            self.system_prompt
        with open('prompt/risk_prompt.txt', 'w') as f:
            f.write(advisor_prompt)
            
        response = self.model.simple_prompt(advisor_prompt)
        print(response)
        response_json = robust_load_json(response[0])
        # response_json = json.loads('{"risks": ["市场需求波动", "政策变动影响", "环境保护风险"]}')
        return response_json['risks']