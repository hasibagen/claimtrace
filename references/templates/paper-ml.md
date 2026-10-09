---
use-case: ML
modality: ml
stage: ml
requires: []
optional: true
tags: [template, ml, machine-learning, feature-selection, classification, hyperparameter-tuning, leakage]
description: "机器学习论文抽取检查单：任务设定/特征工程/特征选择/模型与调参/验证设计与泄露防控/类别不平衡/指标/基线/可复现性 + 方法候选词表 + 数据泄露红旗清单"
---

<!-- 结构契约见 paper.md(frontmatter + 目录布局 + Evidence/Claims 两大嵌入章节);本文件提供 ml 叙事字段检查单。 -->
<!-- 适用:① 纯 ML 方法论文(modality=ml);② 任何模态论文的「数据分析」块含 ML 分类/解码管线时,该块按本检查单展开。 -->
<!-- 重要：LLM 抽取论文 L2/L3 之前，必走 `wiki zotero match` 找到 paperinfo 节点。paper frontmatter 必须含 `paperinfo: "[[paperinfo/<BBT-citekey>]]"`。 -->
<!-- 统计推断(置换检验/效应量)同嵌 paper_stats.md;本检查单的 ★ 三块(特征选择/调参/验证)是用户最关注的参考信息,必须详抽。 -->

# {Title}

**元信息**

- **作者**:
- **年份**:
- **期刊**:
- **DOI**:
- **类型**: 实证 / 方法 / 综述 / 基准测试(benchmark)
- **领域**: 机器学习（神经影像分类 / 通用方法）
- **modality**: ml（或 fnirs/eeg/fmri/multimodal + ML 管线）
- **paperinfo**: [[paperinfo/<BBT-citekey>]] （必加填、从 wiki zotero match 查到）

**研究目的**

（1-3 句话。解决什么分类/解码/方法问题；若为方法论文，点明相对已有方法的改进点。）

**任务设定**

- **任务类型**: 二分类 / 多分类 / 解码 / 跨被试 / 被试内 / BCI 在线-离线
- **分类标签**: （如 患者 vs 对照；任务 A vs B；类别数）
- **样本量**: 被试 n=… ；总样本/试次数=… ；每类样本数=…
- **数据来源**: 自采 / 公开数据集（列名：如 OpenNeuro / ABCD / BCI Competition IV / TUH / 干预数据集名）

**特征工程**

- **原始特征类型**: （HbO/HbR 通道均值峰值斜率 · EEG 频带功率/CSP/ERP 幅值 · 功能连接矩阵/边 · 体素/ROI · 时序窗）
- **特征提取方法**:
- **特征维度**: 原始 d=… → 提取后 d=…（维度/样本比 d:n 值得记录）
- **降维**: （PCA 保留成分数/方差比 · ICA · 自编码器 · 无）

**特征选择 ★**

- **方法**: （从下方词表选或照抄原文；多阶段组合写清顺序，如 t 检验预筛 → SVM-RFE）
- **位置**: **在 CV 训练折内执行（正确） / 在全量数据上先做再 CV（泄露） / 未说明**
- **保留特征数**: k=… 或比例；如何确定 k（固定 / CV 内优选 / 精度曲线拐点）
- **稳定性评估**: （多 seed 重采样一致性 / Stability Selection / 无）

**模型与超参数调优 ★**

- **模型清单**: （本文评估的全部模型；主打模型加粗）
- **超参数与搜索空间**: 逐模型列出调了哪些参数及取值范围（如 SVM: C∈{0.1,1,10}, γ∈{…}；LSTM: units/dropout/lr/…）
- **调优策略**: 网格 / 随机 / 贝叶斯(Optuna/hyperopt/skopt) / 进化 / 默认值不调
- **调参预算**: 试验次数 / 早停准则 / 内层 CV 折数
- **最终选定值**: （报告的最优超参数组合）

**验证设计与泄露防控 ★**

- **验证结构**: 嵌套 CV（外 k₁ 折 × 内 k₂ 折）/ k 折 CV / 留一（LOOCV/LOSO/LOUO）/ 固定 train-val-test 划分比例 / 重复次数与随机种子
- **划分单位**: **被试级（跨被试泛化） / 试次级（同一被试跨折 → 注明是否被试内泄露风险）**
- **泄露防控**: （标准化/特征选择/降维是否全部包在训练折内；pipeline 嵌套方式）
- **置换/显著性检验**: （置换次数 / binomial / McNemar / 置信区间 bootstrap）
- **泄露红旗**: 逐项核对本文件底部「数据泄露红旗清单」，发现即在此标注（无问题写"未见红旗"）

**类别不平衡**

- **不平衡比**: （类别样本比）
- **处理**: 类权重 / SMOTE / 欠采样-过采样 / 无

**评估指标**

- **主指标**: accuracy / balanced accuracy / F1 / AUC-ROC / AUC-PR
- **次指标**: sensitivity/specificity/precision-recall/混淆矩阵
- **报告形式**: 单次值 / 多次运行 均值±std / 逐被试分布

**结果**

（用原文 quote 嵌入关键数值，不要自己翻译）

- > "分类准确率 …%（SD=…）,高于 chance level …%（p=…, 置换检验）"（§3.x, p.x）
- > "SVM-RFE 保留 … 个特征时达到峰值性能 …%"（§3.x, p.x）

**基线对比**

- **对比模型**: （如 LDA/SVM/RF/CNN/LSTM；与本文方法的差距）
- **消融实验**: （去掉特征选择/换验证方式的性能变化）

**可复现性**

- **代码开源**: （GitHub/…；含 commit 或版本）
- **数据开源**: （OpenNeuro/OSF/Zenodo/…）
- **随机种子与硬件**: （训练时长/GPU 型号，如报告）
- **依赖锁定**: requirements/environment/Docker

**结论**（含作者自述局限性）

---

## 方法候选词表（识别用；论文用了词表外方法则照抄原文术语）

### 分类算法

- **传统 ML**: SVM（RBF/linear/poly）、LDA、逻辑回归（L1/L2）、KNN、朴素贝叶斯、决策树
- **集成**: 随机森林、AdaBoost、Gradient Boosting、XGBoost/LightGBM/CatBoost、Stacking
- **深度学习**: 1D/2D/3D-CNN、RNN/LSTM/GRU、Transformer/ViT、GNN（脑网络）、CNN+LSTM 混合、EEGNet 类 SOTA 网络、预训练+微调
- **迁移/域适应**: 跨被试迁移、CORAL/MMD、对抗训练、联邦学习

### 特征选择（三流派 + 深度）

- **Filter**: t 检验/ANOVA/F 检验、互信息-mRMR（Peng 2005）、Relief/ReliefF、方差阈值
- **Wrapper**: SVM-RFE（Guyon 2002）/RFECV、前向-后向序列选择、遗传算法
- **Embedded**: Lasso/L1、Elastic Net、树模型重要性、SHAP/Permutation Importance
- **深度**: 注意力权重、1×1 卷积通道压缩、自编码器、梯度显著性/Grad-CAM
- **稳定性**: Stability Selection（Meinshausen 2010）、多 seed 重采样

### 超参数调优

- 网格搜索 / 随机搜索 / 贝叶斯优化（skopt/hyperopt/Optuna） / 进化算法 / Hyperband-ASHA / 早停

### 验证设计

- k 折 / 分层 k 折 / 嵌套 CV / LOOCV / LOSO/LOUO（跨被试）/ 重复 k 折 / 置换检验 / bootstrap CI

### 工具

- scikit-learn / PyTorch / TensorFlow-Keras / MNE / nilearn / xgboost-lightgbm / imbalanced-learn / optuna-hyperopt / SHAP-LIME

---

## 数据泄露红旗清单（抽取时逐项核对；命中任何一条 → 写入「验证设计-泄露红旗」并在 claim 中保留为方法学观察）

1. **特征选择在 CV 外**：先在全数据上选特征再交叉验证评估
2. **标准化在 CV 外**：用全数据均值/方差做 z-score 后再划分
3. **降维在 CV 外**：PCA/ICA 在全数据拟合
4. **被试内泄露**：试次级划分且同一被试同时出现在训练与测试折（未做 LOSO）
5. **测试集调参**：超参数按测试集表现选取；或无独立测试集时反复汇报最优折
6. **预处理全量估计**：伪迹阈值/滤波参数/特征提取参数用全部数据估计
7. **数据增强泄露**：增强样本（如加噪副本）跨训练-测试划分
8. **重复样本未去重**：同一被试多 session/多版本条目混入划分

> 记录格式示例：`泄露红旗 #1：SVM-RFE 在全量 42 通道上先做，再 10 折 CV（§2.4）`
