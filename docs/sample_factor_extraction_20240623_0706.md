# 2024-06-23 至 2024-07-06 样本因子提取记录

## 输入样本

- 洪水样本 CSV：`drive-download-20260629T152901Z-3-001/ganbei_roi_xiao_20240623_0706_flood_samples.csv`
- 非洪水样本 CSV：`drive-download-20260629T152901Z-3-001/ganbei_roi_xiao_20240623_0706_nonflood_samples.csv`
- 合并样本输出：`outputs/ganbei_roi_xiao_20240623_0706_merged_samples.csv`

合并后样本数：

- 洪水样本：1500
- 非洪水样本：1500
- 总样本：3000

## 输入因子

因子目录：`E:\新tif_裁`

已提取 12 个因子：

- `aspect`
- `curvature`
- `dtr`
- `elevation`
- `hand`
- `lulc2`
- `ndvi`
- `rainfall`
- `slope`
- `soil2`
- `spi`
- `twi`

## 输出结果

加入 `rainfall.tif` 后的训练表：

- `outputs/ganbei_roi_xiao_20240623_0706_samples_with_factors_rainfall.csv`

提取结果：

- 输入样本数：3000
- 删除 NoData 后样本数：2991
- 洪水样本：1496
- 非洪水样本：1495
- 输出字段数：43
- 12 个因子列均无空值

`rainfall` 字段统计：

- 最小值：198.65721
- 最大值：529.5406
- 均值：361.37044
- 中位数：369.04462

## 注意事项

- `rainfall.tif` 的大小、分辨率、范围和 transform 与其他因子一致。
- `rainfall.tif` 的 CRS WKT 与参考 TIF 存在极小字符串差异，主要体现在椭球参数精度末尾；脚本已改为以网格一致性作为硬性检查，CRS 字符串不完全一致时给出警告但继续提取。
- `lulc2` 和 `soil2` 是分类变量，建模时不应简单当作连续变量解释。
