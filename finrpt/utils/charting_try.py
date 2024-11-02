import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.ticker as ticker
import pdb

plt.rcParams['font.family'] = 'SimSun'

dates = pd.date_range(start='2023-09-01', end='2024-09-01', freq='D')

np.random.seed(0)
data_biyadi = np.cumsum(np.random.randn(len(dates)) * 0.5)
data_hushen300 = np.cumsum(np.random.randn(len(dates)) * 0.5)

df = pd.DataFrame({'Date': dates, '比亚迪': data_biyadi, '沪深300': data_hushen300})
df.set_index('Date', inplace=True)

plt.figure(figsize=(10, 6))
plt.plot(df.index, df['比亚迪'], label='比亚迪', color='#9E1F00', linewidth=4)
plt.plot(df.index, df['沪深300'], label='沪深300', color='#d45716', linewidth=4)


# plt.legend(loc='lower center', ncol=2, frameon=False, fontsize=12)
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=18, handlelength=5, frameon=False, labelcolor='#6a6a6a')

plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}%'))

plt.grid(visible=False)

ax = plt.gca()
ax.set_xlim(df.index.min(), df.index.max()) 
ax.spines['left'].set_linewidth(3)
ax.spines['bottom'].set_linewidth(3)
ax.spines['bottom'].set_color('#6a6a6a')
ax.spines['left'].set_color('#6a6a6a')
ax.spines['top'].set_color('none')
ax.spines['right'].set_color('none')

ax.tick_params(axis='x', colors='#6a6a6a', labelsize=17, width=3, length=5)
ax.tick_params(axis='y', colors='#6a6a6a', labelsize=17, width=3, length=5)

plt.tight_layout()
plt.show()
plt.savefig('./test.png')
