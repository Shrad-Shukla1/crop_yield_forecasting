# Methodology for compiling seasonal SIF and crop yield for each of the sub-national units 

1. **Crop mask**
   - At first we reproject crop masks to the grid of the SIF data. The reporjection is done so that overall area is conserved. 
   - We work with two types of crop masks:
      -  The first crop mask (Lu et al., represents all crops)
      - The second set of crop mask is crop specific. This comes from GeoGLAM, known as BEST crop mask. These are available for Wheat, Rice, Soybean and Maize. 

2. **Spatially aggregated seasonal SIF**
   - We use fusion_SCIAMACHY_GOME-2 SIF monthly data 
   - For any given admin unit we first subset gridded SIF data using admin shapefile.
   - For a given crop and the admin unit we then extract *planting year, month, harvesting year and month*. We assume the time period between reported planting month and harvest month to be representative of the growing season and use that period to temporally subset SIF data.
   - We then take the seasonal average of SIF data over the growing season which we consider as seasonal SIF. 
   - Finally we choose three differen stategy to screen and spatially aggregate seasonal SIF over a given admin unit
      - **No mask**: In first case, we consider all of the pixels in a given admin unit and take spatial average of seasonal SIF across all pixels.
      - **All crop mask**: In this case we only select pixels where Lu et al., crop layer shows >10% fractional cropped area.
      - **Crop specific mask**: In this case instead of an all crop layer we use crop type specific mask (e.g. Maize, Wheat, Soybean and Rice) for masking ut SIF data.
   - Spatial aggregation of seasonal SIF data then leads to time-series of SIF data for admin unit, crop to compare with reported crop yield