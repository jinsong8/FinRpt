from finrpt.module.Base import BaseModel
from finrpt.utils.data_processing import robust_load_json
import logging
import pdb
import re
import json
import ast


SYSTEM_PROPMT_ENGLISH = """You are an expert financial analyst specializing in discovering key news that affect stock market trends. I will provide you with the company name and related news articles. Your task is to identify and summarize three most key news items that may influence the company's stock price. Focus on factors such as financial performance, market conditions, regulatory changes, leadership shifts, and any other relevant information. Please limit your analysis to three most key news items, using no more than 3000 tokens. Format your output in JSON for better readability:

{
  "key_news": [
    {
      "news_id": "News ID",
      "news_title": "Title 1",
      "summary": "Brief summary of the news",
      "potential_impact": "Positive/Negative/Neutral"
    },
    {
      "news_id": "News ID",
      "news_title": "Title 2",
      "summary": "Brief summary of the news",
      "potential_impact": "Positive/Negative/Neutral"
    },
    {
      "news_id": "News ID",
      "news_title": "Title 3",
      "summary": "Brief summary of the news",
      "potential_impact": "Positive/Negative/Neutral"
    }
  ]
}
"""

SYSTEM_PROPMT_CHINESE = """您是一位专注于发现影响股市趋势的关键新闻的专家金融分析师。我为您提供以上公司名称和相关新闻文章。您的任务是根据新闻对公司股票价格影响的可能性将新闻排序，选择最多十条最可能影响公司股价的重要的新闻。请关注财务表现、市场状况、监管变化、领导层变动以及其他相关信息。请将您的输出限制在最多十条最重要的新闻上,使用不超过3000个字。为了更好地阅读,请将您的输出格式化为JSON:
{"key_news": [{"date": "新闻日期", "content": "新闻内容", "potential_impact": "正面/负面/中性"}, {"date": "新闻日期", "content": "新闻内容", "potential_impact": "正面/负面/中性"}, ..., {"date": "新闻日期", "content": "新闻内容", "potential_impact": "正面/负面/中性"}]}
"""


class NewsAnalyzer(BaseModel):
    def __init__(self, max_rounds=3, model_name='gpt-4o', language='zh') -> None:
        super().__init__(max_rounds=max_rounds, model_name=model_name, language=language)
        if self.language == 'en':
            self.system_prompt = SYSTEM_PROPMT_ENGLISH
        elif self.language == 'zh':
            self.system_prompt = SYSTEM_PROPMT_CHINESE
    
    def run(self, data, run_path):
        logger = logging.getLogger(run_path)
        company_name = data['company_name']
        if self.language == 'en':
            company_name_prompt = f"Company Name: {company_name}\n"
        elif self.language == 'zh':
            company_name_prompt = f"公司名称: {company_name}\n"
        if self.language == 'en':
            news_prompt = f"News Articles:\n"
        elif self.language == 'zh':
            news_prompt = f"新闻报道:\n"
        for idx, article in enumerate(data['news']):
            if self.language == 'en':
                news_prompt += str(idx + 1) + '.' + f"[News Date:{article['news_time']}\nNews Title:{article['news_title']}\nNews Content:{article['news_summary']}]\n\n"
            elif self.language == 'zh':
                news_prompt += str(idx + 1) + '.' + f"[新闻日期:{article['news_time']}\n新闻标题:{article['news_title']}\n新闻内容:{article['news_summary']}]\n\n"

        propmt = company_name_prompt + news_prompt + '\n\n\n' + self.system_prompt
        logger.debug('<<<prompt>>>\n' + propmt)
        data['save']['news_anlyzer_prompt'] = propmt
        response = self.model.robust_prompt(propmt)
        logger.debug('<<<response>>>\n' + str(response))
        
        response_json = robust_load_json(response[0])
        logger.debug('<<<response_json>>>\n' + str(response_json))
        data['save']['news_anlyzer_response'] = json.dumps(response_json, ensure_ascii=False)
                
        # for key_new in response_json['key_news']:
        #     key_new['raw_new'] = data['news'][int(key_new['news_id']) - 1]
        key_news = response_json['key_news']
        # try:
        #     key_news = ast.literal_eval(open('key_news.txt').readline())
        #     print(key_news)  # 输出加载后的列表
        # except (ValueError, SyntaxError) as e:
        #     print("Error loading list:", e)
        for key_new in key_news:
            key_new['concise_new'] = key_new['content']
            if self.language == 'zh':
                key_new['concise_new'] = '新闻日期:' + key_new['date'] + '    ' + '新闻内容:' + key_new['content']
            else:
                key_new['concise_new'] = 'News Date:' + key_new['date'] + '    ' + 'Summary:' + key_new['news_content']
        key_news = sorted(key_news, key=lambda x: x['date'], reverse=True)
        return key_news
    
    def test(self):
        print(self.run({'company_name': 'Apple', 'news': [{'title': 'Apple Stock Price Rises by $25', 'content': 'The Apple Inc. stock has risen by $25 since last week.'}, {'title': 'New iPhone', 'content': 'A new iPhone XR was released this month.'}]}))
        
        
        
if __name__ == '__main__':
    analyzer = NewsAnalyzer()
    analyzer.test()