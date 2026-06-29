# Project Memory

## 2026-06-29 Literature Reading

- Read local article: `F:\研二\毕业论文\洪涝敏感性\Leveraging machine learning and open-source spatial datasets to enhance flood susceptibility mapping in transboundary river basin.pdf`.
- Article DOI: `10.1080/17538947.2024.2313857`.
- Core workflow: flood inventory preparation, conditioning factor preparation, multicollinearity screening with VIF/TOL, feature relevance with correlation and information gain ratio, model training, ROC/AUROC and confusion-matrix evaluation, susceptibility classification.
- Article models: RF, SVM, ANN, LSTM. RF performed best overall by testing AUROC, MSE, RMSE, F1-score, and Kappa in the reported study.
- Article conditioning factors: elevation, slope, aspect, curvature, distance to river, drainage density, STI, SPI, TWI, soil type, NDVI, LULC, rainfall. Aspect was removed in the paper because of multicollinearity.
- Flood inventory in the paper used historical records, global flood datasets, and Sentinel-1 flood extent extraction. Permanent or seasonal water, steep slopes, and small connected noise patches were masked.

## Local Data Noted Outside Workspace

- Existing related data were seen under `F:\研二\毕业论文\洪涝敏感性`, including Jiangxi 2020 flood training data, flood labels, environmental rasters, ROI shapefiles, and a prior integrated susceptibility map.
- These files were inspected by name only unless otherwise stated; do not treat their contents as verified.

## 2026-06-29 Related References

- Created `docs/related_references_flood_susceptibility.md`.
- The reference list is grouped into target paper, machine-learning flood susceptibility mapping, Sentinel-1/GEE flood extraction, open spatial datasets, flood-risk background, and suggested Chinese CNKI search keywords.
- Chinese CNKI entries were not fabricated; they require manual verification from CNKI/Wanfang or the university library.

## 2026-06-29 Jiangxi 2024 Flood Sample Plan

- Case event: Poyang Lake / Northern Jiangxi flood from `2024-06-23` to `2024-07-06`.
- Study area: Ganbei region; the user already has the ROI and disaster-conditioning factors.
- Created `scripts/gee_poyang_2024_flood_samples.js` to extract flood and non-flood samples from Sentinel-1 in GEE.
- The script uses pre-flood Sentinel-1 from `2024-06-01` to `2024-06-15` and flood-period Sentinel-1 from `2024-06-23` to `2024-07-06` by default.
- Main masks: JRC permanent/long-season water, SRTM slope, connected-pixel filtering, and valid Sentinel-1 coverage.
- The default backscatter drop threshold is `1.5 dB`; it must be calibrated for Ganbei/Poyang Lake before final modelling.
- Revised the GEE sample script so later code comments are in Chinese, non-flood samples avoid a `90 m` flood-edge buffer, and non-flood samples exclude high-frequency water areas using JRC water occurrence greater than `20%`.

## 2026-06-29 TIF Factor Alignment Check

- Checked 12 TIF factors under `E:\新tif_裁`: aspect, curvature, dtr, elevation, hand, lulc2, ndvi, rainfall, slope, soil2, spi, and twi.
- All checked factors have consistent CRS, resolution, width, height, bounds, affine transform, and grid alignment.
- Shared CRS: `CGCS2000 / 3-degree Gauss-Kruger zone 39`, central meridian `117`, unit metre.
- Shared raster size: width `39602`, height `24570`; shared resolution `12.450803695479 m`.
- Reports generated: `outputs/tif_alignment_report.csv`, `outputs/tif_alignment_report.json`, and `outputs/tif_alignment_report.md`.
- `lulc2.tif` and `soil2.tif` are categorical factors; they need categorical treatment or cautious interpretation during modelling.
- `rainfall.tif` still needs content verification: confirm whether it is event rainfall for `2024-06-23` to `2024-07-06` or a climatological rainfall layer.
- User clarified that the current precipitation layer is from 2020, so it should not be used as the 2024 event rainfall factor without replacement or explicit caveat.
- Added `scripts/extract_tif_values_to_samples.py` to extract all aligned TIF factor values to GEE-exported flood/non-flood sample CSVs. The script reprojects GEE WGS84 points to the raster CRS before sampling.
- Added `scripts/gee_export_poyang_2024_event_rainfall.js` to export CHIRPS 2024 event rainfall factors for `2024-06-23` to `2024-07-06`: event total rainfall, max 1-day rainfall, and max 3-day rainfall.
- Added `scripts/align_rainfall_to_factor_grid.py` to align the exported rainfall TIF to `E:\新tif_裁\elevation.tif` so the new rainfall layer matches the existing factor grid.

## 2026-06-29 Emergency Material Demand Manuscript

- Reviewed `F:\研二\毕业论文\应急物资预测\GM应急物资动态需求预测改稿20250416.docx`.
- The manuscript title is about dynamic emergency-relief material demand prediction for flood disasters.
- Its method uses an improved GM(1,1) model for affected-population prediction, then combines inventory/material-demand rules to estimate drinking water, food, medicine, tents, quilts, and signal base-station demand.
- Its case is the 2024 Jiangxi/Poyang Lake flood from late June to early July, which is consistent with the current flood-susceptibility case period.
- It can be coherent with the flood-susceptibility thesis if positioned as a downstream application: susceptibility mapping identifies where flood impacts are likely, while GM(1,1) demand prediction estimates what relief materials are needed after impacts occur.
- Main risk: the two parts should not look like two unrelated papers; the thesis needs a shared problem chain such as "hazard identification - affected population estimation - material demand support".

## 2026-06-29 PyCharm / Anaconda Project Setup

- The first attempt added project files to `F:\studyPy\flood_analysis`; at the user's request, the generated files were rolled back from that original project. Only empty directories created during the first attempt may remain because directory deletion is intentionally avoided by project safety rules.
- Created a separate PyCharm project at `F:\studyPy\flood_analysis_2024`.
- The new project uses the user-specified Conda interpreter: `E:\Anaconda3\envs\flood_analysis\python.exe` (Python 3.9.19).
- New project structure includes `scripts`, `configs`, `docs`, `data/raw`, `data/intermediate`, `data/processed`, `outputs/samples`, `outputs/rasters`, `outputs/metrics`, `outputs/tables`, `models`, `figures`, and `reports`.
- Copied reusable scripts into the new project: TIF alignment check, sample-factor extraction, rainfall-grid alignment, Sentinel-1 flood sample GEE script, and CHIRPS event rainfall GEE export script.
- Added PyCharm run configuration examples under `F:\studyPy\flood_analysis_2024\.idea\runConfigurations`.
- The copied Python scripts compiled successfully with `E:\Anaconda3\envs\flood_analysis\python.exe -m py_compile`.
- Dependency check in the specified Conda environment found pandas, numpy, rasterio, scikit-learn, xgboost, matplotlib, seaborn, joblib, and geopandas available; rioxarray, xarray, and earthengine-api/ee were missing.
- Added `environment.yml` and `docs/dependency_check.md` to the new project to document the intended Conda environment and missing packages.
- Fixed PyCharm run configurations in `F:\studyPy\flood_analysis_2024\.idea\runConfigurations` after PyCharm reported `ModuleRootManager.getInstance must not be null`; the fix added `<module name="flood_analysis_2024" />` to each Python run configuration.

## 2026-06-29 Smaller ROI Update

- User narrowed the study area to `F:\研二\毕业论文\洪涝敏感性\研究区_xiao\roi.shp`.
- The ROI shapefile has 21 polygon/multipolygon features, CRS `EPSG:4326`, bounds approximately `(115.1015, 28.1606, 117.2563, 30.0795)`, and area approximately `25,174.46 km2`.
- Exported the ROI to `F:\studyPy\flood_analysis_2024\data\raw\roi_xiao.geojson` for local project use and optional GEE upload.
- Updated `F:\studyPy\flood_analysis_2024\scripts\extract_tif_values_to_samples.py` to support a `--roi` argument and filter samples outside the smaller ROI before extracting TIF factor values.
- Updated PyCharm run configuration `03_extract_sample_factors.xml` to include `--roi data/raw/roi_xiao.geojson`.
- Updated `F:\studyPy\flood_analysis_2024\scripts\gee_poyang_2024_flood_samples.js` with a smaller-ROI Asset placeholder `users/your_username/roi_xiao`; the user must replace it with the real GEE Asset path after uploading the ROI.
- Added `F:\studyPy\flood_analysis_2024\docs\roi_xiao_usage.md` and updated `configs/project_paths.example.json`.

## 2026-06-29 CNKI Flood Susceptibility References

- Searched CNKI in the user's logged-in browser for `洪水易发性`, `洪水易发性 样本点`, and related sample-selection terms.
- Created `docs/cnki_flood_susceptibility_sample_references.md`.
- Important CNKI candidate for sample selection: 孙加慧, 刘庚元, 赵薛强. `基于逆频率比采样方法的洪水易发性评价`. 人民黄河, 2025.
- Other relevant CNKI candidates include 郭传银等 `基于可解释性人工智能绘制空间洪水易发性图`, 邓雅洁 `基于机器学习的中国大陆洪涝易发性评估研究`, 李国豪 `基于多模型融合的山洪灾害易发性评估`, and 曹贤龙 `基于大数据挖掘的洪水灾害易发性评价系统设计`.
- CNKI metadata should be verified from article detail pages or downloaded full texts before final thesis citation.
- Imported 10 CNKI candidate metadata records into the user's Zotero collection `大论文` via the local Zotero Connector API. The collection key is `UZXTKXXT`.
- Generated `outputs/cnki_flood_susceptibility_references.ris`, `outputs/zotero_test_item.json`, and `outputs/zotero_cnki_flood_items_batch.json`.
- The Zotero import contains metadata and notes only; full CNKI PDF/CAJ attachments were not automatically downloaded.
- Created `docs/english_flood_susceptibility_references.md`, grouping English references for machine-learning flood susceptibility mapping, flood inventory/sample construction, Sentinel-1/GEE flood mapping, open spatial datasets, and flood-risk background.
- Created `docs/cnki_honglao_15_journal_candidates.md` and `outputs/cnki_honglao_15_journal_candidates.ris`, selecting 15 CNKI journal-article candidates related to `洪涝`, `洪涝易发性`, `洪水易发性`, flood risk assessment, and flood remote sensing.
- The 15-journal export was generated from a read-only Zotero database snapshot to avoid corrupting Zotero or creating duplicate records. Many selected items already have PDF attachments in Zotero; several still need CNKI PDF/CAJ attachment completion.

## 2026-06-29 Local Shell Preference

- This host uses Windows PowerShell as the working shell. Avoid Bash-only syntax such as `python - <<EOF`, heredoc redirects, and Unix shell assumptions.
- When running inline Python on this host, use PowerShell-compatible patterns such as `python -c "..."` or create a temporary/helper `.py` file and run it.

## 2026-06-29 GEE Flood / Non-Flood Sample Script

- Added workspace script `scripts/gee_extract_2024_flood_nonflood_samples_roi_xiao.js` as a clearer standalone GEE workflow for extracting 2024 event flood and non-flood sample points from the smaller `roi_xiao` study area.
- The script uses Sentinel-1 GRD, event window `2024-06-23` to `2024-07-06`, pre-flood window `2024-06-01` to `2024-06-15`, default `VV` polarization, JRC permanent/high-frequency water masks, SRTM slope mask, connected-pixel filtering, and a flood-edge buffer for conservative non-flood sampling.
- Default sample targets are `3000` flood points and `3000` non-flood points at `100 m` sampling scale. This sampling scale only reduces spatial autocorrelation approximately; strict point-distance filtering or spatial block validation should be done later for thesis-quality robustness.
- The ROI Asset path remains `users/your_username/roi_xiao` and must be replaced after uploading the local smaller ROI to GEE.
- After review, the label image was revised to use `preMedian.multiply(0)` instead of `ee.Image.constant()` so the sample class band inherits the Sentinel-1 projection/grid before `stratifiedSample`.
- When GEE reported `The class band must be integer typed`, the `flood` label band was explicitly converted with `.toByte()` before `stratifiedSample`, and `print('样本标签波段类型', labelImage.bandTypes())` was added for Console verification.
- Because the old submitted GEE export tasks can keep failing with the previous computation graph, the user must click `Run` again in the Code Editor and submit the newly generated tasks after updating the script. The hardened version creates `labelImage` from `ee.Image(0).byte()` and applies `setDefaultProjection(preMedian.projection())`.
- To avoid repeated GEE `Image.stratifiedSample: The class band must be integer typed` errors, the sample script was revised to remove `stratifiedSample` entirely. It now samples flood and non-flood candidates separately with `sample()`, then merges the results. Exported points include `label=1` for flood samples and `label=0` for non-flood samples, while keeping `flood` as a compatibility field.
- If GEE returns very few samples despite large candidate-area diagnostics, the likely cause is `sample()` dropping pixels when any auxiliary export band is masked. The script now unmask-fills diagnostic bands (`s1_drop_db`, Sentinel-1 pre/flood, slope, JRC seasonality/occurrence) and uses `dropNulls: false`. It also prints candidate pixel counts at the sampling scale.
- To improve flood-sample precision, the GEE script now builds `floodCoreMask` by eroding `floodMask` with `floodCoreBufferMeters` (default `30 m`) and samples flood points from this core mask. If core candidate counts are too low, reduce `floodCoreBufferMeters` to `10` or `0`.
- When GEE reported `Number.eq Parameter 'left' is required and may not be null`, the cause was reading `feature.get('label')` in `addCommonProperties` after `sample()` could return null-label features. The script now sets `label` and `flood` directly for each branch (`1` for flood, `0` for non-flood) and uses `dropNulls: true`.
- If GEE shows large candidate pixel counts but actual `sample()` output remains tiny (for example 23 samples), suspect the projection of the first sample band. The script now derives `label` from `s1Drop.multiply(0).add(labelValue).toByte()` instead of a pure constant image, and each `sample()` call explicitly sets `projection: s1Projection`.
- If `sample(numPixels=...)` still returns only 23 samples despite large candidate masks, the script now avoids `numPixels`: it samples all candidate pixels at the chosen scale, applies `randomColumn('random', seed)`, sorts by `random`, and uses `limit(targetSamples)` for the final flood/non-flood sample counts.
- The GEE sample script now exports sample points both as CSV and SHP: flood samples, non-flood samples, and merged samples. SHP export generates multiple sidecar files that must be kept together when downloaded.
