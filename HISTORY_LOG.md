# History Log

2026-06-29: Read the 2024 International Journal of Digital Earth flood susceptibility paper and extracted its method logic for possible Jiangxi 2024 rainstorm replication.
2026-06-29: Created a grouped related-reference list for flood susceptibility mapping and Jiangxi 2024 rainstorm replication.
2026-06-29: Added a GEE Sentinel-1 script to extract flood and non-flood sample points for the 2024-06-23 to 2024-07-06 Poyang Lake / Ganbei flood event.
2026-06-29: Revised the GEE flood sample extraction script with Chinese comments and stricter non-flood sample filtering.
2026-06-29: Checked 12 disaster-conditioning TIF factors in E:\新tif_裁 and confirmed consistent CRS, resolution, extent, shape, and transform.
2026-06-29: Added a local script to extract aligned TIF factor values to GEE-exported flood/non-flood sample points.
2026-06-29: Added GEE and local alignment scripts to remake the 2024-06-23 to 2024-07-06 event rainfall TIF.
2026-06-29: Reviewed the emergency-material demand prediction manuscript and assessed its coherence with the 2024 Poyang/Ganbei flood susceptibility thesis plan.
2026-06-29: Rolled back generated files from the original F:\studyPy\flood_analysis project and created a separate F:\studyPy\flood_analysis_2024 PyCharm project using E:\Anaconda3\envs\flood_analysis.
2026-06-29: Fixed PyCharm run configurations in F:\studyPy\flood_analysis_2024 by adding the project module name to resolve the ModuleRootManager null error.
2026-06-29: Added the smaller ROI from F:\研二\毕业论文\洪涝敏感性\研究区_xiao\roi.shp to the new PyCharm project, including GeoJSON export, local sample filtering, and GEE Asset placeholder guidance.
2026-06-29: Searched CNKI for flood susceptibility and sample-selection literature and created a candidate reference list focused on flood susceptibility mapping and sample point selection.
2026-06-29: Imported 10 CNKI flood susceptibility/sample-selection candidate metadata records into the Zotero collection 大论文; full-text attachments still require manual CNKI/Zotero Connector capture.
2026-06-29: Added an English reference list for flood susceptibility mapping, Sentinel-1/GEE flood extraction, sample construction, CHIRPS/JRC/SRTM/MERIT datasets, and flood-risk background.
2026-06-29: Exported 15 CNKI journal-article candidates on flood/flood-susceptibility topics from Zotero metadata into Markdown and RIS for Zotero import.
2026-06-29: Recorded the local shell preference to use PowerShell-compatible commands and avoid Bash-only syntax on this Windows host.
2026-06-29: Added a standalone GEE script for extracting 2024 flood and non-flood sample points in the smaller roi_xiao study area.
2026-06-29: Checked the roi_xiao GEE flood/non-flood sampling script and revised the label image so sample classes inherit the Sentinel-1 projection instead of a default constant-image projection.
2026-06-29: Fixed the GEE stratifiedSample class-band type error by converting the `flood` label band to Byte before sampling.
2026-06-29: Hardened the GEE sample label construction by creating the `flood` class band from `ee.Image(0).byte()` and setting the Sentinel-1 projection before `stratifiedSample`.
2026-06-29: Replaced GEE `stratifiedSample` with separate flood and non-flood `sample` calls, adding `label=1` for flood points and `label=0` for non-flood points.
2026-06-29: Fixed low GEE sample counts by unmasking diagnostic export bands and setting `dropNulls: false` so sample counts are controlled by flood/non-flood candidate masks rather than auxiliary-band NoData intersections.
2026-06-29: Added a conservative `floodCoreMask` to the GEE sampling script so flood sample points are drawn from eroded flood interiors rather than uncertain flood edges.
2026-06-29: Fixed the GEE `Number.eq Parameter left is required` error by assigning `label` and `flood` directly in separate flood/non-flood sample branches instead of reading possibly null feature labels.
2026-06-29: Fixed low GEE sample counts caused by constant-label image projection by deriving label bands from `s1Drop` and specifying `projection: s1Projection` in `sample()`.
2026-06-29: Replaced `sample(numPixels=...)` with full candidate sampling plus `randomColumn().sort().limit()` to avoid GEE returning only 23 samples despite large candidate masks.
2026-06-29: Added SHP exports for flood, non-flood, and merged sample points in the GEE sampling script while keeping CSV exports.
2026-06-29: Merged 1500 flood and 1500 non-flood GEE CSV sample points and extracted 11 local TIF conditioning factors into a 3000-row modelling table.
2026-06-29: Re-ran sample factor extraction after adding `rainfall.tif`, producing a 2991-row modelling table with 12 conditioning factors.
2026-06-30: Completed training-table QC, factor descriptive statistics, Pearson correlation, categorical frequency tables, VIF analysis, and QC figures for the rainfall-inclusive 2024 sample table.
