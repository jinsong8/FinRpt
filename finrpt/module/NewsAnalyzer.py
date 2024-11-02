from finrpt.module.Base import BaseModel
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

SYSTEM_PROPMT_CHINESE = """您是一位专注于发现影响股市趋势的关键新闻的专家金融分析师。我为您提供以上公司名称和相关新闻文章。您的任务是识别并总结可能影响公司股价的十条最重要的新闻。请关注财务表现、市场状况、监管变化、领导层变动以及其他相关信息。请将您的分析限制在十条最重要的新闻上,使用不超过3000个字。为了更好地阅读,请将您的输出格式化为JSON:

{
  "key_news": [
    {
      "news_id": "该新闻在输入新闻中的序号",
      "news_title": "标题",
      "summary": "新闻重述，需要包括新闻的主要内容",
      "potential_impact": "正面/负面/中性"
    },
    {
      "news_id": "该新闻在输入新闻中的序号",  
      "news_title": "标题",
      "summary": "新闻重述，需要包括新闻的主要内容",
      "potential_impact": "正面/负面/中性"
    },
    ...
    {
      "news_id": "该新闻在输入新闻中的序号",
      "news_title": "标题",
      "summary": "新闻重述，需要包括新闻的主要内容",
      "potential_impact": "正面/负面/中性"
    }
  ]
}

"""


class NewsAnalyzer(BaseModel):
    def __init__(self, max_rounds=3, model_name='gpt-4o', language='zh') -> None:
        super().__init__(max_rounds=max_rounds, model_name=model_name, language=language)
        if self.language == 'en':
            self.system_prompt = SYSTEM_PROPMT_ENGLISH
        elif self.language == 'zh':
            self.system_prompt = SYSTEM_PROPMT_CHINESE
    
    def run(self, data):
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
                news_prompt += str(idx + 1) + '.' + f"[News Date:{article['news_time']}\nNews Title:{article['news_title']}\nNews Content:{article['news_content']}]\n"
            elif self.language == 'zh':
                news_prompt += str(idx + 1) + '.' + f"[新闻日期:{article['news_time']}\n新闻标题:{article['news_title']}\n新闻内容:{article['news_content']}]\n"
        # propmt = self.system_prompt + company_name_prompt + news_prompt
        propmt = company_name_prompt + news_prompt + '\n\n\n' + self.system_prompt
        print(propmt)
        response = self.model.simple_prompt(propmt)
        print(response)
        
        try:
            response_json = json.loads(response[0][7:-3].strip())
        except Exception as e:
            try:
                response_json = json.loads(response[0])
            except Exception as e:
                match = re.search(r'\{.*\}', response[0], re.DOTALL)
                response_json = json.loads(match.group(0))
                
        for key_new in response_json['key_news']:
            key_new['raw_new'] = data['news'][int(key_new['news_id']) - 1]
        key_news = response_json['key_news']
        # try:
        #     key_news = ast.literal_eval(open('key_news.txt').readline())
        #     print(key_news)  # 输出加载后的列表
        # except (ValueError, SyntaxError) as e:
        #     print("Error loading list:", e)
        for key_new in key_news:
            if self.language == 'zh':
                key_new['concise_new'] = '新闻日期:' + key_new['raw_new']['news_time'] + '    ' + '新闻摘要:' + key_new['summary']
            else:
                key_new['concise_new'] = 'News Date:' + key_new['raw_new']['news_time'] + '    ' + 'Summary:' + key_new['summary']
        key_news = sorted(key_news, key=lambda x: x['raw_new']['news_time'], reverse=True)
        return key_news
    
    def test(self):
        print(self.run({'company_name': 'Apple', 'news': [{'title': 'Apple Stock Price Rises by $25', 'content': 'The Apple Inc. stock has risen by $25 since last week.'}, {'title': 'New iPhone', 'content': 'A new iPhone XR was released this month.'}]}))
        
        
        
if __name__ == '__main__':
    analyzer = NewsAnalyzer()
    analyzer.test()