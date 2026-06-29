/**** 2024 年鄱阳湖 / 赣北洪灾样本点提取
 *
 * 目的：
 * - 使用 Google Earth Engine 中的 Sentinel-1 SAR 数据，提取 2024-06-23 至
 *   2024-07-06 鄱阳湖洪灾事件的洪水 / 非洪水样本点。
 * - 导出二值洪水栅格和平衡样本点，供后续洪水易发性建模使用。
 *
 * 需要用户修改：
 * - 将 ROI_ASSET 替换为你上传到 GEE 的赣北研究区资产路径。
 *
 * 注意：
 * - 阈值必须结合 Sentinel-2、高清底图、水位记录或新闻/实地洪水位置目视校准。
 * - 本脚本使用 dB 后向散射下降阈值。开阔水体淹没后通常后向散射降低，
 *   但城市、稻田、湿地、阴影和湿土可能造成误判。
 ****/

// =========================
// 1. 参数区
// =========================

// TODO：替换为你的赣北研究区资产。
// 示例：'users/your_name/ganbei_roi'
var ROI_ASSET = 'users/your_username/ganbei_roi';
var roi = ee.FeatureCollection(ROI_ASSET).geometry();

// 用户确定的洪灾事件窗口。
var floodStart = '2024-06-23';
var floodEnd = '2024-07-06';

// 洪前参考窗口。如果该时段已经偏湿或存在明显涨水，应改到更早的稳定无洪水时段。
var preStart = '2024-06-01';
var preEnd = '2024-06-15';

// Sentinel-1 参数。
// 默认使用 VV 极化，和已阅读论文的方法更接近；也可以改成 'VH' 做敏感性对比。
var polarization = 'VV';
// 建议正式实验固定轨道方向，避免升轨/降轨混合造成几何差异。
// 可设置为 'ASCENDING'、'DESCENDING' 或 null。若为 null，脚本会同时使用两种轨道。
var orbitPass = null;

// 洪水提取参数。
var smoothingRadiusMeters = 50;
// 洪期相对洪前的 dB 下降阈值。该值必须在 GEE 中目视校准，不要直接当作最终阈值。
var backscatterDropThresholdDb = 1.5;
var maxSlopeDeg = 5;
var permanentWaterSeasonalityMonths = 10;
var minConnectedPixels = 8;
// 非洪水样本需要避开洪水边界不确定区。值越大，非洪水点越保守。
var floodEdgeBufferMeters = 90;
// 非洪水样本避开常见水面和季节性水面，降低把湖洲、湿地、水田当成稳定非洪水点的风险。
var nonFloodMaxWaterOccurrence = 20;

// 样本参数。
var sampleScale = 10;
var floodSampleCount = 2000;
var nonFloodSampleCount = 2000;
var randomSeed = 20240706;

// 导出参数。
var exportFolder = 'GEE_FLOOD_SAMPLES';
var exportPrefix = 'ganbei_poyang_20240623_0706';

Map.centerObject(roi, 8);
Map.addLayer(roi, {color: 'yellow'}, 'Ganbei ROI', false);

// =========================
// 2. Sentinel-1 预处理
// =========================

function getS1(startDate, endDate) {
  var collection = ee.ImageCollection('COPERNICUS/S1_GRD')
    .filterBounds(roi)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .filter(ee.Filter.eq('resolution_meters', 10))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', polarization))
    .select(polarization);

  if (orbitPass !== null) {
    collection = collection.filter(ee.Filter.eq('orbitProperties_pass', orbitPass));
  }

  return collection;
}

var preCol = getS1(preStart, preEnd);
var floodCol = getS1(floodStart, floodEnd);

print('Pre-flood Sentinel-1 count', preCol.size());
print('Flood-period Sentinel-1 count', floodCol.size());
print('Pre-flood orbit passes', preCol.aggregate_histogram('orbitProperties_pass'));
print('Flood-period orbit passes', floodCol.aggregate_histogram('orbitProperties_pass'));
print('Pre-flood images', preCol.aggregate_array('system:index'));
print('Flood-period images', floodCol.aggregate_array('system:index'));

var preMedian = preCol.median().clip(roi);
var floodMedian = floodCol.median().clip(roi);

// 中值滤波用于抑制 SAR 斑点噪声，但会平滑窄河道和小斑块。
var preSmooth = preMedian.focal_median({
  radius: smoothingRadiusMeters,
  units: 'meters'
});
var floodSmooth = floodMedian.focal_median({
  radius: smoothingRadiusMeters,
  units: 'meters'
});

// 正值表示洪期后向散射低于洪前，通常对应新增水体或湿润区域。
var s1Drop = preSmooth.subtract(floodSmooth).rename('s1_drop_db');

// =========================
// 3. 误差来源掩膜
// =========================

// 使用 JRC Global Surface Water 去除常年水体。
var seasonality = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
  .select('seasonality')
  .clip(roi);
var nonPermanentWater = seasonality.lt(permanentWaterSeasonalityMonths);

// water occurrence 用于约束非洪水样本，避免非洪水点落在湖泊、湿地和常见水面上。
var occurrence = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
  .select('occurrence')
  .clip(roi);
var stableNonWater = occurrence.lte(nonFloodMaxWaterOccurrence);

// 去除陡坡区域，降低地形阴影和雷达几何畸变导致的误判。
var dem = ee.Image('USGS/SRTMGL1_003').clip(roi);
var slope = ee.Terrain.slope(dem).rename('slope_deg');
var lowSlope = slope.lte(maxSlopeDeg);

// 洪水候选像元。
var rawFlood = s1Drop.gt(backscatterDropThresholdDb)
  .and(nonPermanentWater)
  .and(lowSlope)
  .rename('flood');

// 去除孤立噪声斑块。
var connected = rawFlood.connectedPixelCount(100, true);
var floodMask = rawFlood
  .updateMask(rawFlood)
  .updateMask(connected.gte(minConnectedPixels))
  .rename('flood');

// 扩张洪水掩膜，形成边界缓冲区；非洪水样本不从边界附近抽取。
var floodBuffer = floodMask.unmask(0)
  .focal_max({
    radius: floodEdgeBufferMeters,
    units: 'meters'
  })
  .rename('flood_buffer');

// 保守非洪水候选区：
// - 不属于洪水掩膜及其边界缓冲区；
// - 不属于永久水体或高频水面；
// - 坡度较低；
// - 洪前和洪期 Sentinel-1 均有有效观测。
var validS1 = preMedian.mask().and(floodMedian.mask());
var nonFloodMask = floodBuffer.eq(0)
  .and(nonPermanentWater)
  .and(stableNonWater)
  .and(lowSlope)
  .and(validS1)
  .rename('flood');

// 二值标签影像，用于分层抽样。
// flood = 1 表示洪水像元，flood = 0 表示保守非洪水候选像元。
var labelImage = ee.Image(0).rename('flood')
  .where(floodMask.unmask(0).eq(1), 1)
  .updateMask(floodMask.unmask(0).eq(1).or(nonFloodMask.eq(1)))
  .clip(roi);

// 添加诊断波段，导出样本点时一并保留，便于后续质量检查。
var sampleImage = labelImage
  .addBands(ee.Image.pixelLonLat())
  .addBands(s1Drop)
  .addBands(preMedian.rename('s1_pre_' + polarization))
  .addBands(floodMedian.rename('s1_flood_' + polarization))
  .addBands(slope)
  .addBands(seasonality.rename('jrc_seasonality'))
  .addBands(occurrence.rename('jrc_occurrence'));

// =========================
// 4. 样本点抽取
// =========================

var samples = sampleImage.stratifiedSample({
  numPoints: 0,
  classBand: 'flood',
  classValues: [1, 0],
  classPoints: [floodSampleCount, nonFloodSampleCount],
  region: roi,
  scale: sampleScale,
  seed: randomSeed,
  geometries: true,
  tileScale: 4
});

var floodSamples = samples.filter(ee.Filter.eq('flood', 1));
var nonFloodSamples = samples.filter(ee.Filter.eq('flood', 0));

print('Flood samples', floodSamples.size());
print('Non-flood samples', nonFloodSamples.size());
print('Merged samples preview', samples.limit(10));

// =========================
// 5. 地图显示
// =========================

Map.addLayer(preMedian, {min: -25, max: 0}, 'S1 pre-flood ' + polarization, false);
Map.addLayer(floodMedian, {min: -25, max: 0}, 'S1 flood-period ' + polarization, false);
Map.addLayer(s1Drop, {min: 0, max: 5, palette: ['white', 'cyan', 'blue']}, 'S1 drop dB', false);
Map.addLayer(seasonality, {min: 0, max: 12, palette: ['white', 'lightblue', 'blue']}, 'JRC seasonality', false);
Map.addLayer(floodBuffer.updateMask(floodBuffer), {palette: ['orange']}, 'Flood edge buffer', false);
Map.addLayer(floodMask, {palette: ['red']}, 'Detected flood mask', true);
Map.addLayer(floodSamples, {color: 'red'}, 'Flood sample points', false);
Map.addLayer(nonFloodSamples, {color: '00ff00'}, 'Non-flood sample points', false);

// =========================
// 6. 结果导出
// =========================

Export.image.toDrive({
  image: floodMask.unmask(0).toByte(),
  description: exportPrefix + '_flood_mask',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_flood_mask',
  region: roi,
  scale: sampleScale,
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
  collection: samples,
  description: exportPrefix + '_merged_samples',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_merged_samples',
  fileFormat: 'CSV'
});
