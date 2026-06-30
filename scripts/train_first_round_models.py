from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier


DEFAULT_INPUT = Path("outputs/ganbei_roi_xiao_20240623_0706_samples_with_factors_rainfall.csv")
DEFAULT_OUTPUT_DIR = Path("outputs/models_first_round")
DEFAULT_FIGURE_DIR = Path("figures/models_first_round")
DEFAULT_MODEL_DIR = Path("models/first_round")

TARGET_COLUMN = "flood"

# 当前先不用 spi。原因：前期质检发现 spi 极值和标准差异常，用户要求先继续但必须提醒。
CONTINUOUS_FEATURES = [
    "aspect",
    "curvature",
    "dtr",
    "elevation",
    "hand",
    "ndvi",
    "rainfall",
    "slope",
    "twi",
]
CATEGORICAL_FEATURES = ["lulc2", "soil2"]
EXCLUDED_FEATURES = ["spi"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="第一轮洪水易发性样本模型训练。")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="样本因子表 CSV。")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="指标表输出目录。")
    parser.add_argument("--figure-dir", default=str(DEFAULT_FIGURE_DIR), help="图件输出目录。")
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR), help="模型输出目录。")
    parser.add_argument("--test-size", type=float, default=0.3, help="测试集比例。")
    parser.add_argument("--random-state", type=int, default=20240706, help="随机种子。")
    return parser.parse_args()


def make_dirs(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def make_onehot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def get_feature_names(preprocessor: ColumnTransformer) -> list[str]:
    names: list[str] = []
    for name, transformer, columns in preprocessor.transformers_:
        if name == "remainder" and transformer == "drop":
            continue
        if hasattr(transformer, "get_feature_names_out"):
            transformed = transformer.get_feature_names_out(columns)
            names.extend([str(item) for item in transformed])
        else:
            names.extend([str(col) for col in columns])
    return names


def build_models(random_state: int) -> dict[str, Pipeline]:
    tree_preprocessor = ColumnTransformer(
        transformers=[
            ("continuous", "passthrough", CONTINUOUS_FEATURES),
            ("categorical", make_onehot_encoder(), CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    scaled_preprocessor = ColumnTransformer(
        transformers=[
            ("continuous", StandardScaler(), CONTINUOUS_FEATURES),
            ("categorical", make_onehot_encoder(), CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    return {
        "RandomForest": Pipeline(
            steps=[
                ("preprocess", tree_preprocessor),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=500,
                        max_features="sqrt",
                        min_samples_leaf=2,
                        class_weight="balanced",
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "XGBoost": Pipeline(
            steps=[
                ("preprocess", tree_preprocessor),
                (
                    "model",
                    XGBClassifier(
                        n_estimators=500,
                        max_depth=4,
                        learning_rate=0.03,
                        subsample=0.85,
                        colsample_bytree=0.85,
                        objective="binary:logistic",
                        eval_metric="logloss",
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "SVM_RBF": Pipeline(
            steps=[
                ("preprocess", scaled_preprocessor),
                (
                    "model",
                    SVC(
                        kernel="rbf",
                        C=2.0,
                        gamma="scale",
                        probability=True,
                        class_weight="balanced",
                        random_state=random_state,
                    ),
                ),
            ]
        ),
    }


def calc_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "kappa": cohen_kappa_score(y_true, y_pred),
        "roc_auc": roc_auc_score(y_true, y_prob),
        "pr_auc": average_precision_score(y_true, y_prob),
    }


def plot_confusion_matrix(cm: np.ndarray, model_name: str, output_path: Path) -> None:
    plt.figure(figsize=(4.8, 4.2))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Non-flood", "Flood"],
        yticklabels=["Non-flood", "Flood"],
    )
    plt.xlabel("Predicted")
    plt.ylabel("Observed")
    plt.title(f"{model_name} Confusion Matrix")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_roc_curves(roc_rows: list[dict[str, object]], output_path: Path) -> None:
    plt.figure(figsize=(6.2, 5.2))
    for item in roc_rows:
        plt.plot(item["fpr"], item["tpr"], label=f"{item['model']} AUC={item['auc']:.3f}")
    plt.plot([0, 1], [0, 1], "k--", linewidth=1)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def save_feature_importance(model_name: str, pipeline: Pipeline, output_dir: Path, figure_dir: Path) -> None:
    model = pipeline.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        return

    feature_names = get_feature_names(pipeline.named_steps["preprocess"])
    importance = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    importance.to_csv(output_dir / f"{model_name}_feature_importance.csv", index=False, encoding="utf-8-sig")

    top = importance.head(20).iloc[::-1]
    plt.figure(figsize=(7, 6))
    plt.barh(top["feature"], top["importance"])
    plt.xlabel("Importance")
    plt.title(f"{model_name} Feature Importance")
    plt.tight_layout()
    plt.savefig(figure_dir / f"{model_name}_feature_importance.png", dpi=300)
    plt.close()


def write_report(output_path: Path, metrics_df: pd.DataFrame, feature_columns: list[str]) -> None:
    best = metrics_df.sort_values("roc_auc", ascending=False).iloc[0]
    lines = [
        "# 第一轮洪水易发性模型训练报告",
        "",
        "## 建模设置",
        "",
        "- 模型：RandomForest、XGBoost、SVM_RBF",
        "- 划分方式：分层随机划分，训练集 70%，测试集 30%",
        "- 分类变量：`lulc2`、`soil2` 使用 One-Hot 编码",
        "- SVM 连续变量进行了标准化",
        "- RF/XGBoost 连续变量保留原值，分类变量 One-Hot 编码",
        "",
        "## 本轮未使用的因子",
        "",
        "- `spi` 暂不参与本轮建模。",
        "- 原因：前期质检发现 `spi` 极值和标准差异常，计算方法可能需要复核。",
        "- 后续必须补做：无 SPI、原始 SPI、`log1p(spi)` 三组对比实验，或重新计算 SPI。",
        "",
        "## 本轮使用因子",
        "",
        ", ".join(feature_columns),
        "",
        "## 测试集精度",
        "",
        metrics_df.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## 当前最优模型",
        "",
        f"- 按 ROC-AUC 排序，当前最优模型为 `{best['model']}`，ROC-AUC = {best['roc_auc']:.4f}。",
        "",
        "## 注意事项",
        "",
        "- 这是第一轮随机划分结果，不等同于最终论文结果。",
        "- 后续建议补充空间分块验证，避免空间自相关导致精度虚高。",
        "- 若使用模型生成全区易发性图，需要按同样的特征处理流程处理整幅因子栅格。",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    figure_dir = Path(args.figure_dir)
    model_dir = Path(args.model_dir)
    make_dirs(output_dir, figure_dir, model_dir)

    df = pd.read_csv(input_path)
    feature_columns = CONTINUOUS_FEATURES + CATEGORICAL_FEATURES
    missing = [col for col in feature_columns + [TARGET_COLUMN] if col not in df.columns]
    if missing:
        raise ValueError(f"输入表缺少字段：{missing}")

    used_df = df[feature_columns + [TARGET_COLUMN]].replace([np.inf, -np.inf], np.nan).dropna().copy()
    x = used_df[feature_columns]
    y = used_df[TARGET_COLUMN].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    split_info = {
        "input": str(input_path),
        "total_samples_after_dropna": int(len(used_df)),
        "train_samples": int(len(x_train)),
        "test_samples": int(len(x_test)),
        "train_class_counts": {str(k): int(v) for k, v in y_train.value_counts().sort_index().items()},
        "test_class_counts": {str(k): int(v) for k, v in y_test.value_counts().sort_index().items()},
        "features_used": feature_columns,
        "features_excluded": EXCLUDED_FEATURES,
        "random_state": args.random_state,
        "test_size": args.test_size,
    }
    (output_dir / "train_test_split_info.json").write_text(
        json.dumps(split_info, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    metrics_rows = []
    roc_rows = []
    models = build_models(args.random_state)

    for model_name, pipeline in models.items():
        print(f"训练模型：{model_name}")
        pipeline.fit(x_train, y_train)
        y_pred = pipeline.predict(x_test)
        y_prob = pipeline.predict_proba(x_test)[:, 1]

        metrics = calc_metrics(y_test.to_numpy(), y_pred, y_prob)
        metrics["model"] = model_name
        metrics_rows.append(metrics)

        cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
        pd.DataFrame(cm, index=["true_0", "true_1"], columns=["pred_0", "pred_1"]).to_csv(
            output_dir / f"{model_name}_confusion_matrix.csv",
            encoding="utf-8-sig",
        )
        plot_confusion_matrix(cm, model_name, figure_dir / f"{model_name}_confusion_matrix.png")

        fpr, tpr, _ = roc_curve(y_test, y_prob)
        roc_rows.append({"model": model_name, "fpr": fpr, "tpr": tpr, "auc": metrics["roc_auc"]})

        save_feature_importance(model_name, pipeline, output_dir, figure_dir)
        joblib.dump(pipeline, model_dir / f"{model_name}.joblib")

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df = metrics_df[["model", "accuracy", "precision", "recall", "f1", "kappa", "roc_auc", "pr_auc"]]
    metrics_df = metrics_df.sort_values("roc_auc", ascending=False)
    metrics_df.to_csv(output_dir / "model_metrics.csv", index=False, encoding="utf-8-sig")

    plot_roc_curves(roc_rows, figure_dir / "roc_curves.png")
    write_report(output_dir / "first_round_model_report.md", metrics_df, feature_columns)

    print("第一轮模型训练完成")
    print(f"样本数：{len(used_df)}")
    print(f"训练集：{len(x_train)}，测试集：{len(x_test)}")
    print(f"未使用因子：{EXCLUDED_FEATURES}")
    print(f"指标输出：{output_dir / 'model_metrics.csv'}")
    print(f"报告输出：{output_dir / 'first_round_model_report.md'}")


if __name__ == "__main__":
    main()
