---
name: wiki-extract-modeling
description: >-
  DEEP-READ one modeling/surrogate-brain paper (代理脑/数字孪生/全脑模拟/神经质量/
  超网络/DCM 拟合) through the training-validation-test protocol lens, producing a
  didactic 拆解 with a standardized mermaid pipeline. 输出三落位:① paper 节点新增
  `## 建模拆解` 叙事章节(三层讲解 + mermaid,按 templates/paper-modeling.md 检查单);
  ② 达到标准的方法学命题建 claim/evidence;③ syntheses/孪生脑多维框架.md 维度十三
  协议表补行. Use when user says "建模拆解 [论文]" or asks "这篇怎么训练的/怎么验证的"
  or "/modeling <citekey>" on a modeling paper. NOT for 分类解码管线(走 wiki-extract-paper
  + paper-ml.md), NOT for 新论文全量抽取(先走 wiki-extract-paper,再叠加本拆解).
---

# Wiki Extract Modeling(建模论文拆解)

把一篇建模/代理脑论文按「训练协议 - 保真度验证 - 外推测试」三层拆开,写成深入浅出的
`## 建模拆解` 章节,配上标准化 mermaid 流程图,并回流 claim 与合成页。

## 为什么单独立这个 Skill

维度十三(训练与验证协议)暴露的缺口:论文节点现有的「核心方法」「测量工具」段落只回答
"用了什么",不回答"**怎么训练的、凭什么说它是合格的脑替身、外推到哪还成立**"。用户在
Luo 2025 NPI 上被迫手工还原训练-验证-测试链路,说明抽取粒度不够。本 Skill 把这条链路
固化成检查单与图式,让每篇建模论文都产出可跨篇对照的协议描述。

## 何时使用

| 触发 | 场景 |
|---|---|
| `建模拆解 [citekey/full.md]` / `/modeling <citekey>` | 对已 promote 的建模论文补拆解 |
| 抽取中识别 study_type 含 computational_modeling | wiki-extract-paper T2 完成后自动叠加 |
| 用户问 "这篇怎么训练的/怎么验证的/怎么测试的" | 先拆解再回答,拆解即沉淀 |

前置判断:论文属于建模管线(数据→动力学模型→虚拟实验)而非分类解码管线(特征→标签)?
前者用本 Skill(paper-modeling.md),后者用 paper-ml.md;两者兼有则两单都过。

## 标准作业流程 M0-M5

```
M0 定位原文   找到 raw/<citekey>/full.md;确认是建模论文(方法+补充材料里必有
              训练/拟合/优化段落);读 templates/paper-modeling.md 全文作为字段契约
M1 协议还原   只从原文(含 Methods/Supplementary)逐项核实 ★ 三块:
              · 训练协议:数据窗口、学习任务、损失、训练单位(逐被试/群体)、
                优化配置、切分方式——**切分方式原文没写也要如实记"未声明"**
              · 保真度验证:验证什么统计量、在谁的数据上算(训练批/held-out/外部)、数值
              · 外推测试:外推方向(维度十三六分类)、ground truth 类型、数值
              每个数值带回 §/Fig 定位;禁止从二手转述(综述/摘要)补协议细节
M2 深入浅出   按 paper-modeling.md 第八节写三层讲解(比喻层/机制层/协议层)。
              自检:一个没读过原文的研究生读完机制层,能复述"喂什么→学什么→
              怎么确认学像了→怎么用它做真脑做不了的实验"四问,才算合格
M3 mermaid    按 paper-modeling.md 第九节+汇总约定画流程图:八个标准阶段名不得改,
              缺的阶段删节点;细节进节点、关键参数上边;Obsidian 原生渲染 mermaid
M4 三落位     ① paper 节点:在叙事段(渲染器管理段之外)插入 `## 建模拆解` 章节
                 (建议放「测量与分析工具」之后、「主要结果」之前),含八-十节全部内容
              ② claim 判定:方法学命题(如"NPI 框架对代理模型架构鲁棒")达到
                 "可被后续论文支持或反驳"标准才建 claim(走 claim.md 契约);
                 协议描述本身是事实陈述,默认不建 claim
              ③ 合成页:syntheses/孪生脑多维框架.md 维度十三对应外推方向补一行
                 (论文 | 训练窗口 | 验证 | 测试目标),并核对是否刷新该节空白论断
M5 红旗核对   paper-modeling.md 红旗清单逐项过;命中的写进拆解章节末尾,
              多篇复现的红旗(如"随机洗牌切分")考虑升为方法学 claim
```

## 输出契约硬约束

1. **`## 建模拆解` 是叙事章节**,LLM 维护,渲染器不碰(同「研究目的」「结果」地位);
   但不得手改渲染器管理的机械段(核心主张表/证据条目表/两大嵌入章节)。
2. **mermaid 阶段名用标准词表**,这是跨论文汇总可比的唯一保证;节内必写外推方向。
3. **三层讲解缺一不可**——比喻层是后续 PPT/专利交底书直接素材,不是装饰。
4. **协议数值必须可定位**(§/Fig),且与 evidence 节点数值一致;发现节点数值与原文
   不一致时,先修 evidence 再写拆解,拆解不承载与 evidence 冲突的数。
5. 红旗措辞克制:写"属拟合优度,泛化证据另见…"这类事实区分,不写"造假/错误"。
6. 新拆解若发现既有 paper 节点的 raw_path 失效或指向错误论文,顺手修复并记入
   log/ops.md(数据卫生)。

## 已拆解论文登记表(累计 ≥5 篇后在维度十三搭跨论文流程对照)

| citekey | 外推方向 | 代理模型 | 拆解日期 |
|---|---|---|---|
| luo_2025_nat_methods | 时间前推+群体间+仿真到真实 | MLP(one-step-ahead) | 2026-09-02 |
| zhao_2022_cereb_cortex | 状态外推(预期→行为)+个体间 | 单试次 GLM alpha-informed NVC | 2026-09-02 |
| takahashi_2026_bme_front | 状态外推+群体间+干预前后 | 超网络MLP生成vanilla RNN | 2026-09-02 |
| takahashi_2025_npj_digit_med | 状态外推+群体间+仿真到真实 | 三层V-RNN+数据同化 | 2026-09-02 |
| meier_2022_experimental_neurology | 干预前后+仿真到真实 | TVB均场×ANNarchy spiking共仿真 | 2026-09-02 |
| biswas_2024_preliminary | 全部未声明(仿真内) | LIF 神经形态控制器(on-off/dual,灰盒) | 2026-09-03 |
| ravivarapu_2025_arxiv | 仿真内换 seed(拟泛化) | SEA-DBS 强化学习策略+HH 网络环境 | 2026-09-03 |
| liang_2021_ieee_access | 时间前推(前后半段/跨记录) | 深度 Koopman 算子自编码器 | 2026-09-03 |
| kirchhoff_2024_ieee_int_conf_syst_man_cybern | 仿真内(无 held-out,作者自陈) | GP/BLR 贝叶斯优化代理(相位→MEP) | 2026-09-03 |
| castano-candamil_2020_study | 干预前后(会话内 CV→在线) | OLS 震颤解码器+阈值 aDBS | 2026-09-03 |
| zhang_2024_medrxiv_prepr_serv_health_sci | 仿真到真实(方向一致弱验证) | PING E-I 平衡脉冲网络(400E+100I) | 2026-09-03 |
| minai_2025_omiso | 仿真到真实(正向模型生成专家数据) | CNN×LSTM 正向模型+BC 逆模型+PPO | 2026-09-03 |
| luo_2024_arxiv_org | 仿真到真实(仿真训练→真人在线) | DCGAN 生成式刺激优化+闭环组件 | 2026-09-03 |
| domhof_2022_neuroimage | 重测稳定性+群体间 | 6模型×8分区普查(OU/Kuramoto/WC) | 2026-09-02 |
| jirsa_2017_neuroimage | 干预前后+仿真到真实 | Epileptor网络+贝叶斯反演 | 2026-09-02 |
| hashemi_2020_neuroimage | 仿真到真实 | BVEP(NUTS/ADVI,合成闭环) | 2026-09-02 |
| schirner_2018_elife | 时间前推+仿真到真实 | Hybrid TVB(EEG驱动平均场) | 2026-09-02 |
| deco_2017_sci_rep | 仿真到真实 | Hopf振子网络(临界工作点) | 2026-09-02 |
| jiang_2024_ | 群体间 | LaBraM(VQ+对称掩码 Transformer,EEG) | 2026-09-02 |
| dou_2026_ | 群体间+少样本 | INCEPT(组合目标+球谐编码,EEG) | 2026-09-02 |
| tegon_2026_ieee_trans_biomed_eng | 群体间+部署 | FEMBA(双向 Mamba 低通重建,EEG) | 2026-09-02 |
| gijsen_2024_ | 群体间+少样本 | ELM-MIL(EEG-语言对齐,0.93M) | 2026-09-02 |
| helwan_2026_ | 群体间(受限) | DifEEG(去噪扩散 1D U-Net+FiLM,EEG) | 2026-09-02 |
| wang_2026_nat_biomed_eng | 群体间+少样本 | NeuroSTORM(SW-Mamba,fMRI) | 2026-09-02 |
| m_2026_ | 群体间(跨中心受限) | FlexiBrain(JEPA+Mamba+MoE,fMRI native) | 2026-09-02 |
| dong_2026_ | 群体间(跨族裔) | BrainFIBRE(SPID+五专家 MoE,NODDI) | 2026-09-02 |
| tak_2026_nat_neurosci | 群体间+少样本 | BrainIAC(3D SimCLR-ViT-B,MRI) | 2026-09-02 |
| guo_2026_ | 群体间+跨模态 | Brain-OF(ARNESS+MoE+DINT,fMRI+EEG+MEG) | 2026-09-02 |
| huang_2026_imaging_neurosci | 群体间+仿真到真实(生成) | MEG-GPT(61-token 自回归,MEG) | 2026-09-02 |
| zhang_2026_patterns | 群体间+少样本 | Brainfound(扩散→对比→指令三阶段,CT+MRI) | 2026-09-02 |

已满 5 篇,可启动跨论文流程对照。待拆队列:rolls_2022_neuroimage、monteverdi_2023、triebkorn_2022、tesler_2022_mean_field、esmaeili_2026、dollomaja_medrxiv、yan_2026、shaoting_2026、xia_2026、baldy_2025/nina_2025(部分缺 raw 待补附件)。

## 边界

- 不新建 paper/claim 节点(claim 达标时走 wiki-build-claim 流程)
- 不改 frontmatter 的 related_*(归 S5 渲染器体系)
- 快速判断素材不足(原文无 Methods 细节)时:拆解写到手头证据为止,缺口列
  "待补:需补充材料/代码库核实",不得脑补协议参数

## 关联

- 字段契约:`templates/paper-modeling.md`(检查单+词表+红旗+汇总约定)
- 主管线:`skills/wiki-extract-paper/SKILL.md`(本 Skill 是其建模向深化,可叠加执行)
- 汇总落点:`syntheses/孪生脑多维框架.md` 维度十三(六类外推方向)
- 统计契约:`templates/paper_stats.md`;分类解码对照:`templates/paper-ml.md`
