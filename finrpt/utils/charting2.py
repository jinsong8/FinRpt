import os
# import mplfinance as mpf
import pandas as pd

from matplotlib import pyplot as plt
from typing import Annotated, List, Tuple
from pandas import DateOffset
from datetime import datetime, timedelta
from matplotlib.font_manager import FontProperties
import yfinance as yf
import pdb

# from ..data_source.yfinance_utils import YFinanceUtils

# def plot_stock_price_chart(
#     ticker_symbol: Annotated[
#         str, "Ticker symbol of the stock (e.g., 'AAPL' for Apple)"
#     ],
#     start_date: Annotated[
#         str, "Start date of the historical data in 'YYYY-MM-DD' format"
#     ],
#     end_date: Annotated[
#         str, "End date of the historical data in 'YYYY-MM-DD' format"
#     ],
#     save_path: Annotated[str, "File path where the plot should be saved"],
#     verbose: Annotated[
#         str, "Whether to print stock data to console. Default to False."
#     ] = False,
#     type: Annotated[
#         str,
#         "Type of the plot, should be one of 'candle','ohlc','line','renko','pnf','hollow_and_filled'. Default to 'candle'",
#     ] = "candle",
#     style: Annotated[
#         str,
#         "Style of the plot, should be one of 'default','classic','charles','yahoo','nightclouds','sas','blueskies','mike'. Default to 'default'.",
#     ] = "default",
#     mav: Annotated[
#         int | List[int] | Tuple[int, ...] | None,
#         "Moving average window(s) to plot on the chart. Default to None.",
#     ] = None,
#     show_nontrading: Annotated[
#         bool, "Whether to show non-trading days on the chart. Default to False."
#     ] = False,
# ) -> str:
#     """
#     Plot a stock price chart using mplfinance for the specified stock and time period,
#     and save the plot to a file.
#     """
#     # Fetch historical data
#     stock_data = YFinanceUtils.get_stock_data(ticker_symbol, start_date, end_date)
#     if verbose:
#         print(stock_data.to_string())

#     params = {
#         "type": type,
#         "style": style,
#         "title": f"{ticker_symbol} {type} chart",
#         "ylabel": "Price",
#         "volume": True,
#         "ylabel_lower": "Volume",
#         "mav": mav,
#         "show_nontrading": show_nontrading,
#         "savefig": save_path,
#     }
#     # Using dictionary comprehension to filter out None values (MplFinance does not accept None values)
#     filtered_params = {k: v for k, v in params.items() if v is not None}

#     # Plot chart
#     mpf.plot(stock_data, **filtered_params)

#     return f"{type} chart saved to <img {save_path}>"


def get_share_performance(
    data,
    stock_code,
    filing_date,
    save_path='./figs',
) -> str:
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
    info = get_stock_info(stock_code)

    company_change = (
        (target_close - target_close.iloc[0]) / target_close.iloc[0] * 100
    )
    csi300_change = (csi300_close - csi300_close.iloc[0]) / csi300_close.iloc[0] * 100

    start_date = company_change.index.min()
    four_months = start_date + DateOffset(months=4)
    eight_months = start_date + DateOffset(months=8)
    end_date = company_change.index.max()

    plt.rcParams.update({"font.size": 20})  
    plt.figure(figsize=(14, 7))
    plt.plot(
        company_change.index, company_change, label=f'{data["company_name"]} 增长率 %',color="blue")
    plt.plot(
        csi300_change.index, csi300_change, label="沪深300 增长率 %", color="red"
    )

    plt.title(f'{data["company_name"]} vs 沪深300 - 增长率 % 过去一年')
    plt.xlabel("日期")
    plt.ylabel("增长率 %")

    plt.xticks(
        [start_date, four_months, eight_months, end_date],
        [
            start_date.strftime("%Y-%m"),
            four_months.strftime("%Y-%m"),
            eight_months.strftime("%Y-%m"),
            end_date.strftime("%Y-%m"),
        ],
    )

    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    # plt.show()
    plot_path = (
        f"{save_path}/share_performance.png"
        if os.path.isdir(save_path)
        else save_path
    )
    plt.savefig(plot_path)
    plt.close()
    return f"last year stock performance chart saved to <img {plot_path}>"


def get_pe_eps_performance(
    data,
    stock_code,
    filing_date,
    years=4,
    save_path='./figs',
) -> str:
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
    
    
    info = yf.Ticker(stock_code).info

    fig, ax1 = plt.subplots(figsize=(14, 7))
    plt.rcParams.update({"font.size": 20}) 

    color = "tab:blue"
    ax1.set_xlabel("日期")
    ax1.set_ylabel("PE", color=color)
    ax1.plot(dates, pe, color=color)
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.grid(True)

    ax2 = ax1.twinx()
    color = "tab:red"
    ax2.set_ylabel("EPS", color=color)  
    ax2.plot(dates, eps, color=color)
    ax2.tick_params(axis="y", labelcolor=color)

    plt.title(f'{data["company_name"]} PE & EPS 过去{years}年')
    plt.xticks(rotation=45)

    plt.xticks(dates, [d.strftime("%Y-%m") for d in dates])

    plt.tight_layout()
    plot_path = (
        f"{save_path}/pe_eps.png" if os.path.isdir(save_path) else save_path
    )
    plt.savefig(plot_path)
    plt.close()
    return f"pe performance chart saved to <img {plot_path}>"


if __name__ == "__main__":
    date = '2024-10-29'
    data = {
        "company_name": "贵州茅台"
    }
    get_share_performance(data, '600519.SS', filing_date=date)
    get_pe_eps_performance(data, '600519.SS', filing_date=date)
