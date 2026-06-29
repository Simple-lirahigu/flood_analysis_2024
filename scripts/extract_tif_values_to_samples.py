from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import rasterio
from rasterio.warp import transform as transform_coords


DEFAULT_TIF_DIR = Path(r"E:\新tif_裁")
DEFAULT_OUTPUT = Path("outputs/model_training_samples_with_factors.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将洪水/非洪水样本点与本地 TIF 致灾因子匹配，生成建模训练表。"
    )
    parser.add_argument(
        "--samples",
        required=True,
        help="GEE 导出的合并样本 CSV。需包含 flood 字段，以及 .geo 或经纬度字段。",
    )
    parser.add_argument(
        "--tif-dir",
        default=str(DEFAULT_TIF_DIR),
        help="致灾因子 TIF 所在目录。默认：E:\\新tif_裁",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="输出训练表 CSV 路径。",
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
        raise ValueError(
            "样本 CSV 中未找到 longitude/latitude、lon/lat、x/y 或 .geo 字段。"
        )

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
        raise ValueError("样本 CSV 中缺少 flood 字段，无法区分洪水/非洪水样本。")

    xs, ys = get_xy_from_samples(df)

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

    before_count = len(df)
    if args.drop_nodata:
        df = df.dropna(subset=nodata_columns).copy()
    after_count = len(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    label_counts = df["flood"].value_counts(dropna=False).to_dict()
    print("样本因子提取完成")
    print(f"输入样本数：{before_count}")
    print(f"输出样本数：{after_count}")
    print(f"类别数量：{label_counts}")
    print(f"TIF 因子数：{len(tif_paths)}")
    print(f"输出文件：{output_path}")
    print(f"栅格坐标系：{raster_crs}")


if __name__ == "__main__":
    main()
