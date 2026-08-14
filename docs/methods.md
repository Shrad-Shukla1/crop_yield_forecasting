# Methods documentation


## Goal of the project:
Investigate how well SIF correlates with sub-national crop yields in sub Saharan Africa (SSA), and how seasonal SIF can be used to predict the crop productivity in SSA. 

# Key references and summary:
1. He, L., Magney, T., Dutta, D., Yin, Y., Köhler, P., Grossmann, K., et al. (2020). From the ground to space: Using solar‐induced chlorophyll fluorescence to estimate crop productivity. Geophysical Research Letters, 47, e2020GL087474. https://doi.org/ 10.1029/2020GL087474

- The above study highlights the variation in SIF vs NPP/crop productivity relationship in C3 vs C4 crops. Typical C3 crops include soybeans, wheat, barley, oats, and rice, whereas typical C4 crops includecorn, sugarcane, and sorghum. The study shows that in the case of C4 crops, the relationship between SIF and crop productivity is more linear with steeper slope than in the case of C3 crops. The overall relationship in crop productivity and SIF is also based on the ratio of C3 or C4 crops in a sub-national unit. 
- The study also uses seasonally integrated SIF to predict crop yield. 
- Based on the results of the above study. I am planning to the do the following:
    - Calculate the correlation between seasonally aggregated SIF vs crop yield for Maize, Sorghum, Wheat and Millet crops in SSA countries.
    - Calculate the correlation between SIF max vs crop yield for Maize, Sorghum, Wheat and Millet crops in SSA countries.
    - Do the above two with Lu et al. vs IFPRI vs Crop specific masks (BEST mask) 
    - The above analysis will reveal how well remotely sensed SIF is correlated with crop yield for different C3 and C4 crops, and how senstivite is that correlation to how (a) growing season SIF is calculated and (b) how the SIF is masked. 
    - The script I am using for this is here: /home/chc-source/shrad/Scripts/Funded_projects/2026/crop_yield_forecasting/code/python/compile_yield_sif_ts.py
> 08/11/2026
- Today I will work on expanding the SIF vs crop yield correlation from only South Africa to all SSA countries for which 2003-2018 data is available. 
- I will implement the code such that it is easy to experiment with at least two different ways to get growing seasonal SIF which are (a) seasonally integrated SIF and (b) seasonal max SIF. 

### Disaggregating sub-national crop yield data with SIF data
> 07/14/2026

The goal of this project is to disaggregate sub-national yield data to pixel scale. A few main options to do so could be the following:
- Use SIF data to disaggregate sub-national crop yield data
- Use SPAM data to disaggregate sub-national crop yield data
- Use NDVI data to disaggregate sub-national crop yield data

## Things to explore
- How similars are the weights across pixels in a given sub-national unit as per SIF vs NDVI vs SPAM data. 

