# 第一轮模型结果记录：暂不使用 SPI

## 输入数据

- 训练表：`outputs/ganbei_roi_xiao_20240623_0706_samples_with_factors_rainfall.csv`
- 样本数：2991
- 训练集：2093
- 测试集：898
- 划分方式：分层随机划分，测试集比例 30%

## 本轮使用因子

连续因子：

- `aspect`
- `curvature`
- `dtr`
- `elevation`
- `hand`
- `ndvi`
- `rainfall`
- `slope`
- `twi`

分类因子：

- `lulc2`
- `soil2`

## 暂不使用的因子

- `spi`

原因：

- 前期质检发现 `spi` 最大值和标准差异常，可能与 SPI 计算方式、坡度单位、汇流累积单位或极端汇流像元有关。
- 当前先不使用 `spi`，避免异常值影响第一轮模型判断。

必须提醒：

- 后续不能忘记处理 `spi`。
- 至少需要补做三组对比：不用 SPI、原始 SPI、`log1p(spi)`。
- 如果时间允许，建议重新按统一 DEM 水文流程计算 SPI。

## 模型与预处理

模型：

- RandomForest
- XGBoost
- SVM_RBF

预处理：

- `lulc2`、`soil2` 使用 One-Hot 编码。
- SVM 连续变量使用标准化。
- RandomForest 和 XGBoost 连续变量保留原值，分类变量 One-Hot 编码。

## 测试集结果

| 模型 | Accuracy | Precision | Recall | F1 | Kappa | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| RandomForest | 0.8898 | 0.9227 | 0.8508 | 0.8853 | 0.7795 | 0.9533 | 0.9614 |
| XGBoost | 0.8942 | 0.9136 | 0.8708 | 0.8917 | 0.7884 | 0.9497 | 0.9587 |
| SVM_RBF | 0.8686 | 0.9107 | 0.8174 | 0.8615 | 0.7372 | 0.9185 | 0.9252 |

## 初步结论

- 按 ROC-AUC，RandomForest 当前最高，为 0.9533。
- 按 Accuracy、F1 和 Kappa，XGBoost 略高。
- SVM_RBF 表现略低，但仍具有较好的区分能力。
- 第一轮结果说明当前样本和因子体系具有较强可分性。

## 特征重要性

RandomForest 前五个重要特征：

1. `elevation`
2. `lulc2_90`
3. `hand`
4. `ndvi`
5. `rainfall`

XGBoost 前五个重要特征：

1. `lulc2_90`
2. `elevation`
3. `lulc2_80`
4. `soil2_0`
5. `lulc2_40`

说明：

- 地形高程和土地利用类型在第一轮模型中贡献较高。
- `rainfall` 在 RandomForest 中进入前五，在 XGBoost 中重要性较低但仍保留贡献。
- 分类变量的重要性需要结合土地利用和土壤类型代码表解释，不能只写类别编号。

## 重要限制

- 当前只是随机划分验证，可能受到空间自相关影响，精度可能偏高。
- 论文最终建议加入空间分块验证或空间留出验证。
- 后续生成易发性图时，必须保证全区因子栅格与训练特征的预处理方式一致。

## 输出文件

指标与表格：

- `outputs/models_first_round/model_metrics.csv`
- `outputs/models_first_round/train_test_split_info.json`
- `outputs/models_first_round/*_confusion_matrix.csv`
- `outputs/models_first_round/*_feature_importance.csv`
- `outputs/models_first_round/first_round_model_report.md`

图件：

- `figures/models_first_round/roc_curves.png`
- `figures/models_first_round/*_confusion_matrix.png`
- `figures/models_first_round/*_feature_importance.png`

模型：

- `models/first_round/RandomForest.joblib`
- `models/first_round/XGBoost.joblib`
- `models/first_round/SVM_RBF.joblib`
