from finrpt.module.Base import BaseModel
from finrpt.utils.data_processing import robust_load_json
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


PROMPT_ZH = """请根据以上提供的股票的财务数据、关键新闻以及股票年报或半年报的信息撰写一份关于该股票的近期研究报告。研究报告应分为四个段落，每个段落都有一个侧重点和对应标题。请挖掘出四个关注点。为了更好地阅读,请将您的输出格式化为JSON:

{
  "report": [
    {
      "content": "请总结该股票的财务数据，分析其近期的财务表现。",
      "title": "根据conent生成合适的title,title保证语言意义连贯通顺的前提下,最好对仗工整,不建议八字对仗。"
    },
    {
      "content": "根据提供的关键新闻，分析市场对该股票的影响，讨论可能的短期和长期趋势。",
      "title": "根据conent生成合适的title,title保证语言意义连贯通顺的前提下,最好对仗工整,不建议八字对仗。"
    },
    {
      "content": "根据年报或半年报的信息，探讨该公司的战略方向和未来发展潜力。",
      "title": "根据conent生成合适的title,title保证语言意义连贯通顺的前提下,最好对仗工整,不建议八字对仗。"
    },
    {
      "content": "综合以上内容，指出值得关注的机会。不需要分析风险",
      "title": "根据conent生成合适的title,title保证语言意义连贯通顺的前提下,最好对仗工整,不建议八字对仗。"
    }
  ]
}"""

class Advisor(BaseModel):
    def __init__(self, max_rounds=3, model_name="gpt-4", language='zh'):
        super().__init__(max_rounds=max_rounds, model_name=model_name, language=language)
        self.system_prompt = PROMPT_ZH if self.language == 'zh' else PROMPT_EN
            
    def run(self, data):
        financials_prompt = "季度损益:" + data['analyze_income'] + '\n资产负债:' + data['analyze_balance'] + '\n现金流量:' + data['analyze_cash']
        concise_news = [new['concise_new'] for new in data['analyze_news']]
        news_prompt = '\n'.join(concise_news)
        report_prompt = data['report']['title'] + ":[[[" + data['report']['content'].strip() + "]]]"
        advisor_prompt = "分析日期: " + data["date"] + "\n\n" + \
                 "公司名称: " + data["company_name"] + "\n\n" + \
                 "财务数据:\n" + financials_prompt + "\n\n" + \
                 "关键新闻:\n" + news_prompt + "\n\n" + \
                 "股票半年报或年报:\n" + report_prompt + "\n\n" + \
                  self.system_prompt
        with open('./prompt/advisor_prompt.txt', 'w') as f:
            f.write(advisor_prompt)
        response = self.model.simple_prompt(advisor_prompt)
        print(response)
        response_json = robust_load_json(response[0])
        # response_json = json.loads('{"report": [{"content": "贵州茅台在2024年第三季度表现出色，实现总收入396.7亿元，同比增长15.5%，环比增长7.3%。毛利率高达91.2%，营业利润率和净利润率分别为66%和48.2%，显示出强劲的盈利能力。资产负债表显示出稳健的财务结构，流动资产远超流动负债，长期债务较低，股东权益持续增长。经营现金流表现强劲，投资活动中资本支出增加，显示出对未来增长的投入。整体来看，贵州茅台的财务表现稳健，盈利能力和财务健康状况均优于行业平均水平。", "title": "贵州茅台财务表现分析"}, {"content": "近期的关键新闻显示，市场对贵州茅台的信心稳固。中邮证券给予买入评级，易方达基金看好其股东回报水平。茅台的ESG评级提升至BBB级，显示其在环境、社会和治理方面的进步。大宗交易的成交价与市场持平，显示出市场对其价格的认可。尽管中秋期间需求下滑导致股价短期波动，但整体市场情绪依然积极。央行和证监会的政策利好也为茅台市值带来显著提升。短期来看，市场对茅台的信心依然强劲，长期则受益于稳健的财务表现和政策支持。", "title": "市场影响与趋势分析"}, {"content": "贵州茅台在保持核心竞争力的同时，积极拓展市场和提升品牌价值。通过与故宫博物院的合作，茅台在文化遗产保护和利用方面展现出创新的战略方向。公司持续推进数字化转型，提升管理体系现代化水平。段永平对其商业模式和现金流充沛的信心，进一步证明其适合长期持有。未来，茅台将继续依靠其独特的品牌和品质优势，结合政策利好和市场需求，推动高质量发展，值得投资者关注其在国际市场的扩展和创新举措。", "title": "战略方向与发展潜力"}]}')
        return response_json['report']
        
