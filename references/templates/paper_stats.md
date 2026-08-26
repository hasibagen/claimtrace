---
use-case: statistics
modality: meta
stage: stats
requires: []
optional: true
description: "统计方法：假设检验(参数/非参数/置换)+效应量+多重比较(FWE/FDR/cluster)+神经影像特异(嵌套CV/置换检验/混合效应)+贝叶斯"
---

# 统计方法子模板

> 用法：在主模板 `paper.md` 的「数据分析」块下嵌入本文件，按需填写。
> 
> 当论文使用机器学习时，请同时嵌入 `paper_ml.md`（ML 方法独立成块）。

- **软件**: （R / Python statsmodels / JASP / SPSS / MATLAB / Stata）

## 假设检验

### 参数检验

- **t 检验**: （单样本 / 独立样本 / 配对样本）
- **ANOVA**: （单因素 / 重复测量 / 混合模型 / 多因素）
- **回归**: （线性 / 多元 / logistic / 多项式）
- **相关**: （Pearson / Spearman / Kendall）
- **协方差分析（ANCOVA）**: （如适用）

### 非参数检验

- **Mann-Whitney U / Wilcoxon 符号秩**: （独立/配对样本）
- **Kruskal-Wallis / Friedman**: （多组/重复测量）
- **置换检验（Permutation Test）**: （神经影像常用，见 Varoquaux 2017）
- **秩和检验**: 

## 效应量与置信区间

- **Cohen's d / Hedges' g**: （组间差异）
- **η² / partial η²**: （ANOVA）
- **r² / R² / adjusted R²**: （回归）
- **Cramér's V / Phi**: （分类变量）
- **95% 置信区间**: （所有效应量都应报告 CI）
- **贝叶斯证据**: （BF₁₀ / BF₀₁；如适用）

## 多重比较校正

- **FWE**: （Bonferroni / Holm-Bonferroni / max-T）
- **FDR**: （Benjamini-Hochberg / Benjamini-Yekutieli）
- **cluster-based**: （cluster-defining threshold + cluster-level p）
- **TFCE**: （threshold-free cluster enhancement）
- **FDR**: （在 fMRI 中常用）

## 神经影像特异

### 嵌套交叉验证（Nested CV）

> 避免数据泄露，是脑解码研究的标准做法。

- **结构**: （外层 K 折评估泛化性能 + 内层 K' 折做超参数/特征选择）
- **LOUO / LOSO**: （Leave-One-[Subject/Out]-Subject-Out，适合小样本）
- **数据泄露检查**: （特征选择、标准化必须放在 CV 内）

### 置换检验

- **零分布**: （打乱标签 / 自旋检验 spin test / 时间块置换）
- **迭代次数**: （如 1000 / 5000 / 10000）
- **多重比较**: （maxT / minP / TFCE）

### 群体推断（Group-level Inference）

- **混合效应模型（Mixed-Effects）**: （截距随机 / 斜率随机）
- **FLAME / OLS**: （fMRI 群体推断）
- **贝叶斯层次模型**: （如适用）

## 贝叶斯统计

- **Bayes 因子**: （BF₁₀ / BF₀₁；通过 ROPE + BF 解释）
- **贝叶斯回归**: （先验 + 后验 + 95% HDI）
- **贝叶斯层次模型**: （fNIRS/EEG 群体分析）

## 工具与可重复性

- **分析脚本**: （GitHub / OSF / Zenodo）
- **种子固定**: （set.seed / numpy seed）
- **依赖版本**: （renv / requirements.txt / conda env）
- **预注册**: （OSF / AsPredicted；如适用）