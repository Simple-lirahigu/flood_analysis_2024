from __future__ import annotations

import json
import shutil
import textwrap
from datetime import datetime
from pathlib import Path


# 新建独立 PyCharm 项目，不再写入用户原来的 F:\studyPy\flood_analysis。
# 只使用标准库，便于直接用指定 Conda 环境运行。

PROJECT_DIR = Path(r"F:\studyPy\flood_analysis_2024")
SOURCE_DIR = Path(__file__).resolve().parent
CONDA_PYTHON = Path(r"E:\Anaconda3\envs\flood_analysis\python.exe")

DIRS = [
    ".idea/runConfigurations",
    "configs",
    "data/raw",
    "data/intermediate",
    "data/processed",
    "docs",
    "figures",
    "models",
    "outputs/samples",
    "outputs/rasters",
    "outputs/metrics",
    "outputs/tables",
    "reports",
    "scripts",
]

COPY_SCRIPTS = [
    "check_tif_alignment.py",
    "extract_tif_values_to_samples.py",
    "align_rainfall_to_factor_grid.py",
    "gee_poyang_2024_flood_samples.js",
    "gee_export_poyang_2024_event_rainfall.js",
]


def write_text(path: Path, content: str) -> None:
    """写入文本文件；新项目是空目录，可直接写入。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_config(name: str, script_name: str, parameters: str = "") -> str:
    """生成 PyCharm Python 运行配置。"""
    return f"""<component name="ProjectRunConfigurationManager">
  <configuration default="false" name="{name}" type="PythonConfigurationType" factoryName="Python">
    <option name="INTERPRETER_OPTIONS" value="" />
    <option name="PARENT_ENVS" value="true" />
    <option name="SDK_HOME" value="{CONDA_PYTHON}" />
    <option name="WORKING_DIRECTORY" value="$PROJECT_DIR$" />
    <option name="SCRIPT_NAME" value="$PROJECT_DIR$/scripts/{script_name}" />
    <option name="PARAMETERS" value="{parameters}" />
    <method v="2" />
  </configuration>
</component>
"""


def main() -> None:
    if PROJECT_DIR.exists():
        raise FileExistsError(f"新项目目录已存在，为避免覆盖已停止：{PROJECT_DIR}")
    if not CONDA_PYTHON.exists():
        raise FileNotFoundError(f"指定 Conda 环境不存在：{CONDA_PYTHON}")

    created_dirs: list[str] = []
    copied_files: list[str] = []
    written_files: list[str] = []

    for rel_dir in DIRS:
        path = PROJECT_DIR / rel_dir
        path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(path))

    for script in COPY_SCRIPTS:
        src = SOURCE_DIR / script
        dst = PROJECT_DIR / "scripts" / script
        if not src.exists():
            raise FileNotFoundError(f"缺少源脚本：{src}")
        shutil.copy2(src, dst)
        copied_files.append(str(dst))

    project_paths = {
        "说明": "复制为 project_paths.json 后按实际数据路径修改。代码中应优先读取配置，不要到处硬编码路径。",
        "tif_dir": r"E:\新tif_裁",
        "reference_tif": r"E:\新tif_裁\elevation.tif",
        "gee_samples_csv": r"outputs\samples\poyang_2024_flood_samples.csv",
        "rainfall_gee_tif": r"data\raw\rain_event_mm_2024_0623_0706.tif",
        "aligned_rainfall_tif": r"outputs\rasters\rainfall_2024_event_aligned_to_factors.tif",
        "samples_with_factors_csv": r"outputs\samples\model_training_samples_with_factors.csv",
        "model_dir": r"models",
        "figure_dir": r"figures",
    }

    files = {
        "README.md": f"""# flood_analysis_2024

这是独立的新 PyCharm 项目，用于 2024 年赣北/鄱阳湖洪涝易发性预测实验。

## Python 环境

使用已有 Conda 环境：

```text
{CONDA_PYTHON}
```

PyCharm 中设置方式：

1. 打开项目目录：`{PROJECT_DIR}`
2. 进入 `File -> Settings -> Project -> Python Interpreter`
3. 选择 `Add Interpreter -> Existing`
4. 指向 `{CONDA_PYTHON}`

## 推荐流程

1. 在 GEE 中运行 `scripts/gee_poyang_2024_flood_samples.js`，导出洪水/非洪水样本。
2. 在 GEE 中运行 `scripts/gee_export_poyang_2024_event_rainfall.js`，导出 2024-06-23 至 2024-07-06 事件降水。
3. 运行 `scripts/check_tif_alignment.py`，检查致灾因子 TIF 对齐情况。
4. 运行 `scripts/align_rainfall_to_factor_grid.py`，把事件降水对齐到致灾因子网格。
5. 运行 `scripts/extract_tif_values_to_samples.py`，将 TIF 因子属性提取到样本点。
6. 后续再进行模型训练、预测制图、精度评价和论文图表输出。

## 重要说明

- CHIRPS 降水即使重采样到现有 TIF 网格，也不能说它具有 12.45 m 真实空间精度。
- `lulc2.tif` 和 `soil2.tif` 是分类因子，建模和解释时不要简单当作连续变量。
- 论文中需要说明洪水样本来自 Sentinel-1 遥感提取，不是绝对真值。
""",
        "requirements.txt": """numpy
pandas
geopandas
rasterio
rioxarray
xarray
scikit-learn
xgboost
matplotlib
seaborn
joblib
openpyxl
earthengine-api
""",
        ".gitignore": """# Python
__pycache__/
*.py[cod]

# PyCharm local files
.idea/workspace.xml
.idea/tasks.xml
.idea/usage.statistics.xml
.idea/shelf/

# Large data and outputs
*.tif
*.tiff
*.ovr
*.aux.xml
*.pkl
*.joblib
data/raw/
data/intermediate/
data/processed/
outputs/
models/
""",
        "configs/project_paths.example.json": json.dumps(project_paths, ensure_ascii=False, indent=2),
        "docs/pycharm_setup.md": f"""# PyCharm 运行配置说明

## 解释器

```text
{CONDA_PYTHON}
```

这是你指定的 Conda 环境，不使用原 `F:\\studyPy\\flood_analysis` 项目的环境配置。

## 已生成的运行配置

- `01 检查TIF一致性`
- `02 对齐2024事件降水`
- `03 样本点提取因子`

如果 PyCharm 没有自动显示这些配置，手动新建 Python 配置即可：

- Working directory：`$PROJECT_DIR$`
- Script path：选择 `scripts` 下对应脚本
- Python interpreter：`{CONDA_PYTHON}`
""",
        "docs/run_workflow_2024_flood.md": """# 2024 年洪水易发性预测工作流

## 输入

- 研究区：赣北地区
- 洪水事件：2024-06-23 至 2024-07-06 鄱阳湖/赣北洪灾
- 致灾因子：现有 TIF 因子目录 `E:\新tif_裁`
- 洪水样本：建议由 Sentinel-1 洪前/洪期差异提取，并去除永久水体、陡坡和小斑块噪声

## 输出

- 样本因子表：`outputs/samples/model_training_samples_with_factors.csv`
- 对齐降水：`outputs/rasters/rainfall_2024_event_aligned_to_factors.tif`
- 模型结果：`outputs/metrics`
- 论文图件：`figures`

## 论文注意点

样本制作、因子筛选、模型训练、精度评价、易发性分级和不确定性分析都需要写清楚。仅有预测图不够支撑硕士论文。
""",
        ".idea/runConfigurations/01_check_tif_alignment.xml": run_config("01 检查TIF一致性", "check_tif_alignment.py"),
        ".idea/runConfigurations/02_align_2024_rainfall.xml": run_config(
            "02 对齐2024事件降水",
            "align_rainfall_to_factor_grid.py",
            "--input data/raw/rain_event_mm_2024_0623_0706.tif --output outputs/rasters/rainfall_2024_event_aligned_to_factors.tif",
        ),
        ".idea/runConfigurations/03_extract_sample_factors.xml": run_config(
            "03 样本点提取因子",
            "extract_tif_values_to_samples.py",
            "--samples outputs/samples/poyang_2024_flood_samples.csv --output outputs/samples/model_training_samples_with_factors.csv",
        ),
    }

    for rel_path, content in files.items():
        path = PROJECT_DIR / rel_path
        write_text(path, textwrap.dedent(content).lstrip())
        written_files.append(str(path))

    manifest = {
        "project_dir": str(PROJECT_DIR),
        "conda_python": str(CONDA_PYTHON),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "created_dirs": created_dirs,
        "copied_files": copied_files,
        "written_files": written_files,
    }
    manifest_path = PROJECT_DIR / "docs" / "codex_setup_manifest.json"
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({**manifest, "manifest": str(manifest_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
