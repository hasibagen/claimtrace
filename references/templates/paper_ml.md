---
use-case: ML
modality: ml
stage: ml
requires: [paper.md]
optional: true
tags: [template, ml, machine-learning, prediction, regression, continuous-outcome, scale-score]
overlaps: [paper_stats.md#置换检验]
description: "机器学习预测论文(神经影像→量表得分/连续变量)专用叙事模板:预测目标/数据集/输入特征/模型与防泄露/回归评估/可解释性/临床落地;附方法候选清单"
---

# 机器学习预测论文模板（神经影像 → 量表得分/连续变量）

> 用法：主模板 `paper.md` 提供结构契约（frontmatter + 目录布局 + Evidence/Claims 两大嵌入章节），本文件 = ML 论文叙事字段检查单。
>
> 适用：神经影像（fNIRS/EEG/fMRI/MEG/PET）+ 机器学习/深度学习 **预测连续结局**（量表得分 HDRS/PHQ/MMSE/MoCA/FMA/NIHSS、行为得分、脑龄等）。
> 纯方法学、分类任务或聚类论文按需删减；统计推断（置换检验等）见 `paper_stats.md`。

# {Title}

**元信息**

- **作者**:
- **年份**:
- **期刊**:
- **DOI**:
- **类型**: 实证（ML 预测）
- **领域**: 神经影像机器学习
- **modality**: ml（方法侧） + 数据模态（fnirs/eeg/fmri/multimodal）
- **paperinfo**: [[paperinfo/<BBT-citekey>]]（必填，`wiki zotero match` 查到）

**研究目的**

（1-3 句。这篇研究要预测什么、给谁用、临床动机——辅助诊断/疗效评估/预后/筛查。）

**预测目标**

- **目标变量**: （量表名+连续得分 / 行为指标 / 脑龄等；注明连续 or 按 cutoff 二分类）
- **目标来源**: （量表版本、评定者、时间点——基线/治疗后/随访）
- **任务类型**: 回归 / 分类（注明 cutoff 值）/ 两者

**数据集与被试**

- **n**: （训练/验证/测试各自 n；患者/健康对照分组）
- **人群**: （诊断、年龄、采集中心——单中心/多中心、公开数据集还是自采）
- **目标分布**: （均值±SD / range / 偏态与否；影响回归指标解读）
- **划分方式**: （LOSO/LOUO/K 折/嵌套 CV/独立外部测试集）

**输入特征**（神经影像侧）

- **特征类型**: （时域/频域/功能连接/脑网络拓扑/影像组学/深度学习自动特征）
- **维度 vs 样本量**: （特征数、是否维度灾难、降维或选择策略）
- **协变量处理**: （年龄/性别/头动——回归掉还是纳入特征，是否可能预测的是协变量）

**模型与训练**

- **算法**: （SVR/RF/XGBoost/MLP/CNN/Transformer/GNN/多模态融合；对比了哪些）
- **超参数调优**: （Grid/Random/贝叶斯/optuna；在嵌套结构的哪一层）
- **数据泄露防护**（逐项核对，缺失即记录为风险点）:
  - 特征选择/降维是否在 CV 折内完成
  - 标准化/归一化是否仅用训练折拟合
  - 划分是否被试级（同一被试数据不跨 train/test）
  - 目标衍生变量是否混入特征（目标泄露）

**性能评估**（回归为主）

- **主指标**: （R² / Pearson r / RMSE / MAE / MAPE，含置信区间或跨折 SD）
- **一致性**: （Bland-Altman / ICC；与 MCID 最小临床重要差异的关系）
- **显著性**: （置换检验 / 与空模型或临床基线（仅量表）比较）
- **分类补充**: （AUC / balanced accuracy / sensitivity / specificity，注明 cutoff）

**可解释性**

- **方法**: （SHAP / LIME / Grad-CAM / 权重图 / permutation importance）
- **神经科学解释**: （重要性落在哪些脑区/频段/连接；与既有文献一致性）
- **稳定性**: （跨折/跨 seed 的特征重要性是否一致）

**结果**

（嵌原文 quote + 统计值；核心数值必须可 grep：最优模型 + 指标 + CI。）

**结论与局限**

- **结论**: （作者声称的预测能力 + 本文实际支持的程度，claim 与作者结论分开）
- **局限**: （样本量/单中心/无外部验证/过拟合风险/泄露风险/计算成本）
- **临床落地**: （部署形态——云端/边缘/实时性；是否公开代码与模型）

---

## 附录：方法候选清单（抽取时对照识别，不逐条罗列进正文）

### 特征选择

- **Filter**: t 检验/ANOVA/Pearson、互信息 mRMR（Peng 2005）、ReliefF、方差阈值（sklearn SelectKBest）
- **Wrapper**: RFE/SVM-RFE（Guyon 2002）、前向/后向选择、遗传算法
- **Embedded**: Lasso/L1-SVM、Elastic Net、树模型重要性、SHAP/permutation importance
- **深度学习侧**: 注意力权重、1×1 卷积、自编码器表示、Grad-CAM
- **稳定性选择**: Stability Selection（Meinshausen 2010）、多 seed 重采样

### 回归算法

- 线性/Ridge/Lasso/Elastic Net、多项式/样条
- SVR（RBF/linear）、RF Regressor、XGBoost/LightGBM Regressor
- 深度回归：MLP、1D-CNN、LSTM、Transformer、GNN（脑网络）

### 分类算法（对照识别用）

- 传统：SVM（最常用）/RF/KNN/NB/决策树/Logistic（L1/L2）
- 集成：Bagging/AdaBoost/GBDT（XGBoost/LightGBM/CatBoost）/Stacking
- 深度：CNN（1D/2D/3D）、RNN/LSTM/GRU、Transformer/ViT、混合架构、预训练+微调

### 降维与迁移

- PCA/ICA（含组 ICA）/LDA/t-SNE/UMAP（仅可视化）/自编码器
- 跨被试迁移、领域适应（CORAL/MMD/对抗）、联邦学习（多中心）

### 交叉验证与调优

- K 折/分层 K 折/重复 K 折/LOOCV/LOSO/LOUO/**嵌套 CV（神经影像小样本必备）**
- Grid/Random/贝叶斯调参、early stopping

### 工具与可重复性

- scikit-learn、PyTorch/TensorFlow、MNE、nilearn、xgboost/lightgbm、imbalanced-learn、optuna、SHAP/LIME
- 代码（GitHub）/数据（OpenNeuro/OSF/Zenodo）/容器（Docker）/预注册
