# DISCO: Accurate and Reliable Stock Recommendation based on Causal Discovery and Dynamic Risk Modeling

>The stock recommendation has been widely studied in quantitative investment. Prevalent stock recommendation methods take multi-stock historical price features as input, model the correlation relations among stocks, and generate a ranking list of stocks to maximize investors' profits. Many problems in existing works are widely ignored. On the one hand, given that the relations in the stock market are often unidirectional, such as supplier-consumer, the correlation relation discovered in previous works does not accurately depict the market information flow. On the other hand, most previous methods overlook risk assessments, which may lead to intolerable losses in practical stock investing. Lastly, the single-time inference utilized by current methods is not practical for real-world stock market evaluation. In this paper, we propose an accurate and reliable stock recommendation method named DISCO. DISCO employs the causal discovery method and temporal Functional Causal Model (FCM) to discover and utilize the temporal causal graph. Simultaneously, in FCM, the risk is treated as a stochastic component disentangled from the market influences from other stocks. Thus causal discovery and dynamic risk modeling are tightly integrated into FCM to address the first two problems. At the inference stage, for a more comprehensive assessment of the recommendation result, we design a multi-situation inference strategy taking into account possible market situations. Based on these advantages, DISCO becomes an accurate, reliable, and comprehensive market evaluator. Experiments on three real-world stock markets indicate the superior profitability and risk assessment capability of DISCO.

<div align="center">
<img align="center" src="assets/model.jpg" width="90%"/>
</div>


## 🗂️ Preparation

**Datasets for [NASDAQ] and [NYSE]**:

We adopt the data preprocessing from [RSR](https://github.com/fulifeng/Temporal_Relational_Stock_Ranking). You can download all files into the `./data/rsr` directory from their github website.

**Dataset for [TSE]**:

We download data of [Tokyo Stock Exchange](https://www.jpx.co.jp/english/) top 100 stocks from yfiance. We preprocess the data like [RSR](https://github.com/fulifeng/Temporal_Relational_Stock_Ranking) and construct the dataset. You need put the data into `./data/tse` directory.

## 🕹️ Environment Setup

1. Create a new virtual environment
```
conda create --name disco python=3.10
conda activate disco
```
2. Install requirement packages:

```
pip install -r requirements.txt
```

## 🔧 Running

1. Run main experiment:
```
sh scripts/run_.sh
```
2. Run all experiments for [NASDAQ]

```
sh scripts/ablation_nasdaq.sh
```
3. Run all experiments for [NYSE]
```
sh scripts/ablation_nyse.sh
```
4. Run all experiments for [TSE]
```
sh scripts/ablation_tse.sh
```
5. Run all ablation experiments for lag variable:
```
sh scripts/ablation_lag.sh
```
6. Run all ablation experiments for samples_per_graph and Nsamples variables:
```
sh scripts/ablation_MN.sh
```
7. Run all ablation experiments for most_likely_graph variable:
```
sh scripts/most_likely_graph.sh
```

## 🌹 Acknowledgmentsons

This project was adapted from [Rhino](https://github.com/microsoft/causica) and [RSR](https://github.com/fulifeng/Temporal_Relational_Stock_Ranking) repo. Special thanks for providing the foundation for this work.

## 📚 License

This code is distributed under an [MIT LICENSE]. Note that our code depends on other libraries and datasets which each have their own respective licenses that must also be followed.
