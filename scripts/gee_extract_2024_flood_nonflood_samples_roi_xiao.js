/**** 2024-06-23 至 2024-07-06 鄱阳湖/赣北洪灾样本点提取脚本
 *
 * 目的：
 * 1. 使用 Sentinel-1 SAR 洪前/洪期变化检测提取新增洪水候选区。
 * 2. 从洪水候选区抽取洪水样本点 flood = 1。
 * 3. 从稳定非水体、远离洪水边界的位置抽取非洪水样本点 flood = 0。
 * 4. 导出洪水点、非洪水点、合并样本点和洪水掩膜，供后续洪水易发性建模使用。
 *
 * 使用前必须修改：
 * - ROI_ASSET：替换为你上传到 GEE Assets 的 roi_xiao 路径。
 *
 * 重要说明：
 * - GEE 的 filterDate 结束日期是“左闭右开”，所以事件期 2024-06-23 至 2024-07-06
 *   在脚本里写成 2024-06-23 至 2024-07-07。
 * - 本脚本得到的是“基于 Sentinel-1 变化检测的洪水样本候选点”，正式论文中仍建议结合
 *   Sentinel-2、新闻/水位记录、已有洪水范围或人工目视解译做质量检查。
 * - sampleScaleForPointsMeters 用于降低空间自相关风险，但不等于严格最小点间距。
 *   如果要达到高水平论文要求，建议导出后在本地再做最小距离筛选或空间分块验证。
 ****/

// =========================
// 1. 参数区
// =========================

// TODO：替换为你上传到 GEE 的缩小研究区 roi_xiao。
// 示例：var ROI_ASSET = 'projects/ee-yangsimple237/assets/roi';
var ROI_ASSET = 'projects/ee-yangsimple237/assets/roi';
var roiFc = ee.FeatureCollection(ROI_ASSET);
var roi = roiFc.geometry();

// 事件期：用户确定的 2024 年鄱阳湖/赣北洪灾窗口。
var floodStart = '2024-06-23';
var floodEndExclusive = '2024-07-07';
var floodEndInclusive = '2024-07-06';

// 洪前参考期：应尽量选择无明显洪水、无持续强降雨积水的时间。
var preStart = '2024-06-01';
var preEndExclusive = '2024-06-16';
var preEndInclusive = '2024-06-15';

// Sentinel-1 参数。
var polarization = 'VV';
var orbitPass = null; // 可改为 'ASCENDING' 或 'DESCENDING'。正式实验建议固定轨道方向后对比。

// 洪水提取参数。
var smoothingRadiusMeters = 50; // SAR 斑点噪声平滑半径。
var backscatterDropThresholdDb = 1.5; // 洪期相对洪前后向散射下降阈值，需目视校准。
var maxSlopeDeg = 5; // 去除较陡区域，降低地形阴影误判。
var permanentWaterSeasonalityMonths = 10; // JRC seasonality >= 10 视为常年水体。
var nonFloodMaxWaterOccurrence = 20; // 非洪水样本避开水体出现频率较高区域。
var minConnectedPixels = 8; // 去除孤立小斑块。
var floodCoreBufferMeters = 30; // 洪水样本避开洪水边界，只从洪水核心区抽点。若样本太少可改为 10 或 0。
var floodEdgeBufferMeters = 120; // 非洪水点避开洪水边界不确定区。

// 样本参数。
var targetFloodSamples = 1500;
var targetNonFloodSamples = 1500;
var sampleScaleForPointsMeters = 100; // 用较粗采样尺度近似降低样本空间自相关。
var randomSeed = 20240706;

// 导出参数。
var exportFolder = 'GEE_FLOOD_SAMPLES';
var exportPrefix = 'ganbei_roi_xiao_20240623_0706';

Map.centerObject(roi, 8);
Map.addLayer(roiFc, {color: 'yellow'}, '研究区 roi_xiao', false);

// =========================
// 2. Sentinel-1 数据准备
// =========================

function getSentinel1(startDate, endDate) {
  var col = ee.ImageCollection('COPERNICUS/S1_GRD')
    .filterBounds(roi)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .filter(ee.Filter.eq('resolution_meters', 10))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', polarization))
    .select(polarization);

  if (orbitPass !== null) {
    col = col.filter(ee.Filter.eq('orbitProperties_pass', orbitPass));
  }

  return col;
}

var preCol = getSentinel1(preStart, preEndExclusive);
var floodCol = getSentinel1(floodStart, floodEndExclusive);

print('洪前 Sentinel-1 影像数量', preCol.size());
print('洪期 Sentinel-1 影像数量', floodCol.size());
print('洪前轨道方向统计', preCol.aggregate_histogram('orbitProperties_pass'));
print('洪期轨道方向统计', floodCol.aggregate_histogram('orbitProperties_pass'));
print('洪前影像列表', preCol.aggregate_array('system:index'));
print('洪期影像列表', floodCol.aggregate_array('system:index'));

// Sentinel-1 GRD 在 GEE 中为 dB 尺度，使用中值合成降低单景噪声影响。
var preMedian = preCol.median().clip(roi);
var floodMedian = floodCol.median().clip(roi);

// 对 SAR 斑点噪声做中值滤波。半径过大会抹平窄河道和小洪水斑块，需要谨慎。
var preSmooth = preMedian.focal_median({
  radius: smoothingRadiusMeters,
  units: 'meters'
});

var floodSmooth = floodMedian.focal_median({
  radius: smoothingRadiusMeters,
  units: 'meters'
});

// 洪水淹没后，开阔水体通常导致 SAR 后向散射降低。
// 这里定义为洪前 dB - 洪期 dB，数值越大，越可能是新增水体或湿润区。
var s1Drop = preSmooth.subtract(floodSmooth).rename('s1_drop_db');
var validS1 = preMedian.mask().and(floodMedian.mask()).rename('valid_s1');

// =========================
// 3. 辅助掩膜
// =========================

var gsw = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').clip(roi);
var seasonality = gsw.select('seasonality').rename('jrc_seasonality');
var occurrence = gsw.select('occurrence').rename('jrc_occurrence');

// 剔除常年水体，避免把湖泊、主河道当作洪水样本。
var nonPermanentWater = seasonality.lt(permanentWaterSeasonalityMonths);

// 非洪水样本需要更加保守，避开水体出现频率较高的湿地、湖汊、水田等区域。
var stableNonWater = occurrence.lte(nonFloodMaxWaterOccurrence);

// 坡度掩膜，减少山区阴影和雷达几何畸变导致的误判。
var dem = ee.Image('USGS/SRTMGL1_003').clip(roi);
var slope = ee.Terrain.slope(dem).rename('slope_deg');
var lowSlope = slope.lte(maxSlopeDeg);

// =========================
// 4. 洪水掩膜与非洪水候选区
// =========================

var rawFlood = s1Drop.gte(backscatterDropThresholdDb)
  .and(nonPermanentWater)
  .and(lowSlope)
  .and(validS1)
  .rename('raw_flood');

// 连通像元过滤，去除孤立噪声。
var connectedPixels = rawFlood.selfMask().connectedPixelCount(100, true);
var floodMask = rawFlood
  .updateMask(rawFlood)
  .updateMask(connectedPixels.gte(minConnectedPixels))
  .rename('flood_mask');

// 洪水核心区：对洪水掩膜做内部收缩，减少边界混合像元和错标点。
// floodCoreBufferMeters 越大，洪水样本越保守，但可抽样数量会减少。
var floodCoreMask = floodMask.unmask(0)
  .focal_min({
    radius: floodCoreBufferMeters,
    units: 'meters'
  })
  .eq(1)
  .selfMask()
  .rename('flood_core_mask');

// 洪水边界缓冲区。非洪水点不从边界附近抽取，降低错标风险。
var floodBuffer = floodMask.unmask(0)
  .focal_max({
    radius: floodEdgeBufferMeters,
    units: 'meters'
  })
  .rename('flood_buffer');

var nonFloodCandidate = floodBuffer.eq(0)
  .and(nonPermanentWater)
  .and(stableNonWater)
  .and(lowSlope)
  .and(validS1)
  .rename('nonflood_candidate');

// =========================
// 5. 面积诊断
// =========================

function printAreaKm2(maskImage, label) {
  var area = ee.Image.pixelArea()
    .rename('area')
    .updateMask(maskImage)
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: roi,
      scale: 30,
      maxPixels: 1e13,
      tileScale: 4
    });
  print(label + ' 面积 km2', ee.Number(area.get('area')).divide(1e6));
}

printAreaKm2(floodMask, '洪水候选区');
printAreaKm2(floodCoreMask, '洪水核心区');
printAreaKm2(nonFloodCandidate, '非洪水候选区');

// =========================
// 6. 样本影像构建
// =========================

// 这里不再使用 stratifiedSample，避免 GEE 对 classBand 类型的限制。
// 改为洪水区和非洪水区分别 sample，再合并样本。
// label = 1 表示洪水点，label = 0 表示非洪水点。
var s1Projection = preMedian.projection();
var fillValue = -9999;

// 这些波段只是导出后做质检用，不应该因为自身掩膜导致样本点被丢弃。
// 因此先填充值，再由 floodMask / nonFloodCandidate 控制最终抽样范围。
var sampleS1Drop = s1Drop.unmask(fillValue).rename('s1_drop_db');
var samplePreS1 = preMedian.unmask(fillValue).rename('s1_pre_' + polarization);
var sampleFloodS1 = floodMedian.unmask(fillValue).rename('s1_flood_' + polarization);
var sampleSlope = slope.unmask(fillValue).rename('slope_deg');
var sampleSeasonality = seasonality.unmask(0).rename('jrc_seasonality');
var sampleOccurrence = occurrence.unmask(0).rename('jrc_occurrence');

function makeSampleImage(labelValue, candidateMask) {
  // 用 s1Drop 派生标签底图，而不是用纯常量影像，确保第一波段继承 Sentinel-1 网格。
  var labelBand = s1Drop.multiply(0)
    .add(labelValue)
    .toByte()
    .rename('label')
    .updateMask(candidateMask);

  var floodBand = labelBand
    .rename('flood')
    .updateMask(candidateMask);

  return labelBand
    .addBands(floodBand)
    .addBands(ee.Image.pixelLonLat())
    .addBands(sampleS1Drop)
    .addBands(samplePreS1)
    .addBands(sampleFloodS1)
    .addBands(sampleSlope)
    .addBands(sampleSeasonality)
    .addBands(sampleOccurrence)
    .updateMask(candidateMask)
    .clip(roi);
}

var floodSampleImage = makeSampleImage(1, floodCoreMask);
var nonFloodSampleImage = makeSampleImage(0, nonFloodCandidate);

print('洪水样本影像波段类型', floodSampleImage.bandTypes());
print('非洪水样本影像波段类型', nonFloodSampleImage.bandTypes());

function printCandidatePixelCount(maskImage, label) {
  var count = ee.Image.constant(1)
    .rename('count')
    .updateMask(maskImage)
    .reduceRegion({
      reducer: ee.Reducer.count(),
      geometry: roi,
      scale: sampleScaleForPointsMeters,
      maxPixels: 1e13,
      tileScale: 4
    });
  print(label + ' 可抽样像元数量', count.get('count'));
}

printCandidatePixelCount(floodMask, '洪水候选区');
printCandidatePixelCount(floodCoreMask, '洪水核心区');
printCandidatePixelCount(nonFloodCandidate, '非洪水候选区');

// =========================
// 7. 分区随机抽样
// =========================

// 不再使用 sample(numPixels=...)，因为它在复杂投影/掩膜下可能只返回很少样本。
// 这里先按 100 m 网格抽出候选区有效像元，再添加随机数、排序、截取目标数量。
var floodCandidateSamples = floodSampleImage.sample({
  region: roi,
  projection: s1Projection,
  scale: sampleScaleForPointsMeters,
  geometries: true,
  dropNulls: true,
  tileScale: 4
});

var nonFloodCandidateSamples = nonFloodSampleImage.sample({
  region: roi,
  projection: s1Projection,
  scale: sampleScaleForPointsMeters,
  geometries: true,
  dropNulls: true,
  tileScale: 4
});

print('洪水候选样本点总数', floodCandidateSamples.size());
print('非洪水候选样本点总数', nonFloodCandidateSamples.size());

var floodRawSamples = floodCandidateSamples
  .randomColumn('random', randomSeed)
  .sort('random')
  .limit(targetFloodSamples);

var nonFloodRawSamples = nonFloodCandidateSamples
  .randomColumn('random', randomSeed + 1)
  .sort('random')
  .limit(targetNonFloodSamples);

function addCommonProperties(feature, labelValue, sampleType) {
  return feature.set({
    label: labelValue,
    flood: labelValue,
    sample_type: sampleType,
    roi_name: 'roi_xiao',
    event_start: floodStart,
    event_end: floodEndInclusive,
    pre_start: preStart,
    pre_end: preEndInclusive,
    source: 'Sentinel-1 SAR change detection in Google Earth Engine',
    polarization: polarization,
    backscatter_drop_db: backscatterDropThresholdDb,
    smoothing_radius_m: smoothingRadiusMeters,
    slope_threshold_deg: maxSlopeDeg,
    flood_core_buffer_m: floodCoreBufferMeters,
    flood_edge_buffer_m: floodEdgeBufferMeters,
    sample_scale_m: sampleScaleForPointsMeters,
    random_seed: randomSeed
  });
}

var floodSamples = floodRawSamples.map(function(feature) {
  return addCommonProperties(feature, 1, 'flood');
});

var nonFloodSamples = nonFloodRawSamples.map(function(feature) {
  return addCommonProperties(feature, 0, 'nonflood');
});

var samplesWithProps = floodSamples.merge(nonFloodSamples);

print('实际洪水样本数量', floodSamples.size());
print('实际非洪水样本数量', nonFloodSamples.size());
print('合并样本预览', samplesWithProps.limit(10));

// =========================
// 8. 地图显示
// =========================

Map.addLayer(preMedian, {min: -25, max: 0}, '洪前 Sentinel-1 ' + polarization, false);
Map.addLayer(floodMedian, {min: -25, max: 0}, '洪期 Sentinel-1 ' + polarization, false);
Map.addLayer(s1Drop, {min: 0, max: 5, palette: ['white', 'cyan', 'blue']}, '后向散射下降 dB', false);
Map.addLayer(seasonality, {min: 0, max: 12, palette: ['white', 'lightblue', 'blue']}, 'JRC seasonality', false);
Map.addLayer(occurrence, {min: 0, max: 100, palette: ['white', 'lightblue', 'blue']}, 'JRC occurrence', false);
Map.addLayer(slope, {min: 0, max: 15, palette: ['white', 'orange', 'brown']}, '坡度', false);
Map.addLayer(nonFloodCandidate.updateMask(nonFloodCandidate), {palette: ['00aa00']}, '非洪水候选区', false);
Map.addLayer(floodBuffer.updateMask(floodBuffer), {palette: ['orange']}, '洪水边界缓冲区', false);
Map.addLayer(floodMask, {palette: ['red']}, '洪水候选区', true);
Map.addLayer(floodCoreMask, {palette: ['ff00ff']}, '洪水核心抽样区', true);
Map.addLayer(floodSamples, {color: 'red'}, '洪水样本点', false);
Map.addLayer(nonFloodSamples, {color: '00ff00'}, '非洪水样本点', false);

// =========================
// 9. 结果导出
// =========================

Export.image.toDrive({
  image: floodMask.unmask(0).toByte(),
  description: exportPrefix + '_flood_mask',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_flood_mask',
  region: roi,
  scale: 10,
  maxPixels: 1e13
});

Export.table.toDrive({
  collection: floodSamples,
  description: exportPrefix + '_flood_samples',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_flood_samples',
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: nonFloodSamples,
  description: exportPrefix + '_nonflood_samples',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_nonflood_samples',
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: samplesWithProps,
  description: exportPrefix + '_merged_samples',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_merged_samples',
  fileFormat: 'CSV'
});

// 同时导出 Shapefile，便于在 ArcGIS / QGIS 中直接查看样本点空间分布。
// GEE 的 SHP 导出会生成 .shp、.shx、.dbf、.prj 等多个文件，下载后需要放在同一文件夹。
Export.table.toDrive({
  collection: floodSamples,
  description: exportPrefix + '_flood_samples_shp',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_flood_samples',
  fileFormat: 'SHP'
});

Export.table.toDrive({
  collection: nonFloodSamples,
  description: exportPrefix + '_nonflood_samples_shp',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_nonflood_samples',
  fileFormat: 'SHP'
});

Export.table.toDrive({
  collection: samplesWithProps,
  description: exportPrefix + '_merged_samples_shp',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_merged_samples',
  fileFormat: 'SHP'
});
