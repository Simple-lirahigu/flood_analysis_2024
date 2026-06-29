from __future__ import annotations

import csv
import json
from pathlib import Path

import rasterio


INPUT_DIR = Path(r"E:\新tif_裁")
OUTPUT_CSV = Path("outputs/tif_alignment_report.csv")
OUTPUT_JSON = Path("outputs/tif_alignment_report.json")


def round_tuple(values, ndigits=8):
    return tuple(round(float(v), ndigits) for v in values)


def main() -> None:
    tif_paths = sorted(INPUT_DIR.glob("*.tif"))
    if not tif_paths:
        raise SystemExit(f"未找到 TIF 文件：{INPUT_DIR}")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for path in tif_paths:
        with rasterio.open(path) as src:
            row = {
                "name": path.name,
                "path": str(path),
                "crs": src.crs.to_string() if src.crs else "",
                "width": src.width,
                "height": src.height,
                "count": src.count,
                "dtype": ",".join(src.dtypes),
                "nodata": src.nodata,
                "res_x": src.res[0],
                "res_y": src.res[1],
                "left": src.bounds.left,
                "bottom": src.bounds.bottom,
                "right": src.bounds.right,
                "top": src.bounds.top,
                "transform": tuple(src.transform)[:6],
            }
            rows.append(row)

    reference = rows[0]
    for row in rows:
        row["same_crs_as_ref"] = row["crs"] == reference["crs"]
        row["same_size_as_ref"] = (
            row["width"] == reference["width"]
            and row["height"] == reference["height"]
        )
        row["same_res_as_ref"] = round_tuple((row["res_x"], row["res_y"])) == round_tuple(
            (reference["res_x"], reference["res_y"])
        )
        row["same_bounds_as_ref"] = round_tuple(
            (row["left"], row["bottom"], row["right"], row["top"])
        ) == round_tuple(
            (
                reference["left"],
                reference["bottom"],
                reference["right"],
                reference["top"],
            )
        )
        row["same_transform_as_ref"] = round_tuple(row["transform"]) == round_tuple(
            reference["transform"]
        )
        row["aligned_with_ref"] = all(
            [
                row["same_crs_as_ref"],
                row["same_size_as_ref"],
                row["same_res_as_ref"],
                row["same_bounds_as_ref"],
                row["same_transform_as_ref"],
            ]
        )

    fieldnames = [
        "name",
        "crs",
        "width",
        "height",
        "count",
        "dtype",
        "nodata",
        "res_x",
        "res_y",
        "left",
        "bottom",
        "right",
        "top",
        "transform",
        "same_crs_as_ref",
        "same_size_as_ref",
        "same_res_as_ref",
        "same_bounds_as_ref",
        "same_transform_as_ref",
        "aligned_with_ref",
        "path",
    ]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    summary = {
        "input_dir": str(INPUT_DIR),
        "reference_file": reference["name"],
        "file_count": len(rows),
        "all_same_crs": all(row["same_crs_as_ref"] for row in rows),
        "all_same_size": all(row["same_size_as_ref"] for row in rows),
        "all_same_res": all(row["same_res_as_ref"] for row in rows),
        "all_same_bounds": all(row["same_bounds_as_ref"] for row in rows),
        "all_same_transform": all(row["same_transform_as_ref"] for row in rows),
        "all_aligned": all(row["aligned_with_ref"] for row in rows),
        "rows": rows,
    }
    OUTPUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
