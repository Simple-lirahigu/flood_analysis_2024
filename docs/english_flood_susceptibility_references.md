# English References for Flood Susceptibility Mapping and Sample Construction

检索与整理时间：2026-06-29  
用途：支撑 2024 年赣北/鄱阳湖洪灾洪水易发性预测研究，包括机器学习建模、洪水样本构建、Sentinel-1/GEE 洪水提取、降水与开放空间数据来源。

说明：以下为英文候选文献。正式写入论文前，应按学校参考文献格式核对卷期、页码、DOI 和作者全名。

## 1. Flood Susceptibility Mapping / Machine Learning

1. Arora, A., Arabameri, A., Pandey, M., Siddiqui, M. A., Shukla, U. K., Bui, D. T., & Bhardwaj, A. (2021). Optimization of state-of-the-art fuzzy-metaheuristic ANFIS-based machine learning models for flood susceptibility prediction mapping in the Middle Ganga Plain, India. *Science of the Total Environment*, 750, 141565. https://doi.org/10.1016/j.scitotenv.2020.141565
   - 用途：机器学习洪水易发性预测、模型优化、AUC/精度评价。

2. Bui, D. T., Hoang, N. D., Martínez-Álvarez, F., Ngo, P. T. T., Hoa, P. V., Pham, T. D., & Costache, R. (2020). A novel deep learning neural network approach for predicting flash flood susceptibility: A case study at a high frequency tropical storm area. *Science of the Total Environment*, 701, 134413. https://doi.org/10.1016/j.scitotenv.2019.134413
   - 用途：深度学习/神经网络洪水易发性预测，可作为 ANN/LSTM/CNN 类模型参考。

3. Termeh, S. V. R., Kornejady, A., Pourghasemi, H. R., & Keesstra, S. (2018). Flood susceptibility mapping using novel ensembles of adaptive neuro fuzzy inference system and metaheuristic algorithms. *Science of the Total Environment*, 615, 438-451. https://doi.org/10.1016/j.scitotenv.2017.09.262
   - 用途：洪水易发性集成模型、影响因子体系和精度评价参考。

4. Mahmoud, S. H., & Gan, T. Y. (2018). Urbanization and climate change implications in flood risk management: Developing an efficient decision support system for flood susceptibility mapping. *Science of the Total Environment*, 636, 152-167. https://doi.org/10.1016/j.scitotenv.2018.04.282
   - 用途：洪水易发性制图与风险管理、城市化和气候变化背景。

5. Urban flood susceptibility mapping using frequency ratio and multiple decision tree-based machine learning models. *Natural Hazards*. https://doi.org/10.1007/s11069-024-06609-x
   - 用途：频率比与多决策树机器学习方法，适合对照中文“逆频率比采样方法”。
   - 注意：作者、卷期页码需进一步核验。

## 2. Flood Inventory / Flood and Non-flood Sample Construction

6. Tellman, B., Sullivan, J. A., Kuhn, C., et al. (2021). Satellite imaging reveals increased proportion of population exposed to floods. *Nature*, 596, 80-86. https://doi.org/10.1038/s41586-021-03695-w
   - 用途：全球洪水事件数据库、卫星观测洪水范围、洪水暴露分析。
   - 可用于说明遥感洪水清单可作为洪水样本/洪水范围数据来源。

7. DeVries, B., Huang, C., Armston, J., Huang, W., Jones, J. W., & Lang, M. W. (2020). Rapid and robust monitoring of flood events using Sentinel-1 and Landsat data on the Google Earth Engine. *Remote Sensing of Environment*, 240, 111664. https://doi.org/10.1016/j.rse.2020.111664
   - 用途：Sentinel-1 与 Landsat 在 GEE 中快速洪水监测；适合支撑洪水样本提取流程。

8. Clement, M. A., Kilsby, C. G., & Moore, P. (2018). Multi-temporal synthetic aperture radar flood mapping using change detection. *Journal of Flood Risk Management*, 11(2), 152-168. https://doi.org/10.1111/jfr3.12303
   - 用途：多时相 SAR 变化检测洪水制图；支撑洪前/洪期差异法。

9. Twele, A., Cao, W., Plank, S., & Martinis, S. (2016). Sentinel-1-based flood mapping: A fully automated processing chain. *International Journal of Remote Sensing*, 37(13), 2990-3004. https://doi.org/10.1080/01431161.2016.1192304
   - 用途：Sentinel-1 自动化洪水制图流程；适合支撑 SAR 洪水样本构建。

10. Martinis, S., Kuenzer, C., Wendleder, A., Huth, J., Twele, A., Roth, A., & Dech, S. (2015). Comparing four operational SAR-based water and flood detection approaches. *International Journal of Remote Sensing*, 36(13), 3519-3543. https://doi.org/10.1080/01431161.2015.1060647
    - 用途：SAR 水体/洪水检测方法比较；用于说明阈值、误差来源和方法选择。

## 3. Sentinel-1 / Google Earth Engine Flood Mapping

11. Tripathy, P., & Malladi, T. (2022). Global Flood Mapper: A novel Google Earth Engine application for rapid flood mapping using Sentinel-1 SAR. *Natural Hazards*, 114, 1341-1363. https://doi.org/10.1007/s11069-022-05428-2
    - 用途：GEE + Sentinel-1 快速洪水制图；文中使用坡度/高程等掩膜减少山区误判，与你的样本提取脚本逻辑接近。

12. Tiwari, V., Kumar, V., Matin, M. A., Thapa, A., Ellenburg, W. L., Gupta, N., & Thapa, S. (2020). Flood inundation mapping-Kerala 2018; Harnessing the power of SAR, automatic threshold detection method and Google Earth Engine. *PLOS ONE*, 15(8), e0237324. https://doi.org/10.1371/journal.pone.0237324
    - 用途：SAR、自动阈值和 GEE 洪水淹没制图。

13. Singha, M., Dong, J., Sarmah, S., You, N., Zhou, Y., Zhang, G., Doughty, R., & Xiao, X. (2020). Identifying floods and flood-affected paddy rice fields in Bangladesh based on Sentinel-1 imagery and Google Earth Engine. *ISPRS Journal of Photogrammetry and Remote Sensing*, 166, 278-293. https://doi.org/10.1016/j.isprsjprs.2020.06.011
    - 用途：稻田区洪水识别；对鄱阳湖周边稻田/湿地误判讨论有参考价值。

14. Gorelick, N., Hancher, M., Dixon, M., Ilyushchenko, S., Thau, D., & Moore, R. (2017). Google Earth Engine: Planetary-scale geospatial analysis for everyone. *Remote Sensing of Environment*, 202, 18-27. https://doi.org/10.1016/j.rse.2017.06.031
    - 用途：引用 GEE 平台本身。

## 4. Open Spatial Datasets and Conditioning Factors

15. Pekel, J. F., Cottam, A., Gorelick, N., & Belward, A. S. (2016). High-resolution mapping of global surface water and its long-term changes. *Nature*, 540, 418-422. https://doi.org/10.1038/nature20584
    - 用途：JRC Global Surface Water 数据集；支撑永久水体/季节性水体剔除。

16. Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., Verdin, J., Shukla, S., Husak, G., Rowland, J., Harrison, L., Hoell, A., & Michaelsen, J. (2015). The climate hazards infrared precipitation with stations-a new environmental record for monitoring extremes. *Scientific Data*, 2, 150066. https://doi.org/10.1038/sdata.2015.66
    - 用途：CHIRPS 降水数据集；支撑 2024 年事件降水因子。

17. Farr, T. G., Rosen, P. A., Caro, E., Crippen, R., Duren, R., Hensley, S., Kobrick, M., et al. (2007). The Shuttle Radar Topography Mission. *Reviews of Geophysics*, 45(2), RG2004. https://doi.org/10.1029/2005RG000183
    - 用途：SRTM DEM 数据；支撑高程、坡度、坡向等地形因子。

18. Yamazaki, D., Ikeshima, D., Sosa, J., Bates, P. D., Allen, G. H., & Pavelsky, T. M. (2019). MERIT Hydro: A high-resolution global hydrography map based on latest topography dataset. *Water Resources Research*, 55(6), 5053-5073. https://doi.org/10.1029/2019WR024873
    - 用途：河网、水文地形因子、HAND/河流距离等。

## 5. Flood Risk / Background

19. Hirabayashi, Y., Mahendran, R., Koirala, S., Konoshima, L., Yamazaki, D., Watanabe, S., & Kanae, S. (2013). Global flood risk under climate change. *Nature Climate Change*, 3, 816-821. https://doi.org/10.1038/nclimate1911
    - 用途：气候变化背景下洪水风险增加。

20. Milly, P. C. D., Wetherald, R. T., Dunne, K. A., & Delworth, T. L. (2002). Increasing risk of great floods in a changing climate. *Nature*, 415, 514-517. https://doi.org/10.1038/415514a
    - 用途：洪水风险与气候变化背景。

## 6. Suggested Citation Use in This Thesis

- 研究背景：Tellman et al. (2021), Hirabayashi et al. (2013), Milly et al. (2002)
- GEE 平台：Gorelick et al. (2017)
- Sentinel-1 洪水提取：Tripathy & Malladi (2022), DeVries et al. (2020), Tiwari et al. (2020), Twele et al. (2016)
- 样本点/洪水清单构建：Tellman et al. (2021), DeVries et al. (2020), Clement et al. (2018), Martinis et al. (2015)
- 永久水体剔除：Pekel et al. (2016)
- 降水因子：Funk et al. (2015)
- 地形和水文因子：Farr et al. (2007), Yamazaki et al. (2019)
- 机器学习易发性模型：Arora et al. (2021), Bui et al. (2020), Termeh et al. (2018), Mahmoud & Gan (2018)
