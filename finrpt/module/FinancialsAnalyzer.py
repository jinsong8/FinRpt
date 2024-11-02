from finrpt.module.Base import BaseModel
import pdb


INCOME_PROMPT_EN = """Conduct a comprehensive analysis of the company's income statement. Focus on the following areas:

1.Revenue Analysis: Provide an overview of total revenue, including Year-over-Year (YoY) and Quarter-over-Quarter (QoQ) comparisons. Break down revenue sources to identify primary contributors and trends.

2.Cost Analysis: Examine the Cost of Goods Sold (COGS) for potential cost control issues.

3.Profitability Metrics: Review gross, operating, and net profit margins to evaluate cost efficiency, operational effectiveness, and overall profitability.

4.Investor Perspective: Analyze Earnings Per Share (EPS) to understand investor perspectives.

5.Benchmarking: Compare these metrics with historical data and industry or competitor benchmarks to identify growth patterns, profitability trends, and operational challenges.

Summarize your findings in a strategic overview of the company’s financial health in a single paragraph. The summary should be less than 130 words and highlight 4-5 key points with specific data support under respective subheadings."""


INCOME_PROMPT_ZH = """对公司损益表进行全面分析。重点关注以下几个方面：

1.收入分析：提供总收入概况，包括同比（Year-over-Year）和环比（Quarter-over-Quarter）比较。分解收入来源，识别主要贡献者和趋势。

2.成本分析：检查销售成本（COGS），寻找潜在的成本控制问题。

3.盈利能力指标：审查毛利率、营业利润率和净利润率，以评估成本效率、运营效果和整体盈利能力。

4.投资者视角：分析每股收益（EPS），了解投资者的看法。

5.基准比较：将这些指标与历史数据及行业或竞争对手的基准进行比较，以识别增长模式、盈利趋势和运营挑战。

在单段概述中总结您的发现。总结应少于130字。"""


BALANCE_PROMPT_EN = """Conduct a detailed analysis of the company's balance sheet, focusing on the following areas:

1.Asset Structure: Examine the composition of assets to assess financial stability and operational efficiency.

2.Liabilities and Equity: Evaluate liquidity by comparing current assets to current liabilities, and assess solvency through long-term debt ratios. Analyze the equity position to determine long-term investment potential.

3.Historical Comparison: Contrast these metrics with previous years' data to identify financial trends, improvements, or deteriorations.

4.Strategic Assessment: Provide a strategic overview of the company's financial leverage, asset management, and capital structure.

5.Summarize your findings in a single paragraph, less than 130 words, highlighting key insights into the company’s fiscal health and future prospects."""


BALANCE_PROMPT_ZH = """对公司的资产负债表进行详细分析，重点关注以下几个方面：

1.资产结构：检查资产的组成，以评估财务稳定性和运营效率。

2.负债和股东权益：通过比较流动资产与流动负债来评估流动性，并通过长期债务比率评估偿债能力。分析股东权益状况，以确定长期投资潜力。

3.历史比较：将这些指标与前几年的数据进行对比，以识别财务趋势、改善或恶化情况。

4.战略评估：提供公司财务杠杆、资产管理和资本结构的战略概述。

用一段不超过130字的文字总结你的发现，突出公司财务健康状况和未来前景的关键见解。"""


CASH_PROMPT_EN = """Conduct a thorough evaluation of the company's cash flow, focusing on operating, investing, and financing activities. Analyze operational cash flow to gauge core business profitability, examine investing activities for capital expenditures and investment insights, and review financing activities to understand debt, equity movements, and dividend policies. Compare these cash flows to previous periods to identify trends, sustainability, and liquidity risks. Conclude with a concise analysis of the company's cash management effectiveness, liquidity position, and potential for future growth or financial challenges, all within 130 words."""

CASH_PROMPT_ZH = """对公司的现金流进行全面评估，重点关注经营、投资和融资活动。分析经营现金流以衡量核心业务盈利能力，检查投资活动以获取资本支出和投资见解，并审查融资活动以了解债务、股权变动和股息政策。将这些现金流与以前的时期进行比较，以识别趋势、可持续性和流动性风险。最后，简要分析公司的现金管理效果、流动性状况以及未来增长潜力或财务挑战，限于130字。"""

class FinancialsAnalyzer(BaseModel):
    def __init__(self, max_rounds=3, model_name="gpt-4", language='zh'):
        super().__init__(max_rounds=max_rounds, model_name=model_name, language=language)
        self.system_prompt = "You are a helpful assistant that answers questions about financials."
        
    def run(self, data):
        financials = data['financials']
        
        income = financials['stock_income']
        if self.language == 'zh':
            income_prompt = "分析日期:" + data["date"] + "\n\n" +"公司名称:" + data["company_name"] + "\n\n" + "季度损益表:\n" + income.to_string() + "\n\n\n" + "指示:\n" + INCOME_PROMPT_ZH 
        else:
            income_prompt = "Analysis Date: " + data["date"] + "\n\n" + "Company Name:" + data["company_name"] + "\n\n" +"Quarterly Income Statement Table:\n" + income.to_string() + "\n\n\n" + "Instructions:\n" + INCOME_PROMPT_EN
        income_response = self.model.simple_prompt(income_prompt)
        # income_response = ('贵州茅台在2024年第三季度实现总收入约396.7亿元，同比增长15.5%，环比增长7.3%。销售成本稳定，毛利率达91.2%，营业利润率和净利润率分别为66%和48.2%，显示出强劲的盈利能力。每股收益（EPS）未披露，但净利润持续增长。与历史数据相比，盈利能力稳步提升，显示出良好的成本控制和市场需求。与行业基准相比，茅台保持领先地位，尽管面临市场竞争和成本压力。', 2393, 126)
        print(income_response)
        with open('./prompt/income_prompt.txt', 'w') as f:
            f.write(income_prompt)
        
        balance = financials['stock_balance_sheet']
        if self.language == 'zh':
            balance_prompt = "分析日期:" + data["date"] + "\n\n" + "公司名称:" + data["company_name"] + "\n\n" + "资产负债表:\n" + balance.to_string() + "\n\n\n" + "指示:\n" + BALANCE_PROMPT_ZH
        else:
            balance_prompt = "Analysis Date: " + data["date"] + "\n\n" + "Company Name:" + data["company_name"] + "\n\n" + "Quarterly Balance Sheet:\n" + balance.to_string() + "\n\n\n" + "Instructions:\n" + BALANCE_PROMPT_EN
        balance_response = self.model.simple_prompt(balance_prompt)
        # balance_response = ('贵州茅台资产负债表显示其资产结构稳健，流动资产远超流动负债，流动性良好。长期债务较低，偿债能力强。股东权益持续增长，显示出强劲的长期投资潜力。与去年相比，资产和股东权益均有增长，表明财务状况改善。整体来看，公司财务健康，未来前景乐观。', 3218, 92)
        print(balance_response)
        with open('./prompt/balance_prompt.txt', 'w') as f:
            f.write(balance_prompt)
        
        cash = financials['stock_cash_flow']
        if self.language == 'zh':
            cash_prompt = "分析日期:" + data["date"] + "\n\n" + "公司名称:" + data["company_name"] + "\n\n" + "现金流表:\n" + cash.to_string() + "\n\n\n" + "指示:\n" + CASH_PROMPT_ZH
        else:
            cash_prompt = "Analysis Date: " + data["date"] + "\n\n" + "Company Name:" + data["company_name"] + "\n\n" + "Quarterly Cash Flow Table:\n" + cash.to_string() + "\n\n\n" + "Instructions:\n" + CASH_PROMPT_EN
        cash_response = self.model.simple_prompt(cash_prompt)
        # cash_response = ('贵州茅台的经营现金流表现强劲，显示核心业务盈利能力稳健。投资活动中资本支出增加，表明对未来增长的投入。融资活动现金流波动较大，主要受债务和股息支付影响。整体现金管理良好，流动性充足，但需关注融资活动的波动对未来财务稳定性的影响。', 1596, 82)
        print(cash_response)
        with open('./prompt/cash_prompt.txt', 'w') as f:
            f.write(cash_prompt)
            
        return income_response[0], balance_response[0], cash_response[0]
        
        