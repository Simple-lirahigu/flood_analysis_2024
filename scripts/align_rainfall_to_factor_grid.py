from __future__ import annotations

import argparse
from pathlib import Path

import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject


DEFAULT_REFERENCE = Path(r"E:\新tif_裁\elevation.tif")
DEFAULT_OUTPUT = Path("outputs/rainfall_2024_event_aligned_to_factors.tif")


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
        help="参考因子 TIF。默认使用 E:\\新tif_裁\\elevation.tif。",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="对齐后的输出 TIF。",
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
