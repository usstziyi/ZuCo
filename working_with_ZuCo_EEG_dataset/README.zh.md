# 使用 ZuCo EEG 数据集

## 概述

本教程介绍了 "[ZuCo](https://www.nature.com/articles/sdata2018291)：A Simultaneous EEG and Eye-Tracking Resource for Natural Sentence Reading"（一个用于自然句子阅读的同步 EEG 和眼动追踪资源）和 "[ZuCo 2.0](https://arxiv.org/abs/1912.00903)：A dataset of physiological recordings during natural reading and annotation"（一个自然阅读与标注过程中生理记录的数据集）研究中应用于 EEG 数据的预处理步骤。

## 目录

- [ZuCo v.1 数据集](#zuco-v1-数据集)
- [ZuCo v.2 数据集](#zuco-v2-数据集)
- [眼动追踪预处理与特征提取](#眼动追踪预处理与特征提取)
- [EEG 采集](#eeg-采集)
- [EEG 预处理与特征提取](#eeg-预处理与特征提取)
- [数据集下载链接](#数据集下载链接)
- [引用](#引用)

## ZuCo v.1 数据集

ZuCo v.1 是一个结合了被试阅读自然句子时 EEG 和眼动追踪记录的数据集。眼动追踪使得我们能够精确标记被试阅读一个句子时每个单词的边界，进而实现对每个单词对应的 EEG 信号的精确提取。

### 主要特征

1. **被试**：12 名健康的成年母语者
2. **研究设计**：研究设计中三个任务的示意概览（[来源](https://www.nature.com/articles/sdata2018291)）



<p align="center">
  <img src="Figures/schematic_overview.png" alt="三个任务的示意概览" width="600"/>
</p>

3. **阅读材料**：阅读材料包含来自 Stanford Sentiment Treebank（斯坦福情感树库）的电影评论句子，以及来自 Wikipedia 关系抽取语料库的关于知名人物传记性句子。
   - 来自 Stanford Sentiment Treebank 的句子（任务：情感阅读 (SR)）：123 个中性、137 个负面和 140 个正面句子。**共 400 句**
   - 来自 Wikipedia 关系抽取数据集的句子（用于正常阅读 (NR) 任务）：**300 句**
   - 来自 Wikipedia 关系抽取数据集的句子（用于任务特定关系任务 (TSR)）：**407 句**

4. **实验流程**：这些句子以自然阅读场景呈现给被试，即整个句子呈现在屏幕上，被试按照自己的速度阅读每个句子。

## ZuCo v.2 数据集

ZuCo v.2 是 ZuCo v.1 的扩展数据集，包含更多句子和更多被试。

### 主要特征

1. **被试**：18 名健康的成年母语者
2. **任务**：
   - **正常阅读 (NR)**：被试自然地阅读句子，除了理解之外没有特定任务
   - **任务特定阅读范式**：被试判断句子中是否出现了某种特定关系类型
3. **描述性统计**：阅读材料的描述性统计（[来源](https://arxiv.org/abs/1912.00903)）

<p align="center">
  <img src="Figures/zucov2.png" alt="描述性统计" width="600"/>
</p>

4. **数据集重叠**：ZuCo v.1 和 ZuCo v.2 之间存在重叠。本数据集中记录的 100 个正常阅读句子和 85 个任务特定句子在版本 1 中已经被记录过。
5. **实验流程**：与 ZuCo v.1 相同 —— 自然阅读场景，完整句子呈现在屏幕上。

## 眼动追踪预处理与特征提取

EyeLink 1000 追踪器处理眼位数据，识别眼跳、注视和眨眼。

### 定义

- **注视 (Fixation)**：注视是指眼睛相对保持静止在某一特定位置。在数据集中，它由没有眼跳的时间段组成。
- **眼跳 (Saccades)**：眼跳是从一个注视点到另一个注视点的快速眼球运动。

### 眼动追踪特征

1. **注视时长 (GD)**：在首次阅读通道中，眼睛移出当前单词之前对该单词的所有注视之和
2. **总阅读时间 (TRT)**：对当前单词所有注视时长的总和，包括回视
3. **首次注视时长 (FFD)**：对当前单词的第一次注视的时长
4. **单一注视时长 (SFD)**：对当前单词的第一次且唯一的注视时长。SFD 仅适用于从未被重新注视的单词；如果一个单词有多次注视，则它没有 SFD
5. **通过时间 (GPT)**：GPT 衡量读者在读一个单词上花费的所有时间，以及在向前移过当前单词之前返回较早单词所花费的时间

## EEG 采集

### 记录设置

- **系统**：128 通道 EEG Geodesic Hydrocel 系统（Electrical Geodesics，Eugene, Oregon）
- **采样率**：数据以 500 Hz 的采样率记录，带通为 0.1 到 100 Hz
- **记录参考**：所有 EEG 通道均相对于 Cz 电极（头皮顶部中心）处的电压进行测量

## EEG 预处理与特征提取

### 通道配置

- **105 个 EEG 通道**：用于头皮记录
- **9 个 EOG 通道**：用于测量由眼球运动产生的电活动以进行伪迹去除
- **废弃通道**：其余主要位于颈部和面部的通道在数据分析前被丢弃

### 预处理步骤

1. **坏电极识别与替换**：如果一个电极满足以下条件之一，则被认为"坏"：
   - 其记录信号与由其余通道估算出的信号相关性低于 0.85
   - 相比所有其他通道，其线路噪声相对其信号更高（超过 4 个标准差）
   - 其平直线时间超过 5 秒

2. **滤波**：EEG 数据经过 0.5 Hz 高通滤波，并使用 Hamming 窗 sinc 有限冲激响应零相位滤波器进行陷波滤波（49-51 Hz）

3. **伪迹去除**：通过将 EOG 通道对头皮 EEG 通道进行线性回归来去除眼部伪迹

4. **自动伪迹拒绝**：使用多重伪迹拒绝算法 (MARA) 进行自动伪迹拒绝

5. **电极插值**：使用球面样条插值对坏电极进行插值

6. **最终质量检查**：自动扫描后，通过人工目视检查选择噪声通道并进行插值

### 特征提取：振荡功率

不同频段中的振荡功率指的是大脑信号在特定频率范围内节律性神经活动的幅度。神经振荡是神经网络活动的重复模式，可在各频段内进行测量。每个频段都与不同的认知或生理状态相关。

#### 分析的频段

- **Theta 1 (4-6 Hz)** 和 **Theta 2 (6.5-8 Hz)**：与创造力、直觉、做白日梦和幻想相关，是记忆、情绪和感觉的储存库
- **Alpha 1 (8.5-10 Hz)** 和 **Alpha 2 (10.5-13 Hz)**：与注意力、心理意象和感知相关
- **Beta 1 (13.5-18 Hz)** 和 **Beta 2 (18.5-30 Hz)**：与认知任务参与相关
- **Gamma 1 (30.5-40 Hz)** 和 **Gamma 2 (40-49.5 Hz)**：与更高阶的认知功能相关，如注意力、记忆编码、感觉感知和情绪整合

#### 处理方法

振荡功率测量通过对整个任务期间（任务的全部时长）的连续 EEG 信号进行带通滤波来计算，针对五个不同频段，为每个频段生成一个时间序列。

然后对这些时间序列（频段）中的每一个应用希尔伯特变换 (Hilbert Transform)。希尔伯特变换保留了频段振幅的时间信息。这种时间分辨率很重要，因为 EEG 特征需要与由眼动追踪注视所定义的时间段对齐。

## 下载 ZuCo 数据集

- 从 https://osf.io/q3zws/files/ 下的 'OSF Storage' 根目录下载 ZuCo v1.0 的 'task1-SR'、'task2-NR'、'task3-TSR' 的 'Matlab files'，
  解压并将所有 `.mat` 文件分别移动到 `~/datasets/ZuCo/task1-SR/Matlab_files`、`~/datasets/ZuCo/task2-NR/Matlab_files`、`~/datasets/ZuCo/task3-TSR/Matlab_files`。
- 从 https://osf.io/2urht/files/ 下的 'OSF Storage' 根目录下载 ZuCo v2.0 的 'task1-NR' 的 'Matlab files'，解压并将所有 `.mat` 文件移动到 `~/datasets/ZuCo/task2-NR-2.0/Matlab_files`。

## 加载预处理数据

- Jupyter notebook `construct_dataset_v1.ipynb` 提供了关于数据加载方式的详细说明。
- 要自动从 ZuCo v1 和 ZuCo v2 加载数据，直接运行脚本 `load_data_v1.py` 和 `load_data_v2.py`。
  需要指定的主要参数有：
  - `data_dir`：ZuCo 数据集的路径（本地位置）。
  - `save_data_dir`：从两个数据集中提取的 EEG 特征将要保存的位置。

这些 Python 脚本是基于这个 [GitHub 仓库](https://github.com/MikeWangWZHL/EEG-To-Text) 创建的。

## 数据集下载链接

- **ZuCo v.1**：[Nature Scientific Data](https://www.nature.com/articles/sdata2018291)
- **ZuCo v.2**：[arXiv 预印本](https://arxiv.org/abs/1912.00903)

## 引用

如果您在研究中使用此数据集，请引用：

### ZuCo v.1
```
Hollenstein, N., Rotsztejn, J., Troendle, M., Pedroni, A., Zhang, C., & Langer, N. (2018).
ZuCo, a simultaneous EEG and eye-tracking resource for natural sentence reading.
Scientific Data, 5, 180291.
```

### ZuCo v.2
```
Hollenstein, N., de la Torre, M., Langer, N., & Zhang, C. (2019).
ZuCo 2.0: A dataset of physiological recordings during natural reading and annotation.
arXiv preprint arXiv:1912.00903.
```

## 许可证

许可信息请参阅原始数据集出版物。

## 联系方式

关于数据集的问题，请参阅原始出版物中提供的联系信息。