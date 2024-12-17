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
        # advisor_prompt = "分析日期: " + data["date"] + "\n\n" + \
        #          "公司名称: " + data["company_name"] + "\n\n" + \
        #          "财务数据:\n" + financials_prompt + "\n\n" + \
        #          "关键新闻:\n" + news_prompt + "\n\n" + \
        #          "股票半年报或年报:\n" + report_prompt + "\n\n" + \
        #           self.system_prompt
        # logger.debug('<<<prompt>>>\n' + advisor_prompt)
        # for i in range(self.max_rounds):
        #     try:
        #         response = self.model.simple_prompt(advisor_prompt)
        #         logger.debug('<<<response>>>\n' + str(response))
        #         response_json = robust_load_json(response[0])
        #         break
        #     except Exception as e:
        #         print("Error occurred during round {}".format(i+1), e)

        # response_json = json.loads('{"report": [{"content": "贵州茅台在2024年第三季度表现出色，实现总收入396.7亿元，同比增长15.5%，环比增长7.3%。毛利率高达91.2%，营业利润率和净利润率分别为66%和48.2%，显示出强劲的盈利能力。资产负债表显示出稳健的财务结构，流动资产远超流动负债，长期债务较低，股东权益持续增长。经营现金流表现强劲，投资活动中资本支出增加，显示出对未来增长的投入。整体来看，贵州茅台的财务表现稳健，盈利能力和财务健康状况均优于行业平均水平。", "title": "贵州茅台财务表现分析"}, {"content": "近期的关键新闻显示，市场对贵州茅台的信心稳固。中邮证券给予买入评级，易方达基金看好其股东回报水平。茅台的ESG评级提升至BBB级，显示其在环境、社会和治理方面的进步。大宗交易的成交价与市场持平，显示出市场对其价格的认可。尽管中秋期间需求下滑导致股价短期波动，但整体市场情绪依然积极。央行和证监会的政策利好也为茅台市值带来显著提升。短期来看，市场对茅台的信心依然强劲，长期则受益于稳健的财务表现和政策支持。", "title": "市场影响与趋势分析"}, {"content": "贵州茅台在保持核心竞争力的同时，积极拓展市场和提升品牌价值。通过与故宫博物院的合作，茅台在文化遗产保护和利用方面展现出创新的战略方向。公司持续推进数字化转型，提升管理体系现代化水平。段永平对其商业模式和现金流充沛的信心，进一步证明其适合长期持有。未来，茅台将继续依靠其独特的品牌和品质优势，结合政策利好和市场需求，推动高质量发展，值得投资者关注其在国际市场的扩展和创新举措。", "title": "战略方向与发展潜力"}]}')
        # logger.debug('<<<response_json>>>\n' + str(response_json))
        
        finance_write_prompt = "分析日期: " + data["date"] + "\n\n" + \
                 "公司名称: " + data["company_name"] + "\n\n" + \
                 "财务数据:\n" + financials_prompt + "\n\n\n" + PROMPT_FINANCE
        logger.debug('<<<finance_write_prompt>>>\n' + finance_write_prompt)
        data['save']['finance_write_prompt'] = finance_write_prompt
        
        # for report generate
        if data["trend"] > 0:
            finance_write_prompt_ = "因为未来的实际股票走势良好，建议给出正面评价\n\n" + finance_write_prompt
        else:
            finance_write_prompt_ = "因为未来的实际股票走势不好，建议给出负面评价\n\n" + finance_write_prompt
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
        
        # for report generate
        if data["trend"] > 0:
            news_write_prompt_ = "因为未来的实际股票走势良好，建议给出正面评价\n\n" + news_write_prompt
        else:
            news_write_prompt_ = "因为未来的实际股票走势不好，建议给出负面评价\n\n" + news_write_prompt
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
        
        # for report generate
        if data["trend"] > 0:
            report_write_prompt_ = "因为未来的实际股票走势良好，建议给出正面评价\n\n" + report_write_prompt
        else:
            report_write_prompt_ = "因为未来的实际股票走势不好，建议给出负面评价\n\n" + report_write_prompt
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
        
