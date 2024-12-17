from finrpt.module.Base import BaseModel
import os
import pdb
from finrpt.utils.data_processing import robust_load_json
from finrpt.module.OpenAI import OpenAIModel
import logging
import json

PROMPT_TREND = """综合以上内容，给出你的投资建议，预测未来一个月的股票变化趋势，给出买入或卖出的评级。生成股票研报中的单一段落，不超过200字。请返回如下json格式的文本
{"段落": "单一段落内容", "标题": "根据段落内容生成的简洁合适标题", "评级": "买入/卖出"}
"""

PROMPT_TREND = """根据以上信息，请提供投资建议，并预测未来三周该公司股票变化趋势。若该公司股票的预期涨幅高于沪深300指数涨幅，则给予“买入”评级；若低于，则给予"卖出"评级。撰写一段不超过200字的股票研究报告内容。请返回如下json格式的文本
{"段落": "单一段落内容", "标题": "根据段落内容生成的简洁合适标题", "评级": "买入/卖出"}
"""

class Predictor(BaseModel):
    def __init__(self, max_rounds=3, model_name="gpt-4o", language='zh'):
        super().__init__(max_rounds=max_rounds, model_name=model_name, language=language)
        self.model_name = model_name
            
    def run(self, data, run_path):
        logger = logging.getLogger(run_path)
        finance_response_json, news_response_json, report_response_json = data['analyze_advisor']
        risks = data['analyze_risk']
        
        stock_price = ", ".join(str(d) + ": " + str(p) for d, p in zip(data['financials']['stock_data']['date'], data['financials']['stock_data']['Close']))
        csi300_price = ", ".join(str(d) + ": " + str(p) for d, p in zip(data['financials']['csi300_stock_data']['date'], data['financials']['csi300_stock_data']['close']))
        
        trend_write_prompt = "分析日期: " + data["date"] + "\n\n" + \
                  "公司名称: " + data["company_name"] + "\n\n" + \
                  finance_response_json["title"] + "： " + finance_response_json["content"] + "\n\n" + \
                  news_response_json["title"] + "： " + news_response_json["content"] + "\n\n" + \
                  report_response_json["title"] + "： " + report_response_json["content"] + "\n\n" + \
                  "风险评估： " + ", ".join([item for item in risks]) + "\n\n" + \
                  "最近一个月沪深300指数历史价格： " + csi300_price  + "\n\n" + \
                  "最近一个月该股票公司历史价格：" + stock_price +  "\n\n\n" + PROMPT_TREND
        logger.debug('<<<trend_write_prompt>>>\n' + trend_write_prompt)
        data['save']['trend_write_prompt'] = trend_write_prompt

        trend_write_prompt_ = trend_write_prompt
        
        if "finetune" in self.model_name:
            if "llama" in self.model_name:
                trend_model = 'llama_trend:latest'
            elif "qwen" in self.model_name:
                trend_model = 'qwen_trend:latest'
            elif "glm" in self.model_name:
                trend_model = 'glm_trend:latest'
        else:
            trend_model = self.model_name
        
        trend_response, trend_response_json = OpenAIModel(model_name=trend_model, max_rounds=self.max_rounds).json_prompt(trend_write_prompt_)
        logger.debug('<<<trend_response>>>\n' + str(trend_response))
        data['save']['trend_write_response'] = json.dumps(trend_response_json, ensure_ascii=False)
        
        data['analyze_advisor'].append({'content': trend_response_json["段落"], 'title': trend_response_json["标题"], "rating": trend_response_json["评级"]})
        
        return trend_response_json