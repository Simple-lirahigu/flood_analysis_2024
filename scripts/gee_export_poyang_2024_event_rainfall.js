/**** 2024 年鄱阳湖洪灾事件降水因子导出
 *
 * 目的：
 * - 使用 GEE 中的 CHIRPS 日降水数据，生成 2024-06-23 至 2024-07-06
 *   洪灾事件降水因子。
 * - 导出事件累计降水、最大 1 日降水和最大 3 日累计降水。
 *
 * 注意：
 * - CHIRPS 空间分辨率约 0.05 度，明显粗于你的 12.45 m 致灾因子。
 * - 导出的降水 TIF 需要再用本地脚本对齐到现有因子网格。
 * - 如果你后续使用 GPM IMERG，需要单独修改数据集和波段。
 ****/

// =========================
// 1. 参数区
// =========================

// TODO：替换为你的赣北研究区资产。
var ROI_ASSET = 'users/your_username/ganbei_roi';
var roi = ee.FeatureCollection(ROI_ASSET).geometry();

// GEE 的 filterDate 结束日期不包含当天，所以这里结束日期写到 2024-07-07。
var eventStart = '2024-06-23';
var eventEndExclusive = '2024-07-07';

var exportFolder = 'GEE_FLOOD_SAMPLES';
var exportPrefix = 'ganbei_poyang_20240623_0706_chirps';

Map.centerObject(roi, 8);
Map.addLayer(roi, {color: 'yellow'}, '赣北研究区', false);

// =========================
// 2. 读取 CHIRPS 日降水
// =========================

var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
  .filterBounds(roi)
  .filterDate(eventStart, eventEndExclusive)
  .select('precipitation');

print('CHIRPS 日影像数量', chirps.size());
print('CHIRPS 日期', chirps.aggregate_array('system:time_start')
  .map(function(time) {
    return ee.Date(time).format('YYYY-MM-dd');
  }));

// 事件累计降水，单位 mm。
var eventRain = chirps.sum()
  .rename('rain_event_mm')
  .clip(roi);

// 最大 1 日降水，单位 mm/day。
var max1dRain = chirps.max()
  .rename('rain_max_1d_mm')
  .clip(roi);

// 最大 3 日累计降水，单位 mm/3d。
var startDate = ee.Date(eventStart);
var endDate = ee.Date(eventEndExclusive);
var nDays = endDate.difference(startDate, 'day');
var startOffsets = ee.List.sequence(0, nDays.subtract(3));

var rolling3d = ee.ImageCollection.fromImages(
  startOffsets.map(function(offset) {
    offset = ee.Number(offset);
    var winStart = startDate.advance(offset, 'day');
    var winEnd = winStart.advance(3, 'day');
    return chirps
      .filterDate(winStart, winEnd)
      .sum()
      .rename('rain_3d_mm')
      .set('system:time_start', winStart.millis())
      .set('window_start', winStart.format('YYYY-MM-dd'))
      .set('window_end', winEnd.advance(-1, 'day').format('YYYY-MM-dd'));
  })
);

var max3dRain = rolling3d.max()
  .rename('rain_max_3d_mm')
  .clip(roi);

print('3 日滑动窗口数量', rolling3d.size());
print('3 日滑动窗口', rolling3d.aggregate_array('window_start'));

// 合并为多波段影像，便于一次导出。
var rainfallFactors = eventRain
  .addBands(max1dRain)
  .addBands(max3dRain)
  .toFloat();

// =========================
// 3. 地图显示
// =========================

Map.addLayer(eventRain, {
  min: 0,
  max: 300,
  palette: ['white', 'lightblue', 'blue', 'purple']
}, '事件累计降水 mm', true);

Map.addLayer(max1dRain, {
  min: 0,
  max: 120,
  palette: ['white', 'yellow', 'orange', 'red']
}, '最大 1 日降水 mm', false);

Map.addLayer(max3dRain, {
  min: 0,
  max: 200,
  palette: ['white', 'cyan', 'blue', 'purple']
}, '最大 3 日累计降水 mm', false);

// =========================
// 4. 导出
// =========================

// 导出多波段降水因子。后续用本地脚本对齐到现有 TIF 网格。
Export.image.toDrive({
  image: rainfallFactors,
  description: exportPrefix + '_rainfall_factors',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_rainfall_factors',
  region: roi,
  scale: 5566,
  crs: 'EPSG:4326',
  maxPixels: 1e13
});

// 单独导出事件累计降水，便于替换原 rainfall.tif。
Export.image.toDrive({
  image: eventRain.toFloat(),
  description: exportPrefix + '_event_rainfall',
  folder: exportFolder,
  fileNamePrefix: exportPrefix + '_event_rainfall',
  region: roi,
  scale: 5566,
  crs: 'EPSG:4326',
  maxPixels: 1e13
});
