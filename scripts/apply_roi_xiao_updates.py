from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

import geopandas as gpd


# 将缩小后的研究区接入 flood_analysis_2024 项目。
# 注意：GEE 不能直接读取本地 shp，仍需用户把 roi_xiao.geojson 或 roi.shp 上传为 GEE Asset。

PROJECT_DIR = Path(r"F:\studyPy\flood_analysis_2024")
ROI_SHP = Path(r"F:\研二\毕业论文\洪涝敏感性\研究区_xiao\roi.shp")
ROI_GEOJSON = PROJECT_DIR / "data" / "raw" / "roi_xiao.geojson"
ROI_DOC = PROJECT_DIR / "docs" / "roi_xiao_usage.md"
TIF_DIR = Path(r"E:\新tif_裁")
REFERENCE_TIF = TIF_DIR / "elevation.tif"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def export_roi() -> dict:
    gdf = gpd.read_file(ROI_SHP)
    if gdf.crs is None:
        raise ValueError(f"ROI 缺少坐标系：{ROI_SHP}")
    gdf = gdf.to_crs("EPSG:4326")
    ROI_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(ROI_GEOJSON, driver="GeoJSON", encoding="utf-8")
    utm = gdf.estimate_utm_crs()
    area_km2 = float(gdf.to_crs(utm).area.sum() / 1_000_000) if utm else None
    return {
        "rows": int(len(gdf)),
        "crs": str(gdf.crs),
        "bounds": [float(v) for v in gdf.total_bounds],
        "area_km2": area_km2,
        "geometry_types": sorted(gdf.geometry.geom_type.unique().tolist()),
    }


def update_project_paths(roi_info: dict) -> None:
    config = {
        "说明": "复制为 project_paths.json 后按实际数据路径修改。GEE 采样应使用缩小后的研究区 roi_xiao。",
        "roi_shp": str(ROI_SHP),
        "roi_geojson": str(ROI_GEOJSON.relative_to(PROJECT_DIR)),
        "roi_info": roi_info,
        "tif_dir": str(TIF_DIR),
        "reference_tif": str(REFERENCE_TIF),
        "gee_samples_csv": r"outputs\samples\poyang_2024_flood_samples.csv",
        "rainfall_gee_tif": r"data\raw\ganbei_poyang_20240623_0706_chirps_event_rainfall.tif",
        "aligned_rainfall_tif": r"outputs\rasters\rainfall.tif",
        "samples_with_factors_csv": r"outputs\samples\model_training_samples_with_factors.csv",
        "model_dir": "models",
        "figure_dir": "figures",
    }
    write_text(
        PROJECT_DIR / "configs" / "project_paths.example.json",
        json.dumps(config, ensure_ascii=False, indent=2),
    )


def rewrite_align_script() -> None:
    script = r'''
from __future__ import annotations

import argparse
from pathlib import Path

import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject


# 默认使用已经检查过网格一致的致灾因子作为参考网格。
DEFAULT_REFERENCE = Path(r"E:\新tif_裁\elevation.tif")
DEFAULT_OUTPUT = Path("outputs/rasters/rainfall_2024_event_aligned_to_factors.tif")

RESAMPLING_METHODS = {
    "nearest": Resampling.nearest,
    "bilinear": Resampling.bilinear,
    "cubic": Resampling.cubic,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 GEE 导出的 2024 事件降水 TIF 对齐到现有致灾因子网格。"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="GEE 导出的 2024 事件降水 TIF。",
    )
    parser.add_argument(
        "--reference",
        default=str(DEFAULT_REFERENCE),
        help=f"参考因子 TIF。默认：{DEFAULT_REFERENCE}",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"对齐后的输出 TIF。默认：{DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--band",
        type=int,
        default=1,
        help="输入降水 TIF 的波段序号。单波段累计降水用 1。",
    )
    parser.add_argument(
        "--resampling",
        choices=sorted(RESAMPLING_METHODS),
        default="bilinear",
        help="重采样方法。降水连续变量默认 bilinear。",
    )
    parser.add_argument(
        "--nodata",
        type=float,
        default=-9999.0,
        help="输出 NoData 值。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    reference_path = Path(args.reference)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"输入降水 TIF 不存在：{input_path}")
    if not reference_path.exists():
        raise FileNotFoundError(f"参考 TIF 不存在：{reference_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(reference_path) as ref, rasterio.open(input_path) as src:
        if ref.crs is None:
            raise ValueError(f"参考 TIF 缺少坐标系：{reference_path}")
        if src.crs is None:
            raise ValueError(f"输入降水 TIF 缺少坐标系：{input_path}")

        profile = ref.profile.copy()
        profile.update(
            {
                "driver": "GTiff",
                "count": 1,
                "dtype": "float32",
                "nodata": args.nodata,
                "compress": "lzw",
                "BIGTIFF": "YES",
            }
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            reproject(
                source=rasterio.band(src, args.band),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                src_nodata=src.nodata,
                dst_transform=ref.transform,
                dst_crs=ref.crs,
                dst_nodata=args.nodata,
                resampling=RESAMPLING_METHODS[args.resampling],
            )

    with rasterio.open(output_path) as out, rasterio.open(reference_path) as ref:
        aligned = (
            out.crs == ref.crs
            and out.width == ref.width
            and out.height == ref.height
            and out.transform == ref.transform
            and out.bounds == ref.bounds
        )
        print("2024 事件降水 TIF 对齐完成")
        print(f"输入文件：{input_path}")
        print(f"参考文件：{reference_path}")
        print(f"输出文件：{output_path}")
        print(f"输出坐标系：{out.crs}")
        print(f"输出宽高：{out.width} x {out.height}")
        print(f"输出分辨率：{out.res}")
        print(f"是否与参考网格完全一致：{aligned}")


if __name__ == "__main__":
    main()
'''
    write_text(PROJECT_DIR / "scripts" / "align_rainfall_to_factor_grid.py", script)


def rewrite_extract_script() -> None:
    script = r'''
from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.warp import transform as transform_coords
from shapely.geometry import Point


DEFAULT_TIF_DIR = Path(r"E:\新tif_裁")
DEFAULT_ROI = Path("data/raw/roi_xiao.geojson")
DEFAULT_OUTPUT = Path("outputs/samples/model_training_samples_with_factors.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将洪水/非洪水样本点与本地 TIF 致灾因子匹配，生成建模训练表。"
    )
    parser.add_argument(
        "--samples",
        required=True,
        help="GEE 导出的合并样本 CSV。需要包含 flood 字段，以及 .geo 或经纬度字段。",
    )
    parser.add_argument(
        "--tif-dir",
        default=str(DEFAULT_TIF_DIR),
        help=f"致灾因子 TIF 所在目录。默认：{DEFAULT_TIF_DIR}",
    )
    parser.add_argument(
        "--roi",
        default=str(DEFAULT_ROI),
        help="可选。研究区边界 shp/geojson。提供后会先过滤 ROI 外样本。",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"输出训练表 CSV 路径。默认：{DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--point-crs",
        default="EPSG:4326",
        help="样本点坐标系。GEE CSV 默认是 EPSG:4326。",
    )
    parser.add_argument(
        "--drop-nodata",
        action="store_true",
        help="删除任一 TIF 因子为 NoData 或空值的样本。",
    )
    return parser.parse_args()


def get_xy_from_samples(df: pd.DataFrame) -> tuple[list[float], list[float]]:
    """从 GEE CSV 中读取样本点坐标。优先使用 longitude/latitude，其次解析 .geo。"""
    lon_candidates = ["longitude", "lon", "x", "POINT_X"]
    lat_candidates = ["latitude", "lat", "y", "POINT_Y"]

    lon_col = next((col for col in lon_candidates if col in df.columns), None)
    lat_col = next((col for col in lat_candidates if col in df.columns), None)
    if lon_col and lat_col:
        return df[lon_col].astype(float).tolist(), df[lat_col].astype(float).tolist()

    if ".geo" not in df.columns:
        raise ValueError("样本 CSV 未找到 longitude/latitude、lon/lat、x/y 或 .geo 字段。")

    xs = []
    ys = []
    for value in df[".geo"]:
        geom = json.loads(value)
        if geom.get("type") != "Point":
            raise ValueError(f".geo 中存在非 Point 几何：{geom.get('type')}")
        x, y = geom["coordinates"][:2]
        xs.append(float(x))
        ys.append(float(y))
    return xs, ys


def filter_samples_by_roi(
    df: pd.DataFrame,
    xs: list[float],
    ys: list[float],
    point_crs: str,
    roi_path: Path,
) -> tuple[pd.DataFrame, list[float], list[float], int]:
    """按研究区边界过滤样本点，避免旧范围样本混入新研究区。"""
    if not roi_path.exists():
        return df, xs, ys, 0

    roi = gpd.read_file(roi_path)
    if roi.crs is None:
        raise ValueError(f"ROI 缺少坐标系：{roi_path}")

    points = gpd.GeoDataFrame(
        df.copy(),
        geometry=[Point(x, y) for x, y in zip(xs, ys)],
        crs=point_crs,
    ).to_crs(roi.crs)

    roi_union = roi.geometry.union_all()
    mask = points.geometry.within(roi_union) | points.geometry.touches(roi_union)
    filtered = points.loc[mask].drop(columns="geometry").copy()
    filtered_xs = [xs[i] for i, keep in enumerate(mask.tolist()) if keep]
    filtered_ys = [ys[i] for i, keep in enumerate(mask.tolist()) if keep]
    removed = int((~mask).sum())
    return filtered, filtered_xs, filtered_ys, removed


def normalize_nodata(value, nodata):
    """将 NoData 统一转换为空值，便于后续清洗。"""
    if nodata is None:
        return value
    try:
        if float(value) == float(nodata):
            return pd.NA
    except TypeError:
        return value
    return value


def main() -> None:
    args = parse_args()
    sample_path = Path(args.samples)
    tif_dir = Path(args.tif_dir)
    roi_path = Path(args.roi) if args.roi else None
    output_path = Path(args.output)

    if not sample_path.exists():
        raise FileNotFoundError(f"样本 CSV 不存在：{sample_path}")
    if not tif_dir.exists():
        raise FileNotFoundError(f"TIF 目录不存在：{tif_dir}")

    tif_paths = sorted(tif_dir.glob("*.tif"))
    if not tif_paths:
        raise FileNotFoundError(f"TIF 目录中没有 .tif 文件：{tif_dir}")

    df = pd.read_csv(sample_path)
    if "flood" not in df.columns:
        raise ValueError("样本 CSV 缺少 flood 字段，无法区分洪水/非洪水样本。")

    xs, ys = get_xy_from_samples(df)
    original_count = len(df)
    removed_by_roi = 0
    if roi_path is not None:
        df, xs, ys, removed_by_roi = filter_samples_by_roi(df, xs, ys, args.point_crs, roi_path)

    with rasterio.open(tif_paths[0]) as ref:
        raster_crs = ref.crs

    if raster_crs is None:
        raise ValueError(f"参考 TIF 缺少坐标系：{tif_paths[0]}")

    sample_x, sample_y = transform_coords(args.point_crs, raster_crs, xs, ys)
    coords = list(zip(sample_x, sample_y))

    df["sample_x"] = sample_x
    df["sample_y"] = sample_y
    df["sample_crs"] = raster_crs.to_string()

    nodata_columns = []
    for tif_path in tif_paths:
        factor_name = tif_path.stem
        with rasterio.open(tif_path) as src:
            if src.crs != raster_crs:
                raise ValueError(f"坐标系不一致：{tif_path.name}")
            values = [item[0] for item in src.sample(coords)]
            cleaned = [normalize_nodata(value, src.nodata) for value in values]
            df[factor_name] = cleaned
            nodata_columns.append(factor_name)

    before_drop_count = len(df)
    if args.drop_nodata:
        df = df.dropna(subset=nodata_columns).copy()
    after_count = len(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    label_counts = df["flood"].value_counts(dropna=False).to_dict()
    print("样本因子提取完成")
    print(f"原始样本数：{original_count}")
    print(f"ROI 外剔除样本数：{removed_by_roi}")
    print(f"NoData 清洗前样本数：{before_drop_count}")
    print(f"输出样本数：{after_count}")
    print(f"类别数量：{label_counts}")
    print(f"TIF 因子数：{len(tif_paths)}")
    print(f"输出文件：{output_path}")
    print(f"栅格坐标系：{raster_crs}")


if __name__ == "__main__":
    main()
'''
    write_text(PROJECT_DIR / "scripts" / "extract_tif_values_to_samples.py", script)


def update_gee_script() -> None:
    path = PROJECT_DIR / "scripts" / "gee_poyang_2024_flood_samples.js"
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(
        r"var ROI_ASSET = '.*?';",
        "var ROI_ASSET = 'users/your_username/roi_xiao';",
        text,
        count=1,
    )
    note = (
        "// 研究区已缩小：请把 F:/研二/毕业论文/洪涝敏感性/研究区_xiao/roi.shp "
        "或 data/raw/roi_xiao.geojson 上传到 GEE Asset，并将 ROI_ASSET 改为真实 asset 路径。\n"
    )
    if "研究区已缩小" not in text:
        text = note + text
    path.write_text(text, encoding="utf-8")


def update_run_config() -> None:
    path = PROJECT_DIR / ".idea" / "runConfigurations" / "03_extract_sample_factors.xml"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'value="--samples .*?"',
        'value="--samples outputs/samples/poyang_2024_flood_samples.csv --roi data/raw/roi_xiao.geojson --output outputs/samples/model_training_samples_with_factors.csv"',
        text,
        count=1,
    )
    path.write_text(text, encoding="utf-8")


def write_roi_doc(roi_info: dict) -> None:
    doc = f'''
# 缩小研究区 ROI 使用说明

## 本地 ROI

原始文件：

```text
{ROI_SHP}
```

已导出到新项目：

```text
{ROI_GEOJSON}
```

基本信息：

```text
要素数：{roi_info["rows"]}
坐标系：{roi_info["crs"]}
范围：{roi_info["bounds"]}
面积约：{roi_info["area_km2"]:.2f} km²
几何类型：{roi_info["geometry_types"]}
```

## GEE 采样怎么用

GEE 不能直接读取电脑上的 `F:\\...\\roi.shp`。你需要把以下任一文件上传为 GEE Asset：

```text
F:\\研二\\毕业论文\\洪涝敏感性\\研究区_xiao\\roi.shp
F:\\studyPy\\flood_analysis_2024\\data\\raw\\roi_xiao.geojson
```

上传后，在 `scripts/gee_poyang_2024_flood_samples.js` 中修改：

```javascript
var ROI_ASSET = 'users/your_username/roi_xiao';
```

改成你自己的真实 Asset 路径。

## 本地样本属性提取怎么用

`extract_tif_values_to_samples.py` 已支持 `--roi` 参数。建议运行时带上：

```bash
python scripts/extract_tif_values_to_samples.py --samples outputs/samples/poyang_2024_flood_samples.csv --roi data/raw/roi_xiao.geojson --output outputs/samples/model_training_samples_with_factors.csv --drop-nodata
```

这样会先删除 ROI 外样本，再提取 TIF 因子值。
'''
    write_text(ROI_DOC, doc)


def main() -> None:
    roi_info = export_roi()
    update_project_paths(roi_info)
    rewrite_align_script()
    rewrite_extract_script()
    update_gee_script()
    update_run_config()
    write_roi_doc(roi_info)
    print(json.dumps({"roi_geojson": str(ROI_GEOJSON), "roi_info": roi_info}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
