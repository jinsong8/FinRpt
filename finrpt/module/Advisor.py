from finrpt.module.Base import BaseModel
import os
from finrpt.utils.data_processing import robust_load_json
from finrpt.module.OpenAI import OpenAIModel
import logging
import pdb
import json
import re

PROMPT_EN = """Based on the provided financial data, key news, and information from the annual or semi-annual reports of the stock, write a recent research report on the stock. The research report should be divided into three paragraphs, each with a specific focus and corresponding title. Please identify three points of interest.

{
  "report": [
    {
      "content": "Please summarize the financial data of the stock and analyze its recent financial performance.",
      "title": "Generate an appropriate title based on the content"
    },
    {
      "content": "Analyze the impact of key news, annual or semi-annual reports on the market for this stock, and discuss possible short-term and long-term trends.",
      "title": "Generate an appropriate title based on the content"
    },
    {
      "content": "Based on the above, explore the company's strategic direction and future development potential, highlighting opportunities worth noting.",
      "title": "Generate an appropriate title based on the content"
    }
  ]
}"""

PROMPT_ZH_v1="""请根据以上提供的股票的财务数据、关键新闻以及股票年报或半年报的信息信息撰写一份关于该股票的近期研究报告。研究报告应分为三个段落，每个段落都有一个侧重点和对应标题。请挖掘出三个关注点。

确保输出是有效的JSON对象,输出格式:
{
  "report": [
    {
      "content": "请总结该股票的财务数据，分析其近期的财务表现。",
      "title": "根据conent生成合适的title"
    },
    {
      "content": "根据提供的关键新闻，年报或半年报的信息，分析市场对该股票的影响，讨论可能的短期和长期趋势。",
      "title": "根据conent生成合适的title",
    },
    {
      "content": "综合以上内容，探讨该公司的战略方向和未来发展潜力，指出值得关注的机会。",
      "title": "根据conent生成合适的title",
    }
  ]
}"""


PROMPT_ZH = """请根据以上提供的股票的财务数据、关键新闻以及股票年报或半年报的信息撰写一份关于该股票的近期研究报告。研究报告应分为三个段落，每个段落都有一个侧重点和对应标题。为了更好地阅读,请将您的输出格式化为JSON:
{
  "report": [
    {
      "content": "请总结该股票的财务数据，分析其近期的财务表现，包括收入、利润、现金流等关键指标的变化。",
      "title": "根据conent生成合适的title。"
    },
    {
      "content": "根据提供的关键新闻，分析市场对该股票的影响，讨论可能的短期和长期趋势，包括市场情绪和外部因素的影响。",
      "title": "根据conent生成合适的title。"
    },
    {
      "content": "根据年报或半年报的信息，探讨该公司的战略方向和未来发展潜力，评估其在行业中的竞争地位。",
      "title": "根据conent生成合适的title。"
    }
  ]
}"""

PROMPT_FINANCE = """请根据以上提供的股票的财务数据，总结该股票的财务数据，分析其近期的财务表现，包括收入、利润、负债、现金流等关键指标的变化。生成股票研报中的单一段落，不超过200字，生成内容需包括具体财务数据。请返回如下json格式的文本:
{"段落": "单一段落内容", "标题": "根据段落内容生成的简洁合适标题"}"""

PROMPT_NEWS = """请根据以上提供的股票的关键新闻，分析市场对该股票的影响，讨论可能的短期和长期趋势，包括市场情绪和外部因素的影响。生成股票研报中的单一段落，不超过200字。请返回如下json格式的文本:
{"段落": "单一段落内容", "标题": "根据段落内容生成的简洁合适标题"}"""

PROMPT_REPORT = """请根据以上提供的股票的年报或半年报，探讨该公司的战略方向和未来发展潜力，评估其在行业中的竞争地位。生成股票研报中的单一段落，不超过200字。请返回如下json格式的文本:
{"段落": "单一段落内容", "标题": "根据段落内容生成的简洁合适标题"}"""

class Advisor(BaseModel):
    def __init__(self, max_rounds=3, model_name="gpt-4o", language='zh'):
        super().__init__(max_rounds=max_rounds, model_name=model_name, language=language)
        self.system_prompt = PROMPT_ZH if self.language == 'zh' else PROMPT_EN
        self.model_name = model_name
            
    def run(self, data, run_path):
        logger = logging.getLogger(run_path)
        financials_prompt = "季度损益:" + data['analyze_income'] + '\n资产负债:' + data['analyze_balance'] + '\n现金流量:' + data['analyze_cash']
        concise_news = [new['concise_new'] for new in data['analyze_news']]
        news_prompt = '\n'.join(concise_news)
        report_prompt = data['report']['title'] + ":[[[" + data['report']['summary'].strip() + "]]]"
        
        finance_write_prompt = "分析日期: " + data["date"] + "\n\n" + \
                 "公司名称: " + data["company_name"] + "\n\n" + \
                 "财务数据:\n" + financials_prompt + "\n\n\n" + PROMPT_FINANCE
        logger.debug('<<<finance_write_prompt>>>\n' + finance_write_prompt)
        data['save']['finance_write_prompt'] = finance_write_prompt
        
        finance_write_prompt_ = finance_write_prompt
        if "finetune" in self.model_name:
            if "llama" in self.model_name:
                finance_model = 'llama_finance:latest'
            elif "qwen" in self.model_name:
                finance_model = 'qwen_finance:latest'
            elif "glm" in self.model_name:
                finance_model = 'glm_finance:latest'
        else:
            finance_model = self.model_name
        finance_response, finance_response_json = OpenAIModel(model_name=finance_model, max_rounds=self.max_rounds).json_prompt(finance_write_prompt_)
        logger.debug('<<<finance_response>>>\n' + str(finance_response))
        data['save']['finance_write_response'] = json.dumps(finance_response_json, ensure_ascii=False)
        
        news_write_prompt = "分析日期: " + data["date"] + "\n\n" + \
                 "公司名称: " + data["company_name"] + "\n\n" + \
                 "关键新闻:\n" + news_prompt + "\n\n\n" + PROMPT_NEWS
        
        news_write_prompt_ = news_write_prompt
        
        logger.debug('<<<news_write_prompt>>>\n' + news_write_prompt)
        data['save']['news_write_prompt'] = news_write_prompt
        if "finetune" in self.model_name:
            if "llama" in self.model_name:
                news_model = 'llama_news:latest'
            elif "qwen" in self.model_name:
                news_model = 'qwen_news:latest'
            elif "glm" in self.model_name:
                news_model = 'glm_news:latest'
        else:
            news_model = self.model_name
        news_response, news_response_json = OpenAIModel(model_name=news_model, max_rounds=self.max_rounds).json_prompt(news_write_prompt_)
        logger.debug('<<<news_response>>>\n' + str(news_response))
        data['save']['news_write_response'] = json.dumps(news_response_json, ensure_ascii=False)
        
        report_write_prompt = "分析日期: " + data["date"] + "\n\n" + \
                  "公司名称: " + data["company_name"] + "\n\n" + \
                  "股票半年报或年报:\n" + report_prompt + "\n\n\n" + PROMPT_REPORT          
                  
        if len(report_prompt) < 500:
            report_write_prompt = news_write_prompt
        logger.debug('<<<report_write_prompt>>>\n' + report_write_prompt)
        data['save']['report_write_prompt'] = report_write_prompt
        
        report_write_prompt_ = report_write_prompt
        
        if "finetune" in self.model_name:
            if "llama" in self.model_name:
                report_model = 'llama_report:latest'
            elif "qwen" in self.model_name:
                report_model = 'qwen_report:latest'
            elif "glm" in self.model_name:
                report_model = 'glm_report:latest'
        else:
            report_model = self.model_name
        report_response, report_response_json = OpenAIModel(model_name=report_model, max_rounds=self.max_rounds).json_prompt(report_write_prompt_)
        logger.debug('<<<report_response>>>\n' + str(report_response))
        data['save']['report_write_response'] = json.dumps(report_response_json, ensure_ascii=False)
        
        response_json = {
            "report": []
        }
        response_json['report'].append({'content': finance_response_json["段落"], 'title': finance_response_json["标题"]})
        response_json['report'].append({'content': news_response_json["段落"], 'title': news_response_json["标题"]})
        response_json['report'].append({'content': report_response_json["段落"], 'title': report_response_json["标题"]})
        
        return response_json['report']
        
