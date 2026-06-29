# 训练表质检、因子相关性与 VIF 分析

## 输入数据

- 训练表：`outputs/ganbei_roi_xiao_20240623_0706_samples_with_factors_rainfall.csv`
- 样本数：2991
- 洪水样本：1496
- 非洪水样本：1495
- 因子数：12

## 因子类型

连续因子：

- `aspect`
- `curvature`
- `dtr`
- `elevation`
- `hand`
- `ndvi`
- `rainfall`
- `slope`
- `spi`
- `twi`

分类因子：

- `lulc2`
- `soil2`

说明：`lulc2` 和 `soil2` 不应按连续变量解释。后续建模时可以使用树模型直接保留整数编码，但论文解释时必须按类别变量说明；若使用 Logistic Regression、SVM、MLP 等模型，建议做独热编码或其他分类编码。

## 缺失值检查

12 个因子、`flood`、`label`、`longitude`、`latitude` 均无缺失值。

## rainfall 统计

- 最小值：198.65721
- 第一四分位数：342.33162
- 中位数：369.04462
- 均值：361.37044
- 第三四分位数：391.53996
- 最大值：529.54060

## 描述统计中的注意点

- `spi` 最大值为 10297268，标准差较大，后续建模前建议检查其分布，必要时做 `log1p` 变换或分位数缩尾对比实验。
- `twi` 最大值为 19683.25，尺度明显大于多数因子，若使用 SVM、Logistic Regression、MLP 等模型，必须标准化。
- `aspect` 中存在 `-1`，这通常表示平坦区域或无方向值，建模前应确认其含义；可保留为特殊值，也可单独编码为“平坦坡向”。
- `slope` 中位数接近 0，说明样本集中在低坡度区域，这与洪涝过程和研究区低洼地形基本一致。

## 相关性分析

对 10 个连续因子计算 Pearson 相关系数。

结论：

- 按 `|r| >= 0.7` 阈值，未发现高相关连续因子对。
- 当前连续因子之间没有明显的强线性冗余。

## VIF 分析

VIF 只对连续因子计算，未包含 `lulc2` 和 `soil2`。

结果：

| 因子 | VIF |
|---|---:|
| rainfall | 8.220 |
| twi | 3.353 |
| ndvi | 2.660 |
| aspect | 2.562 |
| elevation | 2.198 |
| slope | 1.987 |
| dtr | 1.943 |
| hand | 1.905 |
| curvature | 1.102 |
| spi | 1.015 |

解释：

- `rainfall` 的 VIF 为 8.220，属于中等共线性风险。
- 其他连续因子 VIF 均低于 5，暂未发现明显多重共线性问题。
- 当前不建议直接删除 `rainfall`，因为它是本次 2024 暴雨洪灾事件的重要过程因子；后续可通过特征重要性、Permutation importance 或 SHAP 再判断其贡献。

## 分类变量频数特征

`lulc2`：

- 非洪水样本中 `40` 类最多，共 804 个。
- 洪水样本中 `90` 类最多，共 849 个。

`soil2`：

- 洪水和非洪水样本中 `7` 类均占比较高。
- 洪水样本中 `0` 类数量明显高于非洪水样本。

具体类别含义需要结合你的土地利用和土壤分类表解释，不能只写数字类别。

## 输出文件

统计表：

- `outputs/qc/factor_descriptive_statistics.csv`
- `outputs/qc/factor_group_statistics_by_flood.csv`
- `outputs/qc/factor_correlation_matrix.csv`
- `outputs/qc/factor_high_correlation_pairs.csv`
- `outputs/qc/factor_vif.csv`
- `outputs/qc/categorical_factor_counts.csv`
- `outputs/qc/training_table_qc_report.md`

图件：

- `figures/qc/factor_correlation_heatmap.png`
- `figures/qc/factor_boxplots_by_flood.png`

## 下一步建议

1. 保留 12 个因子进入第一轮模型训练。
2. 对 `lulc2`、`soil2` 明确采用分类变量处理策略。
3. 对 SVM、Logistic Regression、MLP 等模型进行标准化。
4. 对 `spi`、`twi` 做分布检查，必要时做变换对比实验。
5. 第一轮模型建议先训练 RF、XGBoost、SVM，并输出 Accuracy、Precision、Recall、F1、Kappa、ROC-AUC 和混淆矩阵。
