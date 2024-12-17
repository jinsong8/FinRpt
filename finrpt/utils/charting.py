import os
# import mplfinance as mpf
import pandas as pd

from matplotlib import pyplot as plt
from typing import Annotated, List, Tuple
from pandas import DateOffset
from datetime import datetime, timedelta
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FuncFormatter
import yfinance as yf
import numpy as np
import pdb


def get_share_performance(
    data,
    stock_code,
    filing_date,
    save_path='./figs'):
    plt.rcParams['font.family'] = 'SimSun' 
    
    if isinstance(filing_date, str):
        filing_date = datetime.strptime(filing_date, "%Y-%m-%d")

    def fetch_stock_data(ticker):
        start = (filing_date - timedelta(days=365)).strftime("%Y-%m-%d")
        end = filing_date.strftime("%Y-%m-%d")
        ticker = yf.Ticker(ticker)
        historical_data = ticker.history(start=start, end=end)
        return historical_data["Close"]
    
    def get_stock_info(ticker):
        ticker = yf.Ticker(ticker)
        return ticker.info

    target_close = fetch_stock_data(stock_code)
    csi300_close = fetch_stock_data("000300.SS")

    company_change = (
        (target_close - target_close.iloc[0]) / target_close.iloc[0] * 100
    )
    csi300_change = (csi300_close - csi300_close.iloc[0]) / csi300_close.iloc[0] * 100

    plt.figure(figsize=(10, 6))
    plt.plot(company_change.index, company_change, label=data["company_name"], color='#9E1F00', linewidth=6)
    plt.plot(company_change.index, csi300_change, label='沪深300', color='#d45716', linewidth=6)

    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=22, handlelength=5, frameon=False, labelcolor='#6a6a6a')

    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}%'))

    plt.grid(visible=False)

    ax = plt.gca()
    # ax.set_xlim(company_change.index.min(), company_change.index.max()) 
    ax.spines['left'].set_linewidth(3)
    ax.spines['bottom'].set_linewidth(3)
    ax.spines['bottom'].set_color('#6a6a6a')
    ax.spines['left'].set_color('#6a6a6a')
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')

    ax.tick_params(axis='x', colors='#6a6a6a', labelsize=21, width=3, length=5)
    ax.tick_params(axis='y', colors='#6a6a6a', labelsize=21, width=3, length=5)

    plt.tight_layout()
    
    plot_path = (
    f"{save_path}/share_performance.png"
    if os.path.isdir(save_path)
    else save_path)
    plt.savefig(plot_path)
    plt.close()


def get_pe_eps_performance(
    data,
    stock_code,
    filing_date,
    years=4,
    save_path='./figs'):
    plt.rcParams['font.family'] = 'SimSun'
    
    if isinstance(filing_date, str):
        filing_date = datetime.strptime(filing_date, "%Y-%m-%d")
        
    def get_income_stmt(ticker_symbol):
        ticker = yf.Ticker(ticker_symbol)
        income_stmt = ticker.financials
        return income_stmt

    ss = get_income_stmt(stock_code)
    eps = ss.loc["Diluted EPS", :]

    days = round((years + 1) * 365.25)
    start = (filing_date - timedelta(days=days)).strftime("%Y-%m-%d")
    end = filing_date.strftime("%Y-%m-%d")
    historical_data = yf.Ticker(stock_code).history(start=start, end=end)
    
    dates = pd.to_datetime(eps.index[::-1], utc=True)

    results = {}
    for date in dates:
        if date not in historical_data.index:
            close_price = historical_data.asof(date)
        else:
            close_price = historical_data.loc[date]
        results[date] = close_price["Close"]

    pe = [p / e for p, e in zip(results.values(), eps.values[::-1])]
    dates = eps.index[::-1]
    eps = eps.values[::-1]
    
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(dates, pe, label="PE", color='#9E1F00', linewidth=6)
    ax1.set_ylabel('PE', color='#9E1F00', fontsize=21, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#9E1F00', labelsize=21, width=3, length=5)
    ax1.tick_params(axis='x', colors='#6a6a6a', labelsize=21, width=3, length=5)
    ax1.set_xticks(dates)
    
    ax2 = ax1.twinx()
    ax2.plot(dates, eps, label="EPS", color='#d45716', linewidth=6)
    ax2.set_ylabel('EPS', color='#d45716', fontsize=21, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#d45716', labelsize=21, width=3, length=5)
    

    ax1.legend(loc='upper center', bbox_to_anchor=(0.3, -0.1), ncol=2, fontsize=22, handlelength=5, frameon=False, labelcolor='#6a6a6a')
    ax2.legend(loc='upper center', bbox_to_anchor=(0.7, -0.1), ncol=2, fontsize=22, handlelength=5, frameon=False, labelcolor='#6a6a6a')

    plt.grid(visible=False)

    plt.tight_layout()
    
    plot_path = (
        f"{save_path}/pe_eps.png"
        if os.path.isdir(save_path)
        else save_path)
    plt.savefig(plot_path)
    plt.close()
    

def get_revenue_performance(
    res_data,
    stock_code,
    filing_date,
    save_path='./figs'):
    data = res_data['financials']['stock_income']['营业总收入']
    revenue = data[::-1]
    revenue = revenue // 1e8
    yoy = (revenue - revenue.iloc[0]) / revenue.iloc[0] * 100
    quarters = res_data['financials']['stock_income']['日期'][::-1]
    new_quarters = []
    for i, quarter in enumerate(quarters):
        new_quarter = quarter[:4] + '-' + quarter[4:6] 
        new_quarters.append(new_quarter)
    quarters = new_quarters
    
    plt.rcParams['font.family'] = 'SimSun' 

    fig, ax1 = plt.subplots(figsize=(10, 6))
 
    ax1.bar(list(quarters)[-4:], list(revenue)[-4:], color='#9E1F00', label='营业收入（亿元）', width=0.2)
    ax1.set_xticks(quarters)
    # ax1.set_xticklabels(quarters, rotation=45)
    # ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
    ax1.tick_params(axis='y', labelcolor='#6a6a6a', labelsize=21, width=3, length=5, direction='in')
    ax1.tick_params(axis='x', colors='#6a6a6a', labelsize=21)
    ax1.spines['top'].set_visible(False)

    ax2 = ax1.twinx()
    ax2.plot(list(quarters)[-4:], list(yoy)[-4:], color='#d45716', label='yoy')
    ax2.tick_params(axis='y', labelcolor='#6a6a6a', labelsize=21, width=3, length=5, direction='in')
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{int(y)}%'))
    ax2.spines['top'].set_visible(False)

    ax1.legend(loc='upper center', bbox_to_anchor=(0.3, -0.1), ncol=2, fontsize=22, handlelength=5, frameon=False, labelcolor='#6a6a6a')
    ax2.legend(loc='upper center', bbox_to_anchor=(0.75, -0.1), ncol=2, fontsize=22, handlelength=5, frameon=False, labelcolor='#6a6a6a')

    plt.tight_layout()
    plot_path = (
    f"{save_path}/revenue_performance.png"
    if os.path.isdir(save_path)
    else save_path)
    plt.savefig(plot_path)
    plt.close()
    


if __name__ == "__main__":
    date = '2024-10-29'
    data = {
        "company_name": "贵州茅台"
    }
    get_revenue_preformanace(data, '600519.SS', date)
