import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
import yfinance as yf
import pdb

data = yf.Ticker('300750.SZ').quarterly_income_stmt.loc['Operating Income'][:4]
revenue = data[::-1]
revenue = revenue // 1e8
yoy = (revenue - revenue.iloc[0]) / revenue.iloc[0] * 100
quarters = revenue.index

plt.rcParams['font.family'] = 'SimSun' 

fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.bar(quarters, revenue, color='#9E1F00', label='营业收入（亿元）', width=15)
ax1.set_xticks(quarters)
# ax1.set_xticklabels(quarters, rotation=45)
ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
ax1.tick_params(axis='y', labelcolor='#6a6a6a', labelsize=21, width=3, length=5, direction='in')
ax1.tick_params(axis='x', colors='#6a6a6a', labelsize=21)
ax1.spines['top'].set_visible(False)

ax2 = ax1.twinx()
ax2.plot(quarters, yoy, color='#d45716', label='yoy')
ax2.tick_params(axis='y', labelcolor='#6a6a6a', labelsize=21, width=3, length=5, direction='in')
ax2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{int(y)}%'))
ax2.spines['top'].set_visible(False)

ax1.legend(loc='upper center', bbox_to_anchor=(0.3, -0.1), ncol=2, fontsize=22, handlelength=5, frameon=False, labelcolor='#6a6a6a')
ax2.legend(loc='upper center', bbox_to_anchor=(0.75, -0.1), ncol=2, fontsize=22, handlelength=5, frameon=False, labelcolor='#6a6a6a')

plt.tight_layout()
plt.show()

plt.savefig('test.png')