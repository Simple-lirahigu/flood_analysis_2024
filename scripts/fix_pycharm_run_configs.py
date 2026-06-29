from pathlib import Path


# 修复 PyCharm 运行配置缺少 module 导致的 ModuleRootManager.getInstance 报错。

PROJECT_DIR = Path(r"F:\studyPy\flood_analysis_2024")
PYTHON_EXE = r"E:\Anaconda3\envs\flood_analysis\python.exe"
MODULE_NAME = "flood_analysis_2024"

CONFIGS = [
    ("01_check_tif_alignment.xml", "01 检查TIF一致性", "check_tif_alignment.py", ""),
    (
        "02_align_2024_rainfall.xml",
        "02 对齐2024事件降水",
        "align_rainfall_to_factor_grid.py",
        "--input data/raw/rain_event_mm_2024_0623_0706.tif --output outputs/rasters/rainfall_2024_event_aligned_to_factors.tif",
    ),
    (
        "03_extract_sample_factors.xml",
        "03 样本点提取因子",
        "extract_tif_values_to_samples.py",
        "--samples outputs/samples/poyang_2024_flood_samples.csv --output outputs/samples/model_training_samples_with_factors.csv",
    ),
]


def build_config(name: str, script_name: str, parameters: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<component name="ProjectRunConfigurationManager">
  <configuration default="false" name="{name}" type="PythonConfigurationType" factoryName="Python">
    <module name="{MODULE_NAME}" />
    <option name="INTERPRETER_OPTIONS" value="" />
    <option name="PARENT_ENVS" value="true" />
    <option name="SDK_HOME" value="{PYTHON_EXE}" />
    <option name="WORKING_DIRECTORY" value="$PROJECT_DIR$" />
    <option name="SCRIPT_NAME" value="$PROJECT_DIR$/scripts/{script_name}" />
    <option name="PARAMETERS" value="{parameters}" />
    <method v="2" />
  </configuration>
</component>
'''


def main() -> None:
    run_config_dir = PROJECT_DIR / ".idea" / "runConfigurations"
    for filename, name, script_name, parameters in CONFIGS:
        path = run_config_dir / filename
        path.write_text(build_config(name, script_name, parameters), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
