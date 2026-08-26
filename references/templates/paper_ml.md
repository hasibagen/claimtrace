---
use-case: ML
modality: meta
stage: ml
requires: []
optional: true
tags: [template, ml, machine-learning, feature-selection, classification, deep-learning]
overlaps: [paper_stats.md#置换检验]
description: "机器学习方法：特征选择(Filter/Wrapper/Embedded/深度学习)+分类(SVM/RF/KNN/深度学习)+回归+聚类+降维+迁移学习+集成+模型评估+工具"
---

# 机器学习方法子模板

> 用法：在主模板 `paper.md` 的「数据分析」块下嵌入本文件，按需填写。
> 
> 统计推断（显著性检验、置换检验、嵌套 CV 等）请同时嵌入 `paper_stats.md`。

- **任务类型**: （分类 / 回归 / 聚类 / 降维 / 解码 / 生成）
- **工具**: （scikit-learn / PyTorch / TensorFlow / MNE / xgboost / lightgbm / nilearn）

## 特征选择

> 参考 Mwangi 2014 神经影像特征选择综述；多阶段组合效果最佳。

### Filter 方法（过滤式）

- **单变量统计**: （t 检验 / ANOVA / Pearson 相关）
- **互信息 / mRMR**: （Peng 2005，最小冗余最大相关）
- **Relief / ReliefF**: （基于最近邻特征评估）
- **方差阈值 / F 检验**: （sklearn SelectKBest）

### Wrapper 方法（包裹式）

- **递归特征消除（RFE）**: （sklearn RFECV）
- **SVM-RFE**: （Guyon 2002 原始论文）
- **前向/后向选择**: （sequential feature selector）
- **遗传算法**: （如适用）

### Embedded 方法（嵌入式）

- **L1 正则化**: （Lasso / L1-SVM）
- **Elastic Net**: （L1+L2 组合）
- **树模型重要性**: （RF / XGBoost feature importance）
- **SHAP / Permutation Importance**: （事后可解释性）

### 深度学习特征选择

- **注意力机制**: （Transformer attention weights）
- **1×1 卷积**: （特征通道压缩）
- **自编码器表示学习**: （降维后分类）
- **梯度显著性 / Grad-CAM**: （可解释性）

### 稳定性选择

- **Stability Selection**: （Meinshausen 2010）
- **多 seed 重采样**: 

## 分类算法

### 传统机器学习

- **SVM**: （RBF / linear / polynomial kernel；最常用 154 篇/400）
- **随机森林（RF）**: （集成树模型，n_estimators / max_depth）
- **KNN**: （k 值选择 / 距离度量）
- **朴素贝叶斯（NB）**: （高斯 / 多项式 / 伯努利）
- **决策树**: （CART / C4.5 / ID3）
- **Logistic 回归**: （含 L1/L2 正则化）

### 集成学习

- **Bagging**: （Bootstrap Aggregating）
- **Boosting**: （AdaBoost / Gradient Boosting）
- **XGBoost / LightGBM / CatBoost**: （梯度提升树）
- **Stacking**: （多层模型堆叠）

### 深度学习

- **CNN**: （1D-CNN / 2D-CNN / 3D-CNN；用于时序/图像）
- **RNN / LSTM / GRU**: （序列建模）
- **Transformer**: （含 ViT / BERT 类；attention-based）
- **GNN（图神经网络）**: （用于脑网络/图结构数据）
- **混合架构**: （CNN+LSTM / CNN+Transformer）
- **预训练 + 微调**: （如适用）

## 回归算法

- **线性回归 / Ridge / Lasso / Elastic Net**
- **多项式回归 / 样条回归**
- **SVR（支持向量回归）**: （RBF / linear kernel）
- **树回归**: （RF Regressor / XGBoost Regressor）
- **深度回归**: （MLP / 1D-CNN）

## 聚类

- **K-means / K-medoids**
- **层次聚类**: （agglomerative / divisive）
- **DBSCAN / OPTICS**: （密度聚类）
- **谱聚类**: （用于功能连接矩阵）
- **高斯混合模型（GMM）**: 
- **评估指标**: （轮廓系数 / Calinski-Harabasz / Davies-Bouldin）

## 降维

- **PCA**: （主成分分析）
- **ICA**: （独立成分分析；含组 ICA）
- **LDA**: （线性判别分析，监督）
- **t-SNE / UMAP**: （可视化）
- **自编码器**: （深度降维）

## 迁移学习与领域适应

- **跨被试迁移**: （subject-independent / subject-adaptive）
- **领域适应**: （对抗训练 / CORAL / MMD）
- **联邦学习**: （多中心数据）
- **预训练 + 微调**: （如适用）

## 模型评估与验证

### 交叉验证

- **K 折 CV**: （K=5/10）
- **分层 K 折**: （类别平衡）
- **留一法（LOOCV / LOUO / LOSO）**: （小样本）
- **重复 K 折**: （多次随机化）
- **嵌套交叉验证**: （避免数据泄露，**神经影像必备**）

### 评估指标

- **分类**: （accuracy / precision / recall / F1 / AUC-ROC / AUC-PR / 混淆矩阵）
- **回归**: （MSE / MAE / R² / Pearson r）
- **平衡指标**: （balanced accuracy / macro-F1）
- **显著性**: （置换检验 / 二项检验 / McNemar → paper_stats.md#置换检验）

### 模型选择

- **超参数调优**: （Grid Search / Random Search / Bayesian Optimization）
- **验证集划分**: （train / val / test）
- **早停（early stopping）**: （深度学习）

## 工具与库

- **scikit-learn**: （传统 ML 一站式）
- **PyTorch / TensorFlow / Keras**: （深度学习）
- **MNE / MNE-Python**: （EEG/MEG 专用）
- **nilearn**: （神经影像专用）
- **xgboost / lightgbm / catboost**: （梯度提升）
- **imbalanced-learn**: （类别不平衡）
- **optuna / hyperopt**: （超参数优化）
- **SHAP / LIME**: （可解释性）

## 可重复性

- **代码公开**: （GitHub / GitLab）
- **数据公开**: （OpenNeuro / OSF / Zenodo）
- **容器化**: （Docker / Singularity）
- **依赖锁定**: （requirements.txt / environment.yml）
- **预注册**: （OSF / AsPredicted）