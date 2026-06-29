from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.stats.outliers_influence import variance_inflation_factor


DEFAULT_INPUT = Path("outputs/ganbei_roi_xiao_20240623_0706_samples_with_factors_rainfall.csv")
DEFAULT_OUTPUT_DIR = Path("outputs/qc")
DEFAULT_FIGURE_DIR = Path("figures/qc")

FACTOR_COLUMNS = [
    "aspect",
    "curvature",
    "dtr",
    "elevation",
    "hand",
    "lulc2",
    "ndvi",
    "rainfall",
    "slope",
    "soil2",
    "spi",
    "twi",
]

CATEGORICAL_FACTORS = ["lulc2", "soil2"]
CONTINUOUS_FACTORS = [col for col in FACTOR_COLUMNS if col not in CATEGORICAL_FACTORS]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="训练样本表质检、因子统计、相关性和 VIF 分析。")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="样本因子表 CSV。")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="统计表输出目录。")
    parser.add_argument("--figure-dir", default=str(DEFAULT_FIGURE_DIR), help="图件输出目录。")
    return parser.parse_args()


def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def calc_vif(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """计算连续因子的 VIF。分类变量不放入 VIF，避免把类别编码误当连续值。"""
    x = df[columns].replace([np.inf, -np.inf], np.nan).dropna().copy()
    constant_columns = [col for col in columns if x[col].nunique(dropna=True) <= 1]
    used_columns = [col for col in columns if col not in constant_columns]

    if not used_columns:
        return pd.DataFrame(columns=["factor", "vif", "note"])

    x = x[used_columns].astype(float)
    vif_rows = []
    for i, col in enumerate(used_columns):
        try:
            vif = float(variance_inflation_factor(x.values, i))
            note = ""
        except Exception as exc:  # noqa: BLE001
            vif = np.nan
            note = f"计算失败：{exc}"
        vif_rows.append({"factor": col, "vif": vif, "note": note})

    for col in constant_columns:
        vif_rows.append({"factor": col, "vif": np.nan, "note": "常数列，未计算 VIF"})

    return pd.DataFrame(vif_rows).sort_values("vif", ascending=False, na_position="last")


def write_markdown_report(
    output_path: Path,
    df: pd.DataFrame,
    factor_summary: pd.DataFrame,
    vif_df: pd.DataFrame,
    high_corr_pairs: pd.DataFrame,
) -> None:
    class_counts = df["flood"].value_counts(dropna=False).sort_index().to_dict()
    missing_counts = df[FACTOR_COLUMNS + ["flood", "label", "longitude", "latitude"]].isna().sum()
    rainfall_desc = df["rainfall"].describe()

    lines = [
        "# 训练表质检与因子统计报告",
        "",
        "## 数据概况",
        "",
        f"- 样本总数：{len(df)}",
        f"- 洪水/非洪水数量：{class_counts}",
        f"- 因子数量：{len(FACTOR_COLUMNS)}",
        f"- 连续因子：{', '.join(CONTINUOUS_FACTORS)}",
        f"- 分类因子：{', '.join(CATEGORICAL_FACTORS)}",
        "",
        "## 缺失值检查",
        "",
        "```text",
        missing_counts.to_string(),
        "```",
        "",
        "## rainfall 统计",
        "",
        "```text",
        rainfall_desc.to_string(),
        "```",
        "",
        "## VIF 结论",
        "",
    ]

    if vif_df.empty:
        lines.append("- 未生成 VIF 结果。")
    else:
        severe = vif_df[vif_df["vif"] >= 10]
        moderate = vif_df[(vif_df["vif"] >= 5) & (vif_df["vif"] < 10)]
        if severe.empty and moderate.empty:
            lines.append("- 连续因子 VIF 均低于 5，未发现明显多重共线性风险。")
        else:
            if not severe.empty:
                lines.append("- VIF >= 10 的因子需要重点处理或解释：")
                lines.extend([f"  - {row.factor}: {row.vif:.3f}" for row in severe.itertuples()])
            if not moderate.empty:
                lines.append("- 5 <= VIF < 10 的因子存在中等共线性风险：")
                lines.extend([f"  - {row.factor}: {row.vif:.3f}" for row in moderate.itertuples()])

    lines.extend(
        [
            "",
            "## 高相关因子对",
            "",
        ]
    )
    if high_corr_pairs.empty:
        lines.append("- 按 |r| >= 0.7 阈值，未发现高相关连续因子对。")
    else:
        lines.append("- 按 |r| >= 0.7 阈值发现以下高相关因子对：")
        for row in high_corr_pairs.itertuples(index=False):
            lines.append(f"  - {row.factor_1} 与 {row.factor_2}: r = {row.correlation:.3f}")

    lines.extend(
        [
            "",
            "## 输出文件",
            "",
            "- `factor_descriptive_statistics.csv`：全样本描述统计。",
            "- `factor_group_statistics_by_flood.csv`：按洪水/非洪水分组统计。",
            "- `factor_correlation_matrix.csv`：连续因子 Pearson 相关矩阵。",
            "- `factor_high_correlation_pairs.csv`：高相关因子对。",
            "- `factor_vif.csv`：连续因子 VIF。",
            "- `categorical_factor_counts.csv`：分类因子类别频数。",
            "- `figures/qc/factor_correlation_heatmap.png`：相关性热力图。",
            "- `figures/qc/factor_boxplots_by_flood.png`：连续因子分组箱线图。",
            "",
            "## 方法注意",
            "",
            "- `lulc2` 和 `soil2` 是分类变量，不应按连续变量解释。",
            "- VIF 只对连续因子计算，分类变量后续建模应使用类别编码或独热编码。",
            "- 本报告只完成数据质检和因子统计，不代表模型最终筛选结论。",
        ]
    )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    figure_dir = Path(args.figure_dir)
    safe_mkdir(output_dir)
    safe_mkdir(figure_dir)

    df = pd.read_csv(input_path)
    missing_factors = [col for col in FACTOR_COLUMNS if col not in df.columns]
    if missing_factors:
        raise ValueError(f"训练表缺少因子列：{missing_factors}")
    for col in ["flood", "label", "longitude", "latitude"]:
        if col not in df.columns:
            raise ValueError(f"训练表缺少必要字段：{col}")

    factor_df = df[FACTOR_COLUMNS].copy()
    factor_summary = factor_df.describe().T
    factor_summary["missing_count"] = factor_df.isna().sum()
    factor_summary["unique_count"] = factor_df.nunique(dropna=True)
    factor_summary.to_csv(output_dir / "factor_descriptive_statistics.csv", encoding="utf-8-sig")

    group_stats = df.groupby("flood")[FACTOR_COLUMNS].agg(["count", "mean", "std", "min", "median", "max"])
    group_stats.to_csv(output_dir / "factor_group_statistics_by_flood.csv", encoding="utf-8-sig")

    corr = df[CONTINUOUS_FACTORS].corr(method="pearson")
    corr.to_csv(output_dir / "factor_correlation_matrix.csv", encoding="utf-8-sig")

    high_corr_rows = []
    for i, col_a in enumerate(CONTINUOUS_FACTORS):
        for col_b in CONTINUOUS_FACTORS[i + 1 :]:
            value = corr.loc[col_a, col_b]
            if pd.notna(value) and abs(value) >= 0.7:
                high_corr_rows.append(
                    {"factor_1": col_a, "factor_2": col_b, "correlation": float(value), "abs_correlation": abs(float(value))}
                )
    high_corr_pairs = pd.DataFrame(high_corr_rows).sort_values("abs_correlation", ascending=False) if high_corr_rows else pd.DataFrame(columns=["factor_1", "factor_2", "correlation", "abs_correlation"])
    high_corr_pairs.to_csv(output_dir / "factor_high_correlation_pairs.csv", index=False, encoding="utf-8-sig")

    vif_df = calc_vif(df, CONTINUOUS_FACTORS)
    vif_df.to_csv(output_dir / "factor_vif.csv", index=False, encoding="utf-8-sig")

    categorical_rows = []
    for col in CATEGORICAL_FACTORS:
        counts = df.groupby(["flood", col]).size().reset_index(name="count")
        counts["factor"] = col
        counts = counts.rename(columns={col: "category"})
        categorical_rows.append(counts[["factor", "flood", "category", "count"]])
    categorical_counts = pd.concat(categorical_rows, ignore_index=True)
    categorical_counts.to_csv(output_dir / "categorical_factor_counts.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, square=True, linewidths=0.3)
    plt.title("Continuous Factor Pearson Correlation")
    plt.tight_layout()
    plt.savefig(figure_dir / "factor_correlation_heatmap.png", dpi=300)
    plt.close()

    melted = df.melt(id_vars="flood", value_vars=CONTINUOUS_FACTORS, var_name="factor", value_name="value")
    g = sns.catplot(
        data=melted,
        x="flood",
        y="value",
        col="factor",
        kind="box",
        col_wrap=4,
        sharey=False,
        height=3.0,
        aspect=1.1,
        showfliers=False,
    )
    g.set_axis_labels("Flood label", "Value")
    g.fig.suptitle("Continuous Factor Distributions by Flood Label", y=1.02)
    g.fig.tight_layout()
    g.fig.savefig(figure_dir / "factor_boxplots_by_flood.png", dpi=300)
    plt.close(g.fig)

    write_markdown_report(
        output_dir / "training_table_qc_report.md",
        df,
        factor_summary,
        vif_df,
        high_corr_pairs,
    )

    print("训练表质检完成")
    print(f"输入文件：{input_path}")
    print(f"样本数：{len(df)}")
    print(f"类别数量：{df['flood'].value_counts(dropna=False).sort_index().to_dict()}")
    print(f"连续因子数：{len(CONTINUOUS_FACTORS)}")
    print(f"分类因子数：{len(CATEGORICAL_FACTORS)}")
    print(f"输出目录：{output_dir}")
    print(f"图件目录：{figure_dir}")


if __name__ == "__main__":
    main()
